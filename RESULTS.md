# Results log — `ecg_cinc2017`, Shakeel · Manfred · Miguela

**Track:** `ecg_cinc2017` · **Split unit:** `record` · **Primary metric:** macro-F1 (κ reported alongside) ·
**Evaluation mode(s):** new-record (GroupKFold(5) by record, via `t.evaluate`)

**Dataset:** 431 real records (a stratified subset of the CinC-2017 training set, ≥ 40 per class) in
`data_cache/ecg_cinc2017/`. Class counts: N 238 · A 40 · O 113 · ~ 40. Every row below uses these
same records, the same folds and seed 0, unless the row says otherwise.

## Iteration log

Each row reports the metric with its spread (`rep["summary"]`), the confusion matrix and the per-class recall
(confusion rows = true, cols = N A O ~).

| # | Date | What changed & why (one line) | macro-F1 **with spread** · κ | Per-class recall (N / A / O / ~) | Better than previous? | If not — why it was kept | Commit |
|---|---|---|---|---|---|---|---|
| 1 | 2026-10-10 | Supplied baseline, unchanged (`python run_ecg.py`), to set the floor | pooled 0.653 · fold mean 0.649 (sd 0.057, range 0.573–0.718 across 5 folds) · κ 0.522 | 0.73 / 0.65 / 0.62 / 0.75 | — (baseline) | — | `5d2b323` |

**Row 1 — confusion matrix**

| true \ pred | N | A | O | ~ |
|---|---|---|---|---|
| **N** | 173 | 3 | 40 | 22 |
| **A** | 1 | 26 | 12 | 1 |
| **O** | 25 | 11 | 70 | 7 |
| **~** | 5 | 1 | 4 | 30 |

What the baseline shows:
- **N↔O is the largest error.** 40 N records are called O and 25 O records are called N. With only R-R
  statistics, a normal strip with some ectopic beats looks like "Other".
- **A→O (12/40) is the main AF error**, not A→N. The model can tell AF is irregular, but it can't
  separate AF's irregularity from other irregular rhythms. Features that measure the absence of P waves
  or atrial activity might target this.
- **N→~ (22).** Normal strips with some noise get flagged as Noisy, so the quality features fire on more
  than just unusable strips.
- Reference point: the 2017 Challenge winners scored about 0.83 macro-F1. The run's own "hold-out" section
  (0.674) uses a demo split, so it is not a reportable result.

## Comparison budget (written before running, per the "forking paths" section of the template)

Approach: **a comparison budget**, decided as a team before each step. The *proposed* budget for iteration 2,
step 1 is four preprocessing configurations, with everything else held at row 1:

| cfg | why it's in the budget |
|---|---|
| `{"preprocess": "none"}` | the reference (= row 1) |
| `{"preprocess": "bandpass", "ecg_band": (0.5, 40.0), "notch": 50.0}` | removes stationary hum and wander; risk: deletes the 50 Hz evidence for `~` and rounds the QRS |
| `{"preprocess": "wavelet", "wavelet": "db4"}` | removes non-stationary transients; risk: cleans `~` until it looks normal |
| `{"preprocess": "denoise", "impulsive": "median", "baseline": "highpass", "hp_fc": 0.5, "powerline": "notch"}` | one remedy per noise type (Ch. 8) |

Configurations compared so far: **1** (the baseline).

## Decision log — the choices behind the numbers

| Pipeline module | Option chosen | Alternative(s) considered | Why this one (one sentence) | Iteration | Revised later? |
|---|---|---|---|---|---|
| 1. Data loading | 431-record stratified subset (≥ 40 per class) | full 8,528 records; a larger `--subset` | Fast enough to iterate on, and the floor keeps A and ~ learnable. A larger set would change the dataset, so the baseline would need re-running first | 1 | — |
| 2. Preprocessing | `"none"` (shipped default; `_rpeaks` does its own 5–15 Hz band-pass) | `bandpass`, `wavelet`, `denoise` | Not yet tested; it's the reference for the iteration-2 A/B. Two features measure corruption, so cleaning could hurt the `~` class | 1 | planned, iter 2 |
| 3. Feature extraction | 11 shipped features: HR, SDNN, RMSSD, pNN50, CV, irregularity fraction, beat count, QRS/HF ratio, 49–51 Hz power, std, kurtosis | AF-specific features (Poincaré, sample entropy, P-wave absence) | Shipped default and the reference point. A→O confusion suggests the AF features are missing | 1 | planned, iter 2 |
| 4. Feature selection | `select="none"` | ANOVA, mutual information, tree, lasso | 11 features on 431 records is not high-dimensional, so selection isn't the bottleneck yet | 1 | — |
| 5. Classification, incl. `imbalance` | `StandardScaler` → `RandomForestClassifier(200 trees, seed 0)`, `imbalance="balanced"` | `"none"`, `"smote"`, `"threshold"`, gradient boosting | Shipped default. "Balanced" stops the model from defaulting to N on a set where 55% of records are N; to be compared in iter 3 | 1 | planned, iter 3 |
| 6. Inference | `train_baseline` → `write_submission` with the frozen fitted model | — | Fits nothing at predict time | 1 | — |
| 7. Reporting | macro-F1 + κ + fold spread + confusion + per-class recall | accuracy | Accuracy would hide the rare A and ~ classes | 1 | — |

## Revisions — the ones that went **backwards** (Criterion 9's actual evidence)

| # | The downstream result that triggered it | Which earlier decision it indicted | What you changed | What happened to the metric |
|---|---|---|---|---|
| 1 |  |  |  |  |

## Who did what

| Iteration | Who | Modules / tasks owned | Reviewed by |
|---|---|---|---|
| 1 | Shakeel | Reproduced the baseline; set up RESULTS.md, .gitignore and CLAUDE.md |  |

## Final numbers (fill in once, at the end)

| | Value | Under what split |
|---|---|---|
| Primary metric, development (mean + spread) |  |  |
| Secondary metrics (κ / per-class recall) |  |  |
| Held-out set — **scored once, never tuned against** |  |  |
| Supplied baseline, same harness | macro-F1 0.653 (fold mean 0.649 ± 0.057), κ 0.522 | GroupKFold(5) by record, 431 records |
| Yardstick from the dataset card | ≈ 0.83 macro-F1 (2017 Challenge winners) | official hidden test set |
| **Configurations compared** before settling |  |  |
| How option comparison was kept separate from final reporting |  |  |
