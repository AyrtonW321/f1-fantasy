# Phase 4 Plan: Event Models and Fantasy Simulator

**Status:** Revised after grilling (2026-11-10). The revision below overrides the draft text that follows it.

## Revision 2026-11-10 (overrides the draft)

- **Goal:** the best team each weekend, judged on typical points per weekend. One or two big weekends must not drive picks: use robust form (a trimmed mean, shrunk toward the price prior).
- **Data:** 2026 only, for fitting and tuning. The 2023-2025 scoring tests stay. This replaces the "tune 2023-2025, hold out 2026" rule for Phase 4.
- **Evaluation:** walk-forward over every completed 2026 round. Tune settings on rounds 1-10 only, then report across all rounds.
- **Acceptance:** must beat the Phase 2 rolling-5 baseline in the 2026 walk-forward on both per-asset MAE (points per weekend) and season total.
- **Order:** incremental. (1) A Vegas-ready base: robust 2026 form fed into the existing optimizer with the real team from `config/my_team.yaml`. (2) Then race order plus DNF, qualifying, overtakes, sprints and bonuses, each kept only if the backtest improves.
- **Deadline:** pick the Las Vegas team before lock at 2026-11-21 04:00 UTC. Freeze on Nov 20 with the best version that passed.
- **Team state:** `config/my_team.yaml` (gitignored) holds owned assets, bank and free transfers; the user updates it each round. 2027 starts fresh.
- **Chips:** the user has chips left and wants timing advice. 2026 chip rules confirmed by the user and stored in `config/rules_2026.yaml` (`chips`); 2023-2025 chip values are null.
- **Pace:** not used in Phase 4 (cross-driver comparability unresolved).

## Revised task list (2026-11-10)

Every task: 2026 data only, walk-forward, settings tuned on rounds 1-10, kept only if it beats the current best on both 2026 per-asset MAE and season total. Freeze on Nov 20 with the best passing version.

| # | Task | Files | Done when | Status |
|---|---|---|---|---|
| 4.1 | Vegas-ready base: robust form | `src/features/rolling.py` (`robust_mu`), `pipelines/evaluate_form.py`, `pipelines/pick_team.py`, `config/model.yaml` (`form`), `config/my_team.example.yaml` | Beats rolling-5 on MAE and total | Done: MAE 13.47 vs 14.36, total 4363 vs 4269 (trim 0.3, prior weight 2.0) |
| 4.2 | Race order + DNF simulator | `src/models/plackett_luce.py`, `src/models/dnf.py`, `src/sim/montecarlo.py`, `pipelines/evaluate_sim.py`, tests | Simulated expected points beat 4.1 on MAE and total; fixed seed reproduces; samples scored by `src/sim/scoring.py` | Built, disabled: MAE 13.56 vs 13.47, total 4362 vs 4363 (does not beat 4.1). Best DNF shrink at grid edge (200), so per-driver DNF adds nothing over the field rate. 0.35 s/round at 2000 draws |
| 4.3 | Chip planner | `src/optimize/chips.py`, `pipelines/plan_chips.py` | Advises which chip (if any) to play in each of rounds 21-23 from the user's remaining chips; uses `chips` rules | Built (ChatGPT), runs on the example team. Rounds 22-23 use round 21 prices as a proxy. Real advice awaits `my_team.yaml` with `chips_left` |
| 4.4 | Qualifying order | `sim_mu(quali=True)` in `src/sim/montecarlo.py`, `pipelines/evaluate_quali.py`, `reports/phase4_quali.md` | Beats 4.2 | Built, disabled: MAE 13.49 vs 13.56 (4.2) and 13.47 (4.1), but total 4136 vs 4362 (4.2) and 4363 (4.1). Qualifying order feeds the race order as a grid feature and scores qualifying points plus Q2/Q3 teamwork; the total drops, so it does not beat 4.2 |
| 4.5 | Overtakes and positions gained (race session only) | `src/models/poisson.py`, `data/processed/overtakes.parquet` (from TI `raceOvertakes`, `racePositionsGained`, 2023-2026), predictor `overtakes_mu` in `src/features/overtakes.py`, `pipelines/evaluate_overtakes.py`, `reports/phase4_overtakes.md`, test | Gate 1 (rounds 11-20): Poisson overtakes beat flat field mean on deviance, shrunk gained mean beats flat zero; failing parts drop out. Gate 2: surviving term added to the non-event form beats 4.1 on 2026 MAE and season total, tuned on rounds 1-10 | Planned. Overtakes: Poisson regression on shrunk driver mean (2026 only) + track overtaking difficulty (coefficient fitted on 2023-2025, documented exception to 2026-only). Gained can be negative, so a shrunk per-driver mean, not Poisson. Expected values only, no per-draw samples. Sprint session not covered here |
| 4.6 | Sprint weekends (backtest only) | predictor `sprint_mu` in `src/features/sprint.py`, `pipelines/evaluate_sprint.py`, `reports/phase4_sprint.md`, test | Beats previous best (4.5 if it passed, else 4.1) on MAE and total over all 6 sprint rounds (2, 4, 5, 9, 12, 17); all-rounds MAE and total no worse than 4.1; one shrink weight tuned on rounds 1-10; rounds 12 and 17 reported separately as anecdotal | Planned. Base form = `robust_mu` on `total - sprint` every round; on sprint rounds add a per-asset whole-session sprint mean shrunk toward the field mean (no Poisson). No sprint left in 2026, so a pass only enables it for 2027 sprints. Run after 4.5, stacked on the best passing version |
| 4.7 | Bonus events (fastest lap, DotD, pit stops) | `data/processed/bonus.parquet` (built in `pipelines/build_data.py` via `ti_lines.bonus_points`), `bonus_mu` in `src/features/rolling.py`, `pipelines/evaluate_bonus.py` | Beats previous best | Built, disabled: trimmed non-bonus form + shrunk bonus mean scores MAE 13.50 vs 13.47 and total 4330 vs 4363 (better on tuning rounds 1-10 only, 14.42 vs 14.53). Expected values only; ChatGPT's per-draw samplers in `src/models/bonus.py` kept for Phase 6 risk mode. `reports/phase4_bonus.md` |
| 4.8 | Freeze and Las Vegas pick | `pipelines/pick_team.py` | Team, boost, transfers and chip advice printed before 2026-11-21 04:00 UTC | Pending |
**Scope:** Low-parameter qualifying, race, sprint, DNF, positions-gained, and bonus-event models; Monte Carlo point simulation using the existing season-specific scoring engine.
**Prerequisites:** Phase 1-2 scoring/optimizer work is recorded as passing. Phase 3 has complete explicit pace/status coverage for 2025-2026 and a Kalman result above the last-race-order baseline. Pace is optional: the 149 `no_usable_longrun` entrant/weekend rows remain missing and must not be imputed.

