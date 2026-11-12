# Prompt for ChatGPT: Phase 4 tasks 4.6 and benched-driver fix

You are working in the Python repo `f1-fantasy` (F1 Fantasy optimizer). Read `CLAUDE.md`, `docs/progress.md`, `docs/decisions.md`, `docs/known-issues.md` and the Phase 4 plan `docs/superpowers/plans/2026-11-10-phase-4-event-models-simulator.md` (rows 4.1-4.8) first. Follow CLAUDE.md hard rules: game rules only from `config/rules_*.yaml`, every feature uses data known at `known_at <= lock_utc`, ask before adding any dependency, no commits to main, no pushes, never print `F1_DATA_KEY`. Code style: smallest correct diff, reuse existing helpers (`robust_mu` in `src/features/rolling.py`, `run_season` in `src/backtest/walkforward.py`, `mae` and `TUNE_LAST` in `pipelines/evaluate_form.py`, `pipelines/evaluate_sim.py` as the template for an evaluation script). Run `uv run pytest -q`; 209 tests pass today and must still pass.

Create branch `chatgpt/4.6-sprint` off `phase-4.4-qualifying`. Another agent (Claude) works in parallel on task 4.5 in `src/features/overtakes.py`, `src/models/poisson.py`, `pipelines/evaluate_overtakes.py`, `pipelines/build_data.py` and `src/ingest/ti_lines.py`. Do NOT edit those files, and do not edit `src/features/rolling.py` or `src/sim/montecarlo.py` (call them, do not change them).

## Task A: 4.6 sprint weekends (backtest only)

Goal: on sprint weekends, `robust_mu` underpredicts because sprint points are extra, and on normal weekends it is inflated by past sprint points. Data: `data/processed/fantasy_points.parquet` has a separate `sprint` column per asset-round. 2026 sprint rounds: 2, 4, 5, 9, 12, 17 (`races.sprint` is true). No sprint is left in 2026, so this is a backtest to prepare 2027.

Build:
- `src/features/sprint.py` with `sprint_mu(prices, points, races, season, round_, trim, prior_weight, sprint_weight)` returning the same frame shape as `robust_mu` (`OUT_COLS`, passes `assert_known_before_lock`).
  - Base form: `robust_mu` run on `points` with `total` replaced by `total - sprint` (every round).
  - Sprint term: only if the target round is a sprint round, add a per-asset mean of earlier sprint points, shrunk toward the field mean of those sprints: `(n*asset_mean + sprint_weight*field_mean) / (n + sprint_weight)`. Assets with no earlier sprint get the field mean. Whole sprint session in one number; no Poisson.
- `pipelines/evaluate_sprint.py` (copy the structure of `pipelines/evaluate_sim.py`): tune the single `sprint_weight` on rounds 1-10 (only sprints 2, 4, 5, 9 fall there) by per-asset MAE, using `trim` and `prior_weight` from `config/model.yaml` `form`. Report: MAE and season total on all 6 sprint rounds vs 4.1 (`robust_mu`), MAE and total on all rounds vs 4.1, and rounds 12 and 17 separately labelled anecdotal. Write `reports/phase4_sprint.md`.
- `tests/test_sprint.py`: a small synthetic check that a sprint round gets the sprint term, a non-sprint round does not, and the output has no lookahead.

Pass bar (report plainly either way, do not tune to pass): beats 4.1 on MAE and total over the 6 sprint rounds, and all-rounds MAE and total are no worse than 4.1. If it fails, keep the code disabled (do not wire it into `pick_team.py`) and say so in the report. Do not fill any null rule.

## Task B: benched-driver fix (known issue)

`docs/known-issues.md` describes a bug: drivers who are benched for a round (for example HAD in rounds 12-14) still get picked and score 0, because `prices` has no active flag and `robust_mu` scores them on stale form. `src/ingest/build_tables.py` already reads an `IsActive` field from the official data (around line 122).
- Carry the active flag into the `prices` table (column name `active`, boolean) and rebuild via `pipelines/build_data.py` (needs `F1_DATA_KEY` in the environment; do not print it).
- Make `pipelines/pick_team.py` skip inactive drivers (they cannot be picked or kept as a scoring asset). Check first that `active` is false for exactly the benched cases in the data and report the rows; if the flag is unreliable, stop and report instead of working around it.
- Add one test. Do not change `robust_mu`.

## Deliverables

1. Commits on `chatgpt/4.6-sprint` (no push).
2. A short report to me: files changed, test count, the 4.6 result table copied from `reports/phase4_sprint.md`, and for Task B the benched rows found and the flag's reliability.
3. Add one dated line to `docs/progress.md` per task. Record any unfixed finding in `docs/known-issues.md`.
