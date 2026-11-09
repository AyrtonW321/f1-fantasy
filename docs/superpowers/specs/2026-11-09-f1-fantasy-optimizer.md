# F1 Fantasy Optimizer: Resolved Spec

Part 1 records decisions made while reviewing the original build spec. Where they differ, Part 1 wins. Part 2 is the original spec, verbatim.

# Part 1: Locked decisions

## Scope

- The plan covers all 7 phases. Phases 1-2 are the base and are planned at task level.
- Chips are excluded until Phase 6. Their effects get confirmed then.
- FastF1 lap ingest moves from Phase 1 to Phase 3, where its first reader exists. Phase 1 ingests fantasy data and Jolpica results only.

## Data sources

| Data | Source |
|---|---|
| 2023-2025 fantasy prices, points, breakdowns | TracingInsights/fantasy, pinned release, stored in the encrypted archive |
| 2026 and live prices and points | Official `fantasy.formula1.com/feeds/` JSON |
| Session breakdown inputs for the scoring gate, all seasons | TracingInsights `sessionResult` rows |
| Independent totals check | mzafram2001/f1-fantasy (MIT); mismatches reported, not fatal |
| Results, grids, schedules, lock times | Jolpica |

Measured facts:

- `price` on round r is the pre-lock price for round r. Usable as an input.
- `priceChange` on round r equals `price[r+1] - price[r]`: post-race data. Never read it. Derive changes from consecutive prices.
- TracingInsights `roundNumber` for 2023 runs one ahead of Jolpica from Monaco onward. Join on race slug; the canonical round is Jolpica's.
- 2026 slug differences: Jolpica `bahrain-grand-prix-in-malaysia` = TI `bahrain-grand-prix`; Jolpica `brazilian-grand-prix` = TI `sao-paulo-grand-prix`.
- TI driver `id` is team-prefixed (`RED_LAW`); canonical driver asset id is `abbreviation` (`LAW`), so a mid-season team move stays one asset. Canonical constructor id is TI `id`.
- Official 2026 constructor codes differ from TI in two cases: `RBR` = `RED`, `RBS` = `VRB`.
- Official 2026 gameday number equals `MeetingNumber` equals round.
- TI lists 2026 rows for unplayed rounds. A round is complete only when Jolpica has race results.
- A TI row can name a driver who did not take part (2026 Mexico: `TSU` under `VRB`, whose -5 is not in the team total). A constructor counts only drivers appearing in Jolpica's qualifying, sprint or race results for that weekend.

## Scoring (confirmed)

Same in all four seasons:

- Qualifying P1-10: 10, 9, 8, 7, 6, 5, 4, 3, 2, 1. NC -5.
- Sprint P1-8: 8, 7, 6, 5, 4, 3, 2, 1. +/-1 per position, +1 per overtake, fastest lap +5.
- Race P1-10: 25, 18, 15, 12, 10, 8, 6, 4, 2, 1. +/-1 per position, +1 per overtake, fastest lap +10, DOTD +10. NC -20.
- Constructor: sum of both drivers' scores excluding DOTD and using constructor DSQ values below.
- Qualifying teamwork: neither Q2 -1, one Q2 +1, both Q2 +3, one Q3 +5, both Q3 +10.
- Rank pit mode: fastest +10, 2nd +5, 3rd +3, summed.
- Time-band pit mode (per race, fastest stop): under 2.00s +20; 2.00-2.19 +10; 2.20-2.49 +5; 2.50-3.00 +2; over 3.00 0.

Season differences (`null` = never observed):

| Rule | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| Driver qualifying DSQ | -15 | -15 | -5 | -5 |
| Driver sprint NC | -20 | -20 | -20 | -10 |
| Driver sprint DSQ | null | null | null | -10 |
| Driver race DSQ | -25 | -25 | -20 | null |
| Constructor qualifying DSQ, per driver | -15 | -15 | -10 | -10 |
| Constructor sprint DSQ, per driver | null | null | null | -20 |
| Constructor race DSQ, per driver | -25 | -25 | -30 | null |
| Pit scoring | rank | rank | time bands | time bands |
| Overall fastest stop | null | null | +5 | +5 |
| World-record stop | null | null | null | null |

A `null` value raises an error if a session needs it. Never guess.

Three 2023 constructor rows show DSQ lines of -20 or -35; their totals only reconcile with -15 and -25. The table uses the values the totals prove.

## Transfers and team

