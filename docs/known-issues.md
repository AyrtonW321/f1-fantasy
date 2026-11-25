# Known issues

## Data sources

- TracingInsights (TI) has no licence: its data never goes into git as plaintext.
- Official 2026 feeds may vanish when the 2027 game launches: take the final snapshot first (8.2).
- `snapshot_official` raises if the schedule feed fails, but a partial run is silent: check the "wrote N files" line (61 on a good run).
- TI 2023 `roundNumber` runs one ahead of Jolpica from Monaco on: join on slug. mzafram files are numbered by Jolpica round.
- TI lists non-participants and phantom rows (drivers under a team they did not drive for). Two participation rules exist: `build_tables` (TI positions / official IsActive) and the scoring gate (Jolpica results plus TI position).
- Official 2026 feed grows from 33 to 37 players through seat swaps (LAW second PlayerId 116; TSU rounds 12-14; HIR round 19; Camara round 20 on). `build_tables` keys drivers by TLA and keeps the active row.
- `prices.active` (official IsActive) does not identify benched drivers reliably (it also flags whole constructors in round 6). Benched drivers are handled by each team file's `exclude` list; team 1 has `exclude: []` while teams 2 and 3 exclude HIR.
- Official 2026 round 6 (Monaco): 9 assets' session points do not add up to the feed's GamedayPoints; the TI row is used.
- Bonus labels (fastest lap, DotD, pit times) exist only in raw TI rows; 23 of 220 2026 constructor-rounds have no pit time.
- FP2 pace is not comparable across drivers (per-driver centring, no compound offset) and has gaps (149 of 667 FP2 rows without a usable long run). Not used by the picks.
- The cloud session has no `F1_DATA_KEY` and cannot reach fantasy.formula1.com: data tests and snapshots run locally.

## Rules and scoring

- 2023 free-transfer carry-over is assumed; no source confirms it.
- Never observed, left null: 2026 race DSQ, world-record pit stop, pre-2026 sprint DSQ, overall fastest stop before 2025.
- Chip rules confirmed for 2026 only; 2023-2025 chips unconfirmed. `rules_2027.yaml` does not exist yet (8.3).
- Scoring gate pins one source inconsistency (2025 Spanish GP race, AST, withdrawn driver's -20) in `KNOWN_SOURCE_EXCEPTIONS` (`tests/test_scoring_gate.py`).
- mzafram cross-check differs on 2023 round 4 SAR and round 13 ALT; 2024-2026 match exactly. TI and Jolpica finish positions differ for 2023 Qatar sprint and 2025 Emilia-Romagna qualifying (likely penalties); the data test allows at most 10 per season.
- True sprint-weekend lock time unverified; the cutoff uses the first competitive session.

## Model and optimizer

- Main limit: `robust_mu` weighs the whole season equally, so it is slow to see a recent upturn (round 21: BOR 6.6 expected over HUL 4.9, though HUL scored 14, 2, 15, 19, 17, 7, 2, 4 in rounds 13-20). Every fix tried so far lost on season total (`docs/decisions.md`).
- `robust_mu` loses the 2023 season total to rolling-5 by 565 points; not investigated (user kept it).
- The optimizer plans one round at a time: the 10-point penalty is a flat cost and it never holds a transfer back.
- Prices are flat: no price-change prediction (f1fantasytools does predict them).
- Chips: round-to-chip assignment is mostly a tie-break; `plan_chips.py` reuses round 21 prices and expected points for later rounds; autopilot is small (+1 to +7); `final_fix` is not valued. With a chip, `top_teams` returns one team, not five.
- `src/features/rolling.py:31` `fillna(0)` on an object frame raises a pandas FutureWarning; cast to float when next touching it.

## Pipelines and tools

- `pipelines/build_data.py` hardcodes seasons `[2023, 2024, 2025, 2026]` and `BONUS_SEASONS = [2026]` (8.3 fixes this for 2027).
- `pipelines/evaluate_seasons.py` appends to `reports/holdout_2026_log.md` on every run (reruns duplicate entries) and rewrites `config/model.yaml` without its comments when adopting a setting. `--predictor` factories get `tables` without `results`.
- `pick_team.py` without a team file uses the starting 100.0 budget; use `--team N`.
- `scripts/install_task.ps1` (not installed) keeps Task Scheduler's battery defaults; fix with `-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries` before installing. Its run opens a console window.
- pulp is pinned below 4 (version 4 drops the bundled CBC solver).
- graphify hooks in `.claude/settings.json` call bare `graphify`: install it on PATH (`uv tool install graphifyy`).

## App

- `save_team` rewrites the team YAML, so comments in team files are lost.
- With no round left, each team tab shows the "no upcoming round" message twice (error and warning).
- The edit form cannot re-add a used chip.
- First load solves every tab (~5.7 s); a new chip or team state costs one solve set (x3_boost ~3.8 s).
- `config/my_team_1.yaml` has `exclude: []`, so benched HIR can appear in Team 1's alternatives (Teams 2 and 3 exclude it).
- Streamlit does not reload `src/ui/*` modules on save; restart the app after editing them.
- App calls `load_rules(season)` unguarded per team row; it reads a CWD-relative path, so launching from outside the repo root fails (same as the solve path). Use `F1 Fantasy.bat` or run from the repo root.
- TracingInsights posts `race_all.json` a few days after `race.json`; until then the latest round has no bonus or overtakes rows (picks unaffected).
- 2026-11-23: 2 real-data tests fail until TI posts Vegas `_all.json` files (2 scoring-gate tests).
- History rows from Edit team and snapshots log penalty 0 and the current bank; a snapshot is only as right as the team file at the last weekly update before lock. Vegas x2 boosts (RUS, VER, HAD) are assumed, not confirmed.
