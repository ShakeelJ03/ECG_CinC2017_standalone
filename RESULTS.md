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
| E00 | 2026-11-18 | supplied baseline unchanged (11 features, RF, class weights) — the floor | macro-F1 0.634 (sd 0.071, range 0.45–0.81 across 25 record-grouped folds); κ 0.506; F1 N/A/O/~ 0.82/0.62/0.52/0.58 | — (baseline) |  | `<commit>` |
| E01a | 2026-11-18 | 0.5–40 Hz band-pass + 50 Hz notch: removes wander/hum, may blunt the QRS | macro-F1 0.625 (sd 0.067, range 0.42–0.77 across 25 record-grouped folds); κ 0.493; F1 N/A/O/~ 0.81/0.59/0.51/0.58 | vs E00: Δ -0.008, 10/25 folds — **no detectable difference** |  | `<commit>` |
| E01b | 2026-11-18 | db4 wavelet denoising: removes transients without a fixed band | macro-F1 0.638 (sd 0.068, range 0.46–0.80 across 25 record-grouped folds); κ 0.521; F1 N/A/O/~ 0.82/0.62/0.55/0.56 | vs E00: Δ +0.004, 12/25 folds — **no detectable difference** |  | `<commit>` |
| E01c | 2026-11-18 | per-noise-type denoise (median → high-pass 0.5 Hz → notch) | macro-F1 0.605 (sd 0.068, range 0.39–0.73 across 25 record-grouped folds); κ 0.480; F1 N/A/O/~ 0.81/0.56/0.51/0.54 | vs E00: Δ -0.029, 6/25 folds — **real loss** |  | `<commit>` |
| E02 | 2026-11-18 | Pan–Tompkins with adaptive thresholds + search-back instead of one global 30 % threshold | macro-F1 0.668 (sd 0.049, range 0.58–0.78 across 25 record-grouped folds); κ 0.560; F1 N/A/O/~ 0.84/0.57/0.55/0.71 | vs E00: Δ +0.035, 18/25 folds — **real gain** |  | `<commit>` |
| E03a | 2026-11-18 | +21 rhythm features (Poincaré, sample entropy/COSEn, Lorenz plot, ΔRR autocorrelation) | macro-F1 0.770 (sd 0.057, range 0.66–0.86 across 25 record-grouped folds); κ 0.675; F1 N/A/O/~ 0.87/0.78/0.68/0.75 | vs E02: Δ +0.101, 25/25 folds — **real gain** |  | `<commit>` |
| E03b | 2026-11-18 | +11 morphology features (template correlation, QRS width, P wave, QRST-cancelled atrial activity) | macro-F1 0.719 (sd 0.059, range 0.62–0.83 across 25 record-grouped folds); κ 0.605; F1 N/A/O/~ 0.85/0.64/0.59/0.79 | vs E02: Δ +0.051, 22/25 folds — **real gain** |  | `<commit>` |
| E03c | 2026-11-18 | +9 signal-quality indices (bSQI detector agreement, spectral entropy, clipping, RMS bursts) | macro-F1 0.677 (sd 0.043, range 0.60–0.79 across 25 record-grouped folds); κ 0.567; F1 N/A/O/~ 0.84/0.58/0.57/0.72 | vs E02: Δ +0.009, 12/25 folds — **no detectable difference** |  | `<commit>` |
| E03d | 2026-11-18 | +7 db4 wavelet sub-band energies (second feature domain) | macro-F1 0.646 (sd 0.046, range 0.55–0.74 across 25 record-grouped folds); κ 0.529; F1 N/A/O/~ 0.83/0.56/0.52/0.67 | vs E02: Δ -0.023, 9/25 folds — **real loss** |  | `<commit>` |
| E03e | 2026-11-18 | +3 Hilbert-envelope periodicity features (rhythm regularity without a beat detector) | macro-F1 0.669 (sd 0.050, range 0.57–0.78 across 25 record-grouped folds); κ 0.553; F1 N/A/O/~ 0.84/0.60/0.53/0.71 | vs E02: Δ +0.001, 11/25 folds — **no detectable difference** |  | `<commit>` |
| E04 | 2026-11-18 | morphology on top of the rhythm features | macro-F1 0.777 (sd 0.046, range 0.68–0.85 across 25 record-grouped folds); κ 0.684; F1 N/A/O/~ 0.87/0.75/0.70/0.79 | vs E03a: Δ +0.008, 13/25 folds — **no detectable difference** |  | `<commit>` |
| E05 | 2026-11-18 | every feature group together (62 features) | macro-F1 0.780 (sd 0.045, range 0.69–0.85 across 25 record-grouped folds); κ 0.690; F1 N/A/O/~ 0.88/0.75/0.70/0.80 | vs E03a: Δ +0.011, 15/25 folds — **no detectable difference** |  | `<commit>` |
| E06 | 2026-11-18 | parametric AR spectrum instead of Welch for the band-power features | macro-F1 0.766 (sd 0.053, range 0.67–0.87 across 25 record-grouped folds); κ 0.671; F1 N/A/O/~ 0.87/0.78/0.68/0.74 | vs E03a: Δ -0.004, 10/25 folds — **no detectable difference** |  | `<commit>` |
| E07a | 2026-11-18 | gradient boosting instead of random forest | macro-F1 0.764 (sd 0.059, range 0.65–0.90 across 25 record-grouped folds); κ 0.664; F1 N/A/O/~ 0.86/0.79/0.68/0.73 | vs E03a: Δ -0.006, 12/25 folds — **no detectable difference** |  | `<commit>` |
| E07b | 2026-11-18 | RBF-SVM (scaled) instead of random forest | macro-F1 0.761 (sd 0.048, range 0.68–0.84 across 25 record-grouped folds); κ 0.676; F1 N/A/O/~ 0.86/0.77/0.72/0.70 | vs E03a: Δ -0.009, 10/25 folds — **no detectable difference** |  | `<commit>` |
| E08a | 2026-11-18 | no class weights: does the minority-class handling matter? | macro-F1 0.761 (sd 0.058, range 0.65–0.86 across 25 record-grouped folds); κ 0.665; F1 N/A/O/~ 0.87/0.76/0.68/0.74 | vs E03a: Δ -0.008, 9/25 folds — **no detectable difference** |  | `<commit>` |
| E08b | 2026-11-18 | SMOTE inside the fold instead of class weights | macro-F1 0.772 (sd 0.056, range 0.67–0.88 across 25 record-grouped folds); κ 0.684; F1 N/A/O/~ 0.87/0.76/0.71/0.75 | vs E03a: Δ +0.002, 13/25 folds — **no detectable difference** |  | `<commit>` |
| E09 | 2026-11-18 | keep the 25 most informative of 62 features (fit inside each fold) | macro-F1 0.766 (sd 0.044, range 0.67–0.84 across 25 record-grouped folds); κ 0.671; F1 N/A/O/~ 0.87/0.76/0.69/0.75 | vs E05: Δ -0.014, 7/25 folds — **no detectable difference** |  | `<commit>` |
| E10 | 2026-11-18 | REVISIT E01c: is denoising still harmful once the detector is robust? | macro-F1 0.766 (sd 0.058, range 0.65–0.86 across 25 record-grouped folds); κ 0.672; F1 N/A/O/~ 0.87/0.77/0.68/0.75 | vs E03a: Δ -0.003, 13/25 folds — **no detectable difference** |  | `<commit>` |
| E11 | 2026-11-18 | REVISIT: denoise for rhythm, but quality features from the raw strip | macro-F1 0.774 (sd 0.052, range 0.69–0.87 across 25 record-grouped folds); κ 0.680; F1 N/A/O/~ 0.87/0.78/0.68/0.77 | vs E10: Δ +0.008, 15/25 folds — **no detectable difference** |  | `<commit>` |
| E12 | 2026-11-18 | REVISIT E02: the rhythm features with the supplied detector — how much rests on R-peaks? | macro-F1 0.650 (sd 0.069, range 0.50–0.75 across 25 record-grouped folds); κ 0.531; F1 N/A/O/~ 0.81/0.69/0.57/0.52 | vs E03a: Δ -0.119, 2/25 folds — **real loss** |  | `<commit>` |

