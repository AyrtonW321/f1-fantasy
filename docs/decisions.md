# Decisions

Format: date, decision. Why.

- 2026-11-09 Base = Phases 1-2, plan covers all 7. Scoring and the optimizer must be proven before any model sits on them.
- 2026-11-09 Data: TracingInsights pinned release for 2023-25, official feeds for 2026 and live, mzafram totals as cross-check, Jolpica for results and schedules. TI is the only 2023-25 source; official 2026 feeds may vanish; mzafram is an independent check.
- 2026-11-09 Rules per season for all four seasons (rules_2023..2026.yaml), unseen values null. Exact-match scoring across seasons needs each season's real values; null stops guessing.
- 2026-11-09 Chips wait for Phase 6. Timing needs a forward view, and chip rules are unconfirmed.
- 2026-11-09 Budget grows: bank plus current prices, carried round to round. Matches the real game; a fixed 100 forces fake transfers.
- 2026-11-09 Baseline: same-season rolling 5, filled with a price-based prior. Past seasons stay as the answer key for backtests and tuning. Prior-season form misleads across regulation resets.
- 2026-11-09 Tune on 2023-2025, hold out 2026 and log each evaluation, refit on all four for 2027. Tuning and scoring on the same races is self-graded.
- 2026-11-09 FastF1 laps move to Phase 3. Nothing in Phases 1-2 reads them.
- 2026-11-09 Solver: PuLP. Bundles CBC, writes the spec's formulation directly, problem is about 30 assets.
- 2026-11-09 Leakage cutoff = first competitive session of the weekend. True sprint-weekend lock could not be verified; this cannot leak.
- 2026-11-09 One public repo; raw data committed only as an encrypted archive (F1_DATA_KEY). TracingInsights has no licence; user wants public code.
- 2026-11-09 Execution: orchestrator on the main session, Haiku builder and reviewer workers, every check re-run by the orchestrator. Cheap workers stay reliable only if checks are re-run.
