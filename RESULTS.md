# Results log — `ecg_cinc2017`, CM2013 Group [X]

**Track:** `ecg_cinc2017` · **Split unit:** record · **Primary metric:** macro-F1 (4 classes) ·
**Evaluation mode:** new-record

How every number here was made: `experiments/run_experiments.py` (harness in `experiments/harness.py`).
Same 25 folds for every row — 5-fold `StratifiedGroupKFold` grouped by record × 5 seeds — so rows are
compared **fold by fold** (paired). "Real gain/loss" = the mean paired difference is larger than both
2 × its standard error and the **noise floor** (how much the reference moves when only the fold seed
changes, ≈ 0.01–0.02 here). Anything smaller is reported as *no detectable difference*.

**Comparison budget (fixed before running):** 21 configurations on the development set, one change
at a time; a change is kept only on a *real gain*, otherwise we keep the simpler option. The short
list `FINAL_SET` (8 configurations) is then re-run once on the large training set.

## Iteration log — development set (431 records: N 238 · A 40 · O 113 · ~ 40)

The supplied subset in `data_cache/`, which contains no hold-out records (checked). Earlier
iterations stay on this set (allowed by the course); the final comparison is re-run on ≥ 2,000 records.

| # | Date | What changed & why | Primary metric with spread | Better than reference? | If not — why kept | Commit |
|---|---|---|---|---|---|---|
| E00 | 2026-11-18 | supplied baseline unchanged (11 features, RF, class weights) — the floor | macro-F1 0.634 (sd 0.071, range 0.45–0.81 across 25 record-grouped folds); κ 0.506; F1 N/A/O/~ 0.82/0.62/0.52/0.58 | — (baseline) |  | `8285397` |
| E01a | 2026-11-18 | 0.5–40 Hz band-pass + 50 Hz notch: removes wander/hum, may blunt the QRS | macro-F1 0.625 (sd 0.067, range 0.42–0.77 across 25 record-grouped folds); κ 0.493; F1 N/A/O/~ 0.81/0.59/0.51/0.58 | vs E00: Δ -0.008, 10/25 folds — **no detectable difference** |  | `8285397` |
| E01b | 2026-11-18 | db4 wavelet denoising: removes transients without a fixed band | macro-F1 0.638 (sd 0.068, range 0.46–0.80 across 25 record-grouped folds); κ 0.521; F1 N/A/O/~ 0.82/0.62/0.55/0.56 | vs E00: Δ +0.004, 12/25 folds — **no detectable difference** |  | `8285397` |
| E01c | 2026-11-18 | per-noise-type denoise (median → high-pass 0.5 Hz → notch) | macro-F1 0.605 (sd 0.068, range 0.39–0.73 across 25 record-grouped folds); κ 0.480; F1 N/A/O/~ 0.81/0.56/0.51/0.54 | vs E00: Δ -0.029, 6/25 folds — **real loss** |  | `8285397` |
| E02 | 2026-11-18 | Pan–Tompkins with adaptive thresholds + search-back instead of one global 30 % threshold | macro-F1 0.668 (sd 0.049, range 0.58–0.78 across 25 record-grouped folds); κ 0.560; F1 N/A/O/~ 0.84/0.57/0.55/0.71 | vs E00: Δ +0.035, 18/25 folds — **real gain** |  | `8285397` |
| E03a | 2026-11-18 | +21 rhythm features (Poincaré, sample entropy/COSEn, Lorenz plot, ΔRR autocorrelation) | macro-F1 0.770 (sd 0.057, range 0.66–0.86 across 25 record-grouped folds); κ 0.675; F1 N/A/O/~ 0.87/0.78/0.68/0.75 | vs E02: Δ +0.101, 25/25 folds — **real gain** |  | `8285397` |
| E03b | 2026-11-18 | +11 morphology features (template correlation, QRS width, P wave, QRST-cancelled atrial activity) | macro-F1 0.719 (sd 0.059, range 0.62–0.83 across 25 record-grouped folds); κ 0.605; F1 N/A/O/~ 0.85/0.64/0.59/0.79 | vs E02: Δ +0.051, 22/25 folds — **real gain** |  | `8285397` |
| E03c | 2026-11-18 | +9 signal-quality indices (bSQI detector agreement, spectral entropy, clipping, RMS bursts) | macro-F1 0.677 (sd 0.043, range 0.60–0.79 across 25 record-grouped folds); κ 0.567; F1 N/A/O/~ 0.84/0.58/0.57/0.72 | vs E02: Δ +0.009, 12/25 folds — **no detectable difference** |  | `8285397` |
| E03d | 2026-11-18 | +7 db4 wavelet sub-band energies (second feature domain) | macro-F1 0.646 (sd 0.046, range 0.55–0.74 across 25 record-grouped folds); κ 0.529; F1 N/A/O/~ 0.83/0.56/0.52/0.67 | vs E02: Δ -0.023, 9/25 folds — **real loss** |  | `8285397` |
| E03e | 2026-11-18 | +3 Hilbert-envelope periodicity features (rhythm regularity without a beat detector) | macro-F1 0.669 (sd 0.050, range 0.57–0.78 across 25 record-grouped folds); κ 0.553; F1 N/A/O/~ 0.84/0.60/0.53/0.71 | vs E02: Δ +0.001, 11/25 folds — **no detectable difference** |  | `8285397` |
| E04 | 2026-11-18 | morphology on top of the rhythm features | macro-F1 0.777 (sd 0.046, range 0.68–0.85 across 25 record-grouped folds); κ 0.684; F1 N/A/O/~ 0.87/0.75/0.70/0.79 | vs E03a: Δ +0.008, 13/25 folds — **no detectable difference** |  | `8285397` |
| E05 | 2026-11-18 | every feature group together (62 features) | macro-F1 0.780 (sd 0.045, range 0.69–0.85 across 25 record-grouped folds); κ 0.690; F1 N/A/O/~ 0.88/0.75/0.70/0.80 | vs E03a: Δ +0.011, 15/25 folds — **no detectable difference** |  | `8285397` |
| E06 | 2026-11-18 | parametric AR spectrum instead of Welch for the band-power features | macro-F1 0.766 (sd 0.053, range 0.67–0.87 across 25 record-grouped folds); κ 0.671; F1 N/A/O/~ 0.87/0.78/0.68/0.74 | vs E03a: Δ -0.004, 10/25 folds — **no detectable difference** |  | `8285397` |
| E07a | 2026-11-18 | gradient boosting instead of random forest | macro-F1 0.764 (sd 0.059, range 0.65–0.90 across 25 record-grouped folds); κ 0.664; F1 N/A/O/~ 0.86/0.79/0.68/0.73 | vs E03a: Δ -0.006, 12/25 folds — **no detectable difference** |  | `8285397` |
| E07b | 2026-11-18 | RBF-SVM (scaled) instead of random forest | macro-F1 0.761 (sd 0.048, range 0.68–0.84 across 25 record-grouped folds); κ 0.676; F1 N/A/O/~ 0.86/0.77/0.72/0.70 | vs E03a: Δ -0.009, 10/25 folds — **no detectable difference** |  | `8285397` |
| E08a | 2026-11-18 | no class weights: does the minority-class handling matter? | macro-F1 0.761 (sd 0.058, range 0.65–0.86 across 25 record-grouped folds); κ 0.665; F1 N/A/O/~ 0.87/0.76/0.68/0.74 | vs E03a: Δ -0.008, 9/25 folds — **no detectable difference** |  | `8285397` |
| E08b | 2026-11-18 | SMOTE inside the fold instead of class weights | macro-F1 0.772 (sd 0.056, range 0.67–0.88 across 25 record-grouped folds); κ 0.684; F1 N/A/O/~ 0.87/0.76/0.71/0.75 | vs E03a: Δ +0.002, 13/25 folds — **no detectable difference** |  | `8285397` |
| E09 | 2026-11-18 | keep the 25 most informative of 62 features (fit inside each fold) | macro-F1 0.766 (sd 0.044, range 0.67–0.84 across 25 record-grouped folds); κ 0.671; F1 N/A/O/~ 0.87/0.76/0.69/0.75 | vs E05: Δ -0.014, 7/25 folds — **no detectable difference** |  | `8285397` |
| E10 | 2026-11-18 | REVISIT E01c: is denoising still harmful once the detector is robust? | macro-F1 0.766 (sd 0.058, range 0.65–0.86 across 25 record-grouped folds); κ 0.672; F1 N/A/O/~ 0.87/0.77/0.68/0.75 | vs E03a: Δ -0.003, 13/25 folds — **no detectable difference** |  | `8285397` |
| E11 | 2026-11-18 | REVISIT: denoise for rhythm, but quality features from the raw strip | macro-F1 0.774 (sd 0.052, range 0.69–0.87 across 25 record-grouped folds); κ 0.680; F1 N/A/O/~ 0.87/0.78/0.68/0.77 | vs E10: Δ +0.008, 15/25 folds — **no detectable difference** |  | `8285397` |
| E12 | 2026-11-18 | REVISIT E02: the rhythm features with the supplied detector — how much rests on R-peaks? | macro-F1 0.650 (sd 0.069, range 0.50–0.75 across 25 record-grouped folds); κ 0.531; F1 N/A/O/~ 0.81/0.69/0.57/0.52 | vs E03a: Δ -0.119, 2/25 folds — **real loss** |  | `8285397` |

