# Phase 4.5: overtakes and positions gained (2026)

Weights tuned on rounds 1-10: w_o=10.0, w_g=10.0. Gate 1 on rounds 11-20.

## Gate 1: count check

| Target | Model | Baseline | Pass |
|---|---|---|---|
| Overtakes, Poisson deviance (track effect) | 4.384 | 4.408 (flat field mean) | yes |
| Overtakes, Poisson deviance (no track effect) | 4.410 | 4.408 (flat field mean) | info |
| Gained, squared error | 15.956 | 15.871 (flat 0) | no |

## Gate 2: fantasy points

| Predictor | MAE r1-10 | MAE all | Season total |
|---|---|---|---|
| robust form (4.1) trim=0.3 prior_weight=2.0 | 14.53 | 13.47 | 4363 |
| form + overtakes=True gained=False | 14.43 | 13.48 | 4252 |

Beats 4.1 on both MAE (all rounds) and season total: no
