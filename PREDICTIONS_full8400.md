# Predictions for the all-data comparison — written BEFORE running it

Predictions were written before each run (18–19 Nov), but the prediction files only reached git on 25 Nov, so the git history does not itself prove the order. The run itself was at commit `b009d3f`.

Why this iteration: after round 2 on 1,999 records, Noisy (~) is still the weakest class (F1 0.58,
59 records, 3 % of the data), and two feature/classifier changes aimed at it did nothing (E13, E14).
Our diagnosis was "data-limited, not feature-limited". Farhad's email: more records "helps the rare
classes". So the one change in this iteration is **the amount of training data**: all CinC-2017
training records except the 120 hold-out ids (`get_data.py --subset 8528`), into a separate folder.

Same harness, same 25-fold scheme, same decision rule, same 10 configurations as on 1,999 records.

Data: **8,408 records** (N 5046 · A 728 · O 2385 · ~ 249) — every CinC-2017 training record except the 120 hold-out ids, downloaded 2026-11-19 with `get_data.py --subset 8528` into `C:/cm2013_data/ecg/train_full`. Versus 1,999: 4.2× more records overall, **4.2× more Noisy** (59 → 249).

| Run | Prediction (before running) | Why we expect it | What happened | Right? |
|---|---|---|---|---|
| E00 baseline | about 0.58–0.63; Noisy F1 up a little vs 0.37 | more Noisy examples, but the supplied detector still fails on noisy strips | 0.614 ± 0.020; Noisy 0.37 | level yes; Noisy no (unchanged) |
| E02 our detector | real gain over E00 | detector failures don't depend on data size | +0.061, 25/25, real gain | yes |
| E03a rhythm features | real gain over E02 | as on both earlier sets | +0.037, 25/25, real gain | yes |
| **E04 + morphology** | real gain over E03a; macro-F1 about 0.76–0.79; **Noisy F1 up from 0.58 to about 0.63–0.70**; F1(N,A,O) about 0.81–0.82 | the test of our diagnosis: if Noisy is data-limited, ~5× more Noisy records should lift it clearly | +0.032, 25/25, real gain; 0.744 ± 0.017; **Noisy 0.57**; F1(N,A,O) 0.801 | gain yes; level, Noisy and F1(N,A,O) **no** — the diagnosis is falsified |
| E05 all features | about the same as E04 | extra groups added nothing on either earlier set | 0.745 ± 0.019 (E04 0.744) | yes |
| E07a boosting (E03a features) | no detectable difference, possibly a small real gain | boosting tends to gain more from data than a random forest | +0.004, 18/25, no detectable difference | yes |
| E07b SVM | no detectable difference or a real loss | as before | −0.030, 1/25, real loss | yes |
| E10 denoise (revisit) | no detectable difference | no hum to remove | +0.000, 12/25, no detectable difference | yes |
| E13 E04 + quality indices | no detectable difference | redundant with template correlation; more data doesn't change that | +0.001, 17/25, no detectable difference | yes |
| **E14 boosting (E04 features)** | **possibly a real gain** over RF | the one place where more data could change our classifier decision | **+0.012, 20/25, real gain**; 0.756 ± 0.018, κ 0.688, F1(N,A,O) 0.807; Noisy 0.60 | yes |

What would change the final pipeline (rule unchanged — switch only on a *real gain*):
- E04 stays best → final model = E04 retrained on all records (more data, same pipeline).
- E14 a real gain → final model switches to boosting (Revision 3).

## Reflection (fill in after the run)

- **Was Noisy really data-limited? No.** With 4.2× more Noisy records (59 → 249), E04's Noisy F1
  stayed put (0.58 → 0.57), and the supplied baseline's too (0.37 → 0.37). Our round-2 diagnosis is
  falsified. What limits Noisy is more likely the labels: the Challenge paper (Clifford et al. 2017)
  reports that the Noisy class had the poorest agreement between expert annotators — strips one
  reader calls noisy another reads as Normal. More examples of an inconsistent label don't help.
- **Other wrong predictions:** the overall level (E04 0.744, predicted 0.76–0.79) — because Noisy didn't
  move and N/A/O were already near their ceiling for these features (F1(N,A,O) 0.802 → 0.801).
- **What more data did do:** fold SDs roughly halved (E04 0.031 → 0.017; noise floor ≈ 0.003), so the
  comparison became much more sensitive. The random forest had already plateaued (E04 0.747 on 1,999
  vs 0.744 on 8,408), while gradient boosting gained from the extra data (E14 0.741 → 0.756) — the
  pattern we predicted for E14.
- **Final decision (rule unchanged):** E14 is a real gain over E04 → **Revision 3**: switch the
  classifier to gradient boosting, train on all 8,408 records. Boosting settings were fixed in the
  code before any run (learning rate 0.05, 300 iterations, 15 leaves, L2 1.0, class weights) and were
  never tuned on these results.

## Round 2 — targeting the Other class (`--set ectopy`), written 2026-11-25 BEFORE running on 8,408 records

Why: on 8,408 records the largest remaining error is **Other called Normal**; Other F1 is 0.73. Our
features describe the *average* beat, but "Other" is mostly about the *few* beats that differ. From
the literature: Teijeiro et al. (2017 winners) define Other by extrasystoles/ventricular beats,
wide QRS and long PR; Andreotti et al. (Oxford, `beat_class.m`) split beats into two shape templates
to find the ectopic ones. So one change: **+7 beat-by-beat ectopy features** on top of E14.

The features: fraction of abnormal-shape beats (corr < 0.85 with the template); fraction that are
also premature (RR < 85 % of the local median) — the premature-ventricular-beat signature; QRS width
of the abnormal-beat template; correlation between the two templates; 90th-percentile QRS width;
fraction of beats wider than 1.5× the main template; P-peak-to-R-peak interval (PR proxy).

Code check on the dev set (431 records, 113 Other) before writing this: no detectable difference
(Δ +0.000 vs E14), Other F1 0.69 → 0.70. The dev set is too small to judge a gain in one class.

Reference: E14 (macro-F1 0.756 ± 0.018, Other F1 0.73, F1(N,A,O) 0.807).

| Run | Prediction (before running) | Why we expect it | What happened | Right? |
|---|---|---|---|---|
| E15 E14 + 7 ectopy features | **Other F1 up to about 0.74–0.76**; macro-F1 +0.005 to +0.015 — likely a **real gain** with 2,385 Other records, but "no detectable difference" is quite possible | the features target exactly the strips E04's averages miss (isolated ectopic beats); boosting can use rare-event features well; but E04's beat-correlation features already carry part of this |  |  |

Decision rule (unchanged): switch only on a *real gain*, then freeze for good — no more rounds.

### Reflection, round 2 (fill in after the run)

-