**Kept after the development set** (later revised on the full data, see Revision 2)**:** E02 (our Pan–Tompkins) and E03a (rhythm features). Everything else
was *no detectable difference* or a *real loss* on 431 records, so we kept the simpler pipeline
`{qrs: pt, feature_set: base+rr, clf: rf, imbalance: balanced, preprocess: none}`.
E04/E05 (morphology, all groups) were the closest calls (+0.008/+0.011) and are re-tested on the large set.

## Iteration log — final comparison on the large training set

Records used: **1,999** (N 1200 · A 173 · O 567 · ~ 59), downloaded with `get_data.py --subset 2000`
into `C:/cm2013_data/ecg/train`, hold-out excluded. Predictions for every run were written before running (`PREDICTIONS_full2000.md`). Predictions were written before each run (18–19 Nov), but the prediction files only reached git on 25 Nov, so the git history does not itself prove the order. Same harness, same rule.
Note: numbers are not comparable with the dev-set rows (different data; Noisy falls from 9 % to 3 %).

| # | Date | What changed & why | Primary metric with spread | Better than reference? | If not — why kept | Commit |
|---|---|---|---|---|---|---|
| E00 | 2026-11-18 | supplied baseline unchanged — the floor on the large set | macro-F1 0.590 (sd 0.041 across 25 record-grouped folds); κ 0.484; F1(N,A,O) 0.662; F1 N/A/O/~ 0.83/0.60/0.56/0.37 | — (baseline) |  | `07f7809` |
| E02 | 2026-11-18 | our Pan–Tompkins detector | macro-F1 0.650 (sd 0.040); κ 0.557; F1(N,A,O) 0.701; F1 N/A/O/~ 0.86/0.64/0.60/0.50 | vs E00: Δ +0.061, 24/25 folds — **real gain** |  | `07f7809` |
| E03a | 2026-11-18 | +21 rhythm features | macro-F1 0.707 (sd 0.041); κ 0.647; F1(N,A,O) 0.784; F1 N/A/O/~ 0.88/0.78/0.69/0.48 | vs E02: Δ +0.057, 22/25 folds — **real gain** |  | `07f7809` |
| E04 | 2026-11-18 | +11 morphology features on top of the rhythm features | macro-F1 0.747 (sd 0.031); κ 0.671; F1(N,A,O) 0.802; F1 N/A/O/~ 0.89/0.81/0.71/0.58 | vs E03a: Δ +0.040, 21/25 folds — **real gain** | **kept → new final pipeline** (Revision 2) | `07f7809` |
| E05 | 2026-11-18 | every feature group (62) | macro-F1 0.739 (sd 0.037); κ 0.675; F1(N,A,O) 0.803; F1 N/A/O/~ 0.89/0.80/0.72/0.55 | vs E03a: Δ +0.032, 21/25 folds — **real gain** | not kept: 19 more features and a lower mean than E04 | `07f7809` |
| E07a | 2026-11-18 | gradient boosting instead of RF | macro-F1 0.719 (sd 0.032); κ 0.647; F1(N,A,O) 0.783; F1 N/A/O/~ 0.87/0.78/0.70/0.53 | vs E03a: Δ +0.012, 13/25 folds — **no detectable difference** | kept RF (simpler, supplied) | `07f7809` |
| E07b | 2026-11-18 | RBF-SVM instead of RF | macro-F1 0.695 (sd 0.032); κ 0.644; F1(N,A,O) 0.781; F1 N/A/O/~ 0.87/0.76/0.71/0.44 | vs E03a: Δ −0.012, 7/25 folds — **no detectable difference** | kept RF | `07f7809` |
| E10 | 2026-11-18 | REVISIT: denoise (median → high-pass → notch) with the robust detector | macro-F1 0.711 (sd 0.040); κ 0.651; F1(N,A,O) 0.788; F1 N/A/O/~ 0.88/0.79/0.70/0.48 | vs E03a: Δ +0.004, 13/25 folds — **no detectable difference** | confirms Revision 1 on the large set; preprocessing stays off | `07f7809` |

