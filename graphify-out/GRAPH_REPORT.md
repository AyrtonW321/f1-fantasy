# Graph Report - f1-fantasy  (2026-11-14)

## Corpus Check
- 79 files · ~37,783 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 804 nodes · 2433 edges · 29 communities (28 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0b7708cb`
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
- load_rules
- fastf1_pull.py
- walkforward_strength
- load_track_metadata
- fp2_longrun_pace
- sample_bonus
- plackett_luce.py
- test_rolling.py
- poisson.py
- app.py
- logic.py
- ilp.py
- TeamState
- main
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 86 edges
2. `robust_mu()` - 40 edges
3. `optimize()` - 34 edges
4. `run_season()` - 32 edges
5. `build_races()` - 32 edges
6. `DriverLine` - 31 edges
7. `Asset` - 26 edges
8. `score_constructor()` - 26 edges
9. `sim_mu()` - 25 edges
10. `write_jolpica()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `test_load_team_reads_state_and_rejects_unknown_assets()` --calls--> `load_team()`  [INFERRED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `test_reads_config_rules_and_null_raises()` --indirect_call--> `UnknownRuleError`  [INFERRED]
  tests/test_chips.py → src/sim/scoring.py
- `test_season_values_match_spec()` --calls--> `load_rules()`  [EXTRACTED]
  tests/test_scoring.py → src/sim/scoring.py
- `rules()` --calls--> `load_rules()`  [EXTRACTED]
  tests/test_walkforward.py → src/sim/scoring.py
- `_capture_chips()` --calls--> `main()`  [EXTRACTED]
  app.py → pipelines/plan_chips.py

## Import Cycles
- None detected.

## Communities (29 total, 1 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.18
Nodes (29): Asset, InfeasibleTeam, optimize(), Exception, No legal team fits the budget and counts., no_boost: driver ids that may not take the normal boost (used when a chip alread, load_rules(), Path (+21 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.07
Nodes (58): driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, _blank_zero(), _constructor_lines(), finish_mismatches(), _jolpica_finishes(), _load() (+50 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.09
Nodes (68): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, DataFrame (+60 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.16
Nodes (42): gate_mismatches(), Every TI row of every completed session scored with the rules, compared with the, Report only, not a gate: our fantasy_points totals against mzafram Round_Fantasy, totals_mismatches(), official_row(), _points(), DataFrame, Path (+34 more)

### Community 4 - "walkforward.py"
Cohesion: 0.06
Nodes (76): argparse, collections_abc, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., Refresh pre-event safety-car rates from previously observed FastF1 race status., main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for (+68 more)

### Community 5 - "vault.py"
Cohesion: 0.15
Nodes (26): RuntimeError, shutil, _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), Exception (+18 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.16
Nodes (22): _fetch(), _get_page(), pull_jolpica(), Path, Session, Parsed JSON of one page. A 429 waits 5s and retries, up to RETRIES times., All races of one endpoint; pages merged by round, sorted by round., empty_routes() (+14 more)

### Community 7 - "pandas"
Cohesion: 0.28
Nodes (17): _frame(), _full_tables(), _kind(), _lock(), _mus(), _prices(), rules(), _spy() (+9 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.05
Nodes (67): io, json, os, _capture(), default_steps(), due(), execute(), _http() (+59 more)

### Community 9 - "load_rules"
Cohesion: 0.07
Nodes (62): pytest, _pit_retry_accepted(), dnf_probability(), DataFrame, Series, Per-driver race DNF probability, shrunk toward the field rate of the history it, history: race result rows already cut to before the target lock. p = (dnfs + shr, _features() (+54 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (41): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+33 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.13
Nodes (22): _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), compare_order_predictions(), _constructor_prior(), _Filter (+14 more)

### Community 12 - "load_track_metadata"
Cohesion: 0.26
Nodes (16): main(), add_prior_safety_car_rates(), load_track_metadata(), DataFrame, Path, Raised when static track metadata is incomplete or invalid., Attach each event's circuit SC rate using only earlier observed race sessions., TrackMetadataError (+8 more)

### Community 13 - "fp2_longrun_pace"
Cohesion: 0.22
Nodes (18): main(), _fit_driver(), fp2_longrun_pace(), _known_at(), DataFrame, Series, Timestamp, Pre-lock FP2 long-run pace estimates with explicit coverage and fit diagnostics. (+10 more)

### Community 14 - "sample_bonus"
Cohesion: 0.23
Nodes (14): dataclasses, BonusOutcome, _eligible_history(), DataFrame, Timestamp, Empirical bonus-event samplers. History is limited to pre-lock completed rounds., Sample supported labels from prior-round history; unknown feeds return explicit, sample_bonus() (+6 more)

### Community 15 - "plackett_luce.py"
Cohesion: 0.33
Nodes (6): fit(), ndarray, Regularized Plackett-Luce over finishing orders. Log-strength of an entrant = fe, n full orders (entrant indices, winner first). Gumbel-max: argsort of log-streng, Penalized maximum likelihood by Newton steps (the log likelihood is concave in b, sample()

### Community 20 - "test_rolling.py"
Cohesion: 0.40
Nodes (18): baseline_mu(), lock(), mu_of(), points(), prices(), races(), rows: (round, asset_id, price)., rows: (round, asset_id, total) or (round, asset_id, total, known_at). (+10 more)

### Community 21 - "poisson.py"
Cohesion: 0.25
Nodes (8): deviance(), fit(), ndarray, Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shr, Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events, Mean Poisson deviance; lower is better., Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not, shrunk_rate()

### Community 22 - "app.py"
Cohesion: 0.15
Nodes (26): _capture_chips(), _data_tab(), _decision_rows(), main(), _prices(), Local Streamlit dashboard for the F1 Fantasy teams and weekly update., _report_chip_advice(), _round_info() (+18 more)

### Community 23 - "logic.py"
Cohesion: 0.14
Nodes (23): exclude(), load_team(), main(), DataFrame, Path, Benched or unavailable assets: expected points -1000, so the optimizer sells the, OUT -> IN' for each transfer, drivers and constructors paired separately (counts, swaps() (+15 more)

### Community 24 - "ilp.py"
Cohesion: 0.17
Nodes (21): pulp, _actual_points(), DataFrame, estimate_chip(), plan_chips(), DataFrame, Forward chip-value estimates using the configured rules and team optimizer., Return (gain, resulting team, unsupported reason); rules are read via scoring._r (+13 more)

### Community 25 - "TeamState"
Cohesion: 0.44
Nodes (7): TeamState, tables(), test_apply_transfers_writes_backup_team_and_history(), test_history_points_applies_boost_chip_and_penalty(), test_top_teams_chip_and_no_round_left(), test_top_teams_distinct_and_in_budget(), test_validate()

### Community 26 - "main"
Cohesion: 0.33
Nodes (7): main(), historical_value(), DataFrame, Points the chip would have added in one past round (points and mu already cut to, Mean replay gain over earlier completed rounds, sprint weekends vs normal ones k, replay_gain(), test_replay_autopilot_and_no_negative_use_actual_points()

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `test_scoring_gate.py`, `walkforward.py`, `pandas`, `load_rules`, `app.py`, `logic.py`, `ilp.py`, `main`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `walkforward.py` to `load_rules`, `test_rolling.py`, `app.py`, `logic.py`, `main`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `load_rules`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06963645673323093 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09170471841704718 - nodes in this community are weakly interconnected._
- **Should `walkforward.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05821782178217822 - nodes in this community are weakly interconnected._