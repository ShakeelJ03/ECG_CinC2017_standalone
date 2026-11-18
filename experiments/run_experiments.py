"""
experiments/run_experiments.py — the whole iteration plan, one change at a time.

    python experiments/run_experiments.py --data data_cache/ecg_cinc2017 --tag dev431
    python experiments/run_experiments.py --data C:/cm2013_data/ecg/train --tag full2000 --set final
    python experiments/run_experiments.py --data ... --only E02 E03a

Each experiment changes ONE thing against a named reference experiment, and is scored on the same
25 record-grouped folds (see harness.py). Results go to results/<tag>/<id>.json, and a table
ready to paste into RESULTS.md goes to results/<tag>/table.md.

Decision rule, fixed BEFORE running (the "comparison budget" of results_log_TEMPLATE.md):
a change is kept only if the harness calls it a "real gain" (mean paired gain larger than both
twice its standard error and the noise floor); otherwise we keep the simpler option.
"""
from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import Harness, save                     # noqa: E402

BP = {"preprocess": "bandpass", "ecg_band": (0.5, 40.0), "notch": 50.0}
DN = {"preprocess": "denoise", "impulsive": "median", "baseline": "highpass", "hp_fc": 0.5,
      "powerline": "notch"}
PT = {"qrs": "pt"}
RR = {"qrs": "pt", "feature_set": "base+rr"}
ALL = {"qrs": "pt", "feature_set": "base+rr+morph+sqi+env+wav"}

# id, stage, reference id, cfg, what changes and why (the hypothesis)
PLAN = [
    ("E00", "baseline", None, {},
     "supplied baseline unchanged (11 features, RF, class weights) — the floor"),
    ("E01a", "2 preprocess", "E00", BP,
     "0.5–40 Hz band-pass + 50 Hz notch: removes wander/hum, may blunt the QRS"),
    ("E01b", "2 preprocess", "E00", {"preprocess": "wavelet"},
     "db4 wavelet denoising: removes transients without a fixed band"),
    ("E01c", "2 preprocess", "E00", DN,
     "per-noise-type denoise (median → high-pass 0.5 Hz → notch)"),
    ("E02", "3 QRS detection", "E00", PT,
     "Pan–Tompkins with adaptive thresholds + search-back instead of one global 30 % threshold"),
    ("E03a", "3 features", "E02", {"qrs": "pt", "feature_set": "base+rr"},
     "+21 rhythm features (Poincaré, sample entropy/COSEn, Lorenz plot, ΔRR autocorrelation)"),
    ("E03b", "3 features", "E02", {"qrs": "pt", "feature_set": "base+morph"},
     "+11 morphology features (template correlation, QRS width, P wave, QRST-cancelled atrial activity)"),
    ("E03c", "3 features", "E02", {"qrs": "pt", "feature_set": "base+sqi"},
     "+9 signal-quality indices (bSQI detector agreement, spectral entropy, clipping, RMS bursts)"),
    ("E03d", "3 features", "E02", {"qrs": "pt", "feature_set": "base+wav"},
     "+7 db4 wavelet sub-band energies (second feature domain)"),
    ("E03e", "3 features", "E02", {"qrs": "pt", "feature_set": "base+env"},
     "+3 Hilbert-envelope periodicity features (rhythm regularity without a beat detector)"),
    ("E04", "3 features", "E03a", {"qrs": "pt", "feature_set": "base+rr+morph"},
     "morphology on top of the rhythm features"),
    ("E05", "3 features", "E03a", ALL,
     "every feature group together (62 features)"),
    ("E06", "3 spectral", "E03a", {**RR, "spectral_method": "ar"},
     "parametric AR spectrum instead of Welch for the band-power features"),
    ("E07a", "5 classifier", "E03a", {**RR, "clf": "hgb"},
     "gradient boosting instead of random forest"),
    ("E07b", "5 classifier", "E03a", {**RR, "clf": "svm"},
     "RBF-SVM (scaled) instead of random forest"),
    ("E08a", "5 imbalance", "E03a", {**RR, "imbalance": "none"},
     "no class weights: does the minority-class handling matter?"),
    ("E08b", "5 imbalance", "E03a", {**RR, "imbalance": "smote"},
     "SMOTE inside the fold instead of class weights"),
    ("E09", "4 selection", "E05", {**ALL, "select": "mutual_info", "select_k": 25},
     "keep the 25 most informative of 62 features (fit inside each fold)"),
    ("E10", "2 preprocess (revisit)", "E03a", {**RR, **DN},
     "REVISIT E01c: is denoising still harmful once the detector is robust?"),
    ("E11", "2 preprocess (revisit)", "E10", {**RR, **DN, "quality_on": "raw"},
     "REVISIT: denoise for rhythm, but quality features from the raw strip"),
    ("E12", "3 QRS (revisit)", "E03a", {"feature_set": "base+rr"},
     "REVISIT E02: the rhythm features with the supplied detector — how much rests on R-peaks?"),
]