**Round 2 (targeting Noisy, predictions written before running):** neither change helped → pipeline frozen at **E04**.

| # | Date | What changed & why | Primary metric with spread | Better than reference? | If not — why kept | Commit |
|---|---|---|---|---|---|---|
| E13 | 2026-11-18 | +9 signal-quality indices on top of E04, aimed at Noisy | macro-F1 0.742 (sd 0.035); κ 0.679; F1(N,A,O) 0.805; F1 N/A/O/~ 0.89/0.81/0.72/0.55 | vs E04: Δ −0.005, 12/25 folds — **no detectable difference** | not kept: redundant with E04's template correlation; Noisy is data-limited (59 records) | `3449ce5` |
| E14 | 2026-11-18 | gradient boosting on the E04 features | macro-F1 0.741 (sd 0.034); κ 0.675; F1(N,A,O) 0.803; F1 N/A/O/~ 0.88/0.80/0.72/0.55 | vs E04: Δ −0.007, 10/25 folds — **no detectable difference** | kept RF | `3449ce5` |

## Iteration log — all training records (8,408)

Why: Noisy stayed the weakest class on 1,999 records and two changes aimed at it did nothing, so we
diagnosed it as data-limited and changed one thing: the amount of data. Records used: **8,408**
(N 5046 · A 728 · O 2385 · ~ 249) — every CinC-2017 training record except the 120 hold-out ids,
`get_data.py --subset 8528` into `C:/cm2013_data/ecg/train_full`. Predictions written
before running (`PREDICTIONS_full8400.md`). Same harness, same rule, same 10 configurations.

