# CLAUDE.md — ECG CinC-2017 capstone (CM2013, KTH)

Context for Claude Code working in this repo. Read this first, every session.

## The project
- 4-class rhythm classification from a single-lead ECG (300 Hz, ~10–60 s): **N** normal, **A** AF, **O** other rhythm, **~** noisy. One label per recording.
- Team of 3: Shakeel (ML engineer, wants to work through every stage to learn), Manfred, Miguela. Other modules (preprocessing, features) belong to teammates — when touching them, work on a branch and keep changes easy to hand over.
- Graded on reasoning and evidence, **not** on the raw number. Beating the baseline is not required. A defended decision to keep a lower-scoring pipeline can get full marks.
- Key docs in `tracks/`: `ecg_cinc2017_instructions.md`, `ecg_cinc2017_card.md`, `CAPSTONE_REPORT_RUBRIC.md`, `DESIGN_MENUS.md`, `BACKGROUND_MAP.md`, `results_log_TEMPLATE.md`. Read the relevant one before changing a stage.

## Repo layout
- `run_ecg.py` — one-command runner: smoke CV → real CV → demo hold-out `predictions.csv`.
- `tracks/ecg_cinc2017.py` — the track adapter (preprocess, `_rpeaks`, `extract_features`, baseline, download/load).
- `tracks/adapter.py` — shared pipeline, filters/denoise, imbalance options, leakage-safe evaluator (GroupKFold by record).
- `tracks/report.py` — `summarize_results()`; confusion matrix first, then metric with fold spread.
- `data_cache/ecg_cinc2017/` — 431 real records (stratified subset) + `REFERENCE-v3.csv`.
- `notebooks/track_ecg_cinc2017.ipynb` — has a "Decision points on this track" symptom → stage table.

## Verified baseline (2026-10-10, unchanged repo, `python run_ecg.py`)
| | macro-F1 | κ | fold spread |
|---|---|---|---|
| Real, 431 records, GroupKFold(5) by record | **0.653** | **0.522** | 0.649 ± 0.057 (0.573–0.718) |
| Smoke (synthetic — sanity check only, never a result) | 0.768 | 0.687 | 0.759 ± 0.060 |

Confusion (rows = true, cols = N A O ~): N [173 3 40 22] · A [1 26 12 1] · O [25 11 70 7] · ~ [5 1 4 30]
Per-class recall: N 0.73 · A 0.65 · O 0.62 · ~ 0.75. (The dataset card's per-class numbers are stale — use these.)
The run's "hold-out" section (0.674) is a demo split, not a reportable result. Yardstick: Challenge winners ≈ 0.83.

## Non-negotiable rules (break one and the grade is capped)
1. **Split by record** via the supplied evaluator (`t.evaluate(X, y, g)` / GroupKFold). Never bypass it, never use a plain KFold or train_test_split on features.
2. **Fit any scaler, selector, resampler or threshold inside the training fold only.** Use the adapter's hooks (`make_selector`, `baseline(cfg)`), not preprocessing on the full dataset.
3. Report **macro-F1 and κ with the fold spread** (`rep["summary"]`) and the **confusion matrix + per-class recall**. Never bare accuracy, never a lone pooled number.
4. **Never drop or merge the `~` (Noisy) class.** Handle it deliberately.
5. **One change at a time.** Every experiment changes exactly one thing vs. the current reference config, everything else fixed (same seed, same records, same folds).
6. A difference smaller than the fold spread is **not a result** — say so.
7. Never report smoke numbers as results.
8. Keep the 7 stages separable: load → preprocess → features → select → classify → infer → report. Don't collapse them into one script.

## Track-specific trap
Denoising can destroy the label: the QRS/HF ratio and 49–51 Hz powerline features *measure* corruption, and `~` *is* the corrupted class. Cleaning before those features makes Noisy harder. Preferred design to test: rhythm features on the cleaned signal, quality features on the raw signal. Also: a fixed band-pass rounds the QRS and can shift R-peaks.

## How to work
- **Explain as you go.** Shakeel wants to understand each step, not just get code. Before an experiment, state what changes, the hypothesis, and what result would falsify it. After it, interpret the numbers in plain words.
- Every experiment is config-driven (`ECGCinC2017Track(cfg={...})`) and reproducible: fixed seed, record the exact cfg.
- Put experiment code in `experiments/` (e.g. `experiments/exp02_preprocess.py`), saving a small results table (CSV/markdown) per experiment. Don't edit `run_ecg.py` into a mess.
- After **every** experiment, add a dated row to `RESULTS.md`: what changed and why, macro-F1 ± spread, κ, per-class recall, kept or rejected (and why), commit hash. Also keep the **decision log** (rejected alternatives). If a later result makes us revisit an earlier decision, log it explicitly with the triggering symptom — the rubric requires at least one.
- Commit after each experiment with a clear message. Don't commit `__pycache__/`, `.venv/`, or regenerated outputs unless intended.
- Ask before large refactors of `adapter.py` / `report.py` (shared course code).

## Plan
**Iteration 1 (due 2026-10-06, catching up):** baseline reproduced ✅ → create `RESULTS.md` from the template with the baseline row; add `.gitignore`.

**Iteration 2 (2026-10-15 → 10-26) — DSP & features, each one at a time:**
1. Preprocessing A/B: `none` vs `bandpass` vs `wavelet` vs `denoise` (watch `~` recall).
2. Split pipeline: rhythm features from cleaned signal, quality features from raw.
3. Better QRS detection (full Pan–Tompkins with adaptive thresholds / search-back); check R-peaks visually on a few records per class.
4. AF features: Poincaré SD1/SD2, sample entropy of R–R, successive-difference irregularity, atrial activity in TQ segments / P-wave absence.
5. Quality features: beat-template correlation, kurtosis/SQI variants.
6. Optionally more records (`python run_ecg.py --download --subset N`) — note it changes the dataset, so re-run the baseline on the new set first.

**Iteration 3 (by 2026-11-10) — model & validation:** imbalance (`balanced` vs `smote` vs `threshold`), feature selection inside folds, maybe gradient boosting; failure analysis (A↔O confusions, clean-looking `~`).

**Iteration 4 (2026-11-24 → 12-01):** pin env, seed, `smoke()` passes, final `predictions.csv` on the held-out split, report vs baseline and 0.83, slides. Showcase 2026-12-10.
