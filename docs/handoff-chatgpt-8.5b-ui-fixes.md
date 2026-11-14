# Prompt for ChatGPT: Phase 8 task 8.5 review fixes

You built the Streamlit app on branch `chatgpt/8.5-ui-app` (commit 6dc18dd) in the worktree `../f1-fantasy-8.5-ui-app`. Claude reviewed it. Keep working in that same worktree and branch. Same rules as `docs/handoff-chatgpt-8.5-ui-app.md`: no commits to main, no pushes, do NOT edit anything under `src/` or `pipelines/`, `tests/test_ui_logic.py` or `.gitignore`. Smallest correct diff.

## 0. Bring in main first

```
git merge main
```

Main now has the real `src/ui/logic.py` (8.4) plus a `chip=` option on `top_teams` (8.4b). One conflict is expected in `docs/progress.md`: keep both sides' lines.

## Fixes (all in `app.py` unless said)

1. **Pass the team's exclude list.** Every `top_teams(team_state, ...)` call in a team tab must pass `exclude=team.get("exclude", [])`. Today team 2 and 3 exclude HIR, and HIR shows up in team 2's 4th alternative.
2. **Chip-aware picks.** Move the "Chip to play" selectbox above the live pick. When a chip is chosen, call `top_teams(team_state, exclude=..., chip=chip)`: for limitless, wildcard and x3_boost it returns one team (the best for that chip); for other chips it returns the normal top 5. Show `Decision.boost3` in `_decision_rows` (column "3x boost", blank when None). `apply_transfers(n, selected, chip)` must get the decision from that chip-aware list, so the saved history has the right team and 3x driver.
3. **Stale data after "Update data".** After the update exits with code 0, call `st.cache_data.clear()` then `st.rerun()`.
4. **No crash when data is missing.** `top_teams`, `validate`, `history_points` and `next_round` raise `ValueError` when there are no prices for the next round or no round is left (after Abu Dhabi, before 2027 is listed). Catch `ValueError` around each call in the team tabs and the Best teams tab and show it with `st.warning`. The Data tab must always render, so the user can press "Update data".
5. **Show the selected choice.** Above "I made these transfers", show which team will be applied ("Selected: #N" plus its drivers and constructors). Default #1.
6. **Remove the stubs.** Delete `app_stubs.py` and the `try/except ModuleNotFoundError` fallback and the `STUBS` banner; import from `src.ui.logic` directly. Delete your known-issues line about the stubs, and reword your progress line so it does not say the app uses stubs.

Not needed now: re-adding a used chip in the edit form.

## Check

- `uv run pytest -q`: all pass.
- `uv run streamlit run app.py` (or Streamlit `AppTest`) renders every tab with no exception.
- On a COPY of a team file, never the real `config/my_team_*.yaml`: choose x3_boost, apply, and confirm `config/history/team_N.csv` has `boost3` filled. Restore the copy afterwards.

## Deliverables

1. Commits on `chatgpt/8.5-ui-app` (no push).
2. A short report: what changed per fix, test count, how you checked fix 2.
3. Update your line in `docs/progress.md`. Record any unfixed finding in `docs/known-issues.md` with a date.
