# Progress

## Status (2026-11-14)

- Phases 1-7 done. Phase 8 (finish 2026, prepare 2027) in progress: `docs/superpowers/plans/2026-11-14-phase-8-season-end.md`.
- Live predictor: `robust_mu` (trim 0.3, prior weight 2.0). Every add-on tried since (Phases 4-6, 8.1) lost on season total.
- Weekly use: start the app (`F1 Fantasy.bat`), press "Update data" (or run `uv run python -m pipelines.weekly_update --force`) before each lock, then "I made these transfers" per team.

## Next

1. Las Vegas lock 2026-11-21 04:00 UTC (Fri 23:00 Eastern): apply one real round through the app (Phase 8 acceptance 3).
2. Week of 2026-12-07, after Abu Dhabi is scored: 8.2 final 2026 archive (`vault seal`, user runs it with the key).
3. December: 8.3 2027 plumbing (ChatGPT; handoff not written yet).
4. 2027 game launch: confirm `rules_2027.yaml`, run the weekly update on 2027 prices (Phase 8 acceptance 4).

## Results by phase

| Phase | Result |
|---|---|
| 1 Data and scoring | Scoring reproduces every official session total 2023-2026 (one pinned source exception). Raw data only in encrypted `data/raw.tar.gz.enc`. |
| 2 Baseline | Rolling-5 predictor, PuLP optimizer, walk-forward backtest. Totals: 2023 6190, 2024 4561, 2025 4558, 2026 4269. |
| 3 Pace and car strength | FastF1 2025-2026 ingest, FP2 long-run pace, Kalman car strength (2026 Spearman 0.64 vs 0.50 for last-race order). Neither feeds the picks. |
| 4 Event models | `robust_mu` beats rolling-5 on 2026 (MAE 13.47 vs 14.36, total 4363 vs 4269). Simulator, qualifying, overtakes, sprint and bonus terms all lost and are disabled. Chip planner built. Tag `phase4-freeze`. |
| 5 Backtest 2023-2026 | Retune kept trim 0.3 / prior 2.0 (2023-2025 total 14830). Carry-over prior for 2027 rejected. |
| 6 Horizon | Multi-round transfer planning gave no gain; not built. |
| 7 Automation | `pipelines/weekly_update.py` writes `reports/round_{season}_{round}.md`. Run by hand; scheduler scripts in `scripts/` not installed. |
| 8 (so far) | 8.1 recency dropped. 8.4/8.5 Streamlit app (`app.py`, logic in `src/ui/logic.py`): picks, alternatives, chip-aware teams, one-click apply with backups and history. Cached solves (reruns 3.5 s to 0.2 s). 219 tests pass, 8 skipped without data. |

## Log