| # | Date | What changed & why | Primary metric with spread | Better than reference? | If not — why kept | Commit |
|---|---|---|---|---|---|---|
| E00 | 2026-11-19 | supplied baseline unchanged | macro-F1 0.614 (sd 0.020); κ 0.529; F1(N,A,O) 0.695; F1 N/A/O/~ 0.85/0.64/0.59/0.37 | — (baseline) |  | `b009d3f` |
| E02 | 2026-11-19 | our Pan–Tompkins detector | macro-F1 0.674 (sd 0.015); κ 0.599; F1(N,A,O) 0.732; F1 N/A/O/~ 0.88/0.68/0.64/0.50 | vs E00: Δ +0.061, 25/25 — **real gain** |  | `b009d3f` |
| E03a | 2026-11-19 | +21 rhythm features | macro-F1 0.712 (sd 0.017); κ 0.657; F1(N,A,O) 0.786; F1 N/A/O/~ 0.89/0.77/0.70/0.49 | vs E02: Δ +0.037, 25/25 — **real gain** |  | `b009d3f` |
| E04 | 2026-11-19 | +11 morphology features | macro-F1 0.744 (sd 0.017); κ 0.678; F1(N,A,O) 0.801; F1 N/A/O/~ 0.89/0.80/0.71/0.57 | vs E03a: Δ +0.032, 25/25 — **real gain** |  | `b009d3f` |
| E05 | 2026-11-19 | every feature group (62) | macro-F1 0.745 (sd 0.019); κ 0.680; F1(N,A,O) 0.803; F1 N/A/O/~ 0.89/0.80/0.71/0.57 | vs E03a: Δ +0.033, 25/25 — **real gain** | not kept: same as E04 with 19 more features | `b009d3f` |
| E07a | 2026-11-19 | gradient boosting on E03a features | macro-F1 0.716 (sd 0.019); κ 0.657; F1(N,A,O) 0.781; F1 N/A/O/~ 0.88/0.76/0.70/0.52 | vs E03a: Δ +0.004, 18/25 — **no detectable difference** |  | `b009d3f` |
| E07b | 2026-11-19 | RBF-SVM on E03a features | macro-F1 0.681 (sd 0.022); κ 0.631; F1(N,A,O) 0.761; F1 N/A/O/~ 0.87/0.72/0.69/0.44 | vs E03a: Δ −0.030, 1/25 — **real loss** | rejected | `b009d3f` |
| E10 | 2026-11-19 | REVISIT: denoise with the robust detector | macro-F1 0.712 (sd 0.019); κ 0.656; F1(N,A,O) 0.785; F1 N/A/O/~ 0.89/0.77/0.70/0.49 | vs E03a: Δ +0.000, 12/25 — **no detectable difference** | preprocessing stays off | `b009d3f` |
| E13 | 2026-11-19 | E04 + 9 signal-quality indices | macro-F1 0.745 (sd 0.019); κ 0.681; F1(N,A,O) 0.803; F1 N/A/O/~ 0.90/0.80/0.72/0.57 | vs E04: Δ +0.001, 17/25 — **no detectable difference** | not kept | `b009d3f` |
| E14 | 2026-11-19 | gradient boosting on the E04 features | macro-F1 **0.756 (sd 0.018)**; κ 0.688; F1(N,A,O) 0.807; F1 N/A/O/~ 0.89/0.80/0.73/0.60 | vs E04: Δ +0.012, 20/25 — **real gain** | **kept → final pipeline** (Revision 3) | `b009d3f` |
| E15 | 2026-11-25 | +7 beat-by-beat ectopy features (abnormal/premature beats, 2nd template, QRS width, P→R) on top of E14, aimed at Other (literature: Teijeiro 2017 criteria, Andreotti 2017 two-template beat classes) | macro-F1 0.760 (sd 0.020); κ 0.695; F1(N,A,O) 0.812; F1 N/A/O/~ 0.89/0.81/0.74/0.60 | vs E14: Δ +0.004, 16/25 folds — **no detectable difference** | not kept: right direction for Other/AF, but the gain is at the noise level; pipeline frozen at E14 | `fa6f47c` |

