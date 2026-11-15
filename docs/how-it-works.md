# How the program works

This document follows one round from raw data to the team you field. It covers every stage, the maths at each one, and where the code lives. Open problems are in `docs/known-issues.md`; the reasons behind each choice are in `docs/decisions.md`.

## The idea in one paragraph

Every F1 Fantasy round you own 5 drivers and 2 constructors under a budget. Each one scores points from qualifying, the sprint (on sprint weekends) and the race. The program:

1. downloads every result, price and official fantasy score;
2. re-scores them with the official rules to prove the data is right;
3. estimates how many points each driver and constructor will score next round (`mu`);
4. solves for the legal team with the highest expected total, counting the 2x boost and transfer penalties;
5. values the chips and suggests when to play them;
6. shows all of it in a local app where you record the transfers you made.

```
sources ──► data/raw ──► data/processed/*.parquet ──► robust_mu ──► ILP optimizer ──► app / weekly report
(official,     (encrypted     (races, prices,             (expected      (best team,        (My Team,
 Jolpica,       in git as      fantasy_points,             points per     boost,             Best Teams,
 TracingIns.,   .enc)          results, bonus)             asset)         transfers, chips)  Update)
 mzafram)
```

## 1. Data

### Sources

| Source | What it gives | Code |
|---|---|---|
| Official F1 Fantasy feeds | 2026 and live prices, per-session fantasy points, player list | `src/ingest/fantasy_scrape.py` |
| Jolpica (Ergast-compatible API) | Schedules, session times, results, grid, status | `src/ingest/jolpica_pull.py` |
| TracingInsights (pinned GitHub release) | 2023-2025 prices and points; per-session detail (overtakes, positions gained, fastest lap, Driver of the Day, pit times) | `src/ingest/community_pull.py`, `src/ingest/ti_lines.py` |
| mzafram | Round fantasy totals, used only as a cross-check | `src/ingest/community_pull.py`, `src/ingest/crosscheck.py` |
| FastF1 (2025-2026) | Laps, weather, track status for pace research | `src/ingest/fastf1_pull.py` |

### Storage and privacy

- Raw downloads live in `data/raw/` (gitignored). TracingInsights has no licence, so plaintext data never enters git.
- `src/ingest/vault.py` seals `data/raw/` into `data/raw.tar.gz.enc` with the OpenSSL CLI (AES-256-CBC, PBKDF2, 600,000 iterations). The key comes only from the `F1_DATA_KEY` environment variable and is passed to OpenSSL through the child process environment, never on a command line or in a log. Plaintext during seal/unseal stays in the system temp folder.
- `uv run python -m src.ingest.vault unseal` restores `data/raw/`; `seal` writes a new archive.

### Tables

`pipelines/build_data.py` turns raw files into Parquet tables in `data/processed/` (`src/ingest/build_tables.py`):

| Table | One row per | Key columns |
|---|---|---|
| `races` | season, round | `slug`, `sprint`, `lock_utc`, `race_utc`, `completed` |
| `prices` | season, round, asset | `price`, `active`, `known_at` |
| `fantasy_points` | season, round, asset (completed rounds) | `qualifying`, `sprint`, `race`, `total`, `known_at` |
| `results` | season, round, session, driver | `constructor_id`, `position`, `grid`, `status` |
| `price_changes` | season, round, asset | change versus the previous round's snapshot |
| `bonus` | season, round, asset (2026) | fastest lap, DotD and pit-stop points |
| `overtakes` | season, round, driver | `overtakes`, `gained` |

An "asset" is a driver (three-letter code, e.g. `VER`) or a constructor (code, e.g. `RED`).

### No look-ahead: `known_at` and `lock_utc`

Every row records when it became known:

- `lock_utc` = start of the weekend's first competitive session (qualifying, or sprint qualifying on sprint weekends). Team changes close then.
- Prices for a round: `known_at = lock_utc` of that round (the pre-lock snapshot).
- Points and results: `known_at = race_utc + 6 hours`.
- Price changes are computed from consecutive snapshots only. TracingInsights' `priceChange` field is never read, because it is filled after the race.

`src/features/guard.py` (`assert_known_before_lock`) checks every predictor output: any row whose `known_at` is later than the round's lock, or missing, raises `LeakageError`. It fails closed: a missing value counts as a leak.

## 2. Scoring engine