| Rule | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| Starting budget | 100 | 100 | 100 | 100 |
| Drivers, constructors, boost | 5, 2, 2x | 5, 2, 2x | 5, 2, 2x | 5, 2, 2x |
| Free transfers per race | 2 | 2 | 2 | 2 |
| Carry 1 unused, max 3 | yes (assumed) | yes | yes | yes |
| Penalty per extra transfer | 4 | 10 | 10 | 10 |
| Net rule | no | no | no | yes |

2023 carry-over is unconfirmed by any source. `rules_2023.yaml` tags it `assumed`, and any 2023 report prints that.

Budget grows: `budget = bank + sum(current price of owned assets)`. Round 1 of each season starts at 100 with a free team.

## Scoring gate

- Feed breakdown inputs to `scoring.py`, require exact session totals on every completed session of all four seasons, sprints included.
- Targets: TI `sessionResult.totalPoints` for 2023-2025; official `QualifyingPoints`, `SprintPoints`, `RacePoints` for 2026.
- Compare session totals, not component lines.
- Separate check: Jolpica finish positions agree with fantasy rows.
- Tests are marked `data`. They skip visibly without `data/raw/`. With `REQUIRE_DATA=1` absence is a failure.

## Baseline

`mu = (sum(actual) + (5 - k) * prior) / 5`, where `k` is the asset's completed rounds this season (at most the latest 5).

`prior = price[r] * median(points / price)` over all assets and completed rounds this season. Round 1 uses `prior = price[r]`.

Same season only. Prior-season form is tested from Phase 5 and kept only if it beats baseline. Sprint weekends get no adjustment. Reports show totals overall and from round 5.

## Leakage

- Cutoff `lock_utc`: earliest of Qualifying, Sprint, SprintQualifying, SprintShootout start on the Jolpica schedule. This is conservative on sprint weekends, where the true lock could not be verified.
- Live mode uses the official feed's lock flags.
- `prices.known_at = lock_utc`. `fantasy_points.known_at = race start + 6 hours`.

## Learning

- Every past race is predicted using only pre-lock data and compared to actual points.
- Tune on 2023-2025. Score 2026 once as a final check, logging every evaluation in `reports/holdout_2026_log.md`. Refit on all four seasons for 2027.
- Price-based features learned across seasons stay relative within a season, such as price divided by that round's field average.

## Repo and tooling

- Public code repo at `OneDrive\Documents\Coding\f1-fantasy`, its own git repo, never nested in the home directory repo.
- One repo only: `AyrtonW321/f1-fantasy`, public. Plaintext `data/raw/` is gitignored. Raw data is committed only as one encrypted archive, `data/raw.tar.gz.enc`, using the OpenSSL CLI (AES-256-CBC, PBKDF2), so no Python dependency is added.
- Key is env var `F1_DATA_KEY`, kept in the user's password manager and as a GitHub Actions secret for Phase 7. It is never committed. Losing it loses the archive.
- The archive must stay under 95 MB. Each re-seal adds a full new blob to git history, so seal only after a real data change.
- `.venv` (via `UV_PROJECT_ENVIRONMENT`) and FastF1 cache live outside OneDrive.
- Committed tests use hand-written fixtures, never real rows.
- PuLP is the solver. Dependencies get added only in the phase that needs them.
- `config/model.yaml` starts with rolling window and backtest seasons only.

# Part 2: Original spec (verbatim)

# F1 Fantasy Optimizer: Build Spec

## Goal
Build a Python system that predicts fantasy points for every driver and constructor in the **official F1 Fantasy game** and picks the optimal team (5 drivers, 2 constructors, 1 DRS Boost, transfers, chips) under the budget cap. It must update automatically every race weekend.

Target: working backtest on 2023–2026 data, live for Round 1 of the 2027 season.

## Instructions for Claude Code
- Build in the phase order below. Do not start a phase until the previous phase's acceptance criteria pass.
- Python 3.11+. Use `uv` or `pip` with a `pyproject.toml`.
- Every feature row must carry a `known_at` timestamp. No feature may use data from after the lineup lock of the race it predicts. Add a test that enforces this.
- All game rules (scoring values, budget, free transfers, transfer penalty, chips) live in `config/rules_2026.yaml`. Never hard-code them.
- Before coding the rules config, ask me to confirm the current official scoring table and transfer rules (they changed in 2026). Do not guess values.
- Write tests with `pytest` for every module. Keep functions small and typed.
- Ask me before adding any dependency not listed below.

