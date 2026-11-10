# Graph Report - f1-fantasy  (2026-11-10)

## Corpus Check
- 36 files · ~24,782 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .enc 1, .lock 1)

## Summary
- 639 nodes · 1558 edges · 44 communities (40 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `af82835b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- load_rules
- crosscheck.py
- test_build_tables.py
- test_scoring_gate.py
- test_walkforward.py
- vault.py
- test_jolpica_pull.py
- baseline_mu
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
- model.yaml
- driver
- driver
- driver
- driver
- disqualified
- disqualified
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 53 edges
2. `build_races()` - 31 edges
3. `optimize()` - 24 edges
4. `write_jolpica()` - 22 edges
5. `DriverLine` - 22 edges
6. `_round_gate()` - 22 edges
7. `schedule()` - 21 edges
8. `gate_mismatches()` - 20 edges
9. `run_season()` - 19 edges
10. `build_prices_points()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_slugify_strips_accents()` --calls--> `slugify()`  [EXTRACTED]
  tests/test_build_tables.py → src/ingest/build_tables.py
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

## Communities (44 total, 4 thin omitted)

### Community 0 - "load_rules"
Cohesion: 0.10
Nodes (48): Asset, Decision, InfeasibleTeam, next_state(), optimize(), TeamState, _tenths(), _driver_points() (+40 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.07
Nodes (43): driver_code(), _blank_zero(), _constructor_lines(), finish_mismatches(), _jolpica_finishes(), _load(), _official_inconsistent(), _official_index() (+35 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.12
Nodes (48): main(), _asset(), build_all(), build_prices_points(), build_races(), build_results(), _dedupe(), _load() (+40 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.13
Nodes (35): gate_mismatches(), totals_mismatches(), official_row(), _points(), _races(), test_2023_sprint_withdrawal_excluded_from_constructor(), test_2025_phantom_row_under_other_team_excluded_from_constructor(), test_2026_asset_missing_from_official_feed_has_none_expected() (+27 more)

### Community 4 - "test_walkforward.py"
Cohesion: 0.13
Nodes (26): _actual_points(), main(), _max_solve(), RoundResult, run_season(), SeasonResult, write_report(), _frame() (+18 more)

### Community 5 - "vault.py"
Cohesion: 0.13
Nodes (16): _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), seal(), _swap_in(), unseal() (+8 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.16
Nodes (14): _fetch(), _get_page(), pull_jolpica(), empty_routes(), FakeResponse, FakeSession, page(), race() (+6 more)

### Community 7 - "baseline_mu"
Cohesion: 0.19
Nodes (20): assert_known_before_lock(), LeakageError, baseline_mu(), frame(), test_guard_passes_at_lock(), test_guard_raises_after_lock(), lock(), mu_of() (+12 more)

### Community 8 - "json"
Cohesion: 0.08
Nodes (26): _check_member(), pull_mzafram(), pull_tracing_insights(), _get(), _rows(), snapshot_official(), _write(), body() (+18 more)

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

### Community 34 - "model.yaml"
Cohesion: 0.40
Nodes (4): backtest, seasons, baseline, rolling_window

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

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 248 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `load_rules` to `test_scoring_gate.py`, `test_walkforward.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `load_rules` be split into smaller, more focused modules?**
  _Cohesion score 0.09995477159656264 - nodes in this community are weakly interconnected._
- **Why does `build_races()` connect `test_build_tables.py` to `crosscheck.py`, `test_scoring_gate.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07377049180327869 - nodes in this community are weakly interconnected._
- **Why does `_write()` connect `json` to `vault.py`, `test_jolpica_pull.py`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12404371584699453 - nodes in this community are weakly interconnected._