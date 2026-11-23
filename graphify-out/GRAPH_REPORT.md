# Graph Report - f1-fantasy  (2026-11-23)

## Corpus Check
- 85 files · ~42,058 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 901 nodes · 2667 edges · 34 communities (33 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `eff16d6c`
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
- dnf_probability
- InfeasibleTeam
- evaluate_overtakes.py
- test_weekly_update.py
- dnf_probability
- test_community_pull.py
- f1-fantasy

## God Nodes (most connected - your core abstractions)
1. `load_rules()` - 92 edges
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

## Communities (34 total, 1 thin omitted)

### Community 0 - "optimize"
Cohesion: 0.06
Nodes (97): dataclasses, load_team(), main(), Path, pulp, _actual_points(), DataFrame, DataFrame (+89 more)

### Community 1 - "crosscheck.py"
Cohesion: 0.05
Nodes (89): driver_code(), Shared helper for Jolpica driver identity., Three-letter code of a Jolpica Driver dict; falls back to familyName[:3] upper w, _blank_zero(), _constructor_lines(), finish_mismatches(), _jolpica_finishes(), _load() (+81 more)

### Community 2 - "test_build_tables.py"
Cohesion: 0.11
Nodes (63): build_bonus(), build_overtakes(), main(), Path, Build normalized Parquet tables from data/raw into data/processed. Run from the, Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fan, Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertake, re (+55 more)

### Community 3 - "test_scoring_gate.py"
Cohesion: 0.16
Nodes (40): gate_mismatches(), Every TI row of every completed session scored with the rules, compared with the, official_row(), _points(), DataFrame, Path, _races(), Scoring gate and cross-checks: hand-built raw trees (unit) and real raw data (ma (+32 more)

### Community 4 - "walkforward.py"
Cohesion: 0.19
Nodes (16): pandas, main(), Tune and evaluate the Phase 4.6 sprint term on 2026 walk-forward data., assert_known_before_lock(), LeakageError, DataFrame, Exception, A row became known after the lock of the round it feeds. (+8 more)

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
Cohesion: 0.15
Nodes (20): argparse, collections_abc, pathlib, Build the auditable FP2 pace feature table from normalized FastF1 data., exclude(), DataFrame, Pick the team for the next unlocked round from robust season form.  Reads conf, Benched or unavailable assets: expected points -1000, so the optimizer sells the (+12 more)

### Community 9 - "snapshot_official"
Cohesion: 0.19
Nodes (21): _capture(), default_steps(), due(), execute(), _http(), latest_ti_tag(), _local(), main() (+13 more)

### Community 10 - "fastf1_pull.py"
Cohesion: 0.11
Nodes (41): Any, _available_sessions(), configure_cache(), _convert_laps(), event_inventory(), _existing(), FastF1IngestError, _inventory_one() (+33 more)

### Community 11 - "walkforward_strength"
Cohesion: 0.08
Nodes (40): main(), Refresh pre-event safety-car rates from previously observed FastF1 race status., _format_metrics(), main(), DataFrame, Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout., _summary_for(), add_prior_safety_car_rates() (+32 more)

### Community 12 - "weekly_update.py"
Cohesion: 0.19
Nodes (17): _get(), Session, Parsed JSON if the response is valid (200, parses, non-empty), else None., snapshot_official(), drivers(), FakeResponse, FakeSession, Path (+9 more)

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
Cohesion: 0.10
Nodes (32): Series, _trimmed_mean(), dnf_probability(), DataFrame, Series, Per-driver race DNF probability, shrunk toward the field rate of the history it, history: race result rows already cut to before the target lock. p = (dnfs + shr, _features() (+24 more)

### Community 21 - "poisson.py"
Cohesion: 0.25
Nodes (8): deviance(), fit(), ndarray, Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shr, Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events, Mean Poisson deviance; lower is better., Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not, shrunk_rate()

### Community 22 - "app.py"
Cohesion: 0.06
Nodes (68): _applied(), _best_tab(), _cached_top(), _capture_chips(), _cards(), _chip_advice(), _chip_select(), _choose_and_apply() (+60 more)

### Community 23 - "evaluate_seasons.py"
Cohesion: 0.20
Nodes (18): main(), Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-for, mae(), main(), Phase 4 base: robust 2026 form vs rolling-5 baseline, walk-forward.  Settings tu, main(), Phase 4.4: simulator with qualifying order vs the 4.2 simulator and robust form, main() (+10 more)

### Community 24 - "run_season"
Cohesion: 0.15
Nodes (15): json, requests, Path, Snapshot the official F1 Fantasy feeds to {out_dir}/official/{season}/., Data.Value of a feed if it is a list, else []., Atomic write: temp file in the same folder, then os.replace., _rows(), _write() (+7 more)

### Community 25 - "dnf_probability"
Cohesion: 0.21
Nodes (15): _external_predictors(), main(), Evaluate multi-season baselines and re-tune robust form for Phase 5., DataFrame, Aggregate walk-forward prediction and team-score metrics., Return asset MAE, picked-team totals and mean per-round Spearman correlation., season_metrics(), main() (+7 more)

### Community 26 - "InfeasibleTeam"
Cohesion: 0.40
Nodes (18): baseline_mu(), lock(), mu_of(), points(), prices(), races(), rows: (round, asset_id, price)., rows: (round, asset_id, total) or (round, asset_id, total, known_at). (+10 more)

### Community 28 - "evaluate_overtakes.py"
Cohesion: 0.20
Nodes (13): count_scores(), main(), Phase 4.5: overtakes (Poisson) and positions gained (shrunk mean), 2026 walk-for, (overtake deviance of model, of flat mean; gained SSE of model, of flat 0) over, _design(), expected(), overtakes_mu(), DataFrame (+5 more)

### Community 29 - "test_weekly_update.py"
Cohesion: 0.38
Nodes (4): os, races(), test_due_gate(), test_stale_team_warning()

### Community 33 - "dnf_probability"
Cohesion: 0.08
Nodes (20): pytest, shutil, DataFrame, Observed race-to-race fantasy price changes derived from official price snapshot, Calculate observed price changes only between adjacent round snapshots.      The, realized_price_changes(), Path, raw_data() (+12 more)

### Community 35 - "test_community_pull.py"
Cohesion: 0.18
Nodes (18): io, _check_member(), pull_mzafram(), pull_tracing_insights(), Path, Session, Pull TracingInsights season JSON and mzafram round JSON into {raw_dir}., Refuse zip members that could leave the target folder (.., absolute, drive colon (+10 more)

## Knowledge Gaps
- **1 isolated node(s):** `f1-fantasy`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `load_rules()` connect `optimize` to `crosscheck.py`, `test_build_tables.py`, `test_scoring_gate.py`, `walkforward.py`, `pandas`, `test_community_pull.py`, `test_rolling.py`, `app.py`, `evaluate_seasons.py`, `dnf_probability`, `evaluate_overtakes.py`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `robust_mu()` connect `evaluate_seasons.py` to `optimize`, `walkforward.py`, `test_community_pull.py`, `test_rolling.py`, `dnf_probability`, `InfeasibleTeam`, `evaluate_overtakes.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `walkforward_strength()` connect `walkforward_strength` to `test_rolling.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **What connects `f1-fantasy` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `optimize` be split into smaller, more focused modules?**
  _Cohesion score 0.05714285714285714 - nodes in this community are weakly interconnected._
- **Should `crosscheck.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05352743561030235 - nodes in this community are weakly interconnected._
- **Should `test_build_tables.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10675990675990676 - nodes in this community are weakly interconnected._