**Kept after the development set:** E02 (our Pan–Tompkins) and E03a (rhythm features). Everything else
was *no detectable difference* or a *real loss* on 431 records, so we kept the simpler pipeline
`{qrs: pt, feature_set: base+rr, clf: rf, imbalance: balanced, preprocess: none}`.
E04/E05 (morphology, all groups) were the closest calls (+0.008/+0.011) and are re-tested on the large set.

## Iteration log — final comparison on the large training set (fill in from `results/full2000/table.md`)

Records used: ____ (N __ · A __ · O __ · ~ __), downloaded with `get_data.py --subset ____`.

| # | Date | What changed & why | Primary metric with spread | Better than reference? | If not — why kept | Commit |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Decision log

| Pipeline module | Option chosen | Alternative(s) considered | Why this one | Iteration | Revised later? |
|---|---|---|---|---|---|
| 1. Data loading | 431-record dev set, then ≥ 2,000 records for the final comparison | full 8,528 | course minimum is ~2,000; dev set keeps iterations fast | E00 | — |
| 2. Preprocessing | none | band-pass + notch (E01a), wavelet (E01b), denoise (E01c) | no detectable gain; the spectrum (fig 2) has no 50/60 Hz line and almost nothing above 40 Hz, so there is no hum to remove | E01 | **yes, E10** — see revisions |
| 3a. QRS detection | Pan–Tompkins with adaptive thresholds + search-back | supplied single 30 %-threshold detector | +0.035 macro-F1; agrees with wfdb XQRS on 96–99 % of beats vs 82–89 % (qrs_agreement.md) | E02 | confirmed by E12 |
| 3b. Features | base + 21 rhythm features | + morphology, SQI, wavelet, envelope, all | rhythm features +0.101 (25/25 folds); the rest added nothing detectable on top | E03–E05 | re-tested on full data |
| 3c. Spectral estimator | Welch | AR (E06) | no detectable difference; Welch is the non-parametric default with no model order to justify | E06 | — |
| 4. Feature selection | none | mutual information top-25 (E09) | −0.014, worse in 18/25 folds (not detectable) — no reason to add a stage; the forest handles 62 features itself. MI scoring seeded so the run is reproducible | E09 | — |
| 5. Classifier | random forest, 200 trees | gradient boosting (E07a), RBF-SVM (E07b) | no detectable difference; RF is the supplied, simpler, seed-stable choice | E07 | re-tested on full data |
| 5. Imbalance | class weights (`balanced`) | none (E08a), SMOTE (E08b) | no detectable difference on macro-F1; weights keep AF/Noisy recall up without inventing records | E08 | — |
| 6. Inference | `write_submission()` with the frozen `FittedModel` | — | course requirement; cfg parity is enforced by the scaffold | final | — |
| 7. Reporting | macro-F1 ± SD + range over 25 folds, κ, per-class F1/recall, confusion, F1(N,A,O) | pooled number only | rubric criteria 3, 7, 8 | all | — |

