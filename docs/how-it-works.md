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
| `extra_drs` (the game's "X3 boost") | Optimizer: tries every driver as the 3x pick, plus the normal 2x on another |
| `wildcard`, `limitless` | Optimizer: re-run with the transfer penalty off / the budget cap off; gain = difference |
| `autopilot`, `no_negative` | Replay of earlier rounds with the team you would field (`src/optimize/chip_history.py`): average past gain, sprint and normal weekends kept apart; previous season added if fewer than 3 rounds are done |
| `final_fix` | Not valued: needs the qualifying result. Play it after qualifying |
