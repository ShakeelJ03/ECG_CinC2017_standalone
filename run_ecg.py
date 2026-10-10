"""
run_ecg.py — standalone runner for the ECG CinC-2017 track.

    python run_ecg.py              # smoke (synthetic) + real data, if data_cache has it
    python run_ecg.py --download   # fetch the stratified real subset first (needs network)
    python run_ecg.py --smoke-only

Real data lives in data_cache/ecg_cinc2017 (REFERENCE-v3.csv + A0xxxx.hea/.mat).
Outputs (predictions.csv) go to outputs/.
"""
import argparse
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "tracks"))          # adapter.py adds src/ and src/bsp itself

from ecg_cinc2017 import ECGCinC2017Track                 # noqa: E402
from sklearn.metrics import f1_score                      # noqa: E402

CACHE = os.path.join(ROOT, "data_cache", "ecg_cinc2017")
OUT = os.path.join(ROOT, "outputs")


def show(title, rep):
    print(f"\n=== {title} ===")
    print("macroF1=%.3f kappa=%.3f n_records=%d"
          % (f1_score(rep["y_true"], rep["y_pred"], average="macro"),
             rep["cohens_kappa"], rep["n_groups"]))
    print("spread:", rep["summary"])                       # never the pooled number alone (§16.3)
    print("classes:", rep["labels"], "\nconfusion (rows=true):\n", rep["confusion"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="download the real subset first")
    ap.add_argument("--subset", type=int, default=400, help="records to download (stratified)")
    ap.add_argument("--smoke-only", action="store_true")
    args = ap.parse_args()

    t = ECGCinC2017Track()
    print(t.dataset_card())

    show("SMOKE (synthetic) CV", t.run_smoke())
    if args.smoke_only:
        return

    if args.download:
        t.download(CACHE, subset=args.subset)
    if not os.path.exists(os.path.join(CACHE, "REFERENCE-v3.csv")):
        print(f"\nNo real data in {CACHE} — run with --download.")
        return

    recs = t.load(CACHE)
    print(f"\nloaded {len(recs)} real records from {CACHE}")
    X, y, g = t.build_dataset(recs)
    show("REAL CinC-2017 CV (GroupKFold by record)", t.evaluate(X, y, g))

    # hold-out demo: fit on 80% of records, write predictions.csv for the other 20%
    recs = list(np.random.default_rng(0).permutation(recs))
    split = int(0.8 * len(recs))
    model = t.train_baseline(recs[:split])
    os.makedirs(OUT, exist_ok=True)
    out = t.write_submission(recs[split:], os.path.join(OUT, "predictions.csv"), model)
    show("REAL hold-out (scored from predictions.csv)", t.score_submission(out, recs[split:]))
    print("wrote", out)


if __name__ == "__main__":
    main()
