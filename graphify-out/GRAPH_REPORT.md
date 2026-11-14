# Graph Report - f1-fantasy  (2026-11-14)

## Corpus Check
- 79 files · ~37,923 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 810 nodes · 2446 edges · 34 communities (33 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3462a065`
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
- test_ti_lines.py
- pick_team.py
- overtakes.py
- ilp.py
- driver_code
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
10. `TeamState` - 24 edges

## Surprising Connections (you probably didn't know these)
- `test_load_team_reads_state_and_rejects_unknown_assets()` --calls--> `load_team()`  [INFERRED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `test_finish_positions_agree()` --calls--> `finish_mismatches()`  [EXTRACTED]
  tests/test_scoring_gate.py → src/ingest/crosscheck.py
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
Cohesion: 0.22
Nodes (27): Asset, optimize(), no_boost: driver ids that may not take the normal boost (used when a chip alread, TeamState, load_rules(), Path, test_x3_boost_puts_3x_on_best_driver_and_2x_on_the_next(), _dec() (+19 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.16
Nodes (27): _blank_zero(), _constructor_lines(), finish_mismatches(), _jolpica_finishes(), _load(), _official_inconsistent(), _official_index(), _official_parts() (+19 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.11
Nodes (63): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, re (+55 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.14
Nodes (44): gate_mismatches(), DataFrame, Every TI row of every completed session scored with the rules, compared with the, Report only, not a gate: our fantasy_points totals against mzafram Round_Fantasy, totals_mismatches(), official_row(), _points(), DataFrame (+36 more)

### Community 4 - "walkforward.py"
Cohesion: 0.07
Nodes (60): argparse, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., Refresh pre-event safety-car rates from previously observed FastF1 race status., main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for, mae() (+52 more)

### Community 5 - "vault.py"
Cohesion: 0.17
Nodes (24): RuntimeError, _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), Exception, Path (+16 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.14
Nodes (24): requests, _fetch(), _get_page(), pull_jolpica(), Path, Session, Snapshot Jolpica (Ergast-compatible) race data to {raw_dir}/jolpica/{season}/., Parsed JSON of one page. A 429 waits 5s and retries, up to RETRIES times. (+16 more)

### Community 7 - "pandas"
Cohesion: 0.28
Nodes (17): _frame(), _full_tables(), _kind(), _lock(), _mus(), _prices(), rules(), _spy() (+9 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.05
Nodes (68): io, json, os, _capture(), default_steps(), due(), execute(), _http() (+60 more)

### Community 9 - "load_rules"
Cohesion: 0.14
Nodes (28): Series, _trimmed_mean(), _features(), _perf(), point_tables(), DataFrame, ndarray, quali_tables() (+20 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (41): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+33 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.09
Nodes (39): main(), _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), add_prior_safety_car_rates(), load_track_metadata() (+31 more)

### Community 12 - "load_track_metadata"
Cohesion: 0.20
Nodes (26): _driver_points(), DriverLine, _pit_points(), PitResult, Exception, Official F1 Fantasy scoring. Game values come from config/rules_{season}.yaml, n, A rule needed for this score is null (never observed) or not defined., score_constructor() (+18 more)

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

### Community 22 - "app.py"
Cohesion: 0.22
Nodes (18): _best_tab(), _cached_top(), _capture_chips(), _data_tab(), _decision_rows(), _inputs_stamp(), main(), _prices() (+10 more)

### Community 23 - "logic.py"
Cohesion: 0.14
Nodes (29): _actual_points(), DataFrame, Decision, next_state(), _rule(), apply_transfers(), assets(), history_path() (+21 more)

### Community 24 - "ilp.py"
Cohesion: 0.28
Nodes (13): estimate_chip(), plan_chips(), DataFrame, Forward chip-value estimates using the configured rules and team optimizer., Return (gain, resulting team, unsupported reason); rules are read via scoring._r, Assign configured remaining chips to rounds for maximum nonnegative expected gai, _state(), field() (+5 more)

### Community 25 - "TeamState"
Cohesion: 0.09
Nodes (23): pytest, shutil, DataFrame, Observed race-to-race fantasy price changes derived from official price snapshot, Calculate observed price changes only between adjacent round snapshots.      The, realized_price_changes(), dnf_probability(), DataFrame (+15 more)

### Community 26 - "main"
Cohesion: 0.28
Nodes (8): collections_abc, historical_value(), DataFrame, Replay-based chip values for chips that expected points cannot rank (autopilot,, Points the chip would have added in one past round (points and mu already cut to, Mean replay gain over earlier completed rounds, sprint weekends vs normal ones k, replay_gain(), test_replay_autopilot_and_no_negative_use_actual_points()

### Community 27 - "test_ti_lines.py"
Cohesion: 0.14
Nodes (25): bonus_points(), driver_line(), parse_pit(), parse_teamwork(), _points(), _position(), Session, TracingInsights driver and constructor rows turned into scoring inputs (src/sim/ (+17 more)

### Community 28 - "pick_team.py"
Cohesion: 0.24
Nodes (12): exclude(), load_team(), main(), DataFrame, Path, Pick the team for the next unlocked round from robust season form.  Reads conf, Benched or unavailable assets: expected points -1000, so the optimizer sells the, OUT -> IN' for each transfer, drivers and constructors paired separately (counts (+4 more)

### Community 29 - "overtakes.py"
Cohesion: 0.26
Nodes (9): _design(), expected(), overtakes_mu(), DataFrame, ndarray, Phase 4.5: expected race overtakes (Poisson) and positions gained (shrunk mean), Expected overtakes and gained per driver for a race; None without earlier curren, robust_mu of points minus actual overtake/gained points, plus expected overtake/ (+1 more)

### Community 30 - "ilp.py"
Cohesion: 0.25
Nodes (7): dataclasses, pulp, InfeasibleTeam, Exception, ILP team optimizer: best legal team under the budget, counts and transfer rules., No legal team fits the budget and counts., _tenths()

### Community 31 - "driver_code"
Cohesion: 0.43
Nodes (5): driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, test_falls_back_to_family_name(), test_uses_code_when_present()

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `test_build_tables.py`, `test_scoring_gate.py`, `walkforward.py`, `pandas`, `load_rules`, `load_track_metadata`, `app.py`, `logic.py`, `ilp.py`, `test_ti_lines.py`, `pick_team.py`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `walkforward.py` to `load_rules`, `test_rolling.py`, `app.py`, `logic.py`, `pick_team.py`, `overtakes.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `load_rules`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10675990675990676 - nodes in this community are weakly interconnected._
- **Should `test_scoring_gate.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14444444444444443 - nodes in this community are weakly interconnected._
- **Should `walkforward.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07492507492507493 - nodes in this community are weakly interconnected._