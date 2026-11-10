# Graph Report - f1-fantasy  (2026-11-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 634 nodes · 1546 edges · 43 communities (41 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `be12716b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 42

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 53 edges
2. `build_races()` - 30 edges
3. `optimize()` - 24 edges
4. `DriverLine` - 22 edges
5. `_round_gate()` - 22 edges
6. `write_jolpica()` - 21 edges
7. `schedule()` - 20 edges
8. `gate_mismatches()` - 20 edges
9. `run_season()` - 19 edges
10. `score_constructor()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `predictor()` --calls--> `baseline_mu()`  [EXTRACTED]
  tests/test_walkforward.py → src/features/rolling.py
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

## Communities (43 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (48): Asset, Decision, InfeasibleTeam, next_state(), optimize(), TeamState, _tenths(), _driver_points() (+40 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (44): driver_code(), _blank_zero(), _constructor_lines(), finish_mismatches(), _jolpica_finishes(), _load(), _official_inconsistent(), _official_index() (+36 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (47): main(), _asset(), build_all(), build_prices_points(), build_races(), build_results(), _dedupe(), _load() (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (34): gate_mismatches(), official_row(), _points(), _races(), test_2023_sprint_withdrawal_excluded_from_constructor(), test_2025_phantom_row_under_other_team_excluded_from_constructor(), test_2026_asset_missing_from_official_feed_has_none_expected(), test_2026_driver_not_in_jolpica_excluded_from_constructor() (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (27): _actual_points(), main(), _max_solve(), RoundResult, run_season(), SeasonResult, write_report(), _frame() (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (16): _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), seal(), _swap_in(), unseal() (+8 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (14): _fetch(), _get_page(), pull_jolpica(), empty_routes(), FakeResponse, FakeSession, page(), race() (+6 more)

### Community 7 - "Community 7"
Cohesion: 0.20
Nodes (19): assert_known_before_lock(), LeakageError, baseline_mu(), frame(), test_guard_passes_at_lock(), test_guard_raises_after_lock(), lock(), mu_of() (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (12): _check_member(), pull_mzafram(), pull_tracing_insights(), _write(), body(), FakeResponse, FakeSession, make_zip() (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.16
Nodes (12): _get(), _rows(), snapshot_official(), drivers(), FakeResponse, FakeSession, raceday(), seed() (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.20
Nodes (10): constructor, disqualified, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, qualifying (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.20
Nodes (10): constructor, disqualified, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, qualifying (+2 more)

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (9): constructor, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, 1, 2 (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (9): constructor, overall_fastest_stop, pit_bands, pit_ranks, pit_scoring, world_record_stop, 1, 2 (+1 more)

### Community 14 - "Community 14"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 15 - "Community 15"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 17 - "Community 17"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 18 - "Community 18"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 19 - "Community 19"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 20 - "Community 20"
Cohesion: 0.25
Nodes (7): assumed, season, team, boost_multiplier, budget, constructors, drivers

### Community 21 - "Community 21"
Cohesion: 0.25
Nodes (8): race, disqualified, driver_of_the_day, fastest_lap, gained, not_classified, overtake, position

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 23 - "Community 23"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 24 - "Community 24"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 25 - "Community 25"
Cohesion: 0.29
Nodes (7): sprint, disqualified, fastest_lap, gained, not_classified, overtake, position

### Community 26 - "Community 26"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 27 - "Community 27"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 28 - "Community 28"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 30 - "Community 30"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 31 - "Community 31"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (6): teamwork, both_q2, both_q3, neither_q2, one_q2, one_q3

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (6): transfers, carry_max, free, max_free, net, penalty

### Community 34 - "Community 34"
Cohesion: 0.40
Nodes (4): backtest, seasons, baseline, rolling_window

### Community 35 - "Community 35"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 36 - "Community 36"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 37 - "Community 37"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 38 - "Community 38"
Cohesion: 0.40
Nodes (5): driver, qualifying, disqualified, not_classified, position

### Community 39 - "Community 39"
Cohesion: 0.50
Nodes (4): disqualified, qualifying, race, sprint

### Community 40 - "Community 40"
Cohesion: 0.50
Nodes (4): disqualified, qualifying, race, sprint

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges. (Counts symbols only; 246 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `Community 0` to `Community 3`, `Community 4`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0959079283887468 - nodes in this community are weakly interconnected._
- **Why does `build_races()` connect `Community 2` to `Community 1`, `Community 3`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06994047619047619 - nodes in this community are weakly interconnected._
- **Why does `_write()` connect `Community 8` to `Community 9`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.12598870056497175 - nodes in this community are weakly interconnected._