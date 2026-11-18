# ECG CinC-2017 — CM2013 capstone, Group [X]

Single-lead ECG (300 Hz, 9–60 s) → one rhythm label per recording: **Normal (N) / AF (A) / Other (O) / Noisy (~)**.
Team: Shakeel Jegsilan, Manfred Engström, Miguela Berjame Ursaiz.

Built on the course scaffold (`tracks/adapter.py`, `tracks/ecg_cinc2017.py`, updated to the course
repo of 2026-10-29: hold-out ids, `download_holdout()`, `load_cached()`, `cached()`). Our own work is in
`tracks/ecg_team.py` (stages 2, 3, 5) and `experiments/`.

## Install (Python 3.11 recommended; tested 3.13)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-lock.txt -r requirements-real.txt
python -c "import numpy, scipy, sklearn; print(numpy.__version__, scipy.__version__, sklearn.__version__)"
# expect: 2.2.6 1.15.3 1.7.2
```

## Reproduce

| Step | Command | Time |
|---|---|---|
| Plumbing check (synthetic) | `python run_ecg.py --smoke-only` | seconds |
| Development iterations (431 records shipped in `data_cache/`) | `python experiments/run_experiments.py --data data_cache/ecg_cinc2017 --tag dev431` | ~5 min |
| Download the large training set once, **outside the repo** | `python experiments/get_data.py --out C:/cm2013_data/ecg/train --subset 2000` | ~10 min |
| Final comparison on the large set | `python experiments/run_experiments.py --data C:/cm2013_data/ecg/train --tag full2000 --set final` | ~10–15 min |
| Figures for the report | `python experiments/figures.py --data C:/cm2013_data/ecg/train --tag full2000` | ~1 min |
| Freeze model + register expected score | `python experiments/final.py expected --data C:/cm2013_data/ecg/train` → commit `EXPECTED_SCORE.md` | ~1 min |
| Predict the hold-out once | `python experiments/final.py predict --holdout C:/cm2013_data/ecg/holdout` | ~1 min |

Features are cached per configuration (`_feature_cache/` next to the data), so changing only the
classifier re-uses them. Delete that folder if in doubt.

## Evaluation

Split unit: **record** (one recording per group). Every experiment uses the same 25 folds:
5-fold `StratifiedGroupKFold` × 5 seeds; scaling, selection, resampling and the classifier are fit
inside each training fold; `assert_no_holdout` guards the 120 hold-out records. Metrics: macro-F1
(4 classes, primary) with SD and range across folds, Cohen's κ, per-class F1/recall, confusion
matrix, and the Challenge's own score F1(N,A,O) for comparison with the ~0.83 winners.

`RESULTS.md` is the iteration log; `PLAYBOOK.md` is the team's plan.
