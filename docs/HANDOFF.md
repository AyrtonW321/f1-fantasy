# Handoff: F1 Fantasy Optimizer

No prior context. Read this file first, then `CLAUDE.md` and three files in `docs/` (`progress.md`, `decisions.md`, `known-issues.md`).

## What this project is

Python system for official F1 Fantasy game. Reproduces game scoring for 2023-2026, predicts each driver's and constructor's points, picks best team each race under budget cap. Goal: working backtest on 2023-2026, live use from Round 1 of 2027.

Full spec: `docs/superpowers/specs/2026-11-09-f1-fantasy-optimizer.md` (Part 1 = decisions made with user, wins over Part 2 = original spec).
Full plan: `docs/superpowers/plans/2026-11-09-f1-fantasy-optimizer.md`.

## Done so far (Phases 1-3 on `main`; Phase 4 in progress on `codex/phase-3-plan`, uncommitted)

- Phase 1: data pulled (official 2026 feeds, TracingInsights 2023-2025, mzafram, Jolpica), raw data only in encrypted `data/raw.tar.gz.enc`. Per-season rules in `config/rules_2023..2026.yaml`, scoring engine `src/sim/scoring.py`. Scoring reproduces every official session total (one documented exception).
- Phase 2: rolling-5 baseline, PuLP optimizer, walk-forward backtest. Totals: 2023 6190, 2024 4561, 2025 4558, 2026 4269.
- Phase 3: FastF1 2025-2026 ingest, FP2 pace (`src/features/pace.py`), track metadata (`data/static/tracks.csv`), Kalman car strength (`src/models/kalman.py`) beating last-race order. Pace is not comparable across drivers yet and is not used in Phase 4.
- Phase 4 task 4.1 done: `robust_mu` (2026-only trimmed mean shrunk to price prior) beats rolling-5 on 2026: MAE 13.47 vs 14.36, total 4363 vs 4269. `pipelines/pick_team.py` picks the next round's team. 2026 chip rules in `config/rules_2026.yaml`.

## Set up before working

1. Environment variables `F1_DATA_KEY` (password for encrypted data; ask user, never print or commit) and `UV_PROJECT_ENVIRONMENT` (keeps virtualenv outside OneDrive) must be set.
2. Unlock data: `uv run python -m src.ingest.vault unseal`
3. Build tables: `uv run python pipelines/build_data.py`
4. Check everything works: `uv run pytest -q` and `REQUIRE_DATA=1 uv run pytest -m data -q`

## What needs to be done next

Phase 4 plan (revised 2026-11-10, read its "Revision" and "Revised task list" sections first): `docs/superpowers/plans/2026-11-10-phase-4-event-models-simulator.md`.

1. Task 4.2: race order + DNF Monte Carlo simulator. Must beat 4.1 on 2026 MAE and season total.
2. Task 4.3 (ChatGPT): chip planner. Needs the user's team (`config/my_team.yaml`, gitignored) and remaining chips to give real advice; build and test it first with fixtures.
3. Tasks 4.4-4.6 (Claude) one at a time; 4.7 samplers (ChatGPT) wired in by Claude. Each kept only if the backtest improves.
4. Task 4.8: freeze Nov 20 and print the Las Vegas pick before lock (2026-11-21 04:00 UTC).

Also pending: rerun the official 2026 snapshot (`src/ingest/fantasy_scrape.py`) after each remaining 2026 race, then reseal with `uv run python -m src.ingest.vault seal`.

## Who does what (Phase 4, split 2026-11-10)

Claude and ChatGPT share this checkout on branch `codex/phase-3-plan`. Each edits only the files it owns. Nobody commits or pushes without the user's OK. Each one updates only its own row of the Phase 4 task list Status column; Claude owns all other docs edits (`progress.md`, `decisions.md`, `known-issues.md`, this file).

| Owner | Tasks | Files owned |
|---|---|---|
| Claude (side session `p4-race-dnf`) | 4.2 race order + DNF simulator | `src/models/plackett_luce.py`, `src/models/dnf.py`, `src/sim/montecarlo.py`, `pipelines/evaluate_sim.py`, their tests, `reports/phase4_sim.md` |
| Claude (main session) | 4.4 qualifying, 4.5 positions gained, 4.6 sprints, wiring 4.7 samplers into the simulator, 4.8 freeze and Las Vegas pick; all docs | extends the 4.2 files after it lands; `src/models/poisson.py`; `pipelines/pick_team.py` final version; `docs/` |
| ChatGPT | 4.3 chip planner; 4.7 bonus-event models (standalone samplers + data audit, not wired into the simulator) | `src/optimize/chips.py`, `pipelines/plan_chips.py`, `tests/test_chips.py`, `src/models/bonus.py`, `tests/test_bonus.py`, `reports/phase4_bonus_audit.md` |

Shared read-only for everyone: `src/sim/scoring.py`, `src/optimize/ilp.py`, `src/features/rolling.py`, `config/*.yaml`, `data/processed/`. A change needed there goes to the user first.

Interfaces between the two:
- A predictor is `(season, round) -> DataFrame` with columns `season, round, asset_id, kind, price, mu, known_at` (as `robust_mu` returns). The chip planner takes any predictor, so it uses `robust_mu` now and the simulator later with no code change.
- `src/models/bonus.py` exposes samplers the simulator calls per draw: input = pre-lock context for one round plus that draw's simulated race order; output = the bonus outcome (fastest-lap driver, Driver of the Day, constructor pit-stop points), or an explicit `unsupported` status. No reading rounds at or after the target.

## Rules you must follow

- No phase starts before previous phase's acceptance passes.
- Every feature carries `known_at` time; nothing may use data from after lineup lock of race it predicts.
- Game rules live in config files, never in code. `null` rule means "never observed": raise error, do not guess.
- Phase 4: fit and tune on 2026 only, walk-forward; tune on rounds 1-10, report all rounds. (Phase 3 tuned on 2023-2025 with 2026 held out.)
- Never read TracingInsights `priceChange` (post-race data).
- Ask user before adding dependency not in spec's list.
- No plaintext data in git. Pushes need user's OK.