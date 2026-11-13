# Prompt for ChatGPT: Phase 5 tasks 5.1 and 5.2

You are working in the Python repo `f1-fantasy` (F1 Fantasy optimizer). Read `CLAUDE.md`, `docs/progress.md`, `docs/decisions.md`, `docs/known-issues.md` and the Phase 5 plan `docs/superpowers/plans/2026-11-12-phase-5-backtest.md` first. Follow CLAUDE.md hard rules: game rules only from `config/rules_*.yaml`, every feature uses data with `known_at <= lock_utc`, ask before adding any dependency, no commits to main, no pushes, never print `F1_DATA_KEY`. Code style: smallest correct diff, reuse existing helpers (`robust_mu` and `baseline_mu` in `src/features/rolling.py`, `run_season` in `src/backtest/walkforward.py`, `mae` in `pipelines/evaluate_form.py` as the template). Run `uv run pytest -q`; 217 tests pass today and must still pass.

## Worktree (required)

Work in your own git worktree, never the main folder:

```
git worktree add ../f1-fantasy-5.1-metrics -b chatgpt/5.1-metrics main
```

All edits, runs and commits happen in `../f1-fantasy-5.1-metrics`. Claude works in parallel on task 5.3 in `../f1-fantasy-5.3-carryover`, in `src/features/carryover.py` and the `carryover` section of `config/model.yaml`. Do NOT edit those, and do not edit `src/features/rolling.py` (call it, do not change it). The processed Parquet tables are gitignored: copy `data/processed/` from the main folder into the worktree, or run `pipelines/build_data.py` there (needs `F1_DATA_KEY`).

## Task 5.1: metrics and multi-season walk-forward

- `src/backtest/metrics.py`: one function that takes a season's walk-forward result plus actual points and returns per-asset MAE, season total, total from round 5, rounds 1-4 total, and mean per-round Spearman of predicted vs actual asset points (scipy is installed).
- `pipelines/evaluate_seasons.py`: run rolling-5 (`baseline_mu`) and `robust_mu` (settings from `config/model.yaml` `form`) through `run_season` on 2023, 2024, 2025, 2026. Print and write `reports/phase5_seasons.md` with one row per predictor per season. Accept an optional predictor argument so Claude can add the carry-over predictor later without editing your code.
- One test for `metrics.py` on a tiny synthetic frame (known MAE, totals and Spearman).
- Append aggregate 2026 metrics to `reports/holdout_2026_log.md` (aggregate numbers only, dated).

## Task 5.2: re-tune trim and prior weight

- Grid-search `trim` and `prior_weight` on 2023-2025 combined (sum of season totals; report MAE alongside). Use the same grid style as `pipelines/evaluate_form.py`.
- Check the best setting on 2026. Change `config/model.yaml` `form` only if the 2026 season total is no worse than the current 0.3 / 2.0 (4363). Otherwise leave it and say so.
- Log the 2026 check in `reports/holdout_2026_log.md`.

Report plainly either way; do not tune to pass.

## Deliverables

1. Commits on `chatgpt/5.1-metrics` in the worktree (no push).
2. A short report to me: files changed, test count, the season table from `reports/phase5_seasons.md`, the 5.2 best setting and its 2026 result, and whether `config/model.yaml` changed.
3. One dated line per task in `docs/progress.md`. Record any unfixed finding in `docs/known-issues.md`.