- 2026-11-09 to 2026-11-13: Phases 1-6 (details in git history and `docs/decisions.md`).
- 2026-11-14: Phase 7 closed on manual runs. Phase 8: 8.1 dropped; 8.4, 8.4b, 8.5 merged after review; app speed, cleanup and Best teams exclude box; docs cleaned (finished handoffs removed, progress/decisions/known-issues condensed).
- 2026-11-15: 8.9 UI redesign on branch `ui-redesign`: My Team / Best Teams (top 10, Filters popover) / Update tabs; team-coloured asset cards with price and xPts, chip badges (✓ / struck / plain), swap strip and past-swaps log. Task 3 (cards) by ChatGPT, rest by Claude. Headless on real data: 13 rows, cached rerun ~0.4 s; saved-team xPts match the optimizer for all 3 teams. 241 passed. Not merged.
- 2026-11-15: 8.10 UI layout on branch `ui-layout`: three-column team rows (boxed team card | square 3x2 chip tiles | expanders), red-accent header, pill tabs, new Timeline tab (cumulative points per team from round 20, real solid, expected dashed, hover shows transfers/chip/x2). Timeline data and chart by ChatGPT (`src/ui/timeline.py`), rest by Claude. 249 passed; checked in browser at desktop and phone width. Not merged.
- 2026-11-23: Vegas (round 21) scored. Weekly update crashed: TI had Vegas race.json but not race_all.json yet; build_bonus/build_overtakes now skip a missing race_all.json like build_tables does. Round 22 (Qatar) report written, but team files still hold the pre-Vegas teams (no app apply logged), so Qatar picks wait on the real Vegas transfers. Vegas review: model MAE 16.7 (Spearman 0.62); recommended teams 206/244/244 before chips vs 173/260/188 keeping teams; McLaren (113) the big miss.
- 2026-11-23: Team history now kept every round: weekly update snapshots each team file as the next round's lineup (`source=snapshot`, x2 on best expected driver); Edit team form records a played round (round, x2, chip, x3) as `source=edit`; app apply stays `source=app` and replaces a snapshot. Vegas logged from the user's saved teams (no transfers, x2 assumed RUS/VER/HAD, no chip): 173/260/188. Free transfers set to 3 for Qatar; Qatar picks rerun. 247 passed, same 3 real-data failures.
- 2026-11-23: Team header shows the round and race it is for ("Team 1 · Round 22 · Qatar Grand Prix"); Timeline x-axis labels races ("21 Las Vegas"). Real-data timeline test no longer hardcodes round 20.
- 2026-11-25: Confirm banner on My Team when the last race's lineup is only an auto snapshot (Confirm lineup button) or missing (points to Edit team). Last race expander per team: scored vs expected, best team in hindsight under the same budget, model's biggest misses. Failed weekly update keeps the last good report under the FAILED header; report Checks and the Update tab list sources behind (missing official points or TI race_all.json). 253 passed, 2 waiting on TI Vegas files. Checked in the app.
- 2026-11-25: 8.11 skeleton loading on branch `skeleton`: first visit shows pulsing grey boxes for each team row, Best Teams and Timeline before any data loads (reduced motion turns the pulse off); a failed area shows "Couldn't load <thing>..." plus Retry that reruns only that area; Streamlit's stale fade off. 2 scoring-gate tests fail on missing 2026 Las Vegas `qualifying_all.json` (data, not this change).
- 2026-11-25: TracingInsights posted Vegas (tag data-sync-20261123-093633); bonus and overtakes now include round 21, nothing behind, 256 passed. Qatar picks unchanged.
- 2026-11-25: Vegas history corrected to the teams actually played (the recommended transfers; chips NN / x3 VER / x3 ANT): 227/314/309; Qatar rerun. Final Fix helper: `logic.final_fix` plus a "Final Fix (after qualifying)" expander on teams that still hold the chip; worst-qualified driver out (boosted kept), best-qualified affordable driver in. Backtest 2026 r1-21 vs no swap: rule +51 over 18 swaps; quali-aware simulator swap -14 (not built). 257 passed. Checked in the app (pre-quali state).
- 2026-11-25: Vegas fixed again from the user's game: official scores 250/314/309 stored in a new history column `official_points` (overrides the computed score; Edit team has an "Official score" field). Team 3 played No Negative at Vegas, not x3 (x2 ANT assumed); its chips now autopilot, x3_boost, final_fix. Team card outlines the x2 driver in red with an x2 tag. Qatar rerun: Team 3 now x3_boost (ANT -> ALO, BOR -> VER, x3 VER, x2 COL). 258 passed. Checked in the app.
- 2026-11-25: Qatar recorded as applied in the game (T1 autopilot GAS/LAW/LIN -> ALO/LEC/PER x2 LEC; T2 autopilot LAW/VER/VRB -> ALO/ANT/FER x2 ANT; T3 x3_boost ANT/BOR -> ALO/VER x3 VER x2 COL). Chip unlock rule in config: limitless, wildcard, final_fix `from_race: 2`; plan_chips skips locked chips. 259 passed. Next: 2027 chip strategy.
- 2026-11-26: Chip backtest 2023-2026 (`pipelines/evaluate_chips.py`, reports/chip_backtest.md; hindsight, 2026 chip rules on all seasons): mean gain per round Limitless 74, x3 49, No Negative 18, Autopilot 3, Wildcard 2 (11 in rounds 1-6, about 0 after). Sprint weekends lift every chip. Different lead drivers: `optimize(not_priciest=...)` plus `logic.taken_leads`; app picks and weekly pick_team bar other teams' x2/x3 driver and priciest driver (applied teams always; unapplied teams only when numbered lower). Qatar leads already differ (LEC/ANT/VER). 260 passed. Checked in the app.
