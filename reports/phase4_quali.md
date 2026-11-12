# Phase 4.4: simulator with qualifying order (2026)

Tuned on rounds 1-10 by MAE; reported over rounds 1-20. 2000 draws, seed 0. Rounds with fewer than 3 earlier races use robust form.

| Predictor | MAE r1-10 | MAE all | Season total |
|---|---|---|---|
| robust form (4.1) trim=0.3 prior_weight=2.0 | 14.53 | 13.47 | 4363 |
| simulator 4.2 l2=0.01 dnf_shrink=200.0 | 14.58 | 13.56 | 4362 |
| simulator + qualifying l2=0.01 dnf_shrink=200.0 | 14.52 | 13.49 | 4136 |

Qualifying simulator beats 4.1 and 4.2 on both MAE (all rounds) and season total: no
Simulator runtime: 0.19 s per round

Grid (MAE rounds 1-10):

| l2 | dnf_shrink | MAE |
|---|---|---|
| 0.01 | 5.0 | 14.70 |
| 0.01 | 20.0 | 14.56 |
| 0.01 | 50.0 | 14.53 |
| 0.01 | 200.0 | 14.52 |
| 0.1 | 5.0 | 14.70 |
| 0.1 | 20.0 | 14.56 |
| 0.1 | 50.0 | 14.53 |
| 0.1 | 200.0 | 14.52 |
| 1.0 | 5.0 | 14.70 |
| 1.0 | 20.0 | 14.56 |
| 1.0 | 50.0 | 14.54 |
| 1.0 | 200.0 | 14.53 |
| 10.0 | 5.0 | 14.73 |
| 10.0 | 20.0 | 14.65 |
| 10.0 | 50.0 | 14.64 |
| 10.0 | 200.0 | 14.64 |