**Round 2 on all data (2026-11-25):** E15 targeted the largest remaining error (Other → Normal) with beat-level ectopy features: no detectable difference → **frozen at E14**.

**Finding:** Noisy did *not* improve with 4.2× more examples (E04: 0.58 → 0.57), so the data-limited
diagnosis is falsified; the likely limit is label consistency. More data halved the fold SDs, which
made boosting's +0.012 detectable.

## Decision log

| Pipeline module | Option chosen | Alternative(s) considered | Why this one | Iteration | Revised later? |
|---|---|---|---|---|---|
| 1. Data loading | 431-record dev set → 1,999 records → **all 8,408 training records** | stopping at 1,999 | course minimum is ~2,000; we went further to test whether Noisy was data-limited (it wasn't) — but the larger set halves the spread and is what the final model is trained on | E00 → full8400 | yes, twice (more data) |
| 2. Preprocessing | none | band-pass + notch (E01a), wavelet (E01b), denoise (E01c) | no detectable gain; the spectrum (fig 2) has no 50/60 Hz line and almost nothing above 40 Hz, so there is no hum to remove | E01 | **yes, E10** — see revisions |
| 3a. QRS detection | Pan–Tompkins with adaptive thresholds + search-back | supplied single 30 %-threshold detector | +0.035 macro-F1; agrees with wfdb XQRS on 96–99 % of beats vs 82–89 % (qrs_agreement.md) | E02 | confirmed by E12 |
| 3b. Features | base + rhythm + morphology (43) | rhythm only; + SQI, wavelet, envelope; all 62 | dev: rhythm +0.101 (25/25), morphology below the noise. Full data: morphology +0.040 (21/25), all-62 lower than 43 | E03–E05 | **yes, full data** — see Revision 2 |
| 3c. Spectral estimator | Welch | AR (E06) | no detectable difference; Welch is the non-parametric default with no model order to justify | E06 | — |
| 4. Feature selection | none | mutual information top-25 (E09) | −0.014, worse in 18/25 folds (not detectable) — no reason to add a stage; the forest handles 62 features itself. MI scoring seeded so the run is reproducible | E09 | — |
| 5. Classifier | **gradient boosting** (HistGradientBoosting, settings fixed in code, class weights) | random forest (supplied), RBF-SVM | RF vs boosting: no detectable difference on 431 or 1,999 records; on 8,408 boosting is a real gain (+0.012, 20/25). SVM a real loss on 8,408 | E07, E14 | **yes, Revision 3** |
| 5. Imbalance | class weights (`balanced`) | none (E08a), SMOTE (E08b) | no detectable difference on macro-F1; weights keep AF/Noisy recall up without inventing records | E08 | — |
| 6. Inference | `write_submission()` with the frozen `FittedModel` | — | course requirement; cfg parity is enforced by the scaffold | final | — |
| 7. Reporting | macro-F1 ± SD + range over 25 folds, κ, per-class F1/recall, confusion, F1(N,A,O) | pooled number only | rubric criteria 3, 7, 8 | all | — |

## Revisions — decisions we went back and changed

| # | The downstream result that triggered it | Which earlier decision it indicted | What we changed | What happened to the metric |
|---|---|---|---|---|
| 1 | E12: our rhythm features with the **supplied** detector lose −0.119 (2/25 folds better), and the XQRS check shows that detector fails on 21 % of Normal records | E01c's conclusion "denoising hurts" (−0.029, a *real loss*) — it was measured with the fragile detector, which breaks when the filtered signal changes its global threshold | re-ran denoising with the robust detector (E10), and with quality features on the raw strip (E11) | loss disappears: −0.029 → −0.003 (no detectable difference). Preprocessing stays "none", but now because there is nothing in the spectrum to remove — not because filtering is harmful |
| 2 | Full data (1,999 records): E04 is a **real gain** over E03a, +0.040 in 21/25 folds; Noisy F1 0.48 → 0.58 | dev-set decision (E04) to leave morphology out — it was +0.008, below the noise, on only 431 records | `feature_set` → `base+rr+morph`; `FINAL_CFG` in `experiments/final.py` updated | macro-F1 0.707 → **0.747 ± 0.031**, F1(N,A,O) 0.784 → 0.802 — kept |
| 3 | All 8,408 records: E14 (boosting on E04 features) is a **real gain** over E04, +0.012 in 20/25 folds; fold SD halved to ≈ 0.018 so the comparison became sensitive enough | E07/E14 on 1,999 records: keep the random forest (differences within the noise) | `clf` → `hgb`; `FINAL_CFG` updated; final model trained on 8,408 records | macro-F1 0.744 → **0.756 ± 0.018**, F1(N,A,O) 0.807, Noisy F1 0.57 → 0.60 — kept |

## Who did what

| Iteration | Who | Modules / tasks owned | Reviewed by |
|---|---|---|---|
| dev set | Shakeel | harness, classifier/imbalance/selection experiments (E06–E09); reproduced all 21 dev runs on own PC |  |
| full data | Shakeel | download (1,999 records), final comparison (8 runs), predictions + reflection, round 2 (E13–E14) |  |
| all data | Shakeel | download (8,408 records), all-data comparison (10 runs), predictions + reflection, Revision 3; E15 (ectopy features, from literature/GitHub review) |  |
| dev set |  | preprocessing + QRS detection (E01, E02, E10–E12) |  |
| dev set |  | features (E03–E05) |  |

## Final numbers (fill in once, at the end)

| | Value | Under what split |
|---|---|---|
| Primary metric, development (mean + spread) |  | record, 25 folds |
| Secondary metrics (κ / per-class F1 / F1(N,A,O)) |  |  |
| Held-out set — **scored once, never tuned against** | reported back by the instructor |  |
| Supplied baseline, same harness |  |  |
| Yardstick | CinC-2017 winners F1(N,A,O) ≈ 0.83 (Clifford et al. 2017) | hidden test set, 3-class score |
| **Configurations compared** | 21 on the dev set (431) + 10 on 1,999 records + 11 on 8,408 records = 42 | dev set / short lists on the larger sets |
| How option comparison was kept separate from final reporting | comparison budget fixed in advance; final short list re-run on the larger set |  |
