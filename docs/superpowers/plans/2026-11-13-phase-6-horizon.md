# Phase 6 Plan: Rolling transfer horizon

**Status:** Done 2026-11-13. Horizon rejected at the prototype step (no gain); picker unchanged. Overrides the Phase 6 row in the master plan.

## Goal

The picker optimizes one round at a time. A rolling horizon plans transfers over the next k rounds and plays only this round's moves, so it can bank a free transfer for a bigger move later and skip swaps a later round would undo.

## Decisions (grilling 2026-11-13)

- Scope: rolling horizon only. Chips: no new build, only a check that chip rounds behave as today. Prices: flat across the horizon (no price model). Risk mode: skipped.
- Every horizon round uses the same `robust_mu` (0.3 / 2.0). No per-track or per-round terms: every Phase 4 term of that kind lost. Gains can only come from transfer banking and avoiding churn.
- One ILP over rounds r .. r+k-1: transfers, free-transfer carry (`transfers.free`, `carry_max`, `max_free`) and penalties from `config/rules_{season}.yaml`. Budget fixed at this round's value. Play round r's team only. Horizon is cut short at the season's last round.
- Gate: grid k in {2, 3}, no discount, tuned on 2023-2025 combined. Enabled only if best k beats 14830 combined and 2026 is no worse than 4363. Log every 2026 run in `reports/holdout_2026_log.md`. Report transfers, penalties and banked free transfers per season.
- Chips: backtest runs without chips (2023-2025 chip rules are null). Live: on a wildcard or limitless round `pick_team.py` uses the existing chip path and skips the horizon. After limitless the team reverts to the original pre-limitless team; after wildcard it keeps the new team. x3_boost and no_negative sit on top of the horizon's team unchanged. Free transfers after a chip round come from `my_team_*.yaml`, as today.
- Prototype first (CLAUDE.md): scratch run on rounds 1-10; stop and report if below single-round `robust_mu`.

## Tasks

| # | Task | Who | Files | Depends on | Status |
|---|---|---|---|---|---|
| 6.0 | Scratch prototype, rounds 1-10, 2023-2025 | Claude | scratchpad only | - | Done 2026-11-13: k = 2, 3 identical to single-round (2739 / 1791 / 1796, same transfers and penalties). Stopped; 6.1-6.3 cancelled |
| 6.1 | Horizon ILP returning round r's `Decision` | Claude, worktree `../f1-fantasy-6.1-horizon`, branch `claude/6.1-horizon` | `src/optimize/horizon.py`, test | 6.0 passes | Pending |
| 6.2 | Backtest: k grid on 2023-2025, 2026 check, holdout log, transfer stats | ChatGPT, worktree `../f1-fantasy-6.2-eval`, branch `chatgpt/6.2-eval` | `pipelines/evaluate_horizon.py`, `reports/phase6_horizon.md` | 6.1 merged | Pending |
| 6.3 | Wire into `pick_team.py` only if gate passes; chip-round bypass test; docs | Claude | `pipelines/pick_team.py`, docs | 6.2 | Pending |

## Acceptance

1. `reports/phase6_horizon.md`: per season (2023-2026) totals for single-round and k = 2, 3, with transfers, penalties and banked free transfers.
2. Horizon enabled or left disabled by the gate above.
3. Chip rounds give the same picks as today (one test).
4. Decisions in `docs/decisions.md`.
