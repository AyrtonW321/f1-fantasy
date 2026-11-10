# Graph Report - f1-fantasy  (2026-11-10)

## Corpus Check
- 43 files · ~33,321 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .enc 1, .lock 1)

## Summary
- 805 nodes · 2085 edges · 46 communities (42 shown, 4 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5c365f1d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- load_rules
- crosscheck.py
- test_build_tables.py
- test_scoring_gate.py
- test_walkforward.py
- vault.py
- test_kalman.py
- pandas
- json
- constructor
- constructor
- constructor
- constructor
- rules_2023.yaml
- race
- rules_2024.yaml
- race
- rules_2025.yaml
- race
- rules_2026.yaml
- race
- sprint
- sprint
- sprint
- sprint
- teamwork
- transfers
- teamwork
- transfers
- teamwork
- transfers
- teamwork
- transfers
- kalman
- driver
- driver
- driver
- driver
- disqualified
- disqualified
- f1-fantasy
- test_tracks.py
- json

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 53 edges
2. `build_races()` - 31 edges
3. `optimize()` - 24 edges
4. `DriverLine` - 22 edges
5. `_round_gate()` - 22 edges
6. `write_jolpica()` - 22 edges
7. `StrengthFilter` - 21 edges
8. `run_practice()` - 21 edges
9. `schedule()` - 21 edges
10. `build_sessions()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `test_pace_defaults_come_from_config()` --calls--> `_params()`  [EXTRACTED]
  tests/test_pace.py → src/features/pace.py
- `test_infeasible_raises()` --uses--> `InfeasibleTeam`  [INFERRED]
  tests/test_ilp.py → src/optimize/ilp.py
- `test_time_band_boundaries()` --uses--> `DriverLine`  [INFERRED]
  tests/test_scoring.py → src/sim/scoring.py
- `test_driver_line_real_shaped_race_row()` --calls--> `DriverLine`  [EXTRACTED]
  tests/test_ti_lines.py → src/sim/scoring.py
- `test_qualifying_line_has_no_race_fields()` --calls--> `DriverLine`  [EXTRACTED]
  tests/test_ti_lines.py → src/sim/scoring.py

## Import Cycles
- None detected.

## Communities (46 total, 4 thin omitted)

### Community 0 - "load_rules"
Cohesion: 0.10
Nodes (48): Asset, Decision, InfeasibleTeam, next_state(), optimize(), TeamState, _tenths(), _driver_points() (+40 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.07
Nodes (42): driver_code(), _blank_zero(), _constructor_lines(), _jolpica_finishes(), _load(), _official_inconsistent(), _official_index(), _official_parts() (+34 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.09
Nodes (64): main(), _asset(), build_all(), build_prices_points(), build_races(), build_results(), build_sessions(), _dedupe() (+56 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.13
Nodes (36): finish_mismatches(), gate_mismatches(), totals_mismatches(), official_row(), _points(), _races(), test_2023_sprint_withdrawal_excluded_from_constructor(), test_2025_phantom_row_under_other_team_excluded_from_constructor() (+28 more)

### Community 4 - "test_walkforward.py"
Cohesion: 0.14
Nodes (26): _actual_points(), main(), _max_solve(), RoundResult, run_season(), SeasonResult, write_report(), _frame() (+18 more)

### Community 5 - "vault.py"
Cohesion: 0.13
Nodes (16): _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), seal(), _swap_in(), unseal() (+8 more)

### Community 6 - "test_kalman.py"
Cohesion: 0.12
Nodes (26): _apply_grouped(), run_season(), StrengthFilter, constructor_level(), entity_var(), lock_of(), make_params(), make_races() (+18 more)

### Community 7 - "pandas"
Cohesion: 0.09
Nodes (56): assert_known_before_lock(), LeakageError, _compound_deltas(), _fit_stints(), _gap_pct(), _green_clean_mask(), _long_run(), _params() (+48 more)

### Community 8 - "json"
Cohesion: 0.14
Nodes (14): _fetch(), _get_page(), pull_jolpica(), empty_routes(), FakeResponse, FakeSession, page(), race() (+6 more)

### Community 10 - "constructor"
Cohesion: 0.20
Nodes (10): constructor, disqualified, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, qualifying (+2 more)

### Community 11 - "constructor"
Cohesion: 0.20
Nodes (10): constructor, disqualified, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, qualifying (+2 more)

### Community 12 - "constructor"
Cohesion: 0.22
Nodes (9): constructor, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, 1, 2 (+1 more)

### Community 13 - "constructor"
Cohesion: 0.22
Nodes (9): constructor, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, 1, 2 (+1 more)

### Community 14 - "rules_2023.yaml"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 15 - "race"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 16 - "rules_2024.yaml"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 17 - "race"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 18 - "rules_2025.yaml"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 19 - "race"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 20 - "rules_2026.yaml"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 21 - "race"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 22 - "sprint"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 23 - "sprint"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 24 - "sprint"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 25 - "sprint"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 26 - "teamwork"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 27 - "transfers"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 28 - "teamwork"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 29 - "transfers"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 30 - "teamwork"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 31 - "transfers"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 32 - "teamwork"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 33 - "transfers"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 34 - "kalman"
Cohesion: 0.07
Nodes (26): backtest, seasons, baseline, rolling_window, kalman, p0_car, p0_driver, prior_2025_weight (+18 more)

### Community 35 - "driver"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 36 - "driver"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 37 - "driver"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 38 - "driver"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 39 - "disqualified"
Cohesion: 0.50
Nodes (4): disqualified, qualifying, race, sprint

### Community 40 - "disqualified"
Cohesion: 0.50
Nodes (4): disqualified, qualifying, race, sprint

### Community 43 - "test_tracks.py"
Cohesion: 0.17
Nodes (20): blank_ratings(), _clean(), load_tracks(), main(), _parse_overtaking(), write_template(), _csv(), _races() (+12 more)

### Community 44 - "json"
Cohesion: 0.09
Nodes (26): _check_member(), pull_mzafram(), pull_tracing_insights(), _get(), _rows(), snapshot_official(), _write(), body() (+18 more)

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 289 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `load_rules` to `test_scoring_gate.py`, `test_walkforward.py`, `pandas`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `load_rules` be split into smaller, more focused modules?**
  _Cohesion score 0.0965034965034965 - nodes in this community are weakly interconnected._
- **Why does `build_races()` connect `test_build_tables.py` to `crosscheck.py`, `test_scoring_gate.py`, `pandas`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07481005260081823 - nodes in this community are weakly interconnected._
- **Why does `run_season()` connect `test_kalman.py` to `pandas`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08702531645569621 - nodes in this community are weakly interconnected._