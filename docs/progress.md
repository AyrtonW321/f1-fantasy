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
