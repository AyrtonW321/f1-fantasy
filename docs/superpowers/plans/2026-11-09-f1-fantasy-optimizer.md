# F1 Fantasy Optimizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python system reproducing official F1 Fantasy scoring for 2023-2026, picking valid optimal team each round from rolling baseline. Base for full prediction system.

**Architecture:** Raw source files committed only as one encrypted archive, normalized into Parquet tables. `scoring.py` and ILP optimizer read per-season YAML rules. Walk-forward runner carries team state round to round, calls pluggable predictor, so later models replace only baseline.

**Tech Stack:** Python 3.11+, uv, requests, pandas, pyarrow, numpy, pyyaml, PuLP, pytest.

**Spec:** `docs/superpowers/specs/2026-11-09-f1-fantasy-optimizer.md` (Part 1 overrides Part 2)

## Global Constraints

- No phase starts before previous phase's acceptance passes.
- All game rules live in `config/rules_{season}.yaml`, never in code.
- `null` rule value raises `UnknownRuleError` when needed. Never fill one in to make test pass.
- Scoring gate fails on real data: stop, report rows. Do not change rule value without asking user.
- Every feature row has `known_at`. Nothing uses data after that round's `lock_utc`.
- Never read TracingInsights `priceChange`.
- Ask before adding dependency original spec does not list.
- No plaintext data in public repo: real data committed only inside `data/raw.tar.gz.enc`. Committed fixtures hand-written.
- `F1_DATA_KEY` never committed, logged or printed.
- `f1-fantasy` must be own git repo. Run `git rev-parse --show-toplevel` before first commit; must print project folder, not home directory.
- pytest for every module, small typed functions.

## Review Focus

1. Sources disagree on round numbers or race names: joins use slugs, unmatched race raises with its name. Test in Task 4.
2. Driver changes teams mid-season: one asset with continuous form and ownership. Test in Task 4.
3. Owned asset missing from round's list: budget uses last known price, optimizer still returns team. Test in Task 7.
4. Unplayed rounds appear in source files: never count as zero-point form. Test in Task 4 and Task 6.
5. Snapshot rerun meets error or empty response: existing good file stays. Test in Task 1.

---

## File Structure

```
f1-fantasy/
  pyproject.toml, .gitignore
  config/rules_2023.yaml ... rules_2026.yaml, model.yaml
  data/raw.tar.gz.enc   (committed, encrypted)
  data/raw/         (gitignored plaintext, unsealed from the archive)
  data/processed/   (gitignored Parquet)
  pipelines/build_data.py
  reports/
  src/ingest/vault.py               seal and unseal the encrypted archive
  src/ingest/fantasy_scrape.py      official feed snapshots
  src/ingest/community_pull.py      TracingInsights and mzafram copies
  src/ingest/jolpica_pull.py        results and schedules
  src/ingest/build_tables.py        raw files to Parquet tables
  src/ingest/ti_lines.py            TI rows to scoring inputs
  src/ingest/crosscheck.py          totals and finish-position checks
  src/sim/scoring.py                rules loader and scorer
  src/features/rolling.py           baseline mu
  src/features/guard.py             known_at enforcement
  src/optimize/ilp.py               team selection and state
  src/backtest/walkforward.py       season runner and report
  tests/
```

`src/` has no `__init__.py`; pytest uses `pythonpath = ["."]`, imports read `from src.sim.scoring import ...`.

# Phase 1: Ingest and scoring engine

### Task 1: Project scaffold and official feed snapshot

Snapshots first: 2026 feeds may vanish when 2027 game launches.

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `tests/conftest.py`, `src/ingest/fantasy_scrape.py`, `src/ingest/vault.py`
- Test: `tests/test_fantasy_scrape.py`, `tests/test_vault.py`

**Interfaces:**
- Produces: `snapshot_official(out_dir: Path, http: requests.Session) -> list[Path]`; `seal(raw_dir: Path, archive: Path) -> None`; `unseal(archive: Path, raw_dir: Path) -> None`; `MissingKeyError`; constant `MAX_ARCHIVE_BYTES = 95_000_000`; pytest fixture `raw_data() -> Path`; marker `data`.

- [ ] **Step 1: User sets up the key and environment (user does this; the key never enters the chat)**

Repo `AyrtonW321/f1-fantasy` and local folder already exist. Generate key with `openssl rand -base64 32`, save in password manager, set as user env var `F1_DATA_KEY`. Set `UV_PROJECT_ENVIRONMENT` to folder outside OneDrive.

- [ ] **Step 2: Write scaffold**

