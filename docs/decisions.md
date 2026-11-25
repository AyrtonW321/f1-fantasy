# Decisions

Format: date, decision. Why. Grouped by topic; superseded and duplicate entries removed 2026-11-14 (full history in git).

## Project and process

- 2026-11-09 One public repo; raw data committed only as encrypted `data/raw.tar.gz.enc` (`F1_DATA_KEY`). TracingInsights has no licence; user wants public code. Derived reports from fantasy data stay gitignored.
- 2026-11-09 Tune on past seasons, hold out 2026 and log every holdout evaluation (`reports/holdout_2026_log.md`). Tuning and scoring on the same races is self-graded.
- 2026-11-10 Main session does the work directly (earlier orchestrator/Haiku-worker setup voided by user). Parallel work goes to ChatGPT through handoff files, each in its own git worktree; Claude reviews and merges.
- 2026-11-10 graphify installed as a uv tool, code-only graph, `graphify-out/` committed (hook state gitignored). No pyproject change, no repo data sent to an LLM.

## Data

- 2026-11-09 Sources: TracingInsights pinned release for 2023-2025, official feeds for 2026 and live, mzafram totals as cross-check, Jolpica for results and schedules. TI is the only 2023-2025 source; official feeds may vanish.
- 2026-11-09 Prices: use actual official per-round prices; realized changes come from consecutive snapshots (known at the later lock). No price forecast. Never read TI `priceChange` (post-race data).
- 2026-11-09 Leakage cutoff = first competitive session of the weekend. True sprint-weekend lock could not be verified; this cannot leak.
- 2026-11-09 FastF1 detail only for 2025-2026 (auth via local F1 TV account; 500 calls/hour limit, resume from cache). FP2 gaps stay explicit statuses, never fabricated pace; unknown FP2 timing keeps `known_at = NaT`.
- 2026-11-09 mzafram totals joined by Jolpica round, not TI roundNumber.
- 2026-11-10 `snapshot_official` raises when the schedule feed fails. A silent empty run looked like success.
- 2026-11-10 Bonus events (fastest lap, DotD, pit times) read from raw TI rows for 2026; missing pit times stay missing.
- 2026-11-11 Do not filter picks by `prices.active`: official IsActive false also flags non-benched constructors and drivers. Benched drivers go in each team file's `exclude` list.

## Rules and scoring

- 2026-11-09 Rules per season in `config/rules_{season}.yaml`, unseen values null. Exact-match scoring needs each season's real values; null stops guessing.
- 2026-11-09 Budget grows: bank plus current prices, carried round to round. Matches the real game.
- 2026-11-09 Gate participation: a driver row counts only if Jolpica lists him and TI gives a position other than WD. One genuine source inconsistency (2025 Spanish GP AST) is pinned instead of a rule that would break 2023.
- 2026-11-10 2026 chip rules confirmed by user (Limitless, Wildcard, X3 boost, No Negative, Autopilot, Final Fix; one chip per round, each once).

## Model

- 2026-11-09 Solver PuLP (bundled CBC, ~30 assets), pinned below 4 (version 4 drops CBC).
- 2026-11-10 Phase 4: 2026-only, walk-forward, tune on rounds 1-10; a piece is kept only if it beats the live predictor on MAE and season total. Pace left out (not comparable across drivers).
- 2026-11-10 to 2026-11-11 Live predictor `robust_mu` (trimmed season mean shrunk to a price prior). Disabled because they lost season total vs 4363: simulator 4.2 (4362), qualifying 4.4 (4136), overtakes 4.5 (4252), sprint 4.6 (4336), bonus 4.7 (4330). Why they lose: extra terms shrink top assets toward the field, and the optimizer picks top assets.
- 2026-11-12 Chips `autopilot` and `no_negative` valued by replaying earlier rounds (`src/optimize/chip_history.py`); `final_fix` unvalued (needs qualifying). Logic in `docs/how-it-works.md`.
- 2026-11-12 Form setting stays trim 0.3 / prior weight 2.0: maximized combined 2023-2025 points (14830) and matched 2026 (4363).
- 2026-11-13 Carry-over prior for 2027 not enabled: fails the 2024/2025 rounds 1-4 gate (2024 735 vs 804, 2025 770 vs 749) though MAE improves.
- 2026-11-13 `robust_mu` kept despite losing the 2023 total to rolling-5 by 565. User call: 2023 an outlier; robust wins Spearman every season, MAE 3 of 4.
- 2026-11-13 Horizon (multi-round transfers) rejected: k = 2, 3 identical to single-round on 2023-2025 rounds 1-10. With one mu per round the best team is the same each round.
- 2026-11-14 Recency weighting (8.1) dropped at prototype: h = 3, 5, 8 gave 6247, 6277, 6232 vs `robust_mu` 6326 on 2023-2025 rounds 1-10.

## Automation and app

- 2026-11-14 Weekly update runs locally by hand (`weekly_update --force`) before each lock, not GitHub Actions or an installed scheduler. Why: the repo is public (reports would expose picks) and the PC may be off before a lock. Scheduler scripts kept in `scripts/`.
- 2026-11-14 UI is a local Streamlit app inside Phase 8 (logic in `src/ui/logic.py`, no game logic in `app.py`). Why: editing team files by hand was the worst pain point and a later phase would miss the rest of 2026. History logged from round 21 on, no backfill. Dark theme with red accents per user preference.
- 2026-11-14 `top_teams(chip=...)` returns one team for limitless, wildcard and x3_boost. Why: x3 already solves once per driver; a top-5 loop on top would be ~100 solves per click.
- 2026-11-14 App caches `top_teams` results keyed on team state, chip, budget, exclude and data/model/rules file times. Why: each solve costs ~0.2 s and every click reruns the page.
- 2026-11-15 UI redesign (8.9): tabs My Team | Best Teams | Update; team rows of team-coloured cards (drivers filled, constructors outlined, black/white text by luminance). Stays Streamlit with HTML cards from `src/ui/cards.py`, no frontend rewrite. Team colours live in `config/team_colors.yaml`. No xΔ$ column (no price forecast). Row shows the saved team; swaps for the selected choice sit in a strip under it. Why: one glance across all teams, user-chosen in a grilling session.
- 2026-11-15 Timeline (8.10) starts at the last scored round (20 in 2026) with the saved team file, then expected points for rounds left, no back-fill of rounds 1-19. Rounds after the next repeat the next round's best pick. Why: user asked for only the old team plus the next races; the optimizer plans one round at a time.
- 2026-11-23 Team history gets a row every round, not only on "I made these transfers". Why: Vegas was played without an app apply and nothing was recorded. The weekly update snapshots the saved team for the next round; a real apply or edit replaces it. Snapshots do not count as applied. Pulling the real team from fantasy.formula1.com was skipped (needs the user's sign-in).
- 2026-11-25 Last race 'best possible' = best team under the round's team value + bank with no transfer limits, not the best team reachable with free transfers. Why: needs no pre-round state, and shows the ceiling the model missed.
- 2026-11-25 Skeleton loading (8.11) follows the user's skeleton spec in Streamlit terms: skeletons only on a session's first run (later full reruns keep old content), no 150 ms delay or tickets (Streamlit stops stale runs and fragment reruns keep content), errors caught inside each fragment so Retry reruns just that area. Why: Streamlit has no pre-script first frame; this is the closest fit with no new dependency.