#: the short list to re-run on the large (~2,000-record) training set for the final comparison
FINAL_SET = ["E00", "E02", "E03a", "E04", "E05", "E07a", "E07b", "E10"]


def _commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:                                  # noqa: BLE001
        return "uncommitted"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder with the training records")
    ap.add_argument("--tag", required=True, help="name for this data set, e.g. dev431 / full2000")
    ap.add_argument("--set", choices=["all", "final"], default="all")
    ap.add_argument("--only", nargs="*", help="run only these ids (their references run too)")
    args = ap.parse_args()

    plan = {p[0]: p for p in PLAN}
    want = args.only or (FINAL_SET if args.set == "final" else [p[0] for p in PLAN])
    order, seen = [], set()

    def need(i):
        ref = plan[i][2]
        if ref and ref not in seen:
            need(ref)
        if i not in seen:
            seen.add(i); order.append(i)
    for i in want:
        need(i)

    H = Harness(args.data)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "results", args.tag)
    res = {}
    today, commit = datetime.date.today().isoformat(), _commit()
    for i in order:
        _, stage, ref, cfg, why = plan[i]
        r = H.run({**cfg, "seed": 0}, name=f"{i} {stage}")
        r.update({"id": i, "stage": stage, "ref": ref, "why": why, "date": today, "commit": commit,
                  "data": args.data, "n_records": len(H.y)})
        if ref and ref in res:
            r["vs_ref"] = H.compare(r, res[ref])
            v = r["vs_ref"]
            print(f"    vs {ref}: Δ macro-F1 {v['delta']:+.3f} (SE {v['se']:.3f}, noise floor "
                  f"{v['noise_floor']:.3f}), better in {v['wins']}/{v['n']} folds → {v['verdict']}")
        res[i] = r
        save(r, os.path.join(out_dir, f"{i}.json"))
    write_table(out_dir, args.data, H)


def write_table(out_dir, data, H):
    """Rebuild table.md from EVERY result saved under this tag (not only this run), in plan
    order, so running a few experiments with --only never wipes the other rows."""
    import glob
    import json
    saved = {}
    for p in glob.glob(os.path.join(out_dir, "E*.json")):
        with open(p, encoding="utf-8") as f:
            r = json.load(f)
        saved[r.get("id", os.path.basename(p)[:-5])] = r
    rows = []
    for i in [p[0] for p in PLAN if p[0] in saved]:
        r = saved[i]
        m, s = r["mean"], r["sd"]
        lo, hi = min(r["fold_macro_f1"]), max(r["fold_macro_f1"])
        metric = (f"macro-F1 {m['macro_f1']:.3f} (sd {s['macro_f1']:.3f}, range {lo:.2f}–{hi:.2f} "
                  f"across 25 record-grouped folds); κ {m['kappa']:.3f}; F1 N/A/O/~ "
                  f"{m['f1_N']:.2f}/{m['f1_A']:.2f}/{m['f1_O']:.2f}/{m['f1_~']:.2f}")
        v = r.get("vs_ref")
        better = "— (baseline)" if not v else (
            f"vs {r['ref']}: Δ {v['delta']:+.3f}, {v['wins']}/25 folds — **{v['verdict']}**")
        rows.append(f"| {i} | {r.get('date', '?')} | {r['why']} | {metric} | {better} |  "
                    f"| `{r.get('commit', '?')}` |")
    hdr = (f"Data: `{data}` — {H.counts} ({len(H.y)} records). Split unit: record. "
           f"Configurations compared: {len(rows)}.\n\n"
           "| # | Date | What changed & why | Primary metric with spread | Better than reference? "
           "| If not — why kept | Commit |\n|---|---|---|---|---|---|---|\n")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "table.md"), "w", encoding="utf-8") as f:
        f.write(hdr + "\n".join(rows) + "\n")
    print(f"\nwrote {out_dir}/table.md ({len(rows)} rows) — paste the rows into RESULTS.md")


if __name__ == "__main__":
    main()
