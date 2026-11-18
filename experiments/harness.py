"""
experiments/harness.py — the one place every experiment is run from, so all comparisons are fair.

What it does, in order:
  1. loads the training records once (`load_cached`) and checks no hold-out record is in them
  2. runs stages 2+3 (preprocess + features) once per config and CACHES the feature matrix —
     changing only the classifier then costs seconds, not a re-extraction
  3. evaluates with REPEATED, STRATIFIED, record-grouped 5-fold CV (5 repeats = 25 folds).
     Every pipeline sees exactly the same 25 train/test splits, so two pipelines can be compared
     fold by fold (a *paired* comparison), and the repeat-to-repeat wobble gives the noise floor.
     Selection, scaling, resampling and the classifier are all fit inside the training fold.
  4. reports the full panel: macro-F1 (4-class, the course metric) ± SD over folds, Cohen's κ,
     the Challenge's own score F1(N,A,O), per-class F1 and recall, and a confusion matrix.

Usage from the other scripts:  H = Harness(data_dir); res = H.run(cfg); H.compare(res, ref)
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tracks"))

from adapter import cached, data_fingerprint, _transform        # noqa: E402
from ecg_team import ECGTeamTrack, FEATURE_VERSION               # noqa: E402

CLASSES = ["N", "A", "O", "~"]
N_SPLITS, N_REPEATS = 5, 5
PREPROCESS_KEYS = ("preprocess", "ecg_band", "notch", "wavelet", "wavelet_level", "wavelet_mode",
                   "impulsive", "baseline", "powerline", "broadband", "hp_fc", "f0", "q", "win",
                   "causal")
FEATURE_KEYS = PREPROCESS_KEYS + ("qrs", "feature_set", "quality_on", "spectral_method",
                                  "ar_order", "mt_bandwidth")


def _metrics(yt, yp):
    from sklearn.metrics import f1_score, cohen_kappa_score, recall_score
    f1c = f1_score(yt, yp, labels=CLASSES, average=None, zero_division=0)
    rec = recall_score(yt, yp, labels=CLASSES, average=None, zero_division=0)
    return {"macro_f1": float(np.mean(f1c)), "kappa": float(cohen_kappa_score(yt, yp)),
            "f1_NAO": float(np.mean(f1c[:3])),
            **{f"f1_{c}": float(v) for c, v in zip(CLASSES, f1c)},
            **{f"rec_{c}": float(v) for c, v in zip(CLASSES, rec)}}


class Harness:
    def __init__(self, data_dir, cache_dir=None, n_jobs=-1, verbose=True):
        self.data_dir = data_dir
        self.cache_dir = cache_dir or os.path.join(data_dir, "_feature_cache")
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.trk = ECGTeamTrack()
        self.recs = self.trk.load_cached(data_dir)
        self.trk.assert_no_holdout(self.recs)          # hold-out records must never be in here
        self.y = np.array([r.labels[0] for r in self.recs])
        self.groups = np.array([r.group for r in self.recs])
        self.fingerprint = data_fingerprint(data_dir)
        self.counts = {c: int(np.sum(self.y == c)) for c in CLASSES}
        if verbose:
            print(f"[harness] {len(self.recs)} training records {self.counts}")

    # ---- stages 2 + 3, cached ----
    def features(self, cfg):
        fcfg = {k: cfg[k] for k in FEATURE_KEYS if k in cfg}
        key = {"step": "features", "version": FEATURE_VERSION, "cfg": fcfg, "data": self.fingerprint}
        trk = ECGTeamTrack(cfg=fcfg)

        def compute():
            from joblib import Parallel, delayed
            out = Parallel(n_jobs=self.n_jobs)(
                delayed(_one)(trk, r, fcfg) for r in self.recs)
            return np.vstack(out)
        X = cached("features", key, compute, self.cache_dir)
        return X, trk.feature_names(fcfg)

    def folds(self):
        """The same 25 record-grouped, class-stratified splits for every pipeline."""
        from sklearn.model_selection import StratifiedGroupKFold
        out = []
        for rep in range(N_REPEATS):
            cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=rep)
            for tr, te in cv.split(np.zeros(len(self.y)), self.y, self.groups):
                assert not set(self.groups[tr]) & set(self.groups[te]), "record leak"
                out.append((rep, tr, te))
        return out

    # ---- stages 4 + 5 inside every fold ----
    def run(self, cfg, name=""):
        from sklearn.base import clone
        t0 = time.time()
        X, names = self.features(cfg)
        trk = ECGTeamTrack(cfg=cfg)
        clf0 = trk._baseline(cfg)
        per_fold, conf = [], np.zeros((4, 4), int)
        from sklearn.metrics import confusion_matrix
        pooled = {rep: ([], []) for rep in range(N_REPEATS)}
        for rep, tr, te in self.folds():
            sel = trk.select_features(X[tr], self.y[tr], cfg)
            clf = clone(clf0).fit(_transform(sel, X[tr]), self.y[tr])
            yp = clf.predict(_transform(sel, X[te]))
            per_fold.append(_metrics(self.y[te], yp))
            pooled[rep][0].extend(self.y[te]); pooled[rep][1].extend(yp)
            if rep == 0:
                conf += confusion_matrix(self.y[te], yp, labels=CLASSES)
        rep_means = [_metrics(*pooled[r])["macro_f1"] for r in range(N_REPEATS)]
        keys = per_fold[0].keys()
        res = {"name": name, "cfg": cfg, "n_records": len(self.y), "counts": self.counts,
               "n_features": X.shape[1], "feature_names": names,
               "mean": {k: float(np.mean([f[k] for f in per_fold])) for k in keys},
               "sd": {k: float(np.std([f[k] for f in per_fold], ddof=1)) for k in keys},
               "fold_macro_f1": [f["macro_f1"] for f in per_fold],
               "repeat_pooled_macro_f1": rep_means,
               "confusion_rep0": conf.tolist(), "seconds": round(time.time() - t0, 1)}
        if self.verbose:
            print(self.line(res))
        return res

    @staticmethod
    def line(r):
        m, s = r["mean"], r["sd"]
        return (f"{r['name']:<38} macroF1 {m['macro_f1']:.3f} ± {s['macro_f1']:.3f} | κ {m['kappa']:.3f}"
                f" | F1(NAO) {m['f1_NAO']:.3f} | F1 N {m['f1_N']:.2f} A {m['f1_A']:.2f} "
                f"O {m['f1_O']:.2f} ~ {m['f1_~']:.2f} | {r['n_features']} feats, {r['seconds']} s")

    @staticmethod
    def compare(new, ref):
        """Paired comparison on the same 25 folds. 'Real' needs the mean gain to exceed both the
        noise floor (the SD of the reference over its 5 repeats, i.e. what changes when nothing
        changes but the fold seed) and twice the standard error of the paired differences."""
        d = np.array(new["fold_macro_f1"]) - np.array(ref["fold_macro_f1"])
        se = d.std(ddof=1) / np.sqrt(len(d))
        noise = float(np.std(ref["repeat_pooled_macro_f1"], ddof=1))
        verdict = ("real gain" if d.mean() > max(2 * se, noise)
                   else "real loss" if d.mean() < -max(2 * se, noise)
                   else "no detectable difference")
        return {"delta": float(d.mean()), "delta_sd": float(d.std(ddof=1)), "se": float(se),
                "noise_floor": noise, "wins": int(np.sum(d > 0)), "n": len(d), "verdict": verdict}


def _one(trk, rec, cfg):
    return trk.extract_features(trk.preprocess(rec, cfg), cfg)[0]


def save(res, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(res, f, indent=1, default=str)
