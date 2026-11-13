# Phase 5: multi-season walk-forward

Per-asset MAE and per-round Spearman use each predictor's pre-lock asset predictions. Team totals use the season rules.

| Predictor | Season | Asset MAE | Season total | From round 5 | Rounds 1-4 | Mean round Spearman |
|---|---:|---:|---:|---:|---:|---:|
| rolling-5 | 2023 | 12.26 | 6190 | 5067 | 1123 | 0.6246 |
| robust_mu | 2023 | 11.99 | 5625 | 4502 | 1123 | 0.6394 |
| rolling-5 | 2024 | 11.55 | 4561 | 3834 | 727 | 0.6867 |
| robust_mu | 2024 | 11.65 | 4548 | 3792 | 756 | 0.7154 |
| rolling-5 | 2025 | 13.65 | 4558 | 3924 | 634 | 0.5836 |
| robust_mu | 2025 | 13.13 | 4657 | 4047 | 610 | 0.6216 |
| rolling-5 | 2026 | 14.36 | 4269 | 3562 | 707 | 0.6632 |
| robust_mu | 2026 | 13.47 | 4363 | 3656 | 707 | 0.6865 |

## Task 5.2: shared 2023-2025 tuning

Selected by maximum combined season points: trim=0.3, prior_weight=2.0; combined points 14830, mean season MAE 12.26.
2026 check: current trim=0.3, prior_weight=2.0 total 4363; tuned total 4363, MAE 13.47. Retained current setting; config/model.yaml unchanged.

| trim | prior_weight | Combined 2023-2025 points | Mean season MAE |
|---:|---:|---:|---:|
| 0.0 | 0.5 | 14201 | 12.32 |
| 0.0 | 1.0 | 14369 | 12.29 |
| 0.0 | 2.0 | 14412 | 12.31 |
| 0.0 | 3.0 | 14009 | 12.35 |
| 0.0 | 5.0 | 13890 | 12.45 |
| 0.1 | 0.5 | 14526 | 12.31 |
| 0.1 | 1.0 | 14643 | 12.27 |
| 0.1 | 2.0 | 14729 | 12.29 |
| 0.1 | 3.0 | 13690 | 12.34 |
| 0.1 | 5.0 | 13617 | 12.44 |
| 0.2 | 0.5 | 14274 | 12.31 |
| 0.2 | 1.0 | 14354 | 12.28 |
| 0.2 | 2.0 | 14553 | 12.30 |
| 0.2 | 3.0 | 14234 | 12.34 |
| 0.2 | 5.0 | 14129 | 12.44 |
| 0.3 | 0.5 | 14604 | 12.27 |
| 0.3 | 1.0 | 14595 | 12.24 |
| 0.3 | 2.0 | 14830 | 12.26 |
| 0.3 | 3.0 | 14544 | 12.31 |
| 0.3 | 5.0 | 13870 | 12.41 |
| 0.4 | 0.5 | 14735 | 12.27 |
| 0.4 | 1.0 | 14627 | 12.24 |
| 0.4 | 2.0 | 14581 | 12.26 |
| 0.4 | 3.0 | 14328 | 12.31 |
| 0.4 | 5.0 | 14071 | 12.41 |
