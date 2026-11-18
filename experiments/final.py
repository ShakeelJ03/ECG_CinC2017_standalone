"""
experiments/final.py — freeze the final model, register the expected score, predict the hold-out ONCE.

Step 1 (after the final comparison on the large training set):
    python experiments/final.py expected --data C:/cm2013_data/ecg/train
    -> prints the cross-validated score, trains the final model on ALL training records,
       saves models/final_model.pkl and writes EXPECTED_SCORE.md.
    Then:  git add EXPECTED_SCORE.md && git commit -m "Register expected score" && git push

Step 2 (only after that commit exists):
    python experiments/final.py predict --holdout C:/cm2013_data/ecg/holdout
    -> downloads ONLY the 120 hold-out records into their own folder and writes predictions.csv
       with write_submission(). Never edit the file, never score it, never retrain afterwards.
"""
from __future__ import annotations

import argparse
import os
import pickle
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import Harness, ROOT                     # noqa: E402
from ecg_team import ECGTeamTrack                     # noqa: E402

#: The pipeline chosen by the final comparison. Update it from your own full-data results
#: (results/full2000/table.md) before step 1 — and log why in RESULTS.md.
FINAL_CFG = {"seed": 0, "qrs": "pt", "feature_set": "base+rr+morph", "clf": "rf", "imbalance": "balanced"}   # = E04 (full2000, 2026-11-18)

MODEL = os.path.join(ROOT, "models", "final_model.pkl")
EXPECTED = os.path.join(ROOT, "EXPECTED_SCORE.md")


def _git(*a):
    return subprocess.check_output(["git", *a], text=True, cwd=ROOT).strip()


def expected(data):
    H = Harness(data)
    r = H.run(FINAL_CFG, name="FINAL (repeated 5×5 CV)")
    X, _ = H.features(FINAL_CFG)
    trk = ECGTeamTrack(cfg=FINAL_CFG)
    official = trk.evaluate(X, H.y, H.groups, cfg=FINAL_CFG)          # the course's own evaluator
    print("course evaluate():", official["summary"])
    model = trk.train_baseline(H.recs, cfg=FINAL_CFG)
    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    with open(MODEL, "wb") as f:
        pickle.dump(model, f)
    try:
        commit = _git("rev-parse", "--short", "HEAD")
        dirty = bool(_git("status", "--porcelain", "--", "tracks", "experiments"))
    except Exception:                                                   # noqa: BLE001
        commit, dirty = "unknown", True
    m, s = r["mean"], r["sd"]
    text = f"""# Expected score — ECG CinC-2017 (registered before the hold-out is downloaded)

| | |
|---|---|
| Final model commit | `{commit}`{"  ⚠️ code had uncommitted changes — commit first, then re-run" if dirty else ""} |
| Pipeline (cfg) | `{FINAL_CFG}` |
| Training records | {len(H.y)} — {H.counts} (hold-out ids excluded, checked with `assert_no_holdout`) |
| Split unit | record |
| Folds | 5-fold StratifiedGroupKFold (groups = record), repeated 5× with seeds 0–4 = 25 folds |
| **Expected macro-F1 (4 classes)** | **{m['macro_f1']:.3f} ± {s['macro_f1']:.3f}** (mean ± SD across the 25 folds) |
| Cohen's κ | {m['kappa']:.3f} ± {s['kappa']:.3f} |
| Challenge score F1(N,A,O) | {m['f1_NAO']:.3f} ± {s['f1_NAO']:.3f} |
| Per-class F1 N / A / O / ~ | {m['f1_N']:.2f} / {m['f1_A']:.2f} / {m['f1_O']:.2f} / {m['f1_~']:.2f} |
| Course `evaluate()` (5-fold GroupKFold) | {official['summary']} |

Note: the hold-out has 30 records per class, while training follows the dataset's own mix
(Normal-heavy). Per-class recall should transfer; macro-F1 can move because precision on the rare
classes depends on how many of them there are. We registered this number before seeing the
hold-out and will report the hold-out score next to it, whichever way it lands.
"""
    with open(EXPECTED, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    print("NEXT: git add EXPECTED_SCORE.md && git commit -m 'Register expected score' && git push")


def predict(holdout_dir):
    try:
        log = _git("log", "--oneline", "--", "EXPECTED_SCORE.md")
    except Exception:                                                   # noqa: BLE001
        log = ""
    if not log:
        sys.exit("EXPECTED_SCORE.md is not committed yet. Commit it first (that commit is your "
                 "registration), then predict.")
    trk = ECGTeamTrack(cfg=FINAL_CFG)
    if os.path.exists(MODEL):
        with open(MODEL, "rb") as f:
            model = pickle.load(f)
    else:
        sys.exit(f"{MODEL} not found — run the 'expected' step on this machine first.")
    trk.download_holdout(holdout_dir)
    hold = trk.load(holdout_dir)
    out = os.path.join(ROOT, "predictions.csv")
    trk.write_submission(hold, out, model)
    print(f"wrote {out} ({len(hold)} records). Do not open, edit or score it — submit it on Canvas.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["expected", "predict"])
    ap.add_argument("--data", help="training folder (step 1)")
    ap.add_argument("--holdout", help="separate empty folder for the hold-out records (step 2)")
    a = ap.parse_args()
    if a.stage == "expected":
        expected(a.data or sys.exit("--data is required"))
    else:
        predict(a.holdout or sys.exit("--holdout is required"))
