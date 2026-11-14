# Phase 8 Plan: Finish 2026, then prepare 2027

**Status:** Planned 2026-11-14. Phase 7 accepted 2026-11-14 (manual runs), so Phase 8 may start. Not in the master plan; added after Phase 7.

## Goal

Get the most out of the last 2026 rounds (Qatar 22, Abu Dhabi 23), keep the 2026 data before the feeds disappear, then make the pipeline run for 2027. User priority: 2026 first; 2027 work waits until the season is over.

## Decisions (grilling 2026-11-14)

- Scope: recency prototype, final 2026 archive, 2027 plumbing. Benched-driver exclusion skipped (manual `exclude` list works).
- Recency: weight each past race by 0.5^(races ago / h) inside `robust_mu`'s trimmed mean; trim 0.3 and prior weight 2.0 unchanged. Grid h in {3, 5, 8} plus h = infinity (today's `robust_mu`). Prototype in scratch on rounds 1-10 first; stop if below `robust_mu`. Gate: best h on 2023-2025 combined beats 14830 and 2026 is no worse than 4363 (logged in `reports/holdout_2026_log.md`). Fail: dropped, no code.
- UI (grilling 2026-11-14, part of Phase 8 so it serves the last 2026 rounds): local Streamlit app, `uv run streamlit run app.py` or desktop `F1 Fantasy.bat`. Tabs: one per team (current team, live picks, chip advice with "Recompute chips", top 5 reachable alternatives with "Use this one", "I made these transfers" one-click apply, manual edit form, stale warning, season timeline), a shared "Best teams" tab (top 5 overall, budget box default 100.0), a Data tab (next round and lock, "Update data" runs `weekly_update --force` with live log, latest price round, unsealed count).
- Apply writes drivers, constructors, bank = budget - cost, `free_transfers` from `next_state`, removes the played chip from `chips_left`; manual form forces 5 drivers and 2 constructors. Every write first copies the old file to `config/backup/` (gitignored, dated).
- Alternatives: re-solve the ILP with each found team forbidden (no-good cut), n = 5.
- Timeline: each apply appends to `config/history/team_N.csv` (gitignored): round, drivers, constructors, boost, chip, bank, team value. Chart: points per round from `fantasy_points` with boost, chip and penalties, cumulative line, team value line, markers on transfer and chip rounds, hover lineup. No backfill: 2026 starts at round 21 (no record of earlier teams).
- UI fallback: if not ready before the Abu Dhabi lock, YAML files and the weekly report keep working.
- `rules_2027.yaml`: copy of 2026 with every key under `assumed:`; reports print "ASSUMED 2027 rules" until the user confirms them at game launch. Changed rules that cannot be confirmed stay `null`.

## Tasks

| # | Task | When | Who | Files | Status |
|---|---|---|---|---|---|
| 8.1 | Recency prototype; if it passes, add to `robust_mu` (default h = infinity keeps old behaviour) and set h in `config/model.yaml` | Now, before Qatar lock (2026-11-28 18:00 UTC) | Claude: scratch first, then worktree `../f1-fantasy-8.1-recency`, branch `claude/8.1-recency` | `src/features/rolling.py`, `config/model.yaml`, test | Dropped 2026-11-14 at prototype: rounds 1-10 of 2023-2025, robust_mu 6326 vs h=3 6247, h=5 6277, h=8 6232 |
| 8.2 | Final 2026 archive: snapshot after Abu Dhabi is scored, seal, commit | Week of 2026-12-07 | User runs `vault seal` (needs the key); Claude gives the commands and commits | `data/raw.tar.gz.enc` | Pending |
| 8.4 | UI logic in `src/ui/logic.py`: `validate(team) -> list[str]`, `save_team(n, team)` (validated manual edit, backup first), `apply_transfers(n, decision, chip=None)` (backup, team file, history row), `top_teams(team_state or None, budget, n=5) -> list[Decision]`, `history_points(n) -> DataFrame` (round, points, cumulative, team_value, transfers, chip, lineup) | Now, before Abu Dhabi lock (2026-12-05 14:00 UTC) | Claude, worktree `../f1-fantasy-8.4-ui-logic`, branch `claude/8.4-ui-logic` | `src/ui/logic.py`, `tests/test_ui_logic.py`, `.gitignore` | Pending |
| 8.5 | Streamlit app on the 8.4 signatures (stubs until 8.4 merges), no game logic in the app | Same window, parallel with 8.4 | ChatGPT, worktree `../f1-fantasy-8.5-ui-app`, branch `chatgpt/8.5-ui-app`; Claude reviews and merges | `app.py`, `F1 Fantasy.bat`, `pyproject.toml` (`streamlit`, user approved), `docs/how-it-works.md` | Pending |
| 8.3 | 2027 plumbing: seasons from config (not hardcoded in `build_data.py`), `BONUS_SEASONS`, `rules_2027.yaml` with `assumed`, ASSUMED line in the weekly report, fresh 2027 team files from the 100.0 budget | After 8.2 (December) | ChatGPT, worktree `../f1-fantasy-8.3-2027`, branch `chatgpt/8.3-2027`; Claude reviews | `pipelines/build_data.py`, `config/`, `pipelines/weekly_update.py` | Parked |

## Acceptance

1. 8.1 adopted or dropped by its gate; result in `docs/decisions.md` (dropped at prototype, so no report file).
2. Final 2026 snapshot sealed and committed.
3. UI: apply on a copy of a team file matches a hand edit; top 5 alternatives are distinct and within budget; the user runs one real round's transfers through the app.
4. `uv run python -m pipelines.weekly_update --force` runs for a 2027 round once 2027 prices exist, with the ASSUMED line until rules are confirmed.