## Architecture (four layers)
1. **Strength model**: Kalman filter tracking car strength and driver skill, updated after every session.
2. **Event models**: probabilities for quali order, race order, DNF, positions gained, fastest lap, pit stop rank.
3. **Monte Carlo simulator**: simulates each weekend N = 10,000 times and scores each run with the official rules. Outputs a joint distribution of points for every asset.
4. **Optimizer**: integer linear program that selects the team maximizing expected points under constraints.

The ML models never pick the team. They produce point distributions; the optimizer picks.

## Data sources
| Source | Use |
|---|---|
| FastF1 | Lap timing for FP1–3, quali, sprint, race; tyres; stints; weather; pit stops |
| Jolpica API (Ergast replacement) | Historical results, grids, DNFs, standings |
| Official F1 Fantasy site | Prices, fantasy points per asset, ownership %. Scrape the JSON endpoints the site loads; fall back to a manual CSV template if scraping fails |
| Pit stop data | Fastest pit stop times and ranks per team |
| `data/static/tracks.csv` (hand-built) | Track type, overtaking difficulty, safety car rate, sprint flag |

Storage: Parquet in `data/processed/`, with tables `races`, `sessions`, `laps`, `results`, `prices`, `fantasy_points`, `features`.

## Training data windows
| Component | Window | Notes |
|---|---|---|
| Car pace | 2026 only | 2026 regulation reset. Use 2025 constructor order as a weak prior for the first 2–3 rounds only |
| Driver skill | Career, teammate-relative | Teammate gaps cancel out the car |
| Race dynamics (DNF, positions gained, safety car) | 2014–2026 | Add era flag: 2014–21, 2022–25, 2026+ |
| Fantasy prices and points | 2023+ | Earlier game rules differ |

Time-decay sample weights: `w = exp(-lambda * age_in_races)`, default half-life 10 races. Tune `lambda` in the backtest.

## Features (all pre-lock)
**Driver**: rolling teammate quali gap %, rolling race pace gap to teammate, rolling average positions gained, DNF/crash rate, track-type history.

**Constructor**: Kalman car strength, mechanical DNF rate, average pit stop time and rank, upgrade flag.

**Weekend**: FP2 long-run pace, corrected by fitting `lap_time = alpha + beta * lap_number + gamma_compound * tyre_age` per stint and using `alpha`; FP short-run gap to fastest; sprint flag.

**Context**: track overtaking difficulty, safety car probability, rain probability. Grid position only in post-quali models.

## Models

### Layer 1: Kalman strength model (`src/models/kalman.py`)
- Observation: `y[d,r] = theta_car[r] + phi_driver + tau_track + eps`, `eps ~ N(0, sigma^2)`
- Transition: `theta[r] = theta[r-1] + w`, `w ~ N(0, Q)`
- `phi_driver` uses a much smaller process noise than `theta_car`.
- Support a manual `Q` bump for big upgrade weekends and season starts.

### Layer 2: Event models
- **Plackett–Luce ranking** (`plackett_luce.py`): strength `s_d = exp(f(features))`, fit by maximum likelihood. Separate models for quali and race. Must support sampling full orders.
- **LightGBM LambdaRank** (`lgbm_rank.py`): same features, comparison model. Keep or ensemble based on backtest.
- **DNF** (`dnf.py`): logistic regression.
- **Positions gained / overtakes** (`poisson.py`): Poisson regression with track overtaking factor.
- **Fastest lap, Driver of the Day**: empirical frequencies conditioned on finishing position.
- **Pit stop rank**: empirical per-team distribution with recency weighting.

### Layer 3: Monte Carlo simulator (`src/sim/`)
Per simulation:
1. Sample quali order
2. Sample DNFs (Bernoulli per driver)
3. Sample race order conditioned on grid, apply DNFs
4. Sample overtakes, fastest lap, pit stop rank
5. Run `scoring.py` to get points for every asset

Sprint weekends: also simulate sprint quali and sprint.

Output per asset: mean, variance, and the full sample matrix (N x assets) so teammate and constructor correlations are preserved.

### Layer 4: Optimizer (`src/optimize/ilp.py`, PuLP or OR-Tools)
Binary variables: `x_i` (driver owned), `y_j` (constructor owned), `b_i` (driver boosted), `s_k` (asset k swapped in).

Objective:
```
max  sum_i mu_i x_i + sum_i mu_i b_i + sum_j mu_j y_j
     - P * max(0, T - F)
     + lambda_price * sum_k E[price_change_k] * owned_k
```
where `T = sum_k s_k`, `F` = free transfers, and `P` = transfer penalty (both from config).

