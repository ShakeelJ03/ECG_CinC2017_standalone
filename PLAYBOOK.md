# Team playbook: ECG CinC-2017 capstone, from now to 10 December

This file tells the team what we're expected to deliver, what "iterations" means, what has already
been done, and exactly what to do next. Read it once top to bottom before the next meeting.

---

## 1. What we must hand in

**Team deliverables, due Thursday 10 December, 08:00, one Canvas submission per team**
("Capstone Project Report & Predictions"):

| Deliverable | What it is | Where it comes from |
|---|---|---|
| Report (PDF) | at most 20 pages (references and appendix not counted). Introduction, Methods, Results, Discussion, then a Contributions line for each member. Put the repo link and the final-model commit in it. No pasted code. | written by all three of us (§7) |
| `predictions.csv` | our labels for the 120 hold-out records. It must be written by `write_submission()`, never by hand. Don't score it and don't change the model afterwards. | `experiments/final.py predict` |
| Repo link | Graders will clone the repo, install from the lock file and reproduce our numbers. | this repo |

**What the repo must contain:**
- the code and a `README.md` with the run commands (done)
- `requirements-lock.txt` (done)
- `RESULTS.md`, the iteration log (pre-filled for the dev set, see §4)
- `EXPECTED_SCORE.md`, our cross-validated score (mean ± SD), split unit and final-model commit. It
  must be **committed before we download the hold-out**, because that commit time is our
  "registration".

**Presentation:** a 10–15 min talk plus 5–10 min of Q&A at the showcase. **Each of us will get at least one
question about a part we did not build**, so everyone has to understand the whole pipeline.

**Individual work (10 points, each person separately):**
- a 300–500 word essay comparing our project with the shadow team T7 (Sleep-EDF), due shortly
  after the showcase
- a private peer evaluation
- a 150–300 word reflection on one disagreement or workload imbalance

---

## 2. What "iterations" means

An iteration is one controlled experiment:

1. Take the current best pipeline.
2. Change **one thing** (a filter, a feature group, a classifier…).
3. Run it with exactly the same evaluation.
4. Compare, and decide whether to keep the change.
5. Write one row in `RESULTS.md`: what you changed and why, the score **with its spread**,
   whether it was better, and the commit.

Doing this over and over is "iterating". The grade comes from the *evidence trail*, not from the
best number:

- **≥ 2 alternatives at each stage, changed one at a time.** We have 21 (§4).
- **At least one idea that didn't help, reported honestly.** We have several: denoising and wavelet
  features (real losses), feature selection, AR spectra, other classifiers (no gain).
- **At least one earlier decision we went back and changed because of a later result.** This is
  the "revisit" (Criterion 9). We have one already (§4) and a second will very likely come from the
  large-data run.
- **Every number has its spread.** We show the SD and range across folds, never one pooled number.
- **A difference smaller than the noise is not a result.** Our harness measures how much the score
  moves when *nothing* changes but the fold seed, about 0.01–0.02 macro-F1 here. Smaller
  differences are labelled "no detectable difference". Saying that is a good result.

---

## 3. Why our teammates' runs took 40 minutes, and the fix

Each run re-downloaded and/or re-parsed the records and recomputed every feature. Now:

- the data is downloaded **once**, into a folder outside the repo (`get_data.py`)
- parsed records are cached (`load_cached`)
- the feature matrix is cached **per configuration**, so changing only the classifier takes
  seconds

On my machine, the whole 21-experiment plan took **4.5 minutes** on the 431 records. One experiment
on 2,000 records takes about a minute, and the 8-experiment final comparison about 10–15 minutes.

Keep the data folder **outside OneDrive**, e.g. `C:\cm2013_data\ecg\train`. OneDrive syncing
thousands of small files is painfully slow.

---

## 4. What's been done: the development results (431 records)

**Literature review in one paragraph.** On this dataset the winning entries all built on
*rhythm irregularity* features from well-detected R-peaks: Poincaré plots, entropy, successive
differences. They added P-wave/morphology features and signal-quality measures, and fed them to
tree ensembles: random forest (Zabihi et al.), XGBoost (Teijeiro et al.) or cascaded binary
classifiers (Datta et al.). Some combined these with deep networks (Hong et al.). A plain random
forest on good hand-made features tied for first place, so **features matter more than the
classifier**. Note that the Challenge's 0.83 is the mean F1 over **N, A and O only** (Noisy
excluded). Our course metric is the 4-class macro-F1, so we report both. Full references are in §9.

