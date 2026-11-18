"""
experiments/get_data.py — download the training records ONCE, into a folder outside the repo.

    python experiments/get_data.py --out C:/cm2013_data/ecg/train --subset 2000

Takes about 10 minutes the first time; re-running skips files that are already there, so an
interrupted download just resumes. The course's download() keeps the class proportions and skips
the 120 hold-out records automatically. More records help the rare classes (AF, Noisy): use
--subset 3000 or more if your machine and patience allow, and write the number in RESULTS.md.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tracks"))
from ecg_team import ECGTeamTrack                     # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--subset", type=int, default=2000)
a = ap.parse_args()
if os.path.abspath(a.out).startswith(ROOT):
    sys.exit("Put the data OUTSIDE the repository (and outside OneDrive), e.g. C:/cm2013_data/ecg/train")
trk = ECGTeamTrack()
trk.download(a.out, subset=a.subset)
recs = trk.load_cached(a.out)
trk.assert_no_holdout(recs)
from collections import Counter
print(f"{len(recs)} training records:", dict(Counter(r.labels[0] for r in recs)))