`pyproject.toml`: `requires-python = ">=3.11"`; dependencies requests, pandas, pyarrow, numpy, pyyaml; dev group pytest; `[tool.uv] package = false`; `[tool.pytest.ini_options]` with `pythonpath = ["."]` and marker `data`. `.gitignore`: `data/raw/`, `data/processed/`, `.venv/`, `__pycache__/`.

`tests/conftest.py`: fixture `raw_data` returns `Path("data/raw")`. If `data/raw/tracinginsights` absent: `pytest.fail` when env `REQUIRE_DATA=1`, else `pytest.skip("data/raw absent: scoring gate NOT run")`.

- [ ] **Step 3: Write failing tests** using fake session mapping URL to `(status, json)`

```python
def test_snapshot_writes_every_gameday(tmp_path): ...
    # raceday lists GamedayId 1 and 2, Season "2026"
    # expect official/2026/drivers/1.json, drivers/2.json, raceday.json,
    # constraints.json, web_config.json, playerstats/{id}.json for each PlayerId

def test_failed_fetch_keeps_existing_file(tmp_path):
    # existing drivers/1.json holds {"good": 1}; feed returns 403
    # file content unchanged and path absent from returned list

def test_empty_driver_feed_keeps_existing_file(tmp_path):
    # feed returns 200 with {"Data": {"Value": []}}; file content unchanged

# tests/test_vault.py, all set F1_DATA_KEY with monkeypatch
def test_seal_unseal_round_trip(tmp_path): ...
    # nested file content identical after unseal into a new directory

def test_archive_contains_no_plaintext(tmp_path):
    # marker string in a raw file is absent from archive bytes

def test_wrong_key_keeps_existing_raw(tmp_path):
    # unseal with another key raises; existing raw_dir unchanged

def test_missing_key_raises(tmp_path, monkeypatch):
    # F1_DATA_KEY unset: MissingKeyError from seal and unseal

def test_oversize_keeps_old_archive(tmp_path, monkeypatch):
    # MAX_ARCHIVE_BYTES patched to 10: seal raises; existing archive unchanged
```

- [ ] **Step 4: Run** `uv run pytest tests/test_fantasy_scrape.py tests/test_vault.py -v`. Expected: FAIL, modules not found.

- [ ] **Step 5: Implement `snapshot_official` in `src/ingest/fantasy_scrape.py`**

Base URL `https://fantasy.formula1.com/feeds/`. Paths: `schedule/raceday_en.json`, `limits/constraints.json`, `apps/web_config.json`, `drivers/{g}_en.json` for `g` in 1..max `GamedayId` in raceday `Data.Value`, `popup/playerstats_{id}.json` for each `PlayerId` in highest gameday fetched. Response valid when status 200, JSON parses and non-empty; driver feeds also need non-empty `Data.Value`. Write only valid responses. Add `__main__` writing to `data/raw`. Use generic User-Agent.

`src/ingest/vault.py`: build tar with stdlib `tarfile` in temp directory outside repo, then run `openssl enc -aes-256-cbc -pbkdf2 -iter 600000 -salt -pass env:F1_DATA_KEY` by subprocess with no shell. Replace archive with `os.replace` only after success and size check. `unseal` decrypts and extracts to temp directory using `tarfile` `filter="data"`, then swaps into `raw_dir`. Add `__main__` with `seal` and `unseal` commands on `data/raw` and `data/raw.tar.gz.enc`.

- [ ] **Step 6: Run tests.** Expected: PASS.

- [ ] **Step 7: Run the snapshot and seal it.** `uv run python -m src.ingest.fantasy_scrape`, then `uv run python -m src.ingest.vault seal`. Expected: `data/raw/official/2026/drivers/` holds one file per gameday, `git status` lists only `data/raw.tar.gz.enc` from `data/`. Rerun both after final 2026 race.

- [ ] **Step 8: Commit:** `feat: scaffold project and snapshot official feeds`.

### Task 2: Community data and Jolpica pulls

**Files:**
- Create: `src/ingest/community_pull.py`, `src/ingest/jolpica_pull.py`
- Test: `tests/test_community_pull.py`, `tests/test_jolpica_pull.py`

**Interfaces:**
- Produces: `pull_tracing_insights(tag: str, raw_dir: Path, http: requests.Session) -> Path`; `pull_mzafram(raw_dir: Path, http: requests.Session) -> list[Path]`; `pull_jolpica(season: int, raw_dir: Path, http: requests.Session, sleep: Callable[[float], None] = time.sleep) -> list[Path]`.

- [ ] **Step 1: Write failing tests**

