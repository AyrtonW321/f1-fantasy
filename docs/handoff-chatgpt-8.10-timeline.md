# Handoff: Phase 8.10 Task 1 (Timeline data and chart) for ChatGPT

Work **only** in the git worktree `C:\Users\ayrto_kuqm8yg\OneDrive\Documents\Coding\f1-fantasy-timeline` on branch `timeline`. Claude is editing `src/ui/cards.py` and `app.py` in the main folder at the same time, so never touch that folder or those files. Create only `src/ui/timeline.py` and `tests/test_ui_timeline.py`. Commit on `timeline`. Do not merge, push or switch branches.

## Read first

- `CLAUDE.md` (project rules)
- `docs/superpowers/specs/2026-11-15-ui-layout-timeline-design.md` (design)
- `docs/superpowers/plans/2026-11-15-ui-layout-timeline.md`, **Task 1** (your task; follow its interfaces, row rules and tests exactly)
- `src/ui/logic.py` (`history_points`, `top_teams`, `team_state`, `asset_mu`, `next_round`, `load`, `_tables`)
- `src/backtest/walkforward.py` (`_actual_points`)
- If `graphify-out/graph.json` exists, run `graphify query "<question>"` before grepping or reading source files.

## Data

Real data is gitignored. To run the real-data tests, copy `data/processed/` from the main folder into the worktree. Never commit it. Never read TracingInsights `priceChange`. Never print `F1_DATA_KEY`.

## Rules

- No Streamlit import in `timeline.py`, no new dependency.
- Season 2026: rows start at round 20 (highest scored round) with the saved team file, then rounds 21-23.
- Team line colours must not be red `#E10600` or green `#2EB86A`. Expected rounds are dashed.

## Done when

- `uv run pytest -q` passes: the old count plus your new tests.
- Commit on `timeline` with the message `feat: timeline frame and chart`.
- Reply with the commit hash and any choices you made that the plan left open.
