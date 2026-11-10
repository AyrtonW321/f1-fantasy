# Phase 3 Plan: Pace extraction and Kalman strength model

> **For agentic workers:** Same rules as the main plan (`2026-11-09-f1-fantasy-optimizer.md`): Global Constraints there apply unchanged. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Per-driver practice pace for every weekend, and a Kalman filter that tracks car strength and driver skill from sessions known before each lock. Acceptance: its race-order predictions beat "last race's order" on 2023-2025.

**Spec:** `docs/superpowers/specs/2026-11-09-f1-fantasy-optimizer.md` (Part 1 overrides Part 2). Phase 2 acceptance passed on 2026-11-09 (146 tests; baseline totals in `docs/progress.md`).

**Effect on fantasy points:** none yet. Phase 3 adds features and a strength model. Nothing here changes the Phase 2 baseline totals until Phase 4 builds event models on top.

## Where tasks can run

- Tasks 9 (offline parts), 11, 12, 13 are fully testable with hand-written fixtures. They run anywhere, including the cloud container.
- Task 10 (real pull) and Task 14 (acceptance) need network access to the FastF1 backend and `F1_DATA_KEY` to unseal `data/raw`. The cloud container has neither; run them on the user's machine or a session with the key and open network.

## Decisions (confirmed 2026-11-10: user chose the recommended default for all four)

1. **Laps are not put in the encrypted archive.** FastF1 laps for 2023-2026 are re-downloadable and large; the archive must stay under 95 MB and every re-seal adds a full blob to history. Keep the FastF1 cache outside the repo (`FASTF1_CACHE`, outside OneDrive) and `laps.parquet` in gitignored `data/processed/`. Cost: reproducibility depends on FastF1's backend staying available.
2. **Practice long-run pace deviates from the spec's literal formula.** Spec: `lap_time = alpha + beta*lap_number + gamma_compound*tyre_age` per stint. Inside one stint on a fresh set, `lap_number` and `tyre_age` move together, so beta and gamma cannot be separated. Plan: per stint fit `lap_time = alpha + beta*lap_in_stint` (beta absorbs fuel burn plus degradation), use alpha as the pace, and correct compounds with session-wide offsets `delta_compound` estimated from drivers who ran two or more compounds. Test checks the fit is full rank.
3. **2026 is not touched.** Phase 3 tunes nothing and evaluates on 2023-2025 only. Parameters are fixed starting values; tuning is Phase 5.
4. **`fastf1` is added as a dependency now.** It is on the spec's list, so no extra approval is needed; `uv.lock` changes. No `scipy` or `statsmodels`: the filter and regressions use numpy only. Side effect seen on 2026-11-10: `fastf1` 3.9.2 requires pandas below 3, so pandas moved from 3.1.1 to 2.3.3. The 141 existing tests still pass.

## Facts the design rests on

- Lock is the earliest of Qualifying, Sprint, SprintQualifying, SprintShootout. Practice before that is usable. Standard weekend: FP1, FP2 (Friday) and usually FP3 (Saturday morning). Sprint weekends have FP1 only before the lock, so FP2 long-run pace is absent there. Absent means NaN; never imputed, never zero.
- Session `known_at` = start + a per-type delay from `config/model.yaml` (practice 120 min, qualifying 120, sprint 120, race 360 to match `KNOWN_AT_DELAY`). A session feeds round r's features only if `known_at <= lock_utc` of round r. `assert_known_before_lock` runs on every output table.
- Canonical ids: driver = 3-letter abbreviation (FastF1 `Driver` is expected to match; Task 10 verifies on real data), constructor = Jolpica `constructorId` from the `results` table for that round. A driver without a results row that weekend (FP1 rookie) is dropped from observations and counted in the build log.
- Strength sign: `strength = -gap_pct`, so larger is faster. Gaps are percent of lap time, relative to the field median in that session.
- The Kalman filter runs per season (state reset each January: 2026 regulation reset, and the same code is used for 2023-2025). Parameters are shared across seasons.

## File Structure (additions)