```python
def test_ti_extracts_only_season_json(tmp_path):
    # in-memory zip: fantasy-x/data/transformed/2024/a-gp/race_all.json, .csv file,
    # fantasy-x/data/raw/2024/x.json
    # only tracinginsights/2024/a-gp/race_all.json written; SOURCE.json holds tag

def test_ti_drops_circuit_map(tmp_path):
    # race.json written without circuitMapUrl; other keys kept

def test_ti_rejects_path_traversal(tmp_path):
    # member fantasy-x/data/transformed/2024/../../../evil.json raises ValueError

def test_mzafram_ignores_missing_rounds(tmp_path):
    # round_06 returns 404, rounds 5 and 7 exist; both written

def test_jolpica_merges_race_split_across_pages(tmp_path):
    # total 3, limit 2: page 1 has round 1 with 2 Results, page 2 has round 1 with 1 Result
    # results.json is one race with 3 Results

def test_jolpica_retries_429(tmp_path):
    # 429 once then 200 succeeds; sleep called with 5
```

- [ ] **Step 2: Run tests.** Expected: FAIL, modules not found.

- [ ] **Step 3: Implement**

TI archive URL: `https://github.com/TracingInsights/fantasy/archive/refs/tags/{tag}.zip`. Keep only `race.json` and `*_all.json` under `data/transformed/{2023..2026}/`, written to `raw_dir/tracinginsights/{year}/{slug}/`. Remove base64 `circuitMapUrl` from `race.json` to keep archive small. mzafram URL: `https://raw.githubusercontent.com/mzafram2001/f1-fantasy/main/data/{year}/round_{nn:02d}.json`, `nn` in 1..30.

Jolpica base `https://api.jolpi.ca/ergast/f1/{season}/`, endpoints `races`, `results`, `qualifying`, `sprint`, `limit=100`, paging by `offset` until `MRData.total`, 0.5s sleep between pages, 3 retries on 429 with 5s sleep then raise. Output `raw_dir/jolpica/{season}/{endpoint}.json`, list of Race objects merged by `round`. Result list keys: `Results`, `QualifyingResults`, `SprintResults`.

- [ ] **Step 4: Run tests.** Expected: PASS.

- [ ] **Step 5: Pull real data.** Tag `data-sync-20261109-044408`, seasons 2023-2026. Add `__main__` to each module. Run `uv run python -m src.ingest.vault seal`. Expected: archive under 95 MB, included in this task's commit.

- [ ] **Step 6: Commit:** `feat: pull community fantasy data and Jolpica results`.

### Task 3: Rules files and scoring engine

**Files:**
- Create: `config/rules_2023.yaml`, `config/rules_2024.yaml`, `config/rules_2025.yaml`, `config/rules_2026.yaml`, `src/sim/scoring.py`
- Test: `tests/test_scoring.py`

**Interfaces:**
- Produces:

```python
class UnknownRuleError(Exception): ...
Session = Literal["qualifying", "sprint", "race"]

@dataclass(frozen=True)
class DriverLine:
    code: str
    session: Session
    position: int | None = None
    gained: int = 0
    overtakes: int = 0
    fastest_lap: bool = False
    dotd: bool = False
    not_classified: bool = False
    disqualified: bool = False

@dataclass(frozen=True)
class PitResult:
    ranks: tuple[int, ...] = ()
    seconds: float | None = None
    overall_fastest: bool = False
    world_record: bool = False

def load_rules(season: int, config_dir: Path = Path("config")) -> dict: ...
def score_driver(rules: dict, line: DriverLine) -> int: ...
def score_constructor(rules: dict, lines: Sequence[DriverLine],
                      teamwork: str | None = None, pit: PitResult = PitResult()) -> int: ...
```

- [ ] **Step 1: Write the rules files.** Shape, shown for 2026; other seasons' values in spec tables:

```yaml
season: 2026
driver:
  qualifying: {position: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1], not_classified: -5, disqualified: -5}
  sprint: {position: [8, 7, 6, 5, 4, 3, 2, 1], gained: 1, overtake: 1, fastest_lap: 5, not_classified: -10, disqualified: -10}
  race: {position: [25, 18, 15, 12, 10, 8, 6, 4, 2, 1], gained: 1, overtake: 1, fastest_lap: 10, driver_of_the_day: 10, not_classified: -20, disqualified: null}
constructor:
  disqualified: {qualifying: -10, sprint: -20, race: null}
  teamwork: {neither_q2: -1, one_q2: 1, both_q2: 3, one_q3: 5, both_q3: 10}
  pit_scoring: time_bands       # or: rank
  pit_bands: [[2.00, 20], [2.20, 10], [2.50, 5], [3.01, 2]]   # seconds < upper
  pit_ranks: {1: 10, 2: 5, 3: 3}
  overall_fastest_stop: 5
  world_record_stop: null
team: {budget: 100.0, drivers: 5, constructors: 2, boost_multiplier: 2}
transfers: {free: 2, carry_max: 1, max_free: 3, penalty: 10, net: true}
assumed: []                     # rules_2023.yaml: [transfers.carry_max]
```

