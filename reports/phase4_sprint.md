# Phase 4.6: sprint weekends (2026)

Tuned sprint_weight on rounds 1-10 by per-asset MAE; form trim=0.3, prior_weight=2.0. Sprint rounds: 2, 4, 5, 9, 12, 17.

| Scope | Predictor | Per-asset MAE | Picked-team points |
|---|---|---:|---:|
| Six sprint rounds | 4.1 robust_mu | 15.35 | 1442 |
| Six sprint rounds | 4.6 sprint_mu (weight=10.0) | 15.76 | 1427 |
| All completed rounds | 4.1 robust_mu | 13.47 | 4363 |
| All completed rounds | 4.6 sprint_mu (weight=10.0) | 13.46 | 4336 |
| Anecdotal round | 4.1 round 12 | 11.41 | 237 |
| Anecdotal round | 4.6 round 12 | 13.21 | 255 |
| Anecdotal round | 4.1 round 17 | 13.82 | 256 |
| Anecdotal round | 4.6 round 17 | 14.95 | 262 |

Pass bar (sprint MAE and total improve; all-round MAE and total no worse): FAIL.
Sprint predictor is disabled and not wired into pick_team.py.

Sprint-weight tuning grid (rounds 1-10 MAE):

| sprint_weight | MAE |
|---:|---:|
| 0.0 | 14.45 |
| 0.5 | 14.39 |
| 1.0 | 14.35 |
| 2.0 | 14.31 |
| 3.0 | 14.29 |
| 5.0 | 14.28 |
| 10.0 | 14.28 |
