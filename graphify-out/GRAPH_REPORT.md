# Graph Report - f1-fantasy  (2026-11-25)

## Corpus Check
- 86 files · ~44,134 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 941 nodes · 2772 edges · 33 communities (32 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f12e25b2`
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
- confirm_round
- replay_gain
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 93 edges
2. `robust_mu()` - 40 edges
3. `optimize()` - 35 edges
4. `run_season()` - 32 edges
5. `build_races()` - 32 edges
6. `DriverLine` - 31 edges
7. `_team_row_body()` - 28 edges
8. `TeamState` - 28 edges
9. `Asset` - 27 edges
10. `score_constructor()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `test_load_team_reads_state_and_rejects_unknown_assets()` --calls--> `load_team()`  [INFERRED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `_guard()` --calls--> `body()`  [INFERRED]
  app.py → tests/test_community_pull.py
- `test_exclude_pushes_asset_below_everyone_and_rejects_unknown()` --calls--> `exclude()`  [EXTRACTED]
  tests/test_pick_team.py → pipelines/pick_team.py
- `test_replay_autopilot_and_no_negative_use_actual_points()` --calls--> `replay_gain()`  [EXTRACTED]
  tests/test_chips.py → src/optimize/chip_history.py
- `test_reads_config_rules_and_null_raises()` --indirect_call--> `UnknownRuleError`  [INFERRED]
  tests/test_chips.py → src/sim/scoring.py

## Import Cycles
- None detected.

## Communities (33 total, 1 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.08
Nodes (66): load_team(), main(), Path, pulp, estimate_chip(), plan_chips(), DataFrame, Forward chip-value estimates using the configured rules and team optimizer. (+58 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.13
Nodes (27): _area(), _best_tab(), _capture_chips(), _chip_advice(), _data_tab(), _decision_rows(), _guard(), main() (+19 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.09
Nodes (69): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, re (+61 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.16
Nodes (42): gate_mismatches(), Every TI row of every completed session scored with the rules, compared with the, Report only, not a gate: our fantasy_points totals against mzafram Round_Fantasy, totals_mismatches(), official_row(), _points(), DataFrame, Path (+34 more)

### Community 4 - "walkforward.py"
Cohesion: 0.15
Nodes (17): _cached_top(), _choose_and_apply(), _final_fix(), _inputs_stamp(), _last_race(), _picks(), _race_name(), Top choices for the chip; returns (choices, session key of the chosen index). (+9 more)

### Community 5 - "vault.py"
Cohesion: 0.10
Nodes (30): os, RuntimeError, _key(), main(), MissingKeyError, _openssl(), _openssl_enc(), Exception (+22 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.12
Nodes (39): _edit_form(), rounds: round numbers the saved lineup can be recorded as played in (next round, _actual_points(), DataFrame, _rule(), apply_transfers(), final_fix(), _history() (+31 more)

### Community 7 - "pandas"
Cohesion: 0.13
Nodes (20): _best_body(), _cards(), _prices(), asset_card HTML per id: team colour, current price and this round's xPts., _table(), asset_card(), header_row(), _number() (+12 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.06
Nodes (79): argparse, collections_abc, dataclasses, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., Refresh pre-event safety-car rates from previously observed FastF1 race status., main() (+71 more)

### Community 9 - "snapshot_official"
Cohesion: 0.17
Nodes (18): pytest, _frame(), _full_tables(), _kind(), _lock(), _mus(), _prices(), rules() (+10 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (41): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+33 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.08
Nodes (39): main(), _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), add_prior_safety_car_rates(), load_track_metadata() (+31 more)

### Community 12 - "weekly_update.py"
Cohesion: 0.15
Nodes (23): _fetch(), _get_page(), pull_jolpica(), Path, Session, Snapshot Jolpica (Ergast-compatible) race data to {raw_dir}/jolpica/{season}/., Parsed JSON of one page. A 429 waits 5s and retries, up to RETRIES times., All races of one endpoint; pages merged by round, sorted by round. (+15 more)

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
Cohesion: 0.06
Nodes (85): json, driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, _blank_zero(), _constructor_lines(), finish_mismatches(), _jolpica_finishes() (+77 more)

### Community 21 - "poisson.py"
Cohesion: 0.25
Nodes (8): deviance(), fit(), ndarray, Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shr, Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events, Mean Poisson deviance; lower is better., Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not, shrunk_rate()

### Community 22 - "app.py"
Cohesion: 0.10
Nodes (35): Series, _trimmed_mean(), dnf_probability(), DataFrame, Series, Per-driver race DNF probability, shrunk toward the field rate of the history it, history: race result rows already cut to before the target lock. p = (dnfs + shr, _features() (+27 more)

### Community 23 - "evaluate_seasons.py"
Cohesion: 0.18
Nodes (13): shutil, tables(), test_apply_transfers_writes_backup_team_and_history(), test_final_fix(), test_history_points_applies_boost_chip_and_penalty(), test_round_chip(), test_round_source_confirm_and_review(), test_snapshot_and_record_round() (+5 more)

### Community 24 - "walkforward.py"
Cohesion: 0.20
Nodes (10): _applied(), _chip_select(), Per-team chip picker: defaults to the chip advice; locked to the logged chip onc, True once 'I made these transfers' logged this round (with or without a chip); s, advised_chip(), Per logged round: assets out and in versus the previous logged lineup (first row, Chip logged for that round, if any., Chip the plan_chips advice recommends for round_ ('Round N: <chip>;'), None for (+2 more)

### Community 25 - "dnf_probability"
Cohesion: 0.06
Nodes (66): io, _capture(), default_steps(), due(), execute(), _http(), lagging_sources(), latest_ti_tag() (+58 more)

### Community 26 - "InfeasibleTeam"
Cohesion: 0.40
Nodes (18): baseline_mu(), lock(), mu_of(), points(), prices(), races(), rows: (round, asset_id, price)., rows: (round, asset_id, total) or (round, asset_id, total, known_at). (+10 more)

### Community 28 - "evaluate_overtakes.py"
Cohesion: 0.25
Nodes (9): _mu(), exclude(), DataFrame, Benched or unavailable assets: expected points -1000, so the optimizer sells the, asset_mu(), assets(), Asset id to this round's expected points (no exclusions)., This round's assets with robust_mu (config/model.yaml form); excluded ids get mu (+1 more)

### Community 29 - "confirm_round"
Cohesion: 0.33
Nodes (6): _confirm_banner(), Ask the user to confirm the lineup logged for the last race (or record one if no, confirm_round(), How that round's lineup was logged: app, edit or snapshot; None when nothing is, Mark a snapshot row as confirmed by the user (source edit), lineup unchanged., round_source()

### Community 30 - "replay_gain"
Cohesion: 0.50
Nodes (5): historical_value(), DataFrame, Points the chip would have added in one past round (points and mu already cut to, Mean replay gain over earlier completed rounds, sprint weekends vs normal ones k, replay_gain()

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `test_scoring_gate.py`, `walkforward.py`, `test_jolpica_pull.py`, `test_community_pull.py`, `snapshot_official`, `test_rolling.py`, `app.py`, `walkforward.py`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `test_community_pull.py` to `optimize`, `crosscheck.py`, `test_jolpica_pull.py`, `app.py`, `InfeasibleTeam`, `evaluate_overtakes.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `app.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `optimize` be split into smaller, more focused modules?**
  _Cohesion score 0.0806697108066971 - nodes in this community are weakly interconnected._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13227513227513227 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08959644576082933 - nodes in this community are weakly interconnected._