Constraints:
- `sum_i x_i = 5`, `sum_j y_j = 2`, `sum_i b_i = 1`
- `b_i <= x_i`
- `sum cost * owned <= budget`
- `s_k >= owned_k - current_k` for all assets
- Linearize the `max(0, T - F)` term with an auxiliary variable `e >= T - F`, `e >= 0`

Extensions (Phase 6):
- **Rolling horizon** (`horizon.py`): optimize over the next k = 3 races jointly, commit only the current week, re-solve weekly.
- **Risk mode**: maximize P(score > rival score) over simulation scenarios with one binary win indicator per scenario.
- **Chip planner** (`chips.py`): estimate each chip's value at each remaining race from simulations, then solve an assignment problem (each chip once, at most one chip per race). Re-solve weekly.

### Layer 5: Price model (`src/models/price.py`)
Regress next price change on recent points-per-million and current price. Feed expected price change into the objective via `lambda_price`. Default schedule: high early season, decaying to near zero by the final rounds.

## Weekly update pipeline (`pipelines/weekly_update.py`)
| Trigger | Steps |
|---|---|
| Monday after race | Ingest results, prices, fantasy points; Kalman update; refit cheap models |
| Friday after FP2 | Ingest practice laps; compute long-run pace; rebuild weekend features; simulate; draft lineup |
| Before lineup lock | Final simulate and optimize; output team, boost, transfers, chip advice |
| Monthly / off-season | Full LightGBM retrain; retune `lambda` and `Q` via backtest |

Automate with GitHub Actions cron (`.github/workflows/cron.yml`). Output a markdown report to `reports/round_XX.md` with: recommended team, boost, transfers, chip advice, expected points with 10th/90th percentiles, and alternatives within 2 points of optimal.

## Validation (`src/backtest/`)
- Walk-forward only: for each race r, train on data before r, predict r. No random splits.
- Metrics: Spearman rank correlation (quali, race), MAE on fantasy points per asset, Brier score and calibration plot for DNF, total season fantasy score.
- Baseline: rolling 5-race average fantasy points fed into the same optimizer. Any model that does not beat the baseline in the backtest gets dropped.

## Repo structure
```
f1-fantasy/
  config/          rules_2026.yaml, model.yaml
  data/            raw/, processed/, static/
  src/
    ingest/        fastf1_pull.py, jolpica_pull.py, fantasy_scrape.py
    features/      pace.py, rolling.py, track.py
    models/        kalman.py, plackett_luce.py, lgbm_rank.py, dnf.py, poisson.py, price.py
    sim/           montecarlo.py, scoring.py
    optimize/      ilp.py, horizon.py, chips.py
    backtest/      walkforward.py, metrics.py
  pipelines/       weekly_update.py
  reports/
  tests/
  .github/workflows/cron.yml
```

## Dependencies
fastf1, requests, pandas, pyarrow, numpy, scipy, scikit-learn, lightgbm, statsmodels, pulp (or ortools), pyyaml, pytest, matplotlib.

## Build phases and acceptance criteria
1. **Ingest + scoring engine**
   - Pull 2023–2026 results and laps into Parquet.
   - `scoring.py` reproduces official fantasy points for at least 5 real 2026 races (including one sprint weekend) exactly.
2. **Baseline + optimizer**
   - Rolling-average predictions feed the ILP.
   - ILP returns a valid team for any round in under 2 seconds; tests cover budget, counts, boost, and transfer penalty.
3. **Pace extraction + Kalman**
   - FP2 long-run pace computed per driver per weekend.
   - Kalman car strength correlates with actual race order better than last-race order does.
4. **Event models + simulator**
   - Plackett–Luce, DNF, and Poisson models fit and sample.
   - Simulator outputs point distributions; simulated mean points are calibrated within reason against actuals.
5. **Backtest**
   - Walk-forward over 2023–2026 runs end to end.
   - Report compares full model vs baseline on every metric. Tune `lambda` and `Q`.
6. **Horizon, chips, price model, risk mode**
   - Each extension shows improvement over Phase 5 in the backtest or gets left disabled by default.
7. **Automation**
   - Cron pipeline runs end to end and writes `reports/round_XX.md`.

## Known pitfalls
- Leakage through post-lock data. Enforce `known_at`.
- Overfitting: about 24 races per season. Prefer low-parameter models.
- Teammate correlation: never treat assets as independent in the optimizer's risk calculations.
- Rain, red flags, and safety cars drive most variance. Model safety car probability per track.
- Rule changes each season: update the config, not the code.
