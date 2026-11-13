
## Phase 3 Kalman evaluation (2026-11-10)

Training window: 2023-2025. Parameters: car Q=0.04, driver Q=0.004, track Q=0.001, observation variance=0.35.

2026 result: Kalman mean Spearman: 0.6351; last-race-order mean Spearman: 0.5001; rounds: 19

## Phase 3 Kalman evaluation (2026-11-10)

Training window: 2023-2025. Parameters: car Q=0.04, driver Q=0.001, track Q=0.0005, observation variance=0.5, prior weight=0.12, prior rounds=2. State effects centered after each round.

2026 result: Kalman mean Spearman: 0.6356; last-race-order mean Spearman: 0.5001; rounds: 19

## Phase 5 2026 aggregate metrics (2026-11-12)

| Predictor | Asset MAE | Season total | From round 5 | Rounds 1-4 | Mean round Spearman |
|---|---:|---:|---:|---:|---:|
| rolling-5 | 14.36 | 4269 | 3562 | 707 | 0.6632 |
| robust_mu | 13.47 | 4363 | 3656 | 707 | 0.6865 |

5.2 tuned check: trim=0.3, prior_weight=2.0, 2026 total 4363, asset MAE 13.47; retained current setting against current total 4363; config unchanged.
