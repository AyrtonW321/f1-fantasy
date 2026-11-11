# Phase 3 Data Review: 2025–2026

## FastF1 ingest

The target archive is complete: 220/220 expected sessions, 124,876 laps, 21,946 weather observations, and 2,555 track-status observations. The final pull reported no missing sessions, ingest warnings, or event-name mismatches. Race-control messages were enabled during refresh, so all 17,148 FP2 lap rows now have a known `deleted` flag; 316 are marked deleted.

## FP2 pace coverage and fit quality

| Season | Entrant/weekend rows | No FP2 session | FP2 expected | Pre-lock pace estimates | Coverage when FP2 exists | No usable long run | RMSE median / p95 / max (s) | Fits with RMSE > 5s | Estimates under 8 laps |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 2025 | 479 | 120 | 359 | 269 | 74.9% | 90 | 0.32 / 1.24 / 3.54 | 0 | 89 |
| 2026 | 440 | 132 | 308 | 249 | 80.8% | 59 | 0.41 / 2.31 / 5.02 | 1 | 92 |
| Total | 919 | 252 | 667 | 518 | 77.7% | 149 | — | 1 | 181 |

The 252 `no_fp2_session` rows correspond to six sprint weekends in each season. Of the 518 estimates, 427 are `rank_deficient`: their centered reference pace is estimable, but the separate lap-number and tyre-age slopes are not, so those slopes are null. The other 91 fits are full rank.

The first diagnostic pass found RMSE as high as 41 seconds because FastF1's accuracy flag can accept very slow laps and the original uncapped MAD filter was inflated by those laps. The ingest now loads race-control messages, and the pace filter uses the faster half of each stint as its reference with a 10-second cap on the MAD allowance. It excluded 2,603 slow laps across the generated rows. Residual diagnostics improved substantially; one 2026 estimate remains just above 5 seconds RMSE. RMSE here is in-sample fit error, not a forecast-accuracy score.

All 518 retained estimates have valid `known_at` and lock timestamps and are available before the modeled cutoff. No usable estimate is after lock or missing its timing. The pace table and round-level status breakdown are in the ignored processed Parquet data and `reports/phase3_pace_coverage.md`.

## Gaps to resolve before using pace live

There are 149 `no_usable_longrun` rows despite an FP2 session being scheduled. The largest clusters are 2025 Round 3 (20 entrants), 2025 Round 18 (17), 2025 Round 22 (12), and 2026 Round 10 (18). Round 22 has recorded rainfall; Rounds 3, 18, and 2026 Round 10 have no rainfall observations. The strict minimum of four cleaned laps within an eligible stint leaves many drivers without a fit. These are explicit missing-feature statuses under the user's coverage decision; downstream models must keep them missing and report their impact.

Another 181 estimates use fewer than eight laps. They remain visible in the report with observation counts, but should be treated as lower confidence. Keep missing pace explicit; do not fill those rows with another session or fabricated values.

I simulated a looser fallback that accepts stints with at least two cleaned laps when at least four cleaned laps remain across the driver-weekend. It would recover 54 of the 149 gaps, but 49/54 estimates would still have fewer than eight laps, four would have RMSE above five seconds, and the worst RMSE would be 10.13 seconds. Raising that pooled minimum to seven laps recovers only five rows, with RMSE up to 3.76 seconds. The current four-lap-per-stint rule is retained; the broader fallback does not provide enough reliable coverage to justify changing the meaning of a long-run estimate.

## Track safety-car refresh

The prior-only refresh updated `data/static/tracks.csv`. Rates are present for 67/93 event rows: 22/24 in 2024, 24/24 in 2025, and 21/23 in 2026. No 2023 circuit has an earlier same-track race in the loaded history, 2024 China and Imola have no earlier race in the loaded source, and the 2026 Madring and Sepang entries have no prior same-track observations. Those rates remain blank by design rather than using future outcomes.

## Acceptance status

Ingestion coverage passes for the selected seasons, and pace/status coverage passes the user's clarified contract: all 919 expected entrant/weekend rows have an estimate or explicit status. Usable pace is available for 518/667 entrant rows where FP2 was scheduled; 149 remain explicitly `no_usable_longrun` and must be treated as missing by downstream models. Pre-lock checks show no leakage. The existing Kalman evaluation is separate and previously exceeded the last-race-order baseline.

No tests were run for this review, per user instruction.