**What we found, in the order we did it.** Numbers are macro-F1, mean ± SD over 25 folds:

| Stage | Experiment | Result | Decision |
|---|---|---|---|
| — | **E00** supplied baseline | **0.634 ± 0.071** | the floor |
| 2 Preprocessing | E01a band-pass + notch · E01b wavelet · E01c denoise | −0.008 · +0.004 · **−0.029 (real loss)** | keep "none" |
| 3 QRS detection | **E02** our Pan–Tompkins (adaptive thresholds, search-back) | **0.668**, +0.035, real gain | **keep** |
| 3 Features | **E03a** +21 rhythm features | **0.770**, +0.101, better in 25/25 folds | **keep** |
| 3 Features | E03b morphology (+0.051 alone) · E03c SQI · E03d wavelet (loss) · E03e envelope | only morphology helps on its own | — |
| 3 Features | E04 rhythm + morphology · E05 all 62 features | 0.777 · 0.780, not detectable over E03a | re-test on 2,000 |
| 3 Spectral | E06 AR instead of Welch | −0.004 | keep Welch |
| 5 Classifier | E07a gradient boosting · E07b SVM | −0.006 · −0.009 | keep random forest |
| 5 Imbalance | E08a no weights · E08b SMOTE | −0.008 · +0.002 | keep class weights |
| 4 Selection | E09 mutual-info top-25 of 62 | −0.014, worse in 18/25 folds | no selection |
| **Revisits** | E10 denoise again, with the good detector · E11 + quality on raw · E12 rhythm features with the old detector | −0.003 · +0.008 · **−0.119** | see below |

**Current best (E03a): macro-F1 0.770 ± 0.057, κ 0.675, Challenge-style F1(N,A,O) 0.778.** That
is +0.136 over the supplied baseline and about 0.05 below the winners.

**Three findings that make a good report story:**

1. **The supplied R-peak detector is the bottleneck.** It uses one threshold for the whole record
   (30 % of the biggest peak), so a single artifact spike hides every real beat. It disagrees
   with an independent detector (wfdb XQRS) on 21 % of Normal and 23 % of Other records. Ours
   disagrees on 4 % and 2% (`results/dev431/figures/qrs_agreement.md`, fig 1). Every rhythm feature
   sits on top of the R-peaks, which is why E12 collapses.
2. **There is no mains hum to filter.** The spectrum (fig 2) shows no 50 or 60 Hz line and almost
   nothing above 40 Hz, because the AliveCor device already band-limits the signal. So we
   *show* that, instead of notch-filtering by habit, as Farhad asked. It also means the supplied
   "powerline power" feature measures almost nothing.
3. **The revisit (Criterion 9).** E01c said denoising is a *real loss*. But E12 showed that the old
   detector breaks easily, and E01c had been run with it. With the robust detector (E10) the loss
   disappears (−0.029 → −0.003). So the earlier conclusion was wrong for the right reason, and we
   changed why preprocessing stays off: not "filtering hurts" but "there's nothing in the spectrum
   to remove".

**Where the errors are now** (fig 5): a third of the Other records are still called Normal. That
makes sense, because "Other" covers ectopic beats, bundle branch blocks and so on, and many of those
show up in *beat shape* rather than rhythm. So the morphology features are the most promising next
lever, and they're exactly what the full-data run re-tests.

**Honest caveat:** these are on 431 records, the allowed development set. The course requires the
**final comparison and the final model to use ≥ 2,000 records**. That's step 3 below.

---

## 5. What to do, step by step

### Step 1: everyone, this week (about 30 min each)
1. Pull the updated repo, create the venv, and install the lock file (README → Install).
2. Run the development plan:
   `python experiments/run_experiments.py --data data_cache/ecg_cinc2017 --tag dev431`
   You should get exactly the numbers in §4 (E00 = 0.634, E03a = 0.770). If you do, the
   environment is right.
3. Read `tracks/ecg_team.py`, at least the docstrings. Everyone must be able to explain the
   whole pipeline at the Q&A.

### Step 2: the PM / Shakeel, once
Commit the update and put your commit hash into the `<commit>` cells of `RESULTS.md`. Fill in the
"Who did what" table.

