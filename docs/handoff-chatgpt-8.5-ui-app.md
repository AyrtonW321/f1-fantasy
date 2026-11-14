# Prompt for ChatGPT: Phase 8 task 8.5 (Streamlit app)

You are working in the Python repo `f1-fantasy` (F1 Fantasy optimizer, Windows 11, PowerShell 5.1, `uv`). Read `CLAUDE.md`, `docs/progress.md`, `docs/decisions.md` and the Phase 8 plan `docs/superpowers/plans/2026-11-14-phase-8-season-end.md` (UI decisions and tasks 8.4/8.5) first. Follow CLAUDE.md hard rules: the only new dependency allowed is `streamlit` (user approved); no commits to main, no pushes; never read, print or store `F1_DATA_KEY`. Smallest correct diff.

## Worktree (required)

```
git worktree add ../f1-fantasy-8.5-ui-app -b chatgpt/8.5-ui-app main
```

All edits and commits happen in `../f1-fantasy-8.5-ui-app`. Do NOT edit anything under `src/` or `pipelines/`, `tests/test_ui_logic.py` or `.gitignore`.

## The logic API (built by Claude in 8.4, merged to main)

8.4 is merged: import from `src.ui.logic` directly, no stubs. The app calls only these. Every function takes an optional `tables=` (dict of DataFrames) for tests; the app leaves it out and the function reads `data/processed/*.parquet`. `season`/`round_` default to the next uncompleted round.

- `next_round() -> (season, round)`: first round not yet completed.
- `load(n) -> dict`: the parsed `config/my_team_{n}.yaml`. `team_path(n)` and `history_path(n)` give the file paths.
- `validate(team: dict, season=None) -> list[str]`: error messages, empty when valid. `team` has the team-file keys: `exclude`, `drivers` (5), `constructors` (2), `bank`, `free_transfers`, `chips_left`.
- `save_team(n, team, season=None) -> None`: validates, backs up the old file to `config/backup/`, writes `config/my_team_{n}.yaml`. Raises `ValueError` with the `validate` messages joined by `; ` when invalid.
- `apply_transfers(n, decision, chip=None) -> dict`: writes the decision as team n (backup first), logs the round to `config/history/team_{n}.csv`, returns the new team dict. Raises `ValueError` if `chip` is not in `chips_left`. A limitless chip keeps the old team (it reverts next round).
- `top_teams(state, budget=100.0, n=5, exclude=()) -> list[Decision]`: best n distinct teams, best first. `state=None` means best overall under `budget`; otherwise teams reachable from `state` (its own budget, transfer penalties). Pass the team file's `exclude` list. `Decision` and `TeamState` are in `src/optimize/ilp.py` (`Decision.drivers`, `.constructors`, `.boost`, `.boost3`, `.transfers_in`, `.penalty_transfers`, `.cost`, `.budget`, `.expected_points`).
- `history_points(n) -> pandas.DataFrame`: columns `season, round, points, cumulative, team_value, transfers, chip, lineup`. `points` is NaN until the round is scored; `cumulative` resets each season. Empty DataFrame when no history.

For loading a team file into a `TeamState`, use `pipelines.pick_team.load_team`. For chip advice, capture `pipelines.plan_chips.main(["--team", n])` stdout.

## Task 8.5

1. `app.py` (Streamlit):
   - One tab per `config/my_team_[0-9].yaml`:
     - current team table, live best pick (first of `top_teams(state, ...)`), the stale warning text from `pipelines.weekly_update.stale_warning`
     - chip advice from the latest `reports/round_*.md` section for that team, plus a "Recompute chips" button
     - "Other choices": the top 5 from `top_teams`, each with a "Use this one" button
     - "I made these transfers" button calling `apply_transfers`, with a chip selector (from `chips_left`, or none)
     - manual edit form: driver multiselect (exactly 5), constructor multiselect (exactly 2), bank, free transfers, chips checkboxes, exclude; show `validate` errors and do not save while there are any
     - timeline chart from `history_points`: points per round and cumulative, team value as a second line, markers on transfer and chip rounds, lineup on hover. Show "History starts at the first round saved through the app" when empty.
   - "Best teams" tab: `top_teams(None, budget)` with a budget number box defaulting to 100.0.
   - "Data" tab: next round and lock time (local) from `data/processed/races.parquet`, latest price round, unsealed count (`pipelines.weekly_update.unsealed`), and an "Update data" button running `uv run python -m pipelines.weekly_update --force` as a subprocess with its output streamed into the page.
   - No game logic in the app: no point math, no budget math, no YAML writes except through `apply_transfers` or the validated manual form (through `save_team`).
2. `F1 Fantasy.bat` in the repo root: `cd /d "%~dp0"` then `uv run streamlit run app.py`.
3. Add `streamlit` with `uv add streamlit` (updates `pyproject.toml` and `uv.lock`).
4. `docs/how-it-works.md`: a short "Using the app" section (how to start it, what each tab does, where backups and history go).

Check: `uv run streamlit run app.py` starts and every tab renders without errors. Test writes on a copy: never click "I made these transfers" or save on the real team files during development. Run `uv run pytest -q` before committing; all tests must still pass.

## Deliverables

1. Commits on `chatgpt/8.5-ui-app` in the worktree (no push).
2. A short report to me: files changed, a screenshot or description of each tab, test count.
3. One dated line in `docs/progress.md`. Record any unfixed finding in `docs/known-issues.md`.