- [ ] **Step 2: Write failing tests**

```python
def test_race_win_all_bonuses_2026():
    line = DriverLine("VER", "race", position=1, gained=3, overtakes=2, fastest_lap=True, dotd=True)
    assert score_driver(load_rules(2026), line) == 50

def test_positions_lost_are_negative():
    assert score_driver(load_rules(2026), DriverLine("X", "race", position=12, gained=-4)) == -4

def test_sprint_nc_changes_by_season():
    line = DriverLine("X", "sprint", not_classified=True)
    assert score_driver(load_rules(2025), line) == -20
    assert score_driver(load_rules(2026), line) == -10

def test_null_rule_raises():
    with pytest.raises(UnknownRuleError):
        score_driver(load_rules(2026), DriverLine("X", "race", disqualified=True))

def test_constructor_excludes_dotd():
    lines = [DriverLine("A", "race", position=1, dotd=True), DriverLine("B", "race", position=2)]
    assert score_constructor(load_rules(2026), lines) == 43

def test_constructor_uses_own_dsq_value():
    lines = [DriverLine("A", "sprint", disqualified=True), DriverLine("B", "sprint", not_classified=True)]
    assert score_constructor(load_rules(2026), lines) == -30

def test_constructor_qualifying_mexico_2026_shape():
    lines = [DriverLine("LAW", "qualifying", disqualified=True), DriverLine("LIN", "qualifying", position=8)]
    assert score_constructor(load_rules(2026), lines, teamwork="one_q3") == -2

def test_rank_pit_sums():
    lines = [DriverLine("A", "race"), DriverLine("B", "race")]
    assert score_constructor(load_rules(2024), lines, pit=PitResult(ranks=(1, 3))) == 13

@pytest.mark.parametrize("seconds,points", [(1.99, 20), (2.00, 10), (2.19, 10), (2.20, 5), (2.50, 2), (3.00, 2), (3.01, 0)])
def test_time_band_boundaries(seconds, points):
    lines = [DriverLine("A", "race"), DriverLine("B", "race")]
    assert score_constructor(load_rules(2026), lines, pit=PitResult(seconds=seconds)) == points

def test_overall_fastest_stop_null_raises_in_2024():
    with pytest.raises(UnknownRuleError):
        score_constructor(load_rules(2024), [DriverLine("A", "race")], pit=PitResult(overall_fastest=True))
```

- [ ] **Step 3: Run tests.** Expected: FAIL, module not found.

- [ ] **Step 4: Implement `src/sim/scoring.py`.** Constructor scores each line as driver would, minus DOTD, with `constructor.disqualified[session]` replacing driver DSQ value. Teamwork applies only when passed; pit applies only in race sessions.

- [ ] **Step 5: Run tests.** Expected: PASS.

- [ ] **Step 6: Commit:** `feat: add per-season rules and scoring engine`.

### Task 4: Normalized tables

**Files:**
- Create: `src/ingest/build_tables.py`, `pipelines/build_data.py`
- Test: `tests/test_build_tables.py`

**Interfaces:**
- Produces: `slugify(name: str) -> str`; `build_races(season: int, raw_dir: Path) -> pd.DataFrame`; `build_prices_points(season: int, races: pd.DataFrame, raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]`; `build_results(season: int, raw_dir: Path) -> pd.DataFrame`; `build_all(raw_dir: Path, out_dir: Path, seasons: Sequence[int]) -> None`.

Table schemas (`data/processed/{name}.parquet`):

| Table | Columns |
|---|---|
| `races` | season, round, slug, ti_slug_round, sprint, lock_utc, race_utc, completed |
| `prices` | season, round, asset_id, kind, price, known_at, source |
| `fantasy_points` | season, round, asset_id, kind, qualifying, sprint, race, total, known_at, source |
| `results` | season, round, session, driver_code, constructor_id, position, grid, status, known_at |

- [ ] **Step 1: Write failing tests** using fixture directories built under `tmp_path`

