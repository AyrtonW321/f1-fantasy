# FP2 long-run pace coverage

Counts only; driver-level pace values remain in the ignored processed Parquet table.

## Status counts by season

| Season | Status | Entrants |
|---:|---|---:|
| 2025 | fit | 37 |
| 2025 | no_fp2_session | 120 |
| 2025 | no_usable_longrun | 90 |
| 2025 | rank_deficient | 232 |
| 2026 | fit | 54 |
| 2026 | no_fp2_session | 132 |
| 2026 | no_usable_longrun | 59 |
| 2026 | rank_deficient | 195 |

## Fit diagnostics

Estimates with `rank_deficient` status retain the centered reference pace; their unidentified slopes are null. `low sample` counts estimates based on fewer than eight laps.

| Season | FP2 entrant rows | Pre-lock estimates | Coverage | RMSE median / p95 / max (s) | RMSE > 5s | Low sample | Slow laps removed |
|---:|---:|---:|---:|---|---:|---:|---:|
| 2025 | 359 | 269 | 74.9% | 0.32 / 1.24 / 3.54 | 0 | 89 | 1280 |
| 2026 | 308 | 249 | 80.8% | 0.41 / 2.31 / 5.02 | 1 | 92 | 1323 |

## Coverage by round

`usable_prelock` counts estimates whose FP2 data was available by the current lineup-lock cutoff.

| Season | Round | Entrants | Usable pre-lock | Status counts |
|---:|---:|---:|---:|---|
| 2025 | 1 | 20 | 19 | fit: 2, no_usable_longrun: 1, rank_deficient: 17 |
| 2025 | 2 | 20 | 0 | no_fp2_session: 20 |
| 2025 | 3 | 20 | 0 | no_usable_longrun: 20 |
| 2025 | 4 | 20 | 20 | fit: 2, rank_deficient: 18 |
| 2025 | 5 | 20 | 4 | no_usable_longrun: 16, rank_deficient: 4 |
| 2025 | 6 | 20 | 0 | no_fp2_session: 20 |
| 2025 | 7 | 20 | 17 | no_usable_longrun: 3, rank_deficient: 17 |
| 2025 | 8 | 20 | 19 | fit: 6, no_usable_longrun: 1, rank_deficient: 13 |
| 2025 | 9 | 19 | 19 | fit: 7, rank_deficient: 12 |
| 2025 | 10 | 20 | 18 | fit: 5, no_usable_longrun: 2, rank_deficient: 13 |
| 2025 | 11 | 20 | 20 | fit: 3, rank_deficient: 17 |
| 2025 | 12 | 20 | 19 | fit: 1, no_usable_longrun: 1, rank_deficient: 18 |
| 2025 | 13 | 20 | 0 | no_fp2_session: 20 |
| 2025 | 14 | 20 | 20 | rank_deficient: 20 |
| 2025 | 15 | 20 | 15 | fit: 1, no_usable_longrun: 5, rank_deficient: 14 |
| 2025 | 16 | 20 | 19 | no_usable_longrun: 1, rank_deficient: 19 |
| 2025 | 17 | 20 | 9 | no_usable_longrun: 11, rank_deficient: 9 |
| 2025 | 18 | 20 | 3 | no_usable_longrun: 17, rank_deficient: 3 |
| 2025 | 19 | 20 | 0 | no_fp2_session: 20 |
| 2025 | 20 | 20 | 20 | fit: 4, rank_deficient: 16 |
| 2025 | 21 | 20 | 0 | no_fp2_session: 20 |
| 2025 | 22 | 20 | 8 | no_usable_longrun: 12, rank_deficient: 8 |
| 2025 | 23 | 20 | 0 | no_fp2_session: 20 |
| 2025 | 24 | 20 | 20 | fit: 6, rank_deficient: 14 |
| 2026 | 1 | 22 | 16 | fit: 6, no_usable_longrun: 6, rank_deficient: 10 |
| 2026 | 2 | 22 | 0 | no_fp2_session: 22 |
| 2026 | 3 | 22 | 17 | fit: 1, no_usable_longrun: 5, rank_deficient: 16 |
| 2026 | 4 | 22 | 0 | no_fp2_session: 22 |
| 2026 | 5 | 22 | 0 | no_fp2_session: 22 |
| 2026 | 6 | 22 | 21 | fit: 16, no_usable_longrun: 1, rank_deficient: 5 |
| 2026 | 7 | 22 | 18 | fit: 3, no_usable_longrun: 4, rank_deficient: 15 |
| 2026 | 8 | 22 | 20 | no_usable_longrun: 2, rank_deficient: 20 |
| 2026 | 9 | 22 | 0 | no_fp2_session: 22 |
| 2026 | 10 | 22 | 4 | no_usable_longrun: 18, rank_deficient: 4 |
| 2026 | 11 | 22 | 20 | fit: 2, no_usable_longrun: 2, rank_deficient: 18 |
| 2026 | 12 | 22 | 0 | no_fp2_session: 22 |
| 2026 | 13 | 22 | 20 | fit: 6, no_usable_longrun: 2, rank_deficient: 14 |
| 2026 | 14 | 22 | 16 | no_usable_longrun: 6, rank_deficient: 16 |
| 2026 | 15 | 22 | 17 | fit: 1, no_usable_longrun: 5, rank_deficient: 16 |
| 2026 | 16 | 22 | 22 | fit: 6, rank_deficient: 16 |
| 2026 | 17 | 22 | 0 | no_fp2_session: 22 |
| 2026 | 18 | 22 | 19 | fit: 1, no_usable_longrun: 3, rank_deficient: 18 |
| 2026 | 19 | 22 | 18 | fit: 2, no_usable_longrun: 4, rank_deficient: 16 |
| 2026 | 20 | 22 | 21 | fit: 10, no_usable_longrun: 1, rank_deficient: 11 |
