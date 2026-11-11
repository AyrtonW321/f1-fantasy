# Phase 3 Plan: Pace Data and Car Strength

**Status:** Approved for execution (2026-11-09); local F1 TV authentication active. FastF1 detailed-data scope narrowed to 2025-2026; cached pull resumes after FastF1's 500 calls/hour rate limit.
**Scope:** FastF1 ingestion for 2025-2026, static track metadata, FP2 long-run pace features for those seasons, sequential car-strength model.
**Prerequisite:** Phases 1-2 acceptance recorded as passing in `docs/progress.md`.

## Goals and boundaries

- Store FastF1 session metadata and lap-level data for 2025-2026 as Parquet under `data/processed/`. Do not fetch 2024 FastF1 data; preserve existing older-season tables without rebuilding.
- Keep FastF1's mutable cache outside OneDrive, configured by environment variable, documented for local setup.
- Build and maintain `data/static/tracks.csv` with track type, overtaking difficulty, safety-car rate, sprint flag.
- Produce one FP2 coverage/status row for every expected race entrant and weekend. Produce long-run pace estimate where usable data exists; mark absent, unusable, or post-lock FP2 data explicitly; never use post-lock observations as pre-lock feature.
- Estimate race-by-race car strength with state-space/Kalman model; show it predicts race order better than last-race-order baseline.
- Tune model choices using 2023-2025 only. Treat 2026 as logged final holdout evaluation; do not tune against it.

Phase does not add event models, Monte Carlo simulation, fantasy-point prediction, optimizer changes, chip logic, or automation. Do not read TracingInsights `priceChange`. FastF1 specified and approved for addition; now project dependency. Current FastF1 archive access requires eligible F1 TV account. Authenticate locally with FastF1 CLI; never store login credentials in repository.

## Data and timing contracts

- Canonical event identity and round come from existing Jolpica `races` table. Join FastF1 meetings by season and reviewed event alias table where names differ; fail with actionable error on unresolved events.
- Retain raw session/lap facts needed for reproduction: season, round, session identifier/type, driver code, timestamp or lap number, lap time, sector times, compound, tyre age, stint, pit-in/out indicators, track status, source/cache metadata where available. Session rows retain start time, weather, session status. Do not infer unavailable values.
- Convert datetimes to UTC. Feature's `known_at` = earliest time its input data was available from completed FP2 session; leakage guard must reject any feature known after that event's `lock_utc`.
- Cache location must be explicit (`FASTF1_CACHE_DIR`) and outside repository/OneDrive. Ingest command fails if no external cache location or usable archive authentication configured.
- Data tests use synthetic fixtures and mocked FastF1 responses; real-data acceptance is separate, explicitly run command after local data available.
- No plaintext source dumps committed. Processed data and reports stay under existing ignore rules unless repository's data policy deliberately changed.

## Task 1: FastF1 access and event/session inventory

**Files:**
- Create `src/ingest/fastf1_pull.py`.
- FastF1 added as `fastf1>=3.9.2,<4` after user approved Phase 3 execution.
- Create focused tests under `tests/`.

**Work:**
- Define supported season range and session types (practice, qualifying, sprint qualifying/shootout, sprint, race) using FastF1's public API.
- Add small event/session inventory command comparing available FastF1 events and sessions with Jolpica's canonical schedule before downloading all laps.
- Implement event aliases as data/config, not scattered special cases; unresolved or ambiguous joins stop pull.
- Configure and verify external cache path before making FastF1 calls.

**Checks:** mocked tests cover aliases, missing events/sessions, API failures, UTC conversion, cache-path rejection when it resolves inside repo. One-weekend smoke pull required before full historical ingest. If auth not configured, fail with clear message and leave no empty session rows.

## Task 2: Session and lap ingestion to Parquet

**Files:**
- Extend `src/ingest/fastf1_pull.py` or add `src/ingest/fastf1_tables.py` if normalization warrants separate module.
- Use `python -m src.ingest.fastf1_pull` as ingestion CLI.
- Create tests for normalized tables.

**Work:**
- Ingest available practice, qualifying, sprint qualifying/shootout, sprint, race sessions for 2025-2026.
- Write normalized `sessions.parquet` and `laps.parquet` to `data/processed/`, including required timing, tyre, stint, weather, pit-stop, track-status fields when supplied by FastF1.
- Preserve missing values; distinguish unavailable sessions/data from empty sessions. Write `fastf1_session_inventory.parquet` with expected, loaded, not-loaded rows; record row/session counts and warnings per event in local report.
- Make pulls restartable: use FastF1 cache, avoid duplicate keys, allow season/event filters for recovery.
- On FastF1's rate-limit exception: stop current request loop, persist its successful rows and complete expected-session inventory, then resume from cache in later request window.

**Checks:** synthetic tests validate schema/types, stable keys, duplicate handling, missing optional fields, retry/error reporting, deterministic season/event filtering. Pull 2025-2026 and inspect coverage by event/session, driver, lap count before proceeding.

## Task 3: Track metadata

**Files:**
- Create `data/static/tracks.csv`.
- Create `tests/test_tracks.py` and small loader in appropriate feature/data module if needed.