```
config/model.yaml          + sessions, pace, kalman blocks
data/static/tracks.csv     hand-built, committed
data/processed/            + sessions.parquet, laps.parquet, pace.parquet, strength.parquet (gitignored)
src/ingest/build_tables.py + build_sessions
src/ingest/fastf1_pull.py  FastF1 laps to the laps table
src/ingest/tracks.py       tracks.csv loader and checks
src/features/pace.py       practice, race and quali pace
src/models/kalman.py       strength filter and season runner
src/backtest/phase3_check.py  acceptance report
tests/                     test_sessions.py, test_fastf1_pull.py, test_tracks.py, test_pace.py, test_kalman.py, test_phase3_acceptance.py
```

---

### Task 9: Dependency, config and sessions table

**Files:**
- Modify: `pyproject.toml` (add `fastf1`), `uv.lock`, `config/model.yaml`, `src/ingest/build_tables.py` (add `build_sessions`, call it from `build_all`)
- Test: `tests/test_sessions.py`

**Interfaces:**
- Produces: `build_sessions(season: int, raw_dir: Path) -> pd.DataFrame` with columns `season, round, session, start_utc, known_at, usable_pre_lock`. `session` is one of `FP1, FP2, FP3, Q, SQ, S, R` (SQ covers SprintQualifying and SprintShootout).

`config/model.yaml` additions:

```yaml
sessions:
  known_after_start_minutes: {practice: 120, qualifying: 120, sprint: 120, race: 360}
pace:
  long_run_min_laps: 6
  slow_lap_cutoff: 1.07        # drop laps slower than 107% of the driver's median in the stint
  race_clean_laps_min: 15
kalman:
  q_car: 0.0225                # per-round random-walk variance of car strength, pct^2
  q_driver: 0.0001
  q_first_round_multiplier: 1.0   # manual bump of q_car at the first round of a season
  p0_car: 1.0
  p0_driver: 0.04
  sigma: {race: 0.25, qualifying: 0.20, practice_long_run: 0.50, practice_short_run: 0.60}
  prior_2025_weight: 0.0       # off by default; enabled only if Phase 5 shows it helps on 2023-2025
```

These are starting values chosen from the scale of the quantities (cars spread over a few percent of lap time), not fitted. Phase 5 tunes them on 2023-2025.

- [ ] **Step 1: Verify the schedule has practice sessions.** On a machine with the key, check that real `jolpica/{season}/races.json` entries carry `FirstPractice`/`SecondPractice` (fixtures in `tests/test_build_tables.py` already assume it). If not, stop and report; fallback would be `fastf1.get_event_schedule`, which is a decision for the user.
- [ ] **Step 2: Write failing tests**

```python
def test_standard_weekend_has_fp1_fp2_fp3_q_r(): ...
def test_sprint_weekend_has_fp1_sq_s_q_r_and_no_fp2(): ...
def test_known_at_is_start_plus_configured_delay(): ...   # FP2 start 15:00 -> 17:00; race start -> +6h
def test_practice_after_lock_not_usable(): ...            # a practice session starting after lock_utc: usable_pre_lock False
def test_fp1_before_sprint_qualifying_is_usable(): ...
def test_missing_time_raises_value_error_naming_round(): ...
def test_sprint_shootout_maps_to_sq(): ...
```

- [ ] **Step 3: Run tests.** Expected: FAIL.
- [ ] **Step 4: Implement.** `uv add fastf1`, extend config, implement `build_sessions` reusing `_utc` and the clear `ValueError` style of `_lock_utc`. `usable_pre_lock = known_at <= lock_utc` of that round.
- [ ] **Step 5: Run `uv run pytest -q`.** Expected: all prior tests plus the new ones pass.
- [ ] **Step 6: Commit:** `feat: add sessions table and Phase 3 config`.

**Done when:** `uv run pytest tests/test_sessions.py -q` passes and `uv run pytest -q` shows no regressions.

### Task 10: FastF1 laps ingest

**Files:**
- Create: `src/ingest/fastf1_pull.py`
- Modify: `pyproject.toml` (add pytest marker `network`)
- Test: `tests/test_fastf1_pull.py`

