# Graph Report - f1-fantasy  (2026-11-26)

## Corpus Check
- 87 files · ~45,376 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 951 nodes · 2822 edges · 36 communities (35 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 56 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e91a844f`
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
- dnf_probability
- InfeasibleTeam
- evaluate_overtakes.py
- replay_gain
- Path
- main
- _chip_select
- DriverLine
- driver_code
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 96 edges
2. `robust_mu()` - 41 edges
3. `optimize()` - 37 edges
4. `run_season()` - 33 edges
5. `build_races()` - 32 edges
6. `DriverLine` - 31 edges
7. `_team_row_body()` - 28 edges
8. `Asset` - 28 edges
9. `TeamState` - 28 edges
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

## Communities (36 total, 1 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.08
Nodes (65): pulp, estimate_chip(), plan_chips(), DataFrame, Forward chip-value estimates using the configured rules and team optimizer., Return (gain, resulting team, unsupported reason); rules are read via scoring._r, Assign configured remaining chips to rounds for maximum nonnegative expected gai, _state() (+57 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.40
Nodes (6): exclude(), load_team(), main(), DataFrame, Path, Benched or unavailable assets: expected points -1000, so the optimizer sells the

### Community 2 - "test_build_tables.py"
Cohesion: 0.09
Nodes (68): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, DataFrame (+60 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.13
Nodes (48): finish_mismatches(), gate_mismatches(), DataFrame, Every TI row of every completed session scored with the rules, compared with the, One CSV for all seasons: this season's rows are replaced and other seasons' rows, TI numeric finishing positions compared with Jolpica's, for every completed sess, Report only, not a gate: our fantasy_points totals against mzafram Round_Fantasy, _save_season_csv() (+40 more)

### Community 4 - "walkforward.py"
Cohesion: 0.50
Nodes (5): historical_value(), DataFrame, Points the chip would have added in one past round (points and mu already cut to, Mean replay gain over earlier completed rounds, sprint weekends vs normal ones k, replay_gain()

### Community 5 - "vault.py"
Cohesion: 0.18
Nodes (12): _cached_top(), _inputs_stamp(), _last_race(), _leads(), _picks(), Top choices for the chip; returns (choices, session key of the chosen index)., Modified times of everything top_teams reads besides its arguments: data, model, Cached top_teams: each ILP solve costs ~0.2 s, so only re-solve when the team, c (+4 more)

### Community 6 - "test_jolpica_pull.py"
Cohesion: 0.14
Nodes (19): _best_body(), _cards(), _prices(), asset_card HTML per id: team colour, current price and this round's xPts., asset_card(), header_row(), _number(), Small HTML fragments for the dark team calculator view. (+11 more)

### Community 7 - "pandas"
Cohesion: 0.13
Nodes (28): _area(), _best_tab(), _capture_chips(), _chip_advice(), _data_tab(), _decision_rows(), _guard(), main() (+20 more)

### Community 8 - "test_community_pull.py"
Cohesion: 0.06
Nodes (81): argparse, collections_abc, dataclasses, pandas, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for (+73 more)

### Community 9 - "snapshot_official"
Cohesion: 0.28
Nodes (17): _frame(), _full_tables(), _kind(), _lock(), _mus(), _prices(), rules(), _spy() (+9 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (42): Any, re, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError (+34 more)

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
Cohesion: 0.15
Nodes (26): _features(), _perf(), point_tables(), DataFrame, ndarray, quali_tables(), race_line(), _rank() (+18 more)

### Community 21 - "poisson.py"
Cohesion: 0.25
Nodes (8): deviance(), fit(), ndarray, Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shr, Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events, Mean Poisson deviance; lower is better., Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not, shrunk_rate()

### Community 22 - "app.py"
Cohesion: 0.06
Nodes (38): os, pytest, RuntimeError, _key(), main(), MissingKeyError, _openssl(), _openssl_enc() (+30 more)

### Community 23 - "evaluate_seasons.py"
Cohesion: 0.17
Nodes (14): shutil, tables(), test_apply_transfers_writes_backup_team_and_history(), test_final_fix(), test_history_points_applies_boost_chip_and_penalty(), test_official_points_override(), test_round_chip(), test_round_source_confirm_and_review() (+6 more)

### Community 25 - "dnf_probability"
Cohesion: 0.05
Nodes (68): io, json, _capture(), default_steps(), due(), execute(), _http(), lagging_sources() (+60 more)

### Community 26 - "InfeasibleTeam"
Cohesion: 0.40
Nodes (18): baseline_mu(), lock(), mu_of(), points(), prices(), races(), rows: (round, asset_id, price)., rows: (round, asset_id, total) or (round, asset_id, total, known_at). (+10 more)

### Community 28 - "evaluate_overtakes.py"
Cohesion: 0.14
Nodes (27): bonus_points(), driver_line(), parse_pit(), parse_teamwork(), _points(), _position(), Path, Session (+19 more)

### Community 30 - "replay_gain"
Cohesion: 0.11
Nodes (44): _actual_points(), DataFrame, _rule(), apply_transfers(), assets(), confirm_round(), final_fix(), _history() (+36 more)

### Community 31 - "Path"
Cohesion: 0.14
Nodes (17): _choose_and_apply(), _confirm_banner(), _edit_form(), _final_fix(), _mu(), _race_name(), rounds: round numbers the saved lineup can be recorded as played in (next round, Ask the user to confirm the lineup logged for the last race (or record one if no (+9 more)

### Community 33 - "main"
Cohesion: 0.20
Nodes (21): _blank_zero(), _constructor_lines(), _jolpica_finishes(), _load(), _official_inconsistent(), _official_index(), _official_parts(), _official_rank() (+13 more)

### Community 34 - "_chip_select"
Cohesion: 0.20
Nodes (10): _applied(), _chip_select(), Per-team chip picker: defaults to the chip advice; locked to the logged chip onc, True once 'I made these transfers' logged this round (with or without a chip); s, advised_chip(), Per logged round: assets out and in versus the previous logged lineup (first row, Chip logged for that round, if any., Chip the plan_chips advice recommends for round_ ('Round N: <chip>;'), None for (+2 more)

### Community 35 - "DriverLine"
Cohesion: 0.21
Nodes (25): _driver_points(), DriverLine, _pit_points(), PitResult, Exception, A rule needed for this score is null (never observed) or not defined., score_constructor(), score_driver() (+17 more)

### Community 36 - "driver_code"
Cohesion: 0.43
Nodes (5): driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, test_falls_back_to_family_name(), test_uses_code_when_present()

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `_chip_select`, `DriverLine`, `test_scoring_gate.py`, `pandas`, `test_community_pull.py`, `snapshot_official`, `test_rolling.py`, `evaluate_overtakes.py`, `replay_gain`, `Path`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `test_community_pull.py` to `crosscheck.py`, `pandas`, `test_rolling.py`, `InfeasibleTeam`, `replay_gain`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `test_rolling.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `optimize` be split into smaller, more focused modules?**
  _Cohesion score 0.0837245696400626 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09170471841704718 - nodes in this community are weakly interconnected._
- **Should `test_scoring_gate.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13010204081632654 - nodes in this community are weakly interconnected._