## Goals and boundaries

- Produce pre-lock event outcome distributions for 2023-2026 races using only information available at the prediction cutoff.
- Fit full-order models for qualifying and race finishing order; produce DNF probabilities, positions-gained/overtake distributions, and empirical models for bonus events.
- Simulate normal and sprint weekends, apply the existing official rules for each season, and retain joint samples so teammate and constructor outcomes remain correlated.
- Keep the existing optimizer unchanged. This phase supplies its expected-points distributions; full backtest/tuning remains Phase 5.
- Do not forecast fantasy prices, chips, transfer horizons, weather using post-lock observations, or operational automation in this phase.

## Data and timing contracts

- Canonical entrants, constructors, sessions, rounds, and results come from normalized project tables. Use Jolpica race and qualifying results; use official fantasy scoring sources only for points/rule validation, not as model predictors for the same event.
- Detailed FastF1 practice data remains limited to 2025-2026. Fit pace models only from usable FP2 rows with `known_at <= lock_utc`; missing pace remains null with a status feature. Do not substitute FP1, qualifying, or synthetic pace.
- All event predictors must have an auditable `known_at` no later than the modeled lock. Race/grid results and post-race status can be labels only for the event being predicted.
- Fit and tune on rolling history through 2025. Freeze the primary configuration before reporting any 2026 holdout result. Final 2027 refit is outside this phase.
- Missing starts, reserve-driver transitions, constructor changes, and unavailable historical fields must be explicit. No silent row dropping to improve metrics.

## Task 1: Event-model input and feature contract

**Files:**
- Create `src/features/event.py` (or split by a deep interface discovered during implementation).
- Create `reports/phase4_data_audit.md` for aggregate source/coverage findings.

**Work:**
- Inventory which normalized tables support qualifying order, race order, DNF/classification, positions gained, overtakes, fastest lap, Driver of the Day, sprint order, and constructor pit performance.
- Define immutable feature rows keyed by season, round, session, and entrant, including `known_at` and explicit availability/status fields.
- Build only pre-lock predictors: prior Kalman strength, prior driver form/teammate gap, track metadata and prior safety-car rate, sprint/session context, and usable FP2 pace when available.
- Document whether each label has enough reliable historical coverage before fitting. Treat unavailable source fields as unavailable, not zero.

