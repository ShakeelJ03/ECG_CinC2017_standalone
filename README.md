# ECG CinC-2017 — standalone track

Single-lead ECG (300 Hz) → 4-class rhythm: **Normal (N) / AF (A) / Other (O) / Noisy (~)**.
Copied out of the CM2013 repo so it runs on its own; the folder layout matches the original
(`tracks/` + `src/bsp/` + `notebooks/` + `data_cache/`), so every relative path still works.

## Run

```bash
pip install -r requirements.txt -r requirements-real.txt
python run_ecg.py                # smoke test + real-data CV + hold-out predictions.csv
python run_ecg.py --download     # (re)fetch the real subset first; resumes if interrupted
python run_ecg.py --smoke-only   # offline check only
```

Or open `notebooks/track_ecg_cinc2017.ipynb`. It reads `../data_cache/ecg_cinc2017`.

## Contents

| Path | What |
|---|---|
| `run_ecg.py` | one-command runner (smoke → real CV → hold-out) |
| `tracks/ecg_cinc2017.py` | the track adapter: synthetic data, download/load, QRS + R–R/HRV + signal-quality features |
| `tracks/ecg_cinc2017_instructions.md`, `ecg_cinc2017_card.md` | task brief + dataset card |
| `tracks/adapter.py`, `report.py` | shared pipeline, evaluator (GroupKFold by record), reporting |
| `tracks/BACKGROUND_MAP.md`, `DESIGN_MENUS.md` | book sections, literature anchors, design options |
| `tracks/RUBRIC.md`, `CAPSTONE_REPORT_RUBRIC.md`, `HOLDOUT_EVALUATION.md`, `INDIVIDUAL_ASSESSMENT.md`, `START_HERE.md` | assessment docs |
| `tracks/*_TEMPLATE.md` | results log / readiness matrix / card templates |
| `tracks/dataset_manifest.json` | provenance + checksums for all course datasets |
| `src/bsp/` | course helper package (`biosignals`, `metrics`, `notebook_checks`, …) |
| `src/figures/` | ECG-relevant book figures (Pan–Tompkins, HRV, ECG fiducials, leakage, confusion) |
| `data_cache/ecg_cinc2017/` | real data: stratified subset of the training set + `REFERENCE-v3.csv` |
| `outputs/` | `predictions.csv` from the last run |

## Links

**Dataset**
- PhysioNet/CinC Challenge 2017 (v1.0.0): https://physionet.org/content/challenge-2017/1.0.0/
- Raw training files (what `download()` fetches): https://physionet.org/files/challenge-2017/1.0.0/training/
- Labels: https://physionet.org/files/challenge-2017/1.0.0/training/REFERENCE-v3.csv
- Full training set as one zip (~600 MB, 8,528 records): https://physionet.org/content/challenge-2017/1.0.0/#files
- Licence: open (PhysioNet Challenge), direct download, no data-use agreement.

**Literature (from `BACKGROUND_MAP.md`)**
- Clifford GD, et al. (2017). *AF Classification from a Short Single Lead ECG Recording: the PhysioNet/Computing in Cardiology Challenge 2017.* CinC 44. doi:10.22489/CinC.2017.065-469
- Pan J, Tompkins WJ (1985). *A real-time QRS detection algorithm.* IEEE TBME 32(3):230–236. doi:10.1109/TBME.1985.325532
- Task Force of the ESC/NASPE (1996). *Heart rate variability: standards of measurement…* Circulation 93(5):1043–1065. doi:10.1161/01.CIR.93.5.1043
- Search terms: "atrial fibrillation detection single lead ECG", "RR irregularity AF", "ECG signal quality index".
- Book sections: ECG/QRS morphology §1.4 · band-pass + notch §9.6 · Pan–Tompkins §9.9 · HRV §7.11.

**Tools / upstream**
- wfdb-python docs: https://wfdb.readthedocs.io/
- Original course repo: https://github.com/farhad-abtahi/CM2013 · site: https://farhad-abtahi.github.io/CM2013/
- Colab version of the notebook: https://colab.research.google.com/github/farhad-abtahi/CM2013/blob/main/notebooks/track_ecg_cinc2017.ipynb