```python
def test_slugify_strips_accents():
    assert slugify("São Paulo Grand Prix") == "sao-paulo-grand-prix"

def test_ti_2023_round_offset_joins_on_slug(tmp_path):
    # TI race.json says roundNumber 7 for monaco-grand-prix; Jolpica says round 6
    # prices row has round == 6

def test_slug_aliases_join(tmp_path):
    # Jolpica "Brazilian Grand Prix", TI dir sao-paulo-grand-prix: joined

def test_unmatched_race_raises_with_name(tmp_path):
    # TI dir mystery-grand-prix: ValueError containing "mystery-grand-prix"

def test_lock_is_earliest_competitive_session(tmp_path):
    # Race with SprintQualifying Fri 20:30, Sprint Sat 16:00, Qualifying Sat 20:00,
    # FirstPractice Fri 16:30: lock_utc == Fri 20:30

def test_lock_handles_2023_shootout(tmp_path):
    # SprintShootout Sat, Qualifying Fri: lock_utc == Qualifying Fri

def test_unplayed_round_has_no_points_rows(tmp_path):
    # round without Jolpica results: completed False, no fantasy_points rows

def test_team_change_is_one_asset(tmp_path):
    # RED_LAW round 2, VRB_LAW round 3: both asset_id "LAW"

def test_duplicate_driver_keeps_row_with_points(tmp_path):
    # FER_BEA 0 points and HAA_BEA 12 in one round: one row, total 12

def test_official_overrides_2026_and_maps_constructors(tmp_path):
    # official gameday 1 row DriverTLA "RBR": asset_id "RED", source "official"

def test_price_known_at_equals_lock_and_points_after_race(tmp_path):
    # prices.known_at == lock_utc; fantasy_points.known_at == race_utc + 6h
```

- [ ] **Step 2: Run tests.** Expected: FAIL, module not found.

- [ ] **Step 3: Implement**

`SLUG_ALIASES = {"bahrain-grand-prix-in-malaysia": "bahrain-grand-prix", "brazilian-grand-prix": "sao-paulo-grand-prix"}` and `CONSTRUCTOR_ALIASES = {"RBR": "RED", "RBS": "VRB"}`. Canonical round from Jolpica. `ti_slug_round` stores TI's `roundNumber`, used only by mzafram cross-check.

`lock_utc` is minimum of Qualifying, Sprint, SprintQualifying, SprintShootout datetimes; missing time raises. `completed` means round present in Jolpica `results.json`.

TI source: `{session}_all.json` row `price`, `sessionResult.totalPoints.points` per session. 2026 prices and points come from Task 1 snapshot `official/2026/drivers/{round}.json` (`Value`, `QualifyingPoints`, `SprintPoints`, `RacePoints`, parsed as floats), matched on `DriverTLA`.

Jolpica `Driver.code` may be missing; fall back to `familyName[:3].upper()`.

`pipelines/build_data.py` calls `build_all(Path("data/raw"), Path("data/processed"), [2023, 2024, 2025, 2026])`.

- [ ] **Step 4: Run tests.** Expected: PASS.

- [ ] **Step 5: Build real tables.** `uv run python pipelines/build_data.py`. Expected: four Parquet files; `races` has 22, 24, 24, and 23 rows for 2023-2026. Unmatched names raise; add real aliases if spec's list incomplete.

- [ ] **Step 6: Commit:** `feat: normalize raw sources into Parquet tables`.

### Task 5: Scoring gate and cross-checks (Phase 1 acceptance)

**Files:**
- Create: `src/ingest/ti_lines.py`, `src/ingest/crosscheck.py`
- Test: `tests/test_ti_lines.py`, `tests/test_scoring_gate.py`

**Interfaces:**
- Consumes: Task 3 `DriverLine`, `PitResult`, `score_driver`, `score_constructor`; Task 4 tables.
- Produces: `parse_pit(row: dict) -> PitResult`; `parse_teamwork(text: str) -> str | None`; `driver_line(row: dict, session: Session) -> DriverLine`; `weekend_entrants(season: int, round_: int, raw_dir: Path) -> set[str]`; `gate_mismatches(season: int, raw_dir: Path, rules: dict) -> list[dict]`; `totals_mismatches(season: int, raw_dir: Path, points: pd.DataFrame, races: pd.DataFrame) -> list[dict]`; `finish_mismatches(season: int, raw_dir: Path) -> list[dict]`.

- [ ] **Step 1: Write failing tests**