**Interfaces:**
- Produces: `normalize_laps(raw: pd.DataFrame, season: int, round_: int, session: str, constructor_by_driver: dict[str, str], known_at: pd.Timestamp) -> pd.DataFrame` (pure, no network) with columns `season, round, session, driver_code, constructor_id, lap_number, lap_time_s, stint, compound, tyre_life, is_accurate, track_status, in_lap, out_lap, known_at`.
- Produces: `pull_laps(season, round_, session, cache_dir) -> pd.DataFrame` (thin FastF1 wrapper) and a `__main__` that builds `data/processed/laps.parquet` and prints `wrote N laps, M sessions, K sessions missing`.

- [ ] **Step 1: Write failing tests** (hand-written raw DataFrame shaped like FastF1 output)

```python
def test_lap_time_converted_to_seconds(): ...
def test_in_and_out_laps_flagged_from_pit_times(): ...
def test_driver_without_results_row_dropped_and_counted(): ...
def test_missing_lap_time_kept_as_nan_not_zero(): ...
def test_known_at_comes_from_sessions_table_not_lap_timestamps(): ...
def test_unset_cache_dir_raises_clear_error(): ...        # FASTF1_CACHE missing
def test_session_failing_to_load_is_reported_not_skipped_silently(): ...
```

- [ ] **Step 2: Run tests.** Expected: FAIL.
- [ ] **Step 3: Implement.** Cache dir from `FASTF1_CACHE`; raise if unset (never default into the repo or OneDrive). A session that fails to load goes into a printed missing list and the command exits non-zero if any session expected by `sessions.parquet` (completed rounds only) is missing.
- [ ] **Step 4: Run offline tests.** Expected: PASS.
- [ ] **Step 5 (needs network + key): real pull** for 2023-2026 completed rounds. Check on real output: FastF1 `Driver` equals the canonical abbreviation for every driver in `results`; row counts per session are plausible. Report mismatches, do not patch silently.
- [ ] **Step 6: Commit:** `feat: add FastF1 laps ingest`.

**Done when:** offline `uv run pytest tests/test_fastf1_pull.py -q` passes. Real-data half: the pull prints the summary line with `0 sessions missing`, or the missing sessions are listed and the user has decided what to do.

### Task 11: tracks.csv

**Files:**
- Create: `data/static/tracks.csv`, `src/ingest/tracks.py`
- Test: `tests/test_tracks.py`

**Interfaces:**
- Produces: `load_tracks(path: Path, races: pd.DataFrame) -> pd.DataFrame` with columns `slug, circuit_type, overtaking_difficulty, notes`. `circuit_type` in `{street, permanent, hybrid}`; `overtaking_difficulty` integer 1 (easy) to 5 (very hard).

The file is hand-built by the user. The generator writes a template from the Jolpica slugs with the rating columns blank. **Never fill ratings in on the user's behalf.** Safety-car rate is derived from lap `track_status` in Phase 4, not typed here.

- [ ] **Step 1: Write failing tests**

```python
def test_every_race_slug_has_a_row(): ...                  # missing slug raises ValueError naming it
def test_unknown_slug_in_csv_raises(): ...
def test_blank_rating_is_nan_and_reported(): ...           # allowed, but listed
def test_overtaking_out_of_range_raises(): ...
def test_bad_circuit_type_raises(): ...
```

- [ ] **Step 2: Run tests.** Expected: FAIL.
- [ ] **Step 3: Implement** loader and the template writer (`uv run python -m src.ingest.tracks --template`).
- [ ] **Step 4: Run tests.** Expected: PASS.
- [ ] **Step 5: Ask the user to fill the ratings.** Kalman does not need them in Phase 3 (`tau_track` is off by default); Phase 4 does.
- [ ] **Step 6: Commit:** `feat: add tracks loader and template`.

**Done when:** `uv run pytest tests/test_tracks.py -q` passes and the template lists every slug in 2023-2026.

### Task 12: Pace features

**Files:**
- Create: `src/features/pace.py`
- Test: `tests/test_pace.py`

