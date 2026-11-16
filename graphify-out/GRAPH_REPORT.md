# Graph Report - f1-fantasy  (2026-11-15)

## Corpus Check
- 85 files · ~41,429 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 895 nodes · 2645 edges · 34 communities (33 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f9b05a85`
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
- run_season
- pick_team.py
- load_track_metadata
- dnf_probability
- test_chips.py
- test_community_pull.py
- ilp.py
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 91 edges
2. `robust_mu()` - 40 edges
3. `optimize()` - 34 edges
4. `run_season()` - 32 edges
5. `build_races()` - 32 edges
6. `DriverLine` - 31 edges
7. `TeamState` - 28 edges
8. `Asset` - 27 edges
9. `score_constructor()` - 26 edges
10. `sim_mu()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_load_team_reads_state_and_rejects_unknown_assets()` --calls--> `load_team()`  [INFERRED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `test_exclude_pushes_asset_below_everyone_and_rejects_unknown()` --calls--> `exclude()`  [EXTRACTED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `test_infeasible_raises()` --indirect_call--> `InfeasibleTeam`  [INFERRED]
  tests/test_ilp.py → src/optimize/ilp.py
- `test_reads_config_rules_and_null_raises()` --indirect_call--> `UnknownRuleError`  [INFERRED]
  tests/test_chips.py → src/sim/scoring.py
- `test_season_values_match_spec()` --calls--> `load_rules()`  [EXTRACTED]
  tests/test_scoring.py → src/sim/scoring.py

## Import Cycles
- None detected.

## Communities (34 total, 1 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.21
Nodes (28): Asset, next_state(), optimize(), no_boost: driver ids that may not take the normal boost (used when a chip alread, TeamState, load_rules(), Path, test_x3_boost_puts_3x_on_best_driver_and_2x_on_the_next() (+20 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.06
Nodes (83): driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, bonus_points(), driver_line(), parse_pit(), parse_teamwork(), _points() (+75 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.09
Nodes (69): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, re (+61 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.09
Nodes (69): _blank_zero(), _constructor_lines(), finish_mismatches(), gate_mismatches(), _jolpica_finishes(), _load(), _official_inconsistent(), _official_index() (+61 more)

### Community 4 - "walkforward.py"
Cohesion: 0.06
Nodes (88): argparse, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for, mae(), main() (+80 more)

### Community 5 - "vault.py"
Cohesion: 0.17
Nodes (24): RuntimeError, _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), Exception, Path (+16 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.21
Nodes (17): pull_jolpica(), Path, empty_routes(), FakeResponse, FakeSession, page(), Path, race() (+9 more)

### Community 7 - "pandas"
Cohesion: 0.28
Nodes (17): _frame(), _full_tables(), _kind(), _lock(), _mus(), _prices(), rules(), _spy() (+9 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.19
Nodes (21): _capture(), default_steps(), due(), execute(), _http(), latest_ti_tag(), _local(), main() (+13 more)

### Community 9 - "snapshot_official"
Cohesion: 0.19
Nodes (17): _get(), Session, Parsed JSON if the response is valid (200, parses, non-empty), else None., snapshot_official(), drivers(), FakeResponse, FakeSession, Path (+9 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (40): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+32 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.13
Nodes (22): _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), compare_order_predictions(), _constructor_prior(), _Filter (+14 more)

### Community 12 - "weekly_update.py"
Cohesion: 0.16
Nodes (14): requests, Path, Snapshot the official F1 Fantasy feeds to {out_dir}/official/{season}/., Data.Value of a feed if it is a list, else []., Atomic write: temp file in the same folder, then os.replace., _rows(), _write(), _fetch() (+6 more)

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
Cohesion: 0.21
Nodes (17): _actual_points(), DataFrame, Decision, DataFrame, Timeline data and Vega-Lite chart for a team's season points., Build actual and expected point rows from the highest scored round to season end, Return a dark-background Vega-Lite v5 cumulative points chart., timeline_frame() (+9 more)

### Community 21 - "poisson.py"
Cohesion: 0.25
Nodes (8): deviance(), fit(), ndarray, Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shr, Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events, Mean Poisson deviance; lower is better., Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not, shrunk_rate()

### Community 22 - "app.py"
Cohesion: 0.06
Nodes (66): _applied(), _best_tab(), _cached_top(), _capture_chips(), _cards(), _chip_advice(), _chip_select(), _choose_and_apply() (+58 more)

### Community 23 - "evaluate_seasons.py"
Cohesion: 0.67
Nodes (3): InfeasibleTeam, Exception, No legal team fits the budget and counts.

### Community 24 - "run_season"
Cohesion: 0.14
Nodes (21): Cached top_teams: each ILP solve costs ~0.2 s, so only re-solve when the team, c, _top(), exclude(), DataFrame, Benched or unavailable assets: expected points -1000, so the optimizer sells the, assets(), _history(), history_path() (+13 more)

### Community 30 - "pick_team.py"
Cohesion: 0.29
Nodes (9): load_team(), main(), Path, Pick the team for the next unlocked round from robust season form.  Reads conf, OUT -> IN' for each transfer, drivers and constructors paired separately (counts, swaps(), test_exclude_pushes_asset_below_everyone_and_rejects_unknown(), test_load_team_reads_state_and_rejects_unknown_assets() (+1 more)

### Community 31 - "load_track_metadata"
Cohesion: 0.22
Nodes (18): main(), Refresh pre-event safety-car rates from previously observed FastF1 race status., add_prior_safety_car_rates(), load_track_metadata(), DataFrame, Path, Validated event-level circuit metadata used by pre-lock features., Raised when static track metadata is incomplete or invalid. (+10 more)

### Community 33 - "dnf_probability"
Cohesion: 0.07
Nodes (24): os, pytest, shutil, dnf_probability(), DataFrame, Series, Per-driver race DNF probability, shrunk toward the field rate of the history it, history: race result rows already cut to before the target lock. p = (dnfs + shr (+16 more)

### Community 34 - "test_chips.py"
Cohesion: 0.29
Nodes (13): estimate_chip(), plan_chips(), DataFrame, Return (gain, resulting team, unsupported reason); rules are read via scoring._r, Assign configured remaining chips to rounds for maximum nonnegative expected gai, _state(), field(), team() (+5 more)

### Community 35 - "test_community_pull.py"
Cohesion: 0.17
Nodes (19): io, json, _check_member(), pull_mzafram(), pull_tracing_insights(), Path, Session, Pull TracingInsights season JSON and mzafram round JSON into {raw_dir}. (+11 more)

### Community 38 - "ilp.py"
Cohesion: 0.15
Nodes (18): collections_abc, dataclasses, pulp, historical_value(), DataFrame, Replay-based chip values for chips that expected points cannot rank (autopilot,, Points the chip would have added in one past round (points and mu already cut to, Mean replay gain over earlier completed rounds, sprint weekends vs normal ones k (+10 more)

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `test_chips.py`, `walkforward.py`, `test_scoring_gate.py`, `ilp.py`, `pandas`, `test_rolling.py`, `app.py`, `run_season`, `pick_team.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `walkforward.py` to `run_season`, `crosscheck.py`, `pick_team.py`, `app.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `crosscheck.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05543071161048689 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08959644576082933 - nodes in this community are weakly interconnected._
- **Should `test_scoring_gate.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08571428571428572 - nodes in this community are weakly interconnected._