```python
@pytest.mark.parametrize("text,ranks", [
    ("Fastest pit stop", (1,)),
    ("2nd fastest & 3rd fastest pit stop", (2, 3)),
    ("Fastest, 2nd fastest & 3rd fastest pit stop", (1, 2, 3)),
    ("", ()),
    ("Fastest pit stop time", ()),
])
def test_parse_pit_ranks(text, ranks): ...

def test_parse_pit_seconds():
    # "Fastest pit stop of 2.19s" gives seconds == 2.19; "Fastest pit stop of 2s" gives 2.0

def test_parse_teamwork_unknown_raises(): ...

def test_flags_come_from_breakdown_lines():
    # notClassifiedPoints.points -20 gives not_classified True; 0 gives False

def test_entrant_filter_drops_listed_non_participant(tmp_path):
    # VRB rows LAW, LIN, TSU; Jolpica weekend codes LAW, LIN: constructor scored from two

def test_entrants_include_driver_only_in_race_results(tmp_path):
    # driver absent from Jolpica qualifying but in race results still counts

@pytest.mark.data
@pytest.mark.parametrize("season", [2023, 2024, 2025, 2026])
def test_scoring_reproduces_every_completed_session(raw_data, season):
    bad = gate_mismatches(season, raw_data, load_rules(season))
    assert bad == [], f"{len(bad)} mismatches, first: {bad[:20]}"

@pytest.mark.data
@pytest.mark.parametrize("season", [2023, 2024, 2025, 2026])
def test_finish_positions_agree(raw_data, season):
    bad = finish_mismatches(season, raw_data)
    assert bad == [], f"{len(bad)} mismatches, first: {bad[:20]}"
```

- [ ] **Step 2: Run** `uv run pytest tests/test_ti_lines.py tests/test_scoring_gate.py -v`. Expected: FAIL, modules not found.

- [ ] **Step 3: Implement**

No TI field marks DSQ or NC, so `disqualified` and `not_classified` come from non-zero `disqualifiedPoints` and `notClassifiedPoints` lines. Position, gained, overtakes, fastest lap and DOTD come from `{session}Position`, `{session}PositionsGained`, `{session}Overtakes`, `{session}FastestLap`, `raceDriverOfTheDay`. Overall fastest from `raceOverallFastestPitStop`; world record from non-zero `worldRecordPitStopPoints`.

Pit text: contains `" of "` means seconds by regex `of ([\d.]+)s`. Empty or `"Fastest pit stop time"` means none. Otherwise ranks: 1 if starts with `Fastest`, 2 if `2nd`, 3 if `3rd`.

Teamwork text map: `Neither driver reached Q2`, `One driver reached Q2`, `Both drivers reached Q2`, `One driver reached Q3`, `Both drivers reached Q3` to YAML keys.

Constructor lines: driver rows with matching `constructorId` and `abbreviation` in `weekend_entrants`.

Gate target: 2023-2025 `sessionResult.totalPoints.points`; 2026 official session points. Mismatch dict: season, slug, session, asset, expected, actual. Completed rounds only.

`totals_mismatches` compares `fantasy_points.total` with mzafram `Round_Fantasy_Points` (`Driver_Code`, `Team_Code`), locating files by `ti_slug_round`, writes `data/processed/totals_mismatches.csv`. Report, not gate. If entire season mismatches, round numbering assumption wrong; stop and fix join.

- [ ] **Step 4: Run unit tests.** Expected: PASS.

- [ ] **Step 5: Run Phase 1 acceptance.** `REQUIRE_DATA=1 uv run pytest -m data -v`. Expected: 8 passed, 0 skipped. On any mismatch, stop and show user the rows.

- [ ] **Step 6: Run cross-check** and report mismatch counts per season to user.

- [ ] **Step 7: Commit:** `feat: add scoring gate and source cross-checks`.

# Phase 2: Baseline and optimizer

### Task 6: Baseline predictor and leakage guard

**Files:**
- Create: `config/model.yaml`, `src/features/rolling.py`, `src/features/guard.py`
- Test: `tests/test_rolling.py`, `tests/test_guard.py`

**Interfaces:**
- Produces: `baseline_mu(prices: pd.DataFrame, points: pd.DataFrame, races: pd.DataFrame, season: int, round_: int, window: int = 5) -> pd.DataFrame` with columns season, round, asset_id, kind, price, mu, known_at; `assert_known_before_lock(frame: pd.DataFrame, races: pd.DataFrame) -> None`, raising `LeakageError`.

`config/model.yaml`:

```yaml
baseline: {rolling_window: 5}
backtest: {seasons: [2023, 2024, 2025, 2026]}
```

- [ ] **Step 1: Write failing tests**

