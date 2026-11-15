# F1 Fantasy Optimizer

A Python system that picks the best official F1 Fantasy team each round. It reproduces the game's scoring exactly for 2023-2026, predicts each driver's and constructor's points, and solves for the highest-scoring legal team under the budget, transfer and chip rules. A local Streamlit app shows every team you run, the recommended swaps and the chip plan.

Full walkthrough with every formula: [`docs/how-it-works.md`](docs/how-it-works.md).

## Contents

- [What it does](#what-it-does)
- [Design](#design)
- [The maths](#the-maths)
- [Results](#results)
- [Getting started](#getting-started)
- [Weekly routine](#weekly-routine)
- [Project layout](#project-layout)
- [Data and privacy](#data-and-privacy)
- [Limits](#limits)

## What it does

| Step | Output | Code |
|---|---|---|
| Collect data | Prices, session points, results, schedules for 2023-2026 | `src/ingest/` |
| Verify | Every official session score re-computed from the rules | `src/sim/scoring.py`, `src/ingest/crosscheck.py` |
| Predict | Expected points (`mu`) per asset for the next round | `src/features/rolling.py` |
| Optimize | Best team, 2x boost, transfers, penalty transfers | `src/optimize/ilp.py` |
| Plan chips | Which chip to play in which remaining round | `src/optimize/chips.py`, `chip_history.py` |
| Backtest | Season replay with no future data | `src/backtest/` |
| Use | App with all teams, swaps and chips; weekly report | `app.py`, `src/ui/`, `pipelines/weekly_update.py` |

## Design

### Principles

- **Rules in config, never in code.** Every point value, budget, transfer limit and chip lives in `config/rules_{season}.yaml`. A rule never observed is `null`, and using it raises `UnknownRuleError` instead of guessing.
- **Prove the data first.** The scoring engine must reproduce every official session total in 2023-2026 before any model is trusted.
- **No look-ahead.** Every row has a `known_at` time. Nothing used for a round may be known after that round's lock (start of the first competitive session). `assert_known_before_lock` fails closed on any violation.
- **Simple model wins.** A new prediction term is kept only if it beats the live predictor on both error and picked-team season total. Everything tried so far lost, so the live model is a single robust average.
- **Tune on the past, hold out the present.** Settings are tuned on earlier seasons; every evaluation on 2026 is logged.
- **The app holds no game logic.** `app.py` is layout; all calculations are in `src/ui/logic.py` and the modules above.

### Pipeline

```
official feeds, Jolpica, TracingInsights, mzafram
        │  src/ingest/*_pull.py, fantasy_scrape.py
        ▼
data/raw/  ──(vault seal)──►  data/raw.tar.gz.enc   (only form committed)
        │  pipelines/build_data.py
        ▼
data/processed/*.parquet   races · prices · fantasy_points · results · bonus · overtakes
        │  robust_mu  (+ leakage guard)
        ▼
expected points per asset
        │  ILP (PuLP + CBC)
        ▼
best team · boost · transfers · chip plan
        │
        ▼
Streamlit app (My Team · Best Teams · Update)   and   reports/round_{season}_{round}.md
```

### App

- **My Team**: one row per team file, showing the saved team as cards (constructors outlined in team colour, drivers filled with it, black or white text by luminance), price and expected points under each card, cost, bank, free transfers, total expected points and chip badges (gray = played, green ✓ = this weekend, white = left). Under each row: the recommended swaps (`OUT … → IN …`), alternatives, chip advice, an edit form and a past-swaps log.
- **Best Teams**: the top 10 teams overall for a chosen budget and excluded assets.
- **Update**: next lock, latest prices, unsealed files, and a button that runs the weekly update.

## The maths

### Scoring (2026)

| | Qualifying | Sprint | Race |
|---|---|---|---|
| Position points | P1-P10: 10 … 1 | P1-P8: 8 … 1 | P1-P10: 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 |
| Per position gained / overtake | – | +1 / +1 | +1 / +1 |
| Fastest lap | – | +5 | +10 |
| Driver of the Day | – | – | +10 |
| Not classified | -5 | -10 | -20 |

Constructors score both drivers' points (no DotD), plus qualifying teamwork (-1 to +10 by how many reach Q2/Q3) and pit-stop time bands (+20 under 2.00 s down to +2 under 3.01 s, +5 for the overall fastest stop). The boosted driver counts double. Each transfer beyond the free ones costs 10 points.

### Prediction: `robust_mu`

For each asset, using only earlier rounds of the same season known before the lock:

```
c   = trimmed mean of the asset's k past totals (drop 30% at each end)
m   = league median of total / price so far this season
mu  = (k · c + w · price · m) / (k + w),     w = 2.0
```

The trimmed mean ignores one-off crashes and lucky weekends. The price prior (`price · m`) covers round 1 and fades as rounds accumulate. Settings live in `config/model.yaml`.

### Optimization

Integer linear program, solved in about 0.2 s:

```
maximize   Σ mu_i·pick_i + (2 − 1)·Σ mu_i·boost_i − 10·e

subject to Σ pick (drivers) = 5,  Σ pick (constructors) = 2
           Σ boost = 1,  boost_i ≤ pick_i
           Σ price_i·pick_i ≤ bank + value of owned team
           s_i ≥ pick_i − owned_i
           e ≥ Σ s_i − free_transfers,   e ≥ 0
```

An extra transfer is taken only when it adds more than 10 expected points. Benched assets get `mu = −1000`. Next-best teams come from re-solving with a cut that forbids each team already found. Up to 1 unused free transfer carries over, capped at 3.

### Chips

| Chip | Valued by |
|---|---|
| Limitless | Re-solve with no budget cap; gain over the normal best |
| Wildcard | Re-solve with no transfer penalty |
| x3 Boost | For each driver, solve with that driver at 3x and the 2x elsewhere; keep the best |
| No Negative | Replay of earlier rounds: average points saved by flooring negative sessions at 0 |
| Autopilot | Replay: average of best driver's score minus boosted driver's score |
| Final Fix | Not valued (needs the qualifying result) |

The planner then assigns chips to rounds (each chip once, one per round) to maximize the total gain.

## Results

Walk-forward backtest, no chips, transfer rules applied:

| Season | Rolling-5 baseline | `robust_mu` | MAE (baseline / robust) |
|---|---:|---:|---:|
| 2023 | 6190 | 5625 | 12.26 / 11.99 |
| 2024 | 4561 | 4548 | 11.55 / 11.65 |
| 2025 | 4558 | 4657 | 13.65 / 13.13 |
| 2026 | 4269 | 4363 | 14.36 / 13.47 |

`robust_mu` has the better rank correlation every season and the lower error in 3 of 4. Models tried and rejected (all lost on 2026 season total vs 4363): Monte Carlo race simulator (4362), simulated qualifying (4136), overtakes term (4252), sprint term (4336), bonus term (4330), recency weighting, multi-round transfer planning, and a previous-season prior for round 1. Reports are in `reports/`.

## Getting started

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/), the OpenSSL CLI (for the data archive).

```bash
uv sync
```

```bash
uv run pytest -q
```

Tests that need real data are skipped when `data/raw` is absent. To unpack the data (needs the key):

```bash
F1_DATA_KEY=... uv run python -m src.ingest.vault unseal
```

```bash
uv run python pipelines/build_data.py
```

Create a team file from the template:

```bash
cp config/my_team.example.yaml config/my_team_1.yaml
```

Start the app (or double-click `F1 Fantasy.bat` on Windows):

```bash
uv run streamlit run app.py
```

## Weekly routine

1. Before the lock, press **Update data** in the app, or run:

   ```bash
   uv run python -m pipelines.weekly_update --force
   ```

2. On **My Team**, pick the chip and the suggested team for each row.
3. Make the same transfers in the official game.
4. Press **I made these transfers** so the team file, bank, free transfers, chips and history are updated.

Command-line equivalents: `uv run python pipelines/pick_team.py --team 1` and `uv run python pipelines/plan_chips.py --team 1`.

## Project layout

```
app.py              Streamlit app (layout only)
config/             rules_{season}.yaml, model.yaml, team_colors.yaml, my_team_*.yaml
data/               raw.tar.gz.enc (committed); raw/ and processed/ (gitignored)
docs/               how-it-works.md, decisions.md, known-issues.md, progress.md, specs and plans
pipelines/          build_data, pick_team, plan_chips, weekly_update, evaluate_*
reports/            backtest and phase reports, weekly round reports
src/ingest/         downloads, table builder, scoring gate, encrypted vault
src/sim/            scoring engine; Monte Carlo simulator (research)
src/features/       robust_mu, leakage guard, research features
src/models/         Plackett-Luce, Kalman, DNF, Poisson, bonus (research)
src/optimize/       ILP optimizer, chip valuation
src/backtest/       walk-forward backtest, metrics
src/ui/             app logic, HTML cards, team colours
tests/              pytest suite
```

## Data and privacy

- Sources: official F1 Fantasy feeds, [Jolpica](https://github.com/jolpica/jolpica-f1), [TracingInsights](https://github.com/TracingInsights), mzafram, FastF1.
- TracingInsights data has no licence, so raw data is committed only as `data/raw.tar.gz.enc` (AES-256-CBC, PBKDF2 with 600,000 iterations). The key is read only from `F1_DATA_KEY`.
- Team files, history and round reports stay out of git so picks are not published.

## Limits

- `robust_mu` weights the whole season equally, so it reacts slowly to a driver's recent upturn.
- The optimizer plans one round at a time and does not forecast price changes.
- Final Fix is not valued; chip-to-round assignment is mostly a tie-break.
- Chip rules are confirmed for 2026 only; `rules_2027.yaml` is not written yet.

More in [`docs/known-issues.md`](docs/known-issues.md) and [`docs/decisions.md`](docs/decisions.md).