### Step 3: download ≥ 2,000 records and run the final comparison (one person, about 30 min)
```
python experiments/get_data.py --out C:/cm2013_data/ecg/train --subset 2000
python experiments/run_experiments.py --data C:/cm2013_data/ecg/train --tag full2000 --set final
python experiments/figures.py --data C:/cm2013_data/ecg/train --tag full2000
```
`--set final` re-runs the 8-experiment short list (E00, E02, E03a, E04, E05, E07a, E07b, E10).
Paste `results/full2000/table.md` into the second table of `RESULTS.md` and write the record count.

**How to decide the final pipeline** (rule fixed in advance):

- If **E04 or E05 is a "real gain"** over E03a on the full data, switch to it and log it as
  **revision #2**. Trigger: "with 4.6× more records the morphology features become
  detectable". This is the most likely outcome, because more data makes small gains visible.
- Same rule for E07a (boosting).
- Otherwise E03a stays.

Then update `FINAL_CFG` in `experiments/final.py` to match.

### Step 4: optional extra ideas (only if there's time, one change at a time)
Each takes about an hour, and all are from the literature:
- **Lead-inversion fix for morphology:** a better polarity detector, since ~15 % of strips are
  upside down (Teijeiro et al.).
- **Noisy-class rule:** if bSQI < 0.6, predict `~` (a two-stage design like Datta's cascade).
- **More data:** `--subset 4000` helps AF and Noisy the most.
- **Per-class threshold moving on AF:** chosen *inside* the folds, never on the hold-out.

Log each one, including the ones that don't help.

### Step 5: freeze, register, predict (PM, around 1 December)
```
python experiments/final.py expected --data C:/cm2013_data/ecg/train
git add EXPECTED_SCORE.md && git commit -m "Register expected score" && git push
python experiments/final.py predict --holdout C:/cm2013_data/ecg/holdout
git add predictions.csv && git commit -m "Hold-out predictions (final model)" && git push
```
The script refuses to predict until `EXPECTED_SCORE.md` is committed. After this, don't touch the
model again.

### Step 6: report, slides, rehearsal (§7)

---

## 6. Suggested roles, matching the course's four roles

| Person | Role | Owns in the report and Q&A |
|---|---|---|
| Shakeel | ML engineer | harness and validation (§2 logic), classifier/imbalance/selection experiments E06–E09, final model, `EXPECTED_SCORE.md`, `predictions.csv` |
| Manfred or Miguela | Preprocessing lead | spectrum analysis, E01 filters, the Pan–Tompkins detector and its XQRS check, revisits E10–E12 |
| the other | Feature engineer | rhythm/morphology/SQI/wavelet/envelope features, E03–E05, Poincaré figure, the literature behind each feature |
| one of the three | PM (doubled up) | ClickUp, `RESULTS.md` upkeep, merging the report, slides, deadlines |

Each owner runs their own experiments on the full data, writes their Methods/Results section, and
explains it at the showcase. Shakeel reviews everyone's part, so he knows the whole pipeline.

**Schedule:**

| Dates | Goal |
|---|---|
| Nov 18–22 | Step 1–3: everyone reproduces the dev numbers; full-data final comparison done |
| Nov 23–29 | optional extras (step 4); freeze, register and predict (step 5); final figures |
| Nov 30–Dec 6 | write the report (each owner writes their section; PM merges) |
| Dec 7–9 | proofread, check the repo reproduces from a fresh clone, slides, rehearse Q&A |
| **Dec 10, 08:00** | submit on Canvas |

---

## 7. Report outline (≤ 20 pages)

1. **Introduction (1.5 p).** AF definition (irregularly irregular RR, absent P waves); why
   single-lead handheld screening matters; the dataset (8,528 AliveCor strips, 300 Hz, 4 classes,
   imbalanced); the yardstick (winners F1(N,A,O) ≈ 0.83) and the metric difference; our aim.
2. **Methods (6–7 p).**
   - data: records used, hold-out exclusion
   - evaluation: record split, the 25 paired folds, noise floor, decision rule, comparison budget
   - preprocessing and spectrum check (fig 2)
   - QRS detection and its XQRS validation (fig 1, table)
   - feature groups with citations (Poincaré fig 3)
   - classifiers and imbalance handling
3. **Results (5–6 p).**
   - the iteration figure (fig 4)
   - a table of all experiments
   - per-class F1 and confusion matrices, baseline vs final (fig 5)
   - the revisits
   - dev vs full-data numbers
   - the expected score
4. **Discussion (3–4 p).**
   - what helped and why: detection plus rhythm features
   - what didn't: filtering, selection, other classifiers
   - A↔O confusion and Noisy errors (look at a few misclassified records)
   - comparison with the winners and why we're below them: no relabelling, no deep models,
     simpler morphology
   - limitations: label noise, one dataset, the hold-out's balanced class mix
5. **Contributions:** one line each.

---

## 8. Q&A preparation: questions every one of us should be able to answer

- Why is the split by record, and what would leak if we didn't? Why fit the scaler inside the fold?
- Why macro-F1 and not accuracy? Why is our 0.77 not directly comparable to the winners' 0.83?
- How do you know +0.008 is not an improvement? (Noise floor, paired folds.)
- Why no notch filter? (Fig 2: no 50/60 Hz line.)
- Why does the supplied detector fail, and how does Pan–Tompkins fix it?
- What do SD1/SD2, sample entropy and the Lorenz plot measure, and why do they separate AF?
- How is the Noisy class handled? Why can denoising make Noisy harder to detect?
- Which decision did you revisit, and what triggered it?
- What did `EXPECTED_SCORE.md` register, and why commit it before the hold-out?

---

## 9. References for the literature review

1. Clifford GD, Liu C, Moody B, et al. AF classification from a short single lead ECG recording: the PhysioNet/Computing in Cardiology Challenge 2017. *Computing in Cardiology* 2017;44. doi:10.22489/CinC.2017.065-469
2. Pan J, Tompkins WJ. A real-time QRS detection algorithm. *IEEE Trans Biomed Eng* 1985;32(3):230–236. doi:10.1109/TBME.1985.325532
3. Task Force of the ESC and NASPE. Heart rate variability: standards of measurement, physiological interpretation and clinical use. *Circulation* 1996;93(5):1043–1065.
4. Teijeiro T, García CA, Castro D, Félix P. Abductive reasoning as the basis to reproduce expert criteria in ECG atrial fibrillation identification. *Physiol Meas* 2018;39(8):084006 (arXiv:1802.05998).
5. Datta S, Puri C, Mukherjee A, et al. Identifying normal, AF and other abnormal ECG rhythms using a cascaded binary classifier. *Computing in Cardiology* 2017;44.
6. Zabihi M, Bahrami Rad A, Katsaggelos AK, Kiranyaz S, Narkilahti S, Gabbouj M. Detection of atrial fibrillation in ECG hand-held devices using a random forest classifier. *Computing in Cardiology* 2017;44.
7. Hong S, Wu M, Zhou Y, et al. ENCASE: an ENsemble ClASsifiEr for ECG classification using expert features and deep neural networks. *Computing in Cardiology* 2017;44.
8. Li Q, Mark RG, Clifford GD. Robust heart rate estimation from multiple asynchronous noisy sources using signal quality indices and a Kalman filter. *Physiol Meas* 2008;29(1):15–32. (bSQI)
9. Lake DE, Moorman JR. Accurate estimation of entropy in very short physiological time series: the problem of atrial fibrillation detection in implanted ventricular devices. *Am J Physiol Heart Circ Physiol* 2011;300(1):H319–H325. (COSEn)
10. Sarkar S, Ritscher D, Mehra R. A detector for a chronic implantable atrial tachyarrhythmia monitor. *IEEE Trans Biomed Eng* 2008;55(3):1219–1224. (Lorenz-plot AF evidence)
11. Brennan M, Palaniswami M, Kamen P. Do existing measures of Poincaré plot geometry reflect nonlinear features of heart rate variability? *IEEE Trans Biomed Eng* 2001;48(11):1342–1347.
12. Richman JS, Moorman JR. Physiological time-series analysis using approximate entropy and sample entropy. *Am J Physiol Heart Circ Physiol* 2000;278(6):H2039–H2049.

Course book sections: QRS morphology §1.4, band-pass + notch §9.6, Pan–Tompkins §9.9, HRV §7.11,
signal quality §8.2, validation Ch. 12, iteration §16.3.