```python
def test_round_one_mu_equals_price(): ...
    # prices only; mu == price for every asset

def test_partial_history_blends_with_prior():
    # round 3, asset price 20, actual 10 and 20; league median points/price 0.5
    # prior 10.0; mu == (30 + 3 * 10) / 5 == 12.0

def test_only_latest_window_counts():
    # round 7 with six completed rounds: oldest excluded; k == 5, no prior used

def test_prior_uses_current_round_price():
    # price rises round 2 to round 3: prior uses round 3 price

def test_future_rows_ignored():
    # 1000-point row at round 9 does not change round 3 mu

def test_other_season_ignored():
    # previous-season points do not change mu or league median

def test_unplayed_round_is_not_zero_form():
    # no points row for round 2 of an asset: k counts only actual rows

def test_guard_passes_at_lock(): ...
def test_guard_raises_after_lock():
    # known_at one second past lock_utc raises LeakageError naming the round
```

- [ ] **Step 2: Run tests.** Expected: FAIL, modules not found.

- [ ] **Step 3: Implement.** Filter `points` to season and `known_at <= lock_utc` of target round. Formula in spec. `known_at` on output is round's `lock_utc`. Call `assert_known_before_lock` on output.

- [ ] **Step 4: Run tests.** Expected: PASS.

- [ ] **Step 5: Commit:** `feat: add baseline predictor and leakage guard`.

### Task 7: ILP optimizer

**Files:**
- Create: `src/optimize/ilp.py`
- Modify: `pyproject.toml` (add pulp)
- Test: `tests/test_ilp.py`

**Interfaces:**
- Consumes: Task 3 rules dict.
- Produces:

```python
@dataclass(frozen=True)
class Asset:
    id: str
    kind: Literal["driver", "constructor"]
    price: float
    mu: float

@dataclass(frozen=True)
class TeamState:
    owned: Mapping[str, float]   # asset id to last known price
    bank: float
    free_transfers: int

@dataclass(frozen=True)
class Decision:
    drivers: tuple[str, ...]
    constructors: tuple[str, ...]
    boost: str
    transfers_in: tuple[str, ...]
    penalty_transfers: int
    cost: float
    budget: float
    expected_points: float

class InfeasibleTeam(Exception): ...
def optimize(assets: Sequence[Asset], state: TeamState | None, rules: dict) -> Decision: ...
def next_state(state: TeamState | None, decision: Decision, rules: dict) -> TeamState: ...
```

- [ ] **Step 1: Write failing tests** with synthetic asset lists from `make_field()` helper

```python
def test_counts_and_boost(): ...          # 5 drivers, 2 constructors, boost on highest-mu picked driver
def test_budget_respected(): ...          # cheapest top-mu team over budget is not chosen
def test_exact_budget_allowed(): ...      # team costing exactly 100.0 is legal with float prices like 12.1
def test_boost_is_driver_only(): ...      # top-mu asset is a constructor; boost still on a driver
def test_budget_grows_with_prices(): ...  # owned prices rose: previously unaffordable team allowed
def test_first_round_has_no_penalty(): ...# state None: penalty_transfers == 0
def test_within_free_no_penalty(): ...

def test_penalty_size_changes_choice():
    # three swaps each gaining 6 expected points, free_transfers 2
    # rules_2023 (penalty 4): len(transfers_in) == 3, penalty_transfers == 1
    # rules_2026 (penalty 10): len(transfers_in) == 2, penalty_transfers == 0

def test_missing_owned_asset_keeps_value():
    # owned asset absent from list: budget uses last known price, team returned

def test_carry_rules():
    # next_state from state None gives free_transfers 2
    # 2 free, 1 used: next 3; 2 free, 0 used: next 3
    # 3 free, 0 used: next 3; 3 free, 3 used: next 2

def test_next_state_bank_and_prices(): ...# bank == budget - cost; owned maps picks to current prices

def test_solves_under_two_seconds():      # 33 assets
    ...
```

- [ ] **Step 2: Run tests.** Expected: FAIL, module not found.

- [ ] **Step 3: Add pulp and implement.** Formulation from spec: binaries `x_i`, `y_j`, `b_i`, `s_k`, continuous `e >= T - F`, `e >= 0`. Compare costs in integer tenths (`round(price * 10)`) to avoid float budget errors. `budget = bank + sum(current or last known price)`. Sort assets by id and use `PULP_CBC_CMD(msg=False)` for repeatable results. Carry: `F' = min(max_free, free + min(carry_max, max(F - T, 0)))`. Raise `InfeasibleTeam` when no team fits.

