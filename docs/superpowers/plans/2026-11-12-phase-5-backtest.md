# Phase 5 Plan: Multi-season backtest and 2027 cold start

**Status:** Agreed with user after grilling (2026-11-12). Overrides the Phase 5 row in the master plan.

## Goal

Make the picker ready for 2027 Round 1. `robust_mu` uses same-season data only, so rounds 1-4 of a new season run on the price prior alone. Phase 5 checks `robust_mu` across 2023-2026 and tests carrying prior-season form into early rounds.

Dropped from the original plan: Kalman `Q` and price `lambda` tuning. Neither model feeds `pick_team.py`; tuning them changes nothing live.

## Decisions

- Tune `form.trim` and `form.prior_weight` on 2023-2025, all rounds, one shared setting. 2026 is a check only: new settings replace 0.3 / 2.0 only if the 2026 season total is no worse. Log every 2026 run in `reports/holdout_2026_log.md`.
- Carry-over prior, previous season only:
  - Built from race-by-race rows, as points per million (PPM) at each race's price.
  - Car level = the asset's team's previous-season PPM; constructors use their own.
  - Driver skill = previous-season ratio of the driver's points to their teammate's (same car, same rounds). Rookies get 1.0.
  - Driver prior = new team's car level x driver ratio, converted to points at the new-season price. Used for every driver, switchers included.
  - Team renames (alfa -> sauber 2024, sauber -> audi 2026, alphatauri -> rb 2024) map to the same team, in config.
  - Blended with the price prior by one tuned weight `w`; fades as current-season races arrive, as the price prior does.
  - Late-season decay (weight later races more) tested; kept only if it beats equal weights.
- Tune `w` (and decay) on 2024 and 2025 (fed from 2023 and 2024): stable-rule transitions, like 2026 -> 2027. 2026 is reported separately, labelled "regulation reset, not representative", with no veto.
- Carry-over is enabled only if it beats no carry-over on 2024 and 2025 rounds 1-4 totals without lowering either full-season total.
- DNF Brier dropped (DNF model not live).

## Tasks

| # | Task | Who | Files | Depends on | Status |
|---|---|---|---|---|---|
| 5.1 | Metrics and multi-season walk-forward: rolling-5 and `robust_mu` on 2023-2026 | ChatGPT, worktree `../f1-fantasy-5.1-metrics`, branch `chatgpt/5.1-metrics` | `src/backtest/metrics.py`, `pipelines/evaluate_seasons.py`, test | - | Pending |
| 5.2 | Re-tune trim and prior weight on 2023-2025, 2026 check | ChatGPT | `pipelines/evaluate_seasons.py`, `config/model.yaml` only if 2026 total no worse | 5.1 | Pending |
| 5.3 | Carry-over prior | Claude, worktree `../f1-fantasy-5.3-carryover`, branch `claude/5.3-carryover` | `src/features/carryover.py`, rename map in `config/model.yaml`, test | - | Pending |
| 5.4 | Tune and evaluate carry-over on 2024 and 2025 rounds 1-4; 2026 report | Claude | `pipelines/evaluate_carryover.py` | 5.1, 5.3 | Pending |
| 5.5 | Wire the winner into `pick_team.py`; `reports/phase5_backtest.md`; decisions | Claude | `pipelines/pick_team.py`, docs | 5.2, 5.4 | Pending |

## Acceptance

1. `src/backtest/metrics.py` reports per season (2023-2026): per-asset MAE, season total, total from round 5, rounds 1-4 total, Spearman of predicted vs actual asset points. For rolling-5, `robust_mu`, and `robust_mu` + carry-over.
2. Trim and prior weight re-tuned on 2023-2025 and adopted or rejected by the 2026 rule.
3. Carry-over enabled or left disabled by the rule above.
4. `pick_team.py` runs 2027 round 1 with no code change, given new opening prices.
5. Results in `reports/phase5_backtest.md`; decisions in `docs/decisions.md`.
