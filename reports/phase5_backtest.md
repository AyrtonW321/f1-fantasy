# Phase 5: multi-season backtest and 2027 cold start

Result: `robust_mu` (trim 0.3, prior weight 2.0) stays the live predictor for 2027. Carry-over is not enabled.

## 5.1 Walk-forward, every season (from `reports/phase5_seasons.md`)

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

`robust_mu` wins Spearman in every season and MAE in 3 of 4, but loses the 2023 season total by 565 (combined 2023-2025: 14830 vs 15309). User decision 2026-11-13: keep `robust_mu`; 2023 treated as an outlier (it wins 2025 and 2026, ties 2024).

## 5.2 Re-tune

Grid over trim and prior weight on 2023-2025 combined points: best is the current 0.3 / 2.0 (14830). 2026 total 4363, unchanged. `config/model.yaml` not changed.

## 5.3-5.4 Carry-over prior (not enabled)

Prior = previous-season points per million relative to that season's median; drivers get their new team's car level plus their offset to teammates; team renames mapped. Blended into `robust_mu` as `w` pseudo-races. Grid: `w` in 1, 3, 8; late-season half-life none or 6 races.

Walk-forward with transfer limits (`robust_mu` -> best carry-over):

| Season | MAE rounds 1-4 | Team points rounds 1-4 | Season total |
|---|---|---|---|
| 2024 | 11.24 -> 10.74 | 756 -> 702 (worse in every setting) | 4548 -> 4224 |
| 2025 | 14.15 -> 13.06 | 610 -> 774 | 4657 -> 4520 |
| 2026 (regulation reset, no veto) | 17.31 -> 16.98 | 707 -> 907 | 4363 -> 4540 |

Fresh team each round (rounds 1-4, no transfer state), to remove path noise:

| Season | rolling-5 | robust_mu | best carry-over |
|---|---:|---:|---:|
| 2024 | 777 | 804 | 735 |
| 2025 | 749 | 749 | 770 |
| 2026 | 780 | 780 | 928 |

Gate (win 2024 and 2025 rounds 1-4 without lowering season totals): fails. Better MAE again does not turn into team points; the 2024 prior ranked Aston Martin first (strong early 2023), which faded. Prototype kept uncommitted in worktree `../f1-fantasy-5.3-carryover` (`src/features/carryover.py`).

## 2027 Round 1

`pick_team.py` needs no change: with no 2027 history `robust_mu` uses the price prior alone, as in every backtested round 1.