## Revisions — decisions we went back and changed

| # | The downstream result that triggered it | Which earlier decision it indicted | What we changed | What happened to the metric |
|---|---|---|---|---|
| 1 | E12: our rhythm features with the **supplied** detector lose −0.119 (2/25 folds better), and the XQRS check shows that detector fails on 21 % of Normal records | E01c's conclusion "denoising hurts" (−0.029, a *real loss*) — it was measured with the fragile detector, which breaks when the filtered signal changes its global threshold | re-ran denoising with the robust detector (E10), and with quality features on the raw strip (E11) | loss disappears: −0.029 → −0.003 (no detectable difference). Preprocessing stays "none", but now because there is nothing in the spectrum to remove — not because filtering is harmful |
| 2 | *(full data)* | *e.g. E04: morphology features rejected on the dev set* | *if E04/E05 is a real gain on ≥ 2,000 records, switch `feature_set` and log it here* |  |

## Who did what

| Iteration | Who | Modules / tasks owned | Reviewed by |
|---|---|---|---|
| dev set | Shakeel | harness, classifier/imbalance/selection experiments (E06–E09) |  |
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
| **Configurations compared** | 21 on the dev set + __ on the full set | dev set / full-set short list |
| How option comparison was kept separate from final reporting | comparison budget fixed in advance; final short list re-run on the larger set |  |