**Work:**
- Populate one reviewed row per scheduled event (`season`, `round`) with `track_id`, track type, overtaking difficulty, prior-only historical safety-car rate, event-specific sprint flag.
- Define allowed categories/scales; document how safety-car rate calculated, its source window, how new/changed circuits handled. Keep sprint flag event-specific if circuit hosted both sprint and non-sprint weekends; do not encode as invariant circuit property.
- Avoid using race's realized safety-car outcome as feature for that same race. Historical rates must be computed using only prior events or be explicitly static metadata with cutoff.

**Checks:** validate required columns, unique keys, valid categories/ranges, every scheduled circuit covered, no future-derived safety-car statistics in walk-forward feature row.

## Task 4: FP2 long-run pace feature

**Files:**
- Create `src/features/pace.py`.
- Create `tests/test_pace.py`.
- Add pipeline entry point to produce `data/processed/pace.parquet`.

**Interface target:** typed function consuming normalized laps plus event/session metadata, returning one auditable row per driver and weekend, with pace estimate, observation count, compounds/tyre-age range, fit status, uncertainty/diagnostics, `known_at`.

**Model:** pool eligible FP2 long-run laps for one driver/weekend and fit `lap_time = alpha + beta * lap_number + gamma_compound * tyre_age`. Fit per stint underidentified when lap number and tyre age advance together on single compound, so use all eligible stints to estimate common lap trend and compound-specific age slopes. Center lap number and each compound's tyre age at documented reference values; `alpha` = driver's predicted lap time at those reference values. Report fit rank and residual diagnostics. Specify and test outlier, invalid-lap, minimum-sample, compound handling. Never fabricate FP2 observations: if FP2 cancelled or driver has no usable long run, emit explicit missing/status row and report it. Coverage means one status/feature row for every expected entrant; pace estimate required only when valid FP2 long-run data available before lock.

**Checks:** synthetic tests recover known coefficients and alpha, handle multiple compounds/stints, filter invalid/in/out laps and red flags, preserve missingness, produce stable results, enforce `known_at <= lock_utc`. Run coverage report across 2023-2026 and resolve unexplained gaps.

## Task 5: Sequential car-strength model

**Files:**
- Create `src/models/kalman.py`.
- Create `tests/test_kalman.py`.
- Create `reports/phase3_kalman.md` (derived metrics only; no raw fantasy data).

**Model:** implement state-space structure `y[d,r] = theta_car[r] + phi_driver + tau_track + noise`, with car strength evolving between rounds and smaller process noise for driver skill. Use documented performance observation built from existing Jolpica race outcomes and/or pace features; ensure feature availability is pre-lock for prediction being evaluated. Center car, driver, track effects to zero-sum after each race update. Define missing starts, reserve drivers, constructor changes, initial conditions, uncertainty handling. Carry spec's weak prior from prior-season constructor order only for first 2-3 rounds; compare against no-prior variant using 2023-2025 only.

**Checks:** synthetic sequences recover relative strength and respond to known car upgrade; filtering predictions at round r cannot consume observations from r or later when predicting that round; reordered input rows produce same result; missing drivers/team changes do not corrupt state.

## Task 6: Phase 3 evaluation and acceptance

- Build FP2 pace table and report coverage for 2025-2026 by season, round, session availability, driver. Coverage = one row for every expected driver/weekend. Each row either usable pace estimate or explicit status such as no FP2 session, session not loaded, no usable long run, or after lock. Do not fabricate replacement lap pace.
- Evaluate Kalman predictions walk-forward against race order, on same rounds and entrant set as naive baseline predicting previous race's order. Define rank correlation (Spearman) as primary metric; also report per-round coverage and simple error metric. Handle round 1 and new drivers explicitly; do not count them as wins for Kalman model via silent row dropping.
- Tune car, driver, track process noise, observation variance, previous-season prior weight, prior duration on 2023-2025 only. Observation fixed as within-round standardized finishing order. Include no-prior variant (`prior weight = 0`). Freeze choices before 2026 evaluation; log every holdout evaluation.
- Pace coverage acceptance follows the user's clarified no-fabrication decision: produce exactly one pace/status row for every expected entrant/weekend; estimate pace only when a qualifying long run exists, and explicitly mark no FP2, no usable long run, unloaded, or after-lock cases. Report usable-estimate coverage separately; never fill missing pace with a substitute session or synthetic value. Current output covers all 919 expected 2025-2026 entrant/weekend rows, with 518 usable pre-lock pace estimates and 149 `no_usable_longrun` rows among weekends with FP2. Kalman acceptance requires the predeclared aggregate rank correlation to exceed last-race order on comparable rounds; if not, report the result and revise the model/plan.
- Re-run full existing unit suite and `REQUIRE_DATA=1` Phase 1 data gate after implementation; rerun walk-forward Phase 2 acceptance to detect regressions.

## Execution order and review gates

1. Execution approved by user. Key choices: no credentials in chat or git; no fabricated FP2 fallback; post-lock FP2 cannot enter pre-lock predictions.
2. Confirm Phase 1-2 acceptance remains passing before implementation; if data setup requires `F1_DATA_KEY`, request it through user's secure environment workflow and never print it.
3. Implement tasks in order with worker briefs naming files, scope, hard rules, and runnable `Done when:` check. Orchestrator independently reruns each check and requests reviewer review before accepting output.
4. Do not commit or push without user approval. Never commit plaintext data or `F1_DATA_KEY`.
5. After acceptance, update `docs/progress.md`, add dated decisions and known issues, propose any skill edits supported by this session's evidence for user approval.