`src/sim/scoring.py` reproduces the official scoring. All numbers come from `config/rules_{season}.yaml`; none are in code. A rule that was never observed is `null`, and using it raises `UnknownRuleError` instead of guessing.

### 2026 driver points

| Session | Finish position points | Other |
|---|---|---|
| Qualifying | P1-P10: 10, 9, 8, 7, 6, 5, 4, 3, 2, 1 | Not classified or DSQ: -5 |
| Sprint | P1-P8: 8, 7, 6, 5, 4, 3, 2, 1 | +1 per position gained, +1 per overtake, fastest lap +5, not classified or DSQ -10 |
| Race | P1-P10: 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 | +1 per position gained, +1 per overtake, fastest lap +10, Driver of the Day +10, not classified -20 |

Positions gained is net, so positions lost score negative.

### 2026 constructor points

A constructor scores the sum of its two drivers' session points, except Driver of the Day (driver only), plus:

- **Qualifying teamwork**: neither driver in Q2 -1, one in Q2 +1, both in Q2 +3, one in Q3 +5, both in Q3 +10.
- **Fastest pit stop (race)**, by time band: under 2.00 s +20, under 2.20 s +10, under 2.50 s +5, under 3.01 s +2, otherwise 0. Overall fastest stop of the race +5.
- **DSQ**: qualifying -10, sprint -20.

### Worked example

A driver qualifies P3 (+8), finishes the race P2 from P5 (+18, +3 gained), makes 2 overtakes (+2) and wins Driver of the Day (+10): 8 + 18 + 3 + 2 + 10 = **41**. Their constructor gets the same position, gained and overtake points (not DotD) from both drivers, plus teamwork and pit-stop points.

### Team score

- Sum of the 7 assets' totals.
- The boosted driver counts twice (`boost_multiplier: 2`), so the boost adds that driver's score once more.
- Each transfer beyond the free ones costs 10 points.

### The scoring gate

`src/ingest/crosscheck.py` (`gate_mismatches`) re-scores every row of every completed session in 2023-2026 with the engine and compares it with the official session total. The gate passes on all four seasons. One known source inconsistency (2025 Spanish GP race, Aston Martin) is pinned in `tests/test_scoring_gate.py`. The mzafram totals are a second, report-only cross-check.

## 3. Prediction: `robust_mu`

`src/features/rolling.py`. For each asset, `mu` is its expected total points next round.

### Formula

For asset *a* before round *r* of season *s*:

1. Take every earlier round of the same season known before the lock: totals x₁ … x_k.
2. **Trimmed mean** `c`: sort the k totals and drop `floor(k × 0.3)` from each end, then average the rest. One crash or one lucky weekend barely moves it.
3. **Price prior**: `m` is the league median of `total / price` over all priced history rows of the season so far. The prior for the asset is `price × m`, the points a typical asset at that price scores.
4. **Shrink** the trimmed mean toward the prior with weight `w = 2.0`:

```
mu = (k × c + w × price × m) / (k + w)
```

With no history (round 1, k = 0) `mu` is the price prior. After 2 rounds the prior still has half the weight; after 20 rounds about a tenth.

### Example

An asset priced 20.0 with m = 0.9 has prior 18. With k = 10 rounds whose trimmed mean is 24: mu = (10 × 24 + 2 × 18) / 12 = **23.0**.

### Settings

`config/model.yaml`: `form: {trim: 0.3, prior_weight: 2.0}`. Tuned on 2026 rounds 1-10 by MAE, then re-checked on 2023-2025, where it gave the highest combined points (14830).

### What was tried and lost

Every candidate had to beat `robust_mu` on both MAE and the season's picked-team total. None did:

| Attempt | Code | 2026 total vs 4363 |
|---|---|---|
| Rolling-5 mean with price prior (Phase 2 baseline) | `baseline_mu` | 4269 |
| Monte Carlo race simulator (Plackett-Luce order + DNF model) | `src/sim/montecarlo.py`, `src/models/` | 4362 |
| Simulated qualifying | same | 4136 |
| Overtakes term | `src/features/overtakes.py` | 4252 |
| Sprint term | `src/features/sprint.py` | 4336 |
| Separate bonus term (fastest lap, DotD, pit) | `bonus_mu` | 4330 |
| Recency weighting (h = 3, 5, 8) | prototype | lost on 2023-2025 |
| Multi-round transfer planning | prototype | identical to single-round |