**Interfaces:**
- Produces `practice_pace(laps, sessions, races, season, round_) -> pd.DataFrame`: columns `season, round, driver_code, constructor_id, long_run_alpha_s, long_run_gap_pct, long_run_laps, short_run_gap_pct, known_at`. Long run from FP2 only; short run (best lap gap to fastest, in percent) from all practice sessions with `usable_pre_lock`.
- Produces `race_pace(laps, season, round_) -> pd.DataFrame`: `driver_code, constructor_id, race_gap_pct, clean_laps, known_at`.
- Produces `quali_pace(laps, season, round_) -> pd.DataFrame`: `driver_code, constructor_id, quali_gap_pct, known_at` (best lap, percent over pole).
- `practice_pace` calls `assert_known_before_lock` (it takes `races`). `race_pace` and `quali_pace` are used for later rounds and have no `races` argument: `known_at` is the session's own, and the lock check is enforced at use time by `run_season` (Task 13), which applies only observations with `known_at <= lock_utc`.

Rules: long-run stints need at least `long_run_min_laps` laps after dropping in/out laps, non-green `track_status`, and laps slower than `slow_lap_cutoff` times the stint median. Race pace uses green-flag laps after lap 1, excluding in/out laps, and needs `race_clean_laps_min`; otherwise NaN.

- [ ] **Step 1: Write failing tests** (synthetic laps, known truth)

```python
def test_long_run_recovers_known_alpha(): ...             # lap_time = 90.0 + 0.05*lap_in_stint, no noise: alpha == 90.0
def test_stint_below_min_laps_gives_nan(): ...
def test_in_out_and_yellow_laps_excluded(): ...
def test_compound_offset_corrects_soft_vs_medium(): ...   # driver on soft only: alpha shifted by session-wide delta
def test_fit_is_full_rank_for_fresh_tyre_stint(): ...     # decision 2: no lap_number/tyre_age collinearity
def test_gap_is_percent_of_field_median(): ...
def test_sprint_weekend_has_no_long_run_row_values(): ...  # no FP2: NaN, not 0
def test_short_run_uses_only_pre_lock_sessions(): ...      # FP3 after lock excluded
def test_race_pace_requires_clean_laps(): ...
def test_quali_gap_zero_for_pole(): ...
def test_output_known_at_after_lock_raises_leakage_error(): ...
```

- [ ] **Step 2: Run tests.** Expected: FAIL.
- [ ] **Step 3: Implement** with numpy least squares. No SciPy.
- [ ] **Step 4: Run tests.** Expected: PASS.
- [ ] **Step 5: Commit:** `feat: add practice, race and quali pace features`.

**Done when:** `uv run pytest tests/test_pace.py -q` passes. Real-data half is Task 14.

### Task 13: Kalman strength filter

**Files:**
- Create: `src/models/kalman.py`
- Test: `tests/test_kalman.py`

**Model:** state = `[theta_c for each constructor, phi_d for each driver]`, transition identity plus process noise (`q_car` on theta, `q_driver` on phi, with `q_car` multiplied by a manual bump at the first round of a season). Observation for driver d with constructor c(d): `y = theta_c + phi_d + eps`, `eps ~ N(0, sigma_kind^2)`, `y = -gap_pct`. Sessions are processed in `known_at` order, each as one batch update.

**Interfaces:**
- `StrengthFilter(params: dict)` with `.add_entities(constructors, drivers)`, `.predict_step(q_multiplier=1.0)`, `.update(obs: pd.DataFrame)` (columns `driver_code, constructor_id, y, kind`), `.state() -> pd.DataFrame`.
- `run_season(season, observations, races, params) -> pd.DataFrame`: columns `season, round, driver_code, constructor_id, theta, phi, strength, var, known_at`, one row per driver per round, built only from observations with `known_at <= lock_utc` of that round. Calls `assert_known_before_lock`.

- [ ] **Step 1: Write failing tests**

```python
def test_recovers_known_strengths(): ...                  # A=+1, B=0, noise sd 0.1, seed 0, 10 rounds: |theta_A-1|<0.15, A>B
def test_tracks_step_change_faster_with_larger_q(): ...
def test_unobserved_driver_keeps_mean_and_variance_grows(): ...
def test_mid_season_team_move_keeps_phi_joins_new_theta(): ...
def test_nan_observation_skipped(): ...
def test_covariance_stays_symmetric_and_psd(): ...        # after 200 random updates
def test_observation_after_lock_never_used(): ...         # mutate a post-lock y: round-r output identical
def test_round_one_uses_prior_only_with_larger_variance(): ...
def test_prior_2025_weight_zero_means_flat_start(): ...
def test_season_runner_resets_state_each_season(): ...
def test_batch_update_matches_sequential_single_updates(): ...
```

