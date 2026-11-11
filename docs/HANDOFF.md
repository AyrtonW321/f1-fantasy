# Handoff: F1 Fantasy Optimizer

No prior context. Read this file first, then `CLAUDE.md` and three files in `docs/` (`progress.md`, `decisions.md`, `known-issues.md`).

## What this project is

Python system for official F1 Fantasy game. Reproduces game scoring for 2023-2026, predicts each driver's and constructor's points, picks best team each race under budget cap. Goal: working backtest on 2023-2026, live use from Round 1 of 2027.

Full spec: `docs/superpowers/specs/2026-11-09-f1-fantasy-optimizer.md` (Part 1 = decisions made with user, wins over Part 2 = original spec).
Full plan: `docs/superpowers/plans/2026-11-09-f1-fantasy-optimizer.md`.

## Done so far (Phases 1 and 2, all committed and pushed on branch `phase-1-ingest-scoring`)

- Data pulled and stored: official 2026 fantasy feeds, TracingInsights (2023-2025 fantasy data), mzafram (totals cross-check), Jolpica (results and schedules). Raw data committed only as one encrypted file, `data/raw.tar.gz.enc`.
- Per-season rules in `config/rules_2023.yaml` to `rules_2026.yaml`, plus scoring engine (`src/sim/scoring.py`).
- Clean tables in `data/processed/` (built by `pipelines/build_data.py`).
- Phase 1 acceptance passes: scoring reproduces every official session total in all four seasons (one documented source exception).
- Baseline predictor (same-season rolling average with price prior), PuLP team optimizer, walk-forward backtest. Baseline season totals: 2023 6190, 2024 4561, 2025 4558, 2026 4269 (no chips).
- 146 tests pass.

## Set up before working

1. Environment variables `F1_DATA_KEY` (password for encrypted data; ask user, never print or commit) and `UV_PROJECT_ENVIRONMENT` (keeps virtualenv outside OneDrive) must be set.
2. Unlock data: `uv run python -m src.ingest.vault unseal`
3. Build tables: `uv run python pipelines/build_data.py`
4. Check everything works: `uv run pytest -q` and `REQUIRE_DATA=1 uv run pytest -m data -q`

## What needs to be done next

**Phase 3: pace data and car-strength model.** No detailed plan yet.

1. First write task-level plan for Phase 3 in `docs/superpowers/plans/` (same style as existing plan), ask user to review before building anything.
2. Phase 3 content (from spec):
   - Ingest FastF1 laps (practice, qualifying, sprint, race, tyres, stints, weather, pit stops) into Parquet. Keep FastF1 cache outside OneDrive.
   - Build `data/static/tracks.csv` by hand (track type, overtaking difficulty, safety car rate, sprint flag).
   - `src/features/pace.py`: FP2 long-run pace per driver per weekend, fitted as `lap_time = alpha + beta*lap_number + gamma_compound*tyre_age`.
   - `src/models/kalman.py`: car strength over time, `y[d,r] = theta_car[r] + phi_driver + tau_track + noise`.
3. Acceptance: FP2 long-run pace exists for every driver and weekend, and Kalman model correlates with race order better than "last race's order" does.
4. Later phases (4-7: event models and simulator, full backtest and tuning, chips and horizon planning, automation) outlined only in plan.

Also pending: push `main` branch so pull request can be opened, and rerun official 2026 snapshot (`src/ingest/fantasy_scrape.py`) after final 2026 race, then reseal with `uv run python -m src.ingest.vault seal`.

## Rules you must follow

- No phase starts before previous phase's acceptance passes.
- Every feature carries `known_at` time; nothing may use data from after lineup lock of race it predicts.
- Game rules live in config files, never in code. `null` rule means "never observed": raise error, do not guess.
- Tune models on 2023-2025 only. 2026 held out for one final check, every look at it logged.
- Never read TracingInsights `priceChange` (post-race data).
- Ask user before adding dependency not in spec's list. Chips left for Phase 6.
- No plaintext data in git. Pushes need user's OK.