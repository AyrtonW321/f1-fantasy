# Progress

Branches: phase-1-ingest-scoring is on GitHub. claude/graphify-setup-status-zfpzg5 and a local-only `main` (both at the graphify commit and later) are committed locally, not pushed: GitHub returns 403 (Claude GitHub App not installed on the repo).

## Done
- Spec and plan written (docs/superpowers/).
- Orchestrator/worker setup written; Haiku builders and reviewer used for every task.
- Phase 1 complete: official 2026 snapshot, encrypted vault, TracingInsights/mzafram/Jolpica pulls, per-season rules (2023-2026), scoring engine, Parquet tables.
- Phase 1 acceptance PASSES (2026-11-09): `REQUIRE_DATA=1 uv run pytest -m data` gives 8 passed. Scoring reproduces every completed session total in 2023, 2024, 2025 and 2026 (one documented exception, see known-issues). Full suite: 146 passed.
- Phase 2 complete: baseline predictor, leakage guard, PuLP optimizer, walk-forward backtest. Baseline totals (no chips, same-season rolling 5 with price prior):

| Season | Total | From round 5 | Rounds |
|---|---|---|---|
| 2023 | 6190 | 5067 | 22 |
| 2024 | 4561 | 3834 | 24 |
| 2025 | 4558 | 3924 | 24 |
| 2026 | 4269 | 3562 | 20 |

  Every round valid (5 drivers, 2 constructors), max solve 0.18 s. Reports in reports/baseline_{season}.md (gitignored).

## Next
- Install the Claude GitHub App on AyrtonW321/f1-fantasy, then push claude/graphify-setup-status-zfpzg5 and main (GitHub has no main yet).
- Investigate the extra players in the latest official gameday (37 vs 33); needs F1_DATA_KEY to unseal data/raw.
- Phase 3 (FastF1 laps, pace features, Kalman) needs its own task-level plan; none written yet.
- Rerun the official snapshot after the final 2026 race, before the 2027 game launches, then reseal.

## Blocked
- Pushing: GitHub 403, app not installed on the repo.
- Official-feed player investigation: needs F1_DATA_KEY (not set in cloud sessions).

## Log
- 2026-11-09: grilled the spec, wrote spec and plan, created repo, set up orchestrator/worker files and effort setting.
- 2026-11-09: Task 1 built by Haiku builders, re-run and reviewed by orchestrator; real snapshot sealed.
- 2026-11-09: Tasks 2-8 built in parallel batches. Process breach: Phase 2 tasks were committed before the Phase 1 gate passed (done for speed). The gate has since passed and no Phase 2 code changed because of it.
- 2026-11-10: set up graphify (code-only graph in graphify-out/, hooks in .claude/settings.json, rule in CLAUDE.md); created local main (fast-forward of Phase 1-2 plus graphify); small fixes: clear ValueError for a race entry without `time`, snapshot_official raises when the schedule feed fails.
