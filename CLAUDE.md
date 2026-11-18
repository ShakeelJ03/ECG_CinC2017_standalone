# CLAUDE.md — ECG CinC-2017 capstone (CM2013, KTH)

Read `PLAYBOOK.md` first (deliverables, plan, roles, schedule), then `RESULTS.md` (where we are).

## The project
- 4-class rhythm classification from single-lead ECG (300 Hz): N / A / O / ~ (noisy). One label per record.
- Team: Shakeel (ML engineer; wants to understand every stage), Manfred, Miguela. Shadow team T7 (Sleep-EDF).
- Real deadline: **Thu 10 Dec 2026, 08:00** (report PDF ≤ 20 p, `predictions.csv`, repo link).
- Graded on evidence and reasoning, not the raw number.

## Layout
- `tracks/` — course scaffold (updated to course repo 2026-10-29) + **`tracks/ecg_team.py`** (our stages 2, 3, 5; everything is a cfg key).
- `experiments/harness.py` — cached features, 25 paired folds (5-fold StratifiedGroupKFold by record × 5 seeds), noise floor, verdicts.
- `experiments/run_experiments.py` — the iteration PLAN (E00–E12) and `FINAL_SET`; writes `results/<tag>/`.
- `experiments/get_data.py`, `experiments/figures.py`, `experiments/final.py` (expected → commit → predict).
- `data_cache/ecg_cinc2017/` — 431-record dev set (no hold-out ids). Large data lives OUTSIDE the repo and OneDrive.

## Rules (break one and the grade is capped)
1. Split by record; never touch the 120 hold-out ids (`assert_no_holdout`); predict them once, after `EXPECTED_SCORE.md` is committed.
2. Fit scaler/selector/resampler/classifier inside the training fold only (the harness does this).
3. Report macro-F1 ± SD (and range) over folds, κ, per-class F1/recall, confusion; also F1(N,A,O) vs the 0.83 yardstick.
4. Never drop or merge the `~` class.
5. One change at a time against a named reference; a gain smaller than the noise floor / 2×SE is "no detectable difference".
6. Every experiment gets a dated `RESULTS.md` row with its commit; keep the decision log and revisions current.
7. When changing feature code, bump `FEATURE_VERSION` in `tracks/ecg_team.py` (cache key).

## How to work with Shakeel
Explain as you go: before an experiment say what changes, the hypothesis and what would falsify it; after it, read the numbers in plain words. Ask before large refactors of the course files (`adapter.py`, `report.py`, `ecg_cinc2017.py`).
