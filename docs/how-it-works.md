# How the picks are made

One calculation decides keeps, sells, transfers and the boost: the legal team with the highest total expected points. Code: `src/optimize/ilp.py`. Weaknesses are in `docs/known-issues.md`.

## Keep or sell
- Each driver and constructor has a price and an expected score (`robust_mu`: trimmed season mean, shrunk toward a price-based prior).
- Legal team: 5 drivers, 2 constructors, cost within budget. Budget = bank + current value of the owned team at today's prices.
- Team score = sum of expected points + one extra copy of the boosted driver's points (the 2x boost; the model picks who).
- An asset is kept or sold only because that raises the total. Assets in `exclude` (team file) score -1000, so they are sold and never bought.

## Penalty transfers
- `free_transfers` are free; each transfer beyond them costs `transfers.penalty` (10) points, subtracted inside the same calculation.
- An extra transfer happens only if the incoming asset adds more than 10 expected points over the one it replaces.

## Chips
`plan_chips.py` values each remaining chip per remaining round, then picks the chip-to-round assignment with the highest total gain (each chip once, one chip per round).

| Chip (id in code) | Value comes from |
|---|---|
| `x3_boost` | Optimizer: tries every driver as the 3x pick (the normal 2x is forbidden on it), the optimizer then picks the team and the 2x driver; output shows `3x X, 2x Y` |
| `wildcard`, `limitless` | Optimizer: re-run with the transfer penalty off / the budget cap off; gain = difference |
| `autopilot`, `no_negative` | Replay of earlier rounds with the team you would field (`src/optimize/chip_history.py`): average past gain, sprint and normal weekends kept apart; previous season added if fewer than 3 rounds are done |
| `final_fix` | Not valued: needs the qualifying result. Play it after qualifying |

## Using the app

Start the local dashboard from the project folder with `uv run streamlit run app.py`, or double-click `F1 Fantasy.bat`. Each Team tab shows the saved lineup, the current best pick, alternatives, chip advice, a transfer action, a validated manual editor, and saved history. The Best teams tab compares the top lineups at a budget you choose, without the assets in its exclude box (prefilled from the team files). The Data tab shows the next lock and price status and can run the weekly update; its output streams into the page.

Manual edits and applied transfers back up the prior team file under `config/backup/`; transfer history is stored under `config/history/`. History starts with the first round saved through the app. The scheduled or manual update writes round reports under `reports/` and appends its log to `reports/weekly_update.log`. Sealing raw data remains a separate manual step.

## Weekly report

Run before each lock: `uv run python -m pipelines.weekly_update --force` (or "Update data" in the app). It writes `reports/round_{season}_{round}.md` and logs to `reports/weekly_update.log`.

Optional daily 20:00 job (not installed; read the battery note in `docs/known-issues.md` first): `.\scripts\install_task.ps1`, remove with `.\scripts\uninstall_task.ps1`.
