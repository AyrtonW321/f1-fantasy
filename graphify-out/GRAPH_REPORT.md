# Graph Report - f1-fantasy  (2026-11-14)

## Corpus Check
- 78 files · ~36,613 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 792 nodes · 2378 edges · 24 communities (23 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2ab5b190`
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
- `build_bonus()` --calls--> `bonus_points()`  [EXTRACTED]
  pipelines/build_data.py → src/ingest/ti_lines.py

## Import Cycles
- None detected.

## Communities (24 total, 1 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.07
Nodes (84): dataclasses, load_team(), main(), Path, pulp, _actual_points(), DataFrame, DataFrame (+76 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.08
Nodes (54): json, driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, _blank_zero(), _constructor_lines(), _jolpica_finishes(), _load() (+46 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.11
Nodes (63): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, re (+55 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.13
Nodes (48): finish_mismatches(), gate_mismatches(), DataFrame, Every TI row of every completed session scored with the rules, compared with the, One CSV for all seasons: this season's rows are replaced and other seasons' rows, TI numeric finishing positions compared with Jolpica's, for every completed sess, Report only, not a gate: our fantasy_points totals against mzafram Round_Fantasy, _save_season_csv() (+40 more)

### Community 4 - "walkforward.py"
Cohesion: 0.05
Nodes (84): argparse, collections_abc, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for, mae() (+76 more)

### Community 5 - "vault.py"
Cohesion: 0.07
Nodes (44): os, pytest, RuntimeError, shutil, DataFrame, Observed race-to-race fantasy price changes derived from official price snapshot, Calculate observed price changes only between adjacent round snapshots.      The, realized_price_changes() (+36 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.15
Nodes (23): _fetch(), _get_page(), pull_jolpica(), Path, Session, Snapshot Jolpica (Ergast-compatible) race data to {raw_dir}/jolpica/{season}/., Parsed JSON of one page. A 429 waits 5s and retries, up to RETRIES times., All races of one endpoint; pages merged by round, sorted by round. (+15 more)

### Community 7 - "pandas"
Cohesion: 0.28
Nodes (17): _frame(), _full_tables(), _kind(), _lock(), _mus(), _prices(), rules(), _spy() (+9 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.06
Nodes (64): io, _capture(), default_steps(), due(), execute(), _http(), latest_ti_tag(), _local() (+56 more)

### Community 9 - "load_rules"
Cohesion: 0.08
Nodes (58): dnf_probability(), DataFrame, Series, Per-driver race DNF probability, shrunk toward the field rate of the history it, history: race result rows already cut to before the target lock. p = (dnfs + shr, _features(), _perf(), point_tables() (+50 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (41): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+33 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.13
Nodes (22): _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), compare_order_predictions(), _constructor_prior(), _Filter (+14 more)

### Community 12 - "load_track_metadata"
Cohesion: 0.22
Nodes (18): main(), Refresh pre-event safety-car rates from previously observed FastF1 race status., add_prior_safety_car_rates(), load_track_metadata(), DataFrame, Path, Validated event-level circuit metadata used by pre-lock features., Raised when static track metadata is incomplete or invalid. (+10 more)

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
Cohesion: 0.40
Nodes (18): baseline_mu(), lock(), mu_of(), points(), prices(), races(), rows: (round, asset_id, price)., rows: (round, asset_id, total) or (round, asset_id, total, known_at). (+10 more)

### Community 21 - "poisson.py"
Cohesion: 0.25
Nodes (8): deviance(), fit(), ndarray, Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shr, Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events, Mean Poisson deviance; lower is better., Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not, shrunk_rate()

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `test_scoring_gate.py`, `walkforward.py`, `pandas`, `load_rules`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `walkforward.py` to `optimize`, `load_rules`, `test_rolling.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `load_rules`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `optimize` be split into smaller, more focused modules?**
  _Cohesion score 0.06869254341164453 - nodes in this community are weakly interconnected._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07539450613676213 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10675990675990676 - nodes in this community are weakly interconnected._