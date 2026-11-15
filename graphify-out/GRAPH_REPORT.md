# Graph Report - f1-fantasy  (2026-11-15)

## Corpus Check
- 83 files · ~39,880 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 869 nodes · 2577 edges · 26 communities (25 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d5b929dc`
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
- fastf1_pull.py
- walkforward_strength
- fp2_longrun_pace
- sample_bonus
- plackett_luce.py
- test_rolling.py
- poisson.py
- app.py
- main
- dnf_probability
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 88 edges
2. `robust_mu()` - 40 edges
3. `optimize()` - 34 edges
4. `run_season()` - 32 edges
5. `build_races()` - 32 edges
6. `DriverLine` - 31 edges
7. `Asset` - 26 edges
8. `score_constructor()` - 26 edges
9. `TeamState` - 25 edges
10. `sim_mu()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_load_team_reads_state_and_rejects_unknown_assets()` --calls--> `load_team()`  [INFERRED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `test_reads_config_rules_and_null_raises()` --indirect_call--> `UnknownRuleError`  [INFERRED]
  tests/test_chips.py → src/sim/scoring.py
- `test_season_values_match_spec()` --calls--> `load_rules()`  [EXTRACTED]
  tests/test_scoring.py → src/sim/scoring.py
- `rules()` --calls--> `load_rules()`  [EXTRACTED]
  tests/test_walkforward.py → src/sim/scoring.py
- `_top()` --calls--> `TeamState`  [EXTRACTED]
  app.py → src/optimize/ilp.py

## Import Cycles
- None detected.

## Communities (26 total, 1 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.07
Nodes (69): dataclasses, load_team(), main(), Path, main(), pulp, shutil, historical_value() (+61 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.06
Nodes (82): collections_abc, bonus_points(), driver_line(), parse_pit(), parse_teamwork(), _points(), _position(), Path (+74 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.11
Nodes (62): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, _asset() (+54 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.07
Nodes (74): driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, _blank_zero(), _constructor_lines(), finish_mismatches(), gate_mismatches(), _jolpica_finishes() (+66 more)

### Community 4 - "walkforward.py"
Cohesion: 0.05
Nodes (80): argparse, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for, mae(), main() (+72 more)

### Community 5 - "vault.py"
Cohesion: 0.17
Nodes (24): RuntimeError, _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), Exception, Path (+16 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.15
Nodes (23): _fetch(), _get_page(), pull_jolpica(), Path, Session, Snapshot Jolpica (Ergast-compatible) race data to {raw_dir}/jolpica/{season}/., Parsed JSON of one page. A 429 waits 5s and retries, up to RETRIES times., All races of one endpoint; pages merged by round, sorted by round. (+15 more)

### Community 7 - "pandas"
Cohesion: 0.28
Nodes (17): _frame(), _full_tables(), _kind(), _lock(), _mus(), _prices(), rules(), _spy() (+9 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.06
Nodes (65): io, json, _capture(), default_steps(), due(), execute(), _http(), latest_ti_tag() (+57 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (41): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+33 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.13
Nodes (22): _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), compare_order_predictions(), _constructor_prior(), _Filter (+14 more)

### Community 13 - "fp2_longrun_pace"
Cohesion: 0.24
Nodes (17): main(), _fit_driver(), fp2_longrun_pace(), _known_at(), DataFrame, Series, Timestamp, Return one FP2 pace/status row per expected race entrant and weekend.      Estim (+9 more)

### Community 14 - "sample_bonus"
Cohesion: 0.26
Nodes (13): BonusOutcome, _eligible_history(), DataFrame, Timestamp, Empirical bonus-event samplers. History is limited to pre-lock completed rounds., Sample supported labels from prior-round history; unknown feeds return explicit, sample_bonus(), _sample_rate() (+5 more)

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
Cohesion: 0.05
Nodes (84): _best_tab(), _cached_top(), _capture_chips(), _cards(), _chip_advice(), _chip_select(), _choose_and_apply(), _data_tab() (+76 more)

### Community 26 - "main"
Cohesion: 0.22
Nodes (18): main(), Refresh pre-event safety-car rates from previously observed FastF1 race status., add_prior_safety_car_rates(), load_track_metadata(), DataFrame, Path, Validated event-level circuit metadata used by pre-lock features., Raised when static track metadata is incomplete or invalid. (+10 more)

### Community 33 - "dnf_probability"
Cohesion: 0.08
Nodes (20): os, pytest, DataFrame, Observed race-to-race fantasy price changes derived from official price snapshot, Calculate observed price changes only between adjacent round snapshots.      The, realized_price_changes(), dnf_probability(), DataFrame (+12 more)

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `test_scoring_gate.py`, `walkforward.py`, `pandas`, `app.py`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `walkforward.py` to `optimize`, `crosscheck.py`, `test_rolling.py`, `app.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `crosscheck.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `optimize` be split into smaller, more focused modules?**
  _Cohesion score 0.07040328092959672 - nodes in this community are weakly interconnected._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.059499489274770175 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10961538461538461 - nodes in this community are weakly interconnected._