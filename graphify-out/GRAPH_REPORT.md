# Graph Report - f1-fantasy  (2026-11-25)

## Corpus Check
- 86 files · ~43,613 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 937 nodes · 2757 edges · 31 communities (29 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `457fb624`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- optimize
- crosscheck.py
- test_build_tables.py
- test_scoring_gate.py
- walkforward.py
- vault.py
- test_jolpica_pull.py
- pandas
- test_community_pull.py
- snapshot_official
- fastf1_pull.py
- walkforward_strength
- weekly_update.py
- fp2_longrun_pace
- sample_bonus
- plackett_luce.py
- test_rolling.py
- poisson.py
- app.py
- evaluate_seasons.py
- walkforward.py
- dnf_probability
- InfeasibleTeam
- evaluate_overtakes.py
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 93 edges
2. `robust_mu()` - 40 edges
3. `optimize()` - 35 edges
4. `run_season()` - 32 edges
5. `build_races()` - 32 edges
6. `DriverLine` - 31 edges
7. `TeamState` - 28 edges
8. `_team_row_body()` - 27 edges
9. `Asset` - 27 edges
10. `score_constructor()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `test_load_team_reads_state_and_rejects_unknown_assets()` --calls--> `load_team()`  [INFERRED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `_guard()` --calls--> `body()`  [INFERRED]
  app.py → tests/test_community_pull.py
- `test_reads_config_rules_and_null_raises()` --indirect_call--> `UnknownRuleError`  [INFERRED]
  tests/test_chips.py → src/sim/scoring.py
- `test_season_values_match_spec()` --calls--> `load_rules()`  [EXTRACTED]
  tests/test_scoring.py → src/sim/scoring.py
- `rules()` --calls--> `load_rules()`  [EXTRACTED]
  tests/test_walkforward.py → src/sim/scoring.py

## Import Cycles
- None detected.

## Communities (31 total, 2 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.08
Nodes (68): dataclasses, load_team(), main(), Path, pulp, _actual_points(), DataFrame, estimate_chip() (+60 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.10
Nodes (32): _applied(), _area(), _best_tab(), _capture_chips(), _chip_advice(), _chip_select(), _choose_and_apply(), _data_tab() (+24 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.09
Nodes (68): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, DataFrame (+60 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.07
Nodes (74): driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, _blank_zero(), _constructor_lines(), finish_mismatches(), gate_mismatches(), _jolpica_finishes() (+66 more)

### Community 4 - "walkforward.py"
Cohesion: 0.14
Nodes (21): _best_body(), _cached_top(), _cards(), _confirm_banner(), _inputs_stamp(), _last_race(), _mu(), _picks() (+13 more)

### Community 5 - "vault.py"
Cohesion: 0.16
Nodes (25): RuntimeError, _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), Exception, Path (+17 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.11
Nodes (41): _edit_form(), rounds: round numbers the saved lineup can be recorded as played in (next round, apply_transfers(), asset_mu(), assets(), confirm_round(), _history(), history_path() (+33 more)

### Community 7 - "pandas"
Cohesion: 0.13
Nodes (20): asset_card(), best_skeleton(), _boxes(), chip_grid(), header_row(), _number(), Small HTML fragments for the dark team calculator view., Square chip tiles, 3 per row: green = this weekend, struck grey = played, white (+12 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.05
Nodes (80): argparse, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for, mae(), main() (+72 more)

### Community 9 - "snapshot_official"
Cohesion: 0.12
Nodes (27): pytest, dnf_probability(), DataFrame, Series, Per-driver race DNF probability, shrunk toward the field rate of the history it, history: race result rows already cut to before the target lock. p = (dnfs + shr, Path, raw_data() (+19 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (41): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+33 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.08
Nodes (40): main(), Refresh pre-event safety-car rates from previously observed FastF1 race status., _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), add_prior_safety_car_rates() (+32 more)

### Community 12 - "weekly_update.py"
Cohesion: 0.16
Nodes (22): _fetch(), _get_page(), pull_jolpica(), Path, Session, Parsed JSON of one page. A 429 waits 5s and retries, up to RETRIES times., All races of one endpoint; pages merged by round, sorted by round., empty_routes() (+14 more)

### Community 13 - "fp2_longrun_pace"
Cohesion: 0.22
Nodes (18): main(), _fit_driver(), fp2_longrun_pace(), _known_at(), DataFrame, Series, Timestamp, Pre-lock FP2 long-run pace estimates with explicit coverage and fit diagnostics. (+10 more)

### Community 14 - "sample_bonus"
Cohesion: 0.26
Nodes (13): BonusOutcome, _eligible_history(), DataFrame, Timestamp, Empirical bonus-event samplers. History is limited to pre-lock completed rounds., Sample supported labels from prior-round history; unknown feeds return explicit, sample_bonus(), _sample_rate() (+5 more)

### Community 15 - "plackett_luce.py"
Cohesion: 0.33
Nodes (6): fit(), ndarray, Regularized Plackett-Luce over finishing orders. Log-strength of an entrant = fe, n full orders (entrant indices, winner first). Gumbel-max: argsort of log-streng, Penalized maximum likelihood by Newton steps (the log likelihood is concave in b, sample()

### Community 20 - "test_rolling.py"
Cohesion: 0.05
Nodes (88): collections_abc, bonus_points(), driver_line(), parse_pit(), parse_teamwork(), _points(), _position(), Path (+80 more)

### Community 21 - "poisson.py"
Cohesion: 0.25
Nodes (8): deviance(), fit(), ndarray, Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shr, Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events, Mean Poisson deviance; lower is better., Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not, shrunk_rate()

### Community 22 - "app.py"
Cohesion: 0.32
Nodes (3): races(), test_due_gate(), test_stale_team_warning()

### Community 23 - "evaluate_seasons.py"
Cohesion: 0.18
Nodes (12): shutil, tables(), test_apply_transfers_writes_backup_team_and_history(), test_history_points_applies_boost_chip_and_penalty(), test_round_chip(), test_round_source_confirm_and_review(), test_snapshot_and_record_round(), test_swaps_log_diffs_rows() (+4 more)

### Community 24 - "walkforward.py"
Cohesion: 0.40
Nodes (5): driver_teams(), DataFrame, Team colours and readable text colour for the app's asset cards., Driver code to constructor asset id, from each driver's latest result up to `sea, team_colors()

### Community 25 - "dnf_probability"
Cohesion: 0.06
Nodes (66): io, json, os, _capture(), default_steps(), due(), execute(), _http() (+58 more)

### Community 26 - "InfeasibleTeam"
Cohesion: 0.40
Nodes (18): baseline_mu(), lock(), mu_of(), points(), prices(), races(), rows: (round, asset_id, price)., rows: (round, asset_id, total) or (round, asset_id, total, known_at). (+10 more)

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `test_scoring_gate.py`, `walkforward.py`, `test_jolpica_pull.py`, `test_community_pull.py`, `snapshot_official`, `test_rolling.py`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `test_community_pull.py` to `optimize`, `InfeasibleTeam`, `test_rolling.py`, `test_jolpica_pull.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `test_rolling.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `optimize` be split into smaller, more focused modules?**
  _Cohesion score 0.0781981981981982 - nodes in this community are weakly interconnected._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10227272727272728 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09170471841704718 - nodes in this community are weakly interconnected._