Why they lose: extra terms pull the top assets toward the field average, and the optimizer mostly picks top assets. A Kalman filter for car, driver and track strength (`src/models/kalman.py`) and FP2 long-run pace (`src/features/pace.py`) were built as research; neither feeds the picks.

## 4. Optimizer

`src/optimize/ilp.py` solves an integer linear program with PuLP and its bundled CBC solver (~30 assets, about 0.2 s per solve).

### Variables

- `pick_i ∈ {0,1}`: asset *i* is in the team.
- `boost_i ∈ {0,1}`: driver *i* gets the 2x boost.
- `s_i ∈ {0,1}`: asset *i* is bought this round (only when a current team is given).
- `e ≥ 0`: transfers beyond the free ones.

### Objective

```
maximize  Σ mu_i · pick_i  +  (boost_multiplier − 1) · Σ mu_i · boost_i  −  penalty · e
```

### Constraints

```
Σ pick_i over drivers      = 5
Σ pick_i over constructors = 2
Σ boost_i                  = 1,   boost_i ≤ pick_i
Σ price_i · pick_i         ≤ budget         (in integer tenths, so 100.0 is exact)
s_i ≥ pick_i − owned_i                       (bought = picked and not owned)
e   ≥ Σ s_i − free_transfers
```

- **Budget** = bank + current value of the team you own, at this round's prices. Price rises on your assets raise your budget, as in the game.
- **Penalty transfers**: each one costs 10 points inside the same objective, so an extra transfer happens only when the incoming asset adds more than 10 expected points over what it replaces.
- **Excluded assets** (benched drivers, from a team file's `exclude` list) get `mu = −1000`, so they are sold and never bought.
- **Next-best teams**: each found team is forbidden with a cut `Σ pick over that team ≤ 6`, then the model is solved again. This gives the top 5 (My Team) or top 10 (Best Teams).

### Free transfers after the round

`next_state`: unused free transfers carry over, at most 1 (`carry_max`), and the total never exceeds 3 (`max_free`). Base is 2 per round. Bank after the round = budget − cost.

## 5. Chips

Each chip can be played once per season, at most one per round (`config/rules_2026.yaml`). `src/optimize/chips.py` estimates each chip's gain for each remaining round; `plan_chips` then tries every assignment of chips to rounds and keeps the one with the highest total gain.

| Chip | Effect | How its value is estimated |
|---|---|---|
| `limitless` | No budget cap and unlimited transfers for one round; the team reverts next round | Re-solve with the budget set to the price of every asset; gain = new best − normal best |
| `wildcard` | Unlimited free transfers, budget cap stays | Re-solve with the penalty set to 0 |
| `x3_boost` | One driver scores 3x, another keeps the normal 2x | For each driver: give it `mu × 3`, forbid the 2x on it, solve; keep the best |
| `no_negative` | Any negative session score counts as 0 | Replay: average points the chip would have saved on your fielded team in earlier rounds |
| `autopilot` | 2x goes to your highest-scoring driver after the fact | Replay: average of (best driver's score − boosted driver's score) in earlier rounds |
| `final_fix` | One driver swap after qualifying | Not valued; needs the qualifying result. Decide after qualifying |

The replay (`src/optimize/chip_history.py`) uses the same season's completed rounds, keeps sprint and normal weekends apart when there are at least 2 of the same kind, and adds the previous season when fewer than 3 rounds are done.

## 6. Backtest

`src/backtest/walkforward.py` replays a season round by round with no knowledge of the future:

1. predict `mu` with data known before that round's lock;
2. optimize the team from the previous round's state;
3. score the chosen team with the actual points (boost and penalties applied);
4. carry the state (owned team, bank, free transfers) forward.

`src/backtest/metrics.py` reports MAE of `mu` against actual totals, the season total, the total from round 5, the rounds 1-4 total and the mean per-round Spearman rank correlation.

Tuning rules: tune on past seasons, hold 2026 out, and log every 2026 evaluation in `reports/holdout_2026_log.md`.

### Results (no chips)

| Season | Rolling-5 total | `robust_mu` total | MAE (rolling-5 / robust) | Spearman (rolling-5 / robust) |
|---|---:|---:|---:|---:|
| 2023 | 6190 | 5625 | 12.26 / 11.99 | 0.625 / 0.639 |
| 2024 | 4561 | 4548 | 11.55 / 11.65 | 0.687 / 0.715 |
| 2025 | 4558 | 4657 | 13.65 / 13.13 | 0.584 / 0.622 |
| 2026 | 4269 | 4363 | 14.36 / 13.47 | 0.663 / 0.687 |

`robust_mu` wins Spearman in every season and MAE in 3 of 4. It loses the 2023 total by 565 points; that season is treated as an outlier and `robust_mu` was kept. Detailed reports: `reports/phase5_backtest.md`, `reports/phase5_seasons.md`, `reports/baseline_{season}.md`.

## 7. Weekly use

### Team files

One file per team: `config/my_team_1.yaml`, `my_team_2.yaml`, … (gitignored; template `config/my_team.example.yaml`):

```yaml
exclude: []            # benched assets, e.g. [HIR]
drivers: [VER, NOR, PIA, HAD, BEA]
constructors: [MCL, VRB]
bank: 0.0              # unspent money, millions
free_transfers: 2
chips_left: [limitless, wildcard, x3_boost, no_negative, autopilot, final_fix]
```

### Weekly update

`uv run python -m pipelines.weekly_update --force` (or **Update data** in the app):

1. snapshot the official feeds, Jolpica, the newest TracingInsights tag and mzafram;
2. rebuild the tables;
3. for each team file, run `pipelines/pick_team.py` and `pipelines/plan_chips.py`;
4. write `reports/round_{season}_{round}.md` with checks: stale team files, missing prices, unsealed raw files.

Without `--force` it runs only when the next lock is under 48 hours away and no good report exists. A failed step writes a `FAILED at <step>` report; the full trace goes to `reports/weekly_update.log`.

## 8. The app

Start with `F1 Fantasy.bat` or `uv run streamlit run app.py` from the project folder. `app.py` holds only layout; logic is in `src/ui/logic.py`, HTML cards in `src/ui/cards.py`, colours in `src/ui/style.py` and `config/team_colors.yaml`.

### My Team tab

One row per team file:

| Team | CR | x2 | DR | $ | xPts | Chips |
|---|---|---|---|---|---|---|
| name | 2 constructor cards | boosted driver | 4 other drivers | cost, bank, free transfers | expected points | chip badges |

- **Cards**: drivers are filled with their team colour; constructors are outlined in it. Text is black or white by WCAG relative luminance (`L = 0.2126 R + 0.7152 G + 0.0722 B` on linearised RGB; white when L < 0.4). Each card shows price, then `mu`. A driver's team is taken from their latest result; drivers with none are grey.
- **xPts** for the saved team = Σ mu + mu of the best driver (the 2x). With `x3_boost`, the best driver gets 3x and the second best 2x. It matches the optimizer for a team with no transfers.
- **Chip badges**: gray and struck through = played earlier; green with ✓ = this weekend's chip; white = still available. The selector defaults to the chip advice; once you log the round it locks.
- **Swap strip** under the row: `OUT … → IN …` for the selected choice, then its lineup, cost and xPts.
- **Expanders**: Alternatives (top 5, "Use #n" and "I made these transfers"), Chip advice (recompute), Edit team (validated form), Past swaps (per-round log and a points timeline).

"I made these transfers" writes the new team file (backup in `config/backup/`), updates bank, free transfers and chips, and appends a row to `config/history/team_{n}.csv`. A chip whose team reverts next round (limitless) keeps the old team and bank.

### Best Teams tab

The top 10 teams with no transfer limits, under a budget (default 100) and minus excluded assets, set in the Filters popover.

### Update tab

Next round, lock time, latest price round and unsealed file count as tiles, plus the **Update data** button with streamed output.

## 9. Code map

| Folder | Contents |
|---|---|
| `config/` | `rules_{season}.yaml`, `model.yaml`, `team_colors.yaml`, team files |
| `src/ingest/` | Downloads, table builder, scoring gate, encrypted vault |
| `src/sim/` | Scoring engine, Monte Carlo simulator (research) |
| `src/features/` | `robust_mu` and research features, leakage guard |
| `src/models/` | Plackett-Luce, Kalman, DNF, Poisson, bonus (research) |
| `src/optimize/` | ILP optimizer, chip valuation and replay |
| `src/backtest/` | Walk-forward backtest and metrics |
| `src/ui/` | App logic, HTML cards, colours |
| `pipelines/` | Command-line entry points (build, pick, plan chips, weekly update, evaluations) |
| `tests/` | pytest suite; tests needing real data are skipped without it |
| `reports/` | Backtest and phase reports, weekly round reports |
