# Phase 4 bonus source audit (2026)

Re-audit 2026-11-10 (replaces the first version, which checked only `data/processed/` and missed the raw rows).

Source: `data/raw/tracinginsights/2026/<slug>/race_all.json`, parsed with `src/ingest/ti_lines.py` (`driver_line`, `parse_pit`), the same parsers the Phase 1 scoring gate uses to reproduce official session totals. Aggregates only.

| Round | Sprint | Race fastest-lap labels | DotD labels | Sprint fastest-lap labels | Constructors with pit-stop time |
|---:|---|---:|---:|---:|---:|
| 1 | no | 1 | 1 | - | 9 of 11 |
| 2 | yes | 1 | 1 | 1 | 10 of 11 |
| 3 | no | 1 | 1 | - | 11 of 11 |
| 4 | yes | 1 | 1 | 1 | 11 of 11 |
| 5 | yes | 1 | 1 | 1 | 11 of 11 |
| 6 | no | 1 | 1 | - | 5 of 11 |
| 7 | no | 1 | 1 | - | 11 of 11 |
| 8 | no | 1 | 1 | - | 9 of 11 |
| 9 | yes | 1 | 1 | 1 | 11 of 11 |
| 10 | no | 1 | 1 | - | 8 of 11 |
| 11 | no | 1 | 1 | - | 11 of 11 |
| 12 | yes | 1 | 1 | 1 | 11 of 11 |
| 13 | no | 1 | 1 | - | 6 of 11 |
| 14 | no | 1 | 1 | - | 11 of 11 |
| 15 | no | 1 | 1 | - | 10 of 11 |
| 16 | no | 1 | 1 | - | 11 of 11 |
| 17 | yes | 1 | 1 | 1 | 8 of 11 |
| 18 | no | 1 | 1 | - | 11 of 11 |
| 19 | no | 1 | 1 | - | 11 of 11 |
| 20 | no | 1 | 1 | - | 11 of 11 |

## Findings

| Event | Coverage | Pre-lock use | Decision |
|---|---|---|---|
| Race fastest lap | 20/20 rounds, exactly one label each | Labels known after each race; usable as history for later rounds | Supported |
| Driver of the Day | 20/20 rounds, exactly one label each | Same | Supported |
| Sprint fastest lap | 6/6 sprint weekends | Same | Supported (no sprints left in 2026) |
| Constructor pit stops | 197/220 constructor-rounds have a stop time | Same; 2026 scores by time band (`driver`/`constructor` pit rules in `config/rules_2026.yaml`), so the time distribution is the input | Supported; constructor-rounds without a time stay missing, not zero |

Rows without a pit time are not imputed. No source in this checkout gives pre-race information for these events; samplers use earlier-round labels only.
