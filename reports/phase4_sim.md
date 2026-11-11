# Phase 4.2: race-order + DNF simulator (2026)

Tuned on rounds 1-10 by MAE; reported over rounds 1-20. 2000 draws, seed 0. Rounds with fewer than 3 earlier races use robust form.

| Predictor | MAE r1-10 | MAE all | Season total |
|---|---|---|---|
| robust form (4.1) trim=0.3 prior_weight=2.0 | 14.53 | 13.47 | 4363 |
| simulator l2=0.01 dnf_shrink=200.0 | 14.58 | 13.56 | 4362 |

Simulator beats 4.1 on both MAE (all rounds) and season total: no
Simulator runtime: 0.35 s per round

Grid (MAE rounds 1-10):

| l2 | dnf_shrink | MAE |
|---|---|---|
| 0.01 | 5.0 | 14.69 |
| 0.01 | 20.0 | 14.60 |
| 0.01 | 50.0 | 14.59 |
| 0.01 | 200.0 | 14.58 |
| 0.1 | 5.0 | 14.69 |
| 0.1 | 20.0 | 14.60 |
| 0.1 | 50.0 | 14.59 |
| 0.1 | 200.0 | 14.58 |
| 1.0 | 5.0 | 14.69 |
| 1.0 | 20.0 | 14.61 |
| 1.0 | 50.0 | 14.59 |
| 1.0 | 200.0 | 14.58 |
| 10.0 | 5.0 | 14.71 |
| 10.0 | 20.0 | 14.64 |
| 10.0 | 50.0 | 14.62 |
| 10.0 | 200.0 | 14.62 |
