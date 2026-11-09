# Known issues

- 2023 free-transfer carry-over is assumed; no source confirms it.
- Never observed, left null: 2026 race DSQ, world-record pit stop, pre-2026 sprint DSQ, overall fastest stop before 2025.
- Chip effects are third-party only; confirm with the user before Phase 6.
- TracingInsights has no licence; its data must never appear in git as plaintext.
- TracingInsights 2023 roundNumber is one ahead of Jolpica from Monaco on; join on slug.
- TI lists non-participants (2026 Mexico: TSU under VRB); count only drivers in Jolpica results.
- Official 2026 feeds may vanish when the 2027 game launches: snapshot first.
- snapshot_official returns nothing silently when the schedule feed fails on a network error; check the printed "wrote N files" line (61 on a good run).
- Official feed lists 37 players in the latest gameday, 33 in gameday 1; the extra rows are not yet explained.
- True sprint-weekend lock time unverified; cutoff uses the first competitive session.