- [ ] **Step 2: Run tests.** Expected: FAIL.
- [ ] **Step 3: Implement** in numpy (about 30 entities; no performance concern). Use the Joseph form for the covariance update. Teammates share `theta_c`, so `phi_d` is identified from within-team gaps; `p0_driver` is small so the common component goes into `theta`.
- [ ] **Step 4: Run tests.** Expected: PASS.
- [ ] **Step 5: Commit:** `feat: add Kalman strength filter`.

**Done when:** `uv run pytest tests/test_kalman.py -q` passes, including the lock-mutation test.

### Task 14: Phase 3 acceptance

**Files:**
- Create: `src/backtest/phase3_check.py`, `tests/test_phase3_acceptance.py` (marked `data`)
- Output: `reports/phase3_kalman.md` (gitignored, derived from fantasy-adjacent data)

Run from the project folder: `uv run python -m src.backtest.phase3_check --seasons 2023 2024 2025`.

**Metric.** For each completed round r >= 2 in a season: rank drivers by Kalman `strength` (built from data known before `lock_utc` of r, including that weekend's practice), and compare to the actual race classification from `results` (classified finishers) with Spearman rank correlation. Control: rank by each driver's finishing position in round r-1 (drivers present in both rounds). Extra, report-only: mean finish over the last 5 rounds.

**Gates**
1. **Pace coverage.** On standard weekends (FP2 present) in 2023-2025, at least 80% of drivers who started the race have a `long_run_alpha_s`. The 80% is a starting guess; if it fails, report the weekends and reasons (wet FP2, red flags) and let the user decide. Do not lower it to pass.
2. **Kalman beats last-race order.** Mean Spearman higher than the control in at least 2 of 3 seasons and pooled. Also holds with `q_car` at 0.5x and 2x the default (not a knife-edge).
3. **No leakage.** `assert_known_before_lock` passes on `pace` and `strength` for every round; the mutation test from Task 13 passes on real data.
4. **2026 untouched.** The script refuses `--seasons` containing 2026 unless `--holdout` is passed, and then appends the evaluation to `reports/holdout_2026_log.md` before printing results.

- [ ] **Step 1: Write the acceptance test** (`-m data`, runs only with `REQUIRE_DATA=1` and real data) asserting gates 1 to 4; add a unit test for the 2026 refusal that needs no data.
- [ ] **Step 2: Implement** the report: per season table (rounds, Kalman mean, control mean, 5-round mean, win count), coverage table, list of shortfalls.
- [ ] **Step 3 (needs network + key):** run it. If gate 2 fails, stop and report the numbers. Do not tune on 2023-2025 to rescue it inside this phase without asking; tuning is Phase 5.
- [ ] **Step 4: Update docs:** `progress.md` (dated log line, results table), `decisions.md` (the four decisions above, with the user's answers), `known-issues.md` (any weekends lacking pace, sprint-weekend gaps).
- [ ] **Step 5: Commit:** `feat: add Phase 3 acceptance check`.

**Done when:** `REQUIRE_DATA=1 uv run pytest -m data tests/test_phase3_acceptance.py` passes and `reports/phase3_kalman.md` shows all four gates met, or the failing rows are with the user.

---

## Not in Phase 3

Event models and the simulator (Phase 4); tuning `Q`, `sigma` and `lambda` (Phase 5); pit-stop data; weather and safety-car features; sprint-session pace as Kalman observations; `tau_track` (config flag off); driver skill from seasons before 2023; any change to the fantasy-point predictor or the backtest totals.

## Open items for the user

1. Answers to the four decisions above (defaults are the recommendations).
2. Fill the rating columns of `data/static/tracks.csv` when the template exists.
3. Run Tasks 10 and 14 where the FastF1 backend and `F1_DATA_KEY` are available.
