# Expected score — ECG CinC-2017 (registered before the hold-out is downloaded)

| | |
|---|---|
| Final model commit | `ebc203d` |
| Pipeline (cfg) | `{'seed': 0, 'qrs': 'pt', 'feature_set': 'base+rr+morph', 'clf': 'hgb', 'imbalance': 'balanced'}` |
| Training records | 8408 — {'N': 5046, 'A': 728, 'O': 2385, '~': 249} (hold-out ids excluded, checked with `assert_no_holdout`) |
| Split unit | record |
| Folds | 5-fold StratifiedGroupKFold (groups = record), repeated 5× with seeds 0–4 = 25 folds |
| **Expected macro-F1 (4 classes)** | **0.756 ± 0.018** (mean ± SD across the 25 folds) |
| Cohen's κ | 0.688 ± 0.016 |
| Challenge score F1(N,A,O) | 0.807 ± 0.013 |
| Per-class F1 N / A / O / ~ | 0.89 / 0.80 / 0.73 / 0.60 |
| Course `evaluate()` (5-fold GroupKFold) | mean macro_f1 0.758 (sd 0.016, range 0.743-0.780 across 5 folds) |

Note: the hold-out has 30 records per class, while training follows the dataset's own mix
(Normal-heavy). Per-class recall should transfer; macro-F1 can move because precision on the rare
classes depends on how many of them there are. We registered this number before seeing the
hold-out and will report the hold-out score next to it, whichever way it lands.
