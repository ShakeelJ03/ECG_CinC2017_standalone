# Project status — 18 Nov 2026 (evening)

ECG CinC-2017 track: classify each single-lead ECG strip (300 Hz, 9–60 s) as **Normal (N), AF (A),
Other rhythm (O) or Noisy (~)**. Primary metric: macro-F1 over the 4 classes. Split unit: record.
Deadline: **Thu 10 Dec, 08:00** — report PDF (≤ 20 pages), `predictions.csv`, repo link.

## In one paragraph

We built our own version of the track (`tracks/ecg_team.py`) and a fair test harness
(`experiments/harness.py`). The biggest problems in the supplied baseline were a fragile R-peak
detector and too-simple rhythm features. Replacing both, then adding beat-shape features, took
macro-F1 from **0.590 to 0.747 ± 0.031** on 1,999 records. The Challenge-style score F1(N,A,O) is
**0.802**; the 2017 winners got 0.83. The weakest class is Noisy (F1 0.58, only 59 examples), so
tonight's run tests whether **more data** fixes it.

## How we test every change

- **One change at a time** against a named reference experiment (E00, E02, … are just our run numbers).
- **Same 25 folds for every run**: 5-fold `StratifiedGroupKFold` grouped by record, repeated with 5
  seeds. Two pipelines are compared fold by fold.
- **Noise floor**: how much the score moves when only the fold seed changes (≈ 0.005–0.02). A change
  is a **real gain** only if it beats the noise floor and twice its standard error; otherwise it is
  **no detectable difference** (that is an honest result, not a failure).
- Scaler, selector and classifier are fit **inside** each training fold; the 120 hold-out records are
  never used (checked in code).
- **Predictions are written before each big run** (`PREDICTIONS_*.md`), then checked
  afterwards ("Reflect & improve" in the track notebook).

## What we found

**Phase 1 — development set (431 records, 21 runs).** Exploration, allowed on the small set by Farhad.

- Spectrum: **no 50/60 Hz mains hum** and almost nothing above 40 Hz (the AliveCor device already
  filters), so filtering gave no gain.
- The **supplied R-peak detector fails** on ~1 in 5 Normal records (one global threshold, so one
  artifact spike hides all beats). Our Pan–Tompkins detector (adaptive thresholds, search-back)
  agrees with wfdb's XQRS detector on 96–99 % of beats → **real gain**.
- **21 rhythm features** (Poincaré, sample entropy, Lorenz plot, successive differences) → **real
  gain**, better in 25/25 folds.
- Other classifiers, SMOTE, feature selection, AR spectra, wavelet/envelope features: no detectable
  difference (or worse).
- **Revision 1:** "denoising hurts" (first result) was caused by the fragile detector; with our
  detector the loss disappears.

**Phase 2 — 1,999 records (10 runs, predictions written first).** The official comparison.

| Run | What it adds | macro-F1 | Verdict vs its reference |
|---|---|---|---|
| E00 | supplied baseline | 0.590 ± 0.041 | — |
| E02 | our detector | 0.650 | real gain (+0.061) |
| E03a | + rhythm features | 0.707 | real gain (+0.057) |
| **E04** | **+ beat-shape features** | **0.747 ± 0.031** (κ 0.671, F1(N,A,O) 0.802) | **real gain (+0.040)** |
| E05 | all 62 features | 0.739 | lower than E04 with more features |
| E07a / E07b | boosting / SVM | 0.719 / 0.695 | no detectable difference |
| E10 | denoise (revisit) | 0.711 | no detectable difference |
| E13 | E04 + quality features (for Noisy) | 0.742 | no detectable difference |
| E14 | E04 with boosting | 0.741 | no detectable difference |

- **Revision 2:** beat-shape features were "below the noise" on the small set but a **real gain**
  with 1,999 records, so we put them back. Most of the gain was in Noisy (0.48 → 0.58).
- 6 of 8 predictions fully right; the wrong ones are explained in `PREDICTIONS_full2000.md`.
- **Current final pipeline (E04):** no filtering · our Pan–Tompkins detector · 43 features (base +
  rhythm + beat shape) · random forest with class weights.

## Running tonight

All CinC-2017 training records except the hold-out (~8,400; ~280 Noisy instead of 59), the same 10
experiments, tag `full8400`. Predictions are in `PREDICTIONS_full8400.md` (written before running).
The key question: **does Noisy F1 rise clearly with more Noisy examples?** If boosting (E14) becomes a
real gain, that would be Revision 3.

## Next

1. Read the `full8400` results, fill in the predictions file and `RESULTS.md`, decide the final model.
2. `experiments/final.py expected` → commit `EXPECTED_SCORE.md` → `final.py predict` (hold-out, once)
   → commit `predictions.csv`.
3. Figures, report (≤ 20 p), slides, Q&A practice — every member must be able to explain every step.

## Where things are

| File | What |
|---|---|
| `RESULTS.md` | the graded log: every run, decisions, both revisions |
| `PREDICTIONS_full2000.md`, `PREDICTIONS_full8400.md` | predictions before each big run + reflection |
| `PLAYBOOK.md` | deliverables, roles, schedule, report outline, Q&A questions, references |
| `walkthrough/ecg_walkthrough.html` | each step with its reasoning, code and figures (open in a browser) |
| `tracks/ecg_team.py` | our detector, features and classifiers |
| `experiments/` | harness, experiment plan, figures, final model + hold-out |
| `results/<tag>/` | raw results per run and `table.md` |
