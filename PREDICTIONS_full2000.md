# Predictions for the final comparison (1,999 records) — written BEFORE running it

Written on 18 Nov before `run_experiments.py --tag full2000 --set final` was run (it ran at commit `07f7809`). Predictions were written before each run (18–19 Nov), but the prediction files only reached git on 25 Nov, so the git history does not itself prove the order. After the run
we filled in "What happened" and the reflection ("Reflect & improve", step 1 of the track notebook:
*was your prediction right? If the number surprised you, why?*).

Data: 1,999 training records — N 1200 · A 173 · O 567 · ~ 59 (`get_data.py --subset 2000`, hold-out
excluded). Compared with the dev set (431: N 238 · A 40 · O 113 · ~ 40), AF has 4.3× more examples,
Other 5×, but Noisy only 1.5× — and Noisy drops from 9 % to 3 % of the data.

## Round 1 — the final comparison (`--set final`)

| Run | Prediction (before running) | Why we expected it | What happened | Right? |
|---|---|---|---|---|
| E00 baseline | macro-F1 about 0.60–0.66; Noisy F1 lower than on the dev set | same features; Noisy is now only 3 % of the data, and the supplied detector fails most on Noisy strips | 0.590 ± 0.041; Noisy F1 0.37 (dev 0.58) | partly — Noisy fell as predicted, the overall level was below the range |
| E02 our detector | real gain over E00 again | the detector failures we measured don't depend on how many records we have | +0.061, 24/25 folds, **real gain** | yes |
| E03a rhythm features | real gain over E02; macro-F1 about 0.75–0.80 | AF's defining irregularity; dev gain was +0.10 in 25/25 folds | +0.057, 22/25, **real gain**; macro-F1 0.707, F1(N,A,O) 0.784 | gain yes, level no — N/A/O are as good as on the dev set (F1(N,A,O) 0.784 vs 0.778), Noisy (0.48) pulls the 4-class mean down |
| E04 + morphology | **real gain over E03a**, mostly in Other | 5× more Other records; Other shows in beat shape | +0.040, 21/25, **real gain**; Noisy 0.48 → 0.58, AF 0.78 → 0.81, Other 0.69 → 0.71 | gain yes, "mostly Other" no — most of it is Noisy |
| E05 all features | about the same as E04 | SQI/wavelet/envelope added nothing on the dev set | 0.739 vs E04 0.747 (19 more features, slightly lower) | yes |
| E07a gradient boosting | no detectable difference vs RF, maybe a small gain | boosting needs more data | +0.012, 13/25, no detectable difference | yes |
| E07b SVM | no detectable difference vs RF | with good features the classifier matters little | −0.012, 7/25, no detectable difference | yes |
| E10 denoise (revisit) | no detectable difference vs E03a | no hum in the spectrum; dev revisit already showed this | +0.004, 13/25, no detectable difference | yes |

Expected weakest class: **Noisy** — right (0.58 even in E04). Expected main confusion: Other → Normal — check in fig 5.

### Reflection, round 1

- **Right:** both real gains (detector, rhythm features), classifier choice not mattering, denoising
  neutral, Noisy being the weakest class. 6 of 8 predictions fully right.
- **Wrong, and why:** (1) the absolute levels were lower than on the dev set. That's not a
  regression: Noisy fell from 9 % to 3 % of the data with only 59 examples, so its F1 drops and drags
  the 4-class macro-F1 down, while F1(N,A,O) stayed the same. Lesson: never compare numbers across
  datasets, only within one. (2) The morphology gain came mostly from Noisy, not Other. In hindsight
  that fits: beat-to-template correlation and R-amplitude variability measure how consistent the
  beats are, which is also a signal-quality measure.
- **Decision revisited:** on the dev set we left morphology out (+0.008, below the noise). With 4.6×
  more data it is a real gain (+0.040, 21/25 folds). We reversed the decision → **Revision 2** in
  RESULTS.md; `FINAL_CFG` is now E04.
- **What it sent us to next:** Noisy is still the weakest class (0.58) → round 2.

## Round 2 — targeting the Noisy class (`--set noisy`), written before running on the full data

Reference: E04 (macro-F1 0.747 ± 0.031, Noisy F1 0.58). Two runs, one change each. (The code was
smoke-tested on the dev set first: both runs there were no detectable difference.)

| Run | Prediction (before running) | Why we expect it | What happened | Right? |
|---|---|---|---|---|
| E13 E04 + 9 signal-quality indices | Noisy F1 up a little (to about 0.60–0.65); overall **no detectable difference** or a small real gain | these are built for Noisy (detector agreement, spectral entropy, clipping, RMS bursts), but E04's template correlation already captures part of the same thing, and 59 Noisy records is very few | 0.742 ± 0.035, Δ −0.005, 12/25 folds, no detectable difference; Noisy F1 0.58 → 0.55 | overall yes, Noisy no |
| E14 E04 with gradient boosting | **no detectable difference** vs RF | on E03a boosting was +0.012, not detectable; more features shouldn't change that much | 0.741 ± 0.034, Δ −0.007, 10/25 folds, no detectable difference | yes |

Decision rule (unchanged): switch only on a *real gain*; otherwise keep E04 and freeze.

### Reflection, round 2

- **Right:** neither change is detectable overall; the classifier still doesn't matter.
- **Wrong, and why:** the quality indices did not lift Noisy (0.58 → 0.55, inside the noise). E04
  already measures quality through beat-to-template correlation and the four supplied quality
  features, so the new indices are largely redundant; and with 59 Noisy records (3 %) the class is
  limited by data, not by features. Nine extra weak features can even dilute the random forest's
  feature sampling slightly.
- **Reference chain reproduced exactly** (E00–E04 identical to round 1).
- **Decision:** no real gain → keep E04 and freeze. Noisy remains the main limitation; more Noisy
  examples (a larger download) is the most promising future work.