**Checks:**
- Each feature has a source and timestamp; the existing leakage guard rejects any feature known after lock.
- All rows use canonical season/round/entrant keys and do not duplicate entrants within a session.

## Task 2: Qualifying and race order models

**Files:**
- Create `src/models/plackett_luce.py`.
- Add `tests/test_plackett_luce.py`.

**Work:**
- Fit separate low-parameter Plackett-Luce models for qualifying and race order, using regularized entrant strengths derived from the feature contract.
- Sample complete finishing orders without replacement. Race-order modeling must state whether the target is classified finish order or all starters, and handle DNFs consistently with Task 3.
- Keep any LambdaRank comparison as a separately reported challenger; add LightGBM only if an auditable walk-forward comparison justifies its dependency and complexity.

**Checks:**
- Samples contain every eligible entrant exactly once, respect deterministic seeds, and produce sensible probabilities for synthetic strength orderings.
- Compare walk-forward Spearman and log likelihood against a simple last-session / prior-season baseline on matching entrant sets.

## Task 3: DNF, gained-position, and bonus models

**Files:**
- Create `src/models/dnf.py` and `src/models/poisson.py` (or a smaller shared interface if sources require it).
- Add focused tests for each model.

**Work:**
- Fit a regularized logistic DNF model from pre-lock features and historical labels; model season, constructor, driver, track, and prior pace/strength only where available without leakage.
- Fit a low-parameter count model for gained positions/overtakes with track difficulty. Preserve negative positions gained as a distinct quantity; do not turn net position change into a fabricated overtake count.
- Estimate fastest-lap and Driver-of-the-Day outcomes empirically conditional on available pre-lock context and race result simulation state.
- Inventory pit-stop-rank sources. Add a team-level recency-weighted empirical distribution only if the normalized source supports reliable, comparable stop times; otherwise emit an explicit unsupported status and omit its bonus contribution rather than guessing.

**Checks:**
- DNF probabilities are bounded and calibrated with walk-forward Brier/log-loss metrics.
- Count outcomes are nonnegative, overdispersion is checked, and positions-gained sampling respects start/finish position constraints.
- Bonus samplers return only valid outcomes and document sparse-sample fallbacks.

## Task 4: Joint weekend Monte Carlo simulator

**Files:**
- Create `src/sim/montecarlo.py`.
- Add `tests/test_montecarlo.py`.

**Work:**
- Sample qualifying order, sprint qualifying/sprint when scheduled, race DNFs, race order conditioned on grid and survival, and supported bonus outcomes.
- Score every sample through `src/sim/scoring.py` using the correct season rules. Preserve common scenario IDs across drivers and constructors so team totals and correlations can be calculated from the same simulation draw.
- Return per-asset sample arrays plus mean, variance, and selected quantiles; make simulation count and random seed explicit. Support the planned 10,000-draw default after a runtime check.
- Keep lineup optimization outside the simulator.

**Checks:**
- Every simulated score matches the scoring engine for a hand-constructed event fixture.
- Constructors are scored from their actual simulated driver lines and supported constructor events.
- Sprint and non-sprint event shapes both work, and fixed seeds reproduce identical samples.
- Runtime is measured on a representative season weekend; do not trade away joint samples for speed without documenting the consequence.

## Task 5: Calibration and Phase 4 acceptance

- Run strictly walk-forward predictions on 2023-2025 for development. Freeze model choices before a single 2026 holdout evaluation.
- Report coverage by model/target and entrant, qualifying/race rank correlation, DNF Brier score and calibration, count-model error, and simulated asset-point MAE/calibration against official outcomes.
- Compare against simple baselines on identical races and entrant sets. Report uncertainty and missing-feature coverage; do not silently exclude difficult weekends.
- Phase 4 acceptance: each supported event model fits and samples; simulator produces season-rule-correct joint point samples for sprint and non-sprint fixtures; walk-forward calibration report is written; no feature leaks beyond lock. Unsupported bonus sources are explicitly disabled with coverage stated.
- If a model fails to beat its baseline or is poorly calibrated, keep it disabled by default and report the failure rather than forcing an ensemble.

## Execution order and review gates

1. User reviews and approves this task-level plan before code implementation.
2. Audit sources and feature availability first; finalize model targets from available data.
3. Implement features and individual samplers, then the joint simulator and calibration report.
4. Do not change optimizer, chip, horizon, or price-forecast behavior in this phase.
5. Do not commit or push without user approval. Never commit plaintext raw data or secrets.