- [ ] **Step 4: Run tests.** Expected: PASS.

- [ ] **Step 5: Commit:** `feat: add ILP team optimizer`.

### Task 8: Walk-forward baseline run (Phase 2 acceptance)

**Files:**
- Create: `src/backtest/walkforward.py`
- Test: `tests/test_walkforward.py`

**Interfaces:**
- Consumes: Task 6 `baseline_mu`; Task 7 `optimize`, `next_state`, `Asset`.
- Produces: `Predictor = Callable[[int, int], pd.DataFrame]`; `RoundResult(round: int, decision: Decision, actual_points: float, solve_seconds: float)`; `SeasonResult(season: int, rounds: list[RoundResult], total: float, total_from_round_5: float, assumptions: list[str])`; `run_season(season: int, tables: dict[str, pd.DataFrame], rules: dict, predict: Predictor) -> SeasonResult`; `write_report(result: SeasonResult, path: Path) -> None`.

- [ ] **Step 1: Write failing tests** on synthetic 6-round season

```python
def test_actual_points_counts_boost_and_penalty():
    # boost driver's actual counted twice; penalty subtracted

def test_state_carries_between_rounds():
    # budget in round 2 equals bank plus round 2 prices of round 1 team

def test_predictor_gets_no_future_points():
    # spy predictor records calls; only (season, r) in round order

def test_incomplete_rounds_skipped(): ...

def test_asset_without_points_row_scores_zero(): ...

def test_totals_overall_and_from_round_five():
    # total == sum of all; total_from_round_5 == sum for round >= 5

def test_report_prints_assumptions(tmp_path):
    # assumptions ["transfers.carry_max"] appear in the report
```

- [ ] **Step 2: Run tests.** Expected: FAIL, module not found.

- [ ] **Step 3: Implement.** Loop completed rounds in order. Skip chips. Add `__main__`: `--season` builds baseline predictor with `rolling_window` from `model.yaml`, writes `reports/baseline_{season}.md` with per-round team, boost, transfers, points, both totals.

- [ ] **Step 4: Run tests.** Expected: PASS.

- [ ] **Step 5: Run Phase 2 acceptance.** For each season 2023-2026: `uv run python -m src.backtest.walkforward --season 2024`. Expected: report for each; every round valid; max solve time under 2s. Then `uv run pytest -v`. Expected: all pass.

- [ ] **Step 6: Commit:** `feat: add walk-forward baseline backtest`.

# Phases 3-7: outline

Each phase gets own task-level plan after previous acceptance passes. Designing now would fix schemas before first reader exists.

| Phase | Build | Carried-over decisions | Acceptance |
|---|---|---|---|
| 3 Pace + Kalman | FastF1 ingest (`laps`, `sessions`) for 2025-2026, cache outside OneDrive, `tracks.csv`, `features/pace.py`, `models/kalman.py` | Tune only on 2023-2025. Prior-year order as weak prior in first 2-3 rounds. | FP2 long-run per driver per weekend in 2025-2026. Kalman correlates with race order better than last-race order. |
| 4 Events + simulator | `models/plackett_luce.py`, `lgbm_rank.py`, `dnf.py`, `poisson.py`, `sim/montecarlo.py` reusing `scoring.py` | Season rules by year. Null rules must be resolved or simulated around, with user asked. | Models fit and sample; calibrated. Task plan: `plans/2026-11-10-phase-4-event-models-simulator.md` (revised 2026-11-10). |
| 5 Backtest | `backtest/metrics.py`, Kalman `Q` and `lambda` tuning, reuse `run_season` | Hold out 2026. Log every 2026 evaluation in `reports/holdout_2026_log.md`. Refit on all four for 2027. Test prior-season form. Compare from round 5 and overall. | Every metric compared with baseline. Losing models dropped. Revised 2026-11-12: `plans/2026-11-12-phase-5-backtest.md` (2027 cold start; Kalman Q and lambda tuning dropped). |
| 6 Horizon, chips, observed price changes, risk | `optimize/horizon.py`, `chips.py`, risk mode | Confirm chip rules per season first. Use captured round prices and realized changes in budget/horizon comparisons; no future-price prediction. | Extensions evaluated against Phase 5; observed prices and budget stay season-correct. |
| 7 Automation | `pipelines/weekly_update.py`, `.github/workflows/cron.yml`, `reports/round_XX.md` | `F1_DATA_KEY` as Actions secret; workflow unseals before running, reseals after new snapshots. Real deadlines from feed lock flags. Time Monte Carlo against Actions minutes. | Cron writes report unattended. |