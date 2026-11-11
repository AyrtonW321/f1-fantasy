"""Phase 4 base: robust 2026 form vs rolling-5 baseline, walk-forward.

Settings tuned on rounds 1-10 by per-asset MAE; reported over every completed round.
Run: uv run python pipelines/evaluate_form.py
"""
import itertools
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.walkforward import run_season
from src.features.rolling import baseline_mu, robust_mu
from src.sim.scoring import load_rules

SEASON, TUNE_LAST = 2026, 10
TRIMS, WEIGHTS = (0.0, 0.1, 0.2, 0.3, 0.4), (0.5, 1.0, 2.0, 3.0, 5.0)


def mae(predict, rounds, points):
    errs = []
    for r in rounds:
        actual = points[(points["season"] == SEASON) & (points["round"] == r)][["asset_id", "kind", "total"]]
        joined = predict(SEASON, r).merge(actual, on=["asset_id", "kind"])
        errs.append((joined["mu"] - joined["total"]).abs())
    return float(pd.concat(errs).mean())


def main():
    tables = {n: pd.read_parquet(f"data/processed/{n}.parquet") for n in ("races", "prices", "fantasy_points")}
    races, prices, points = tables["races"], tables["prices"], tables["fantasy_points"]
    rounds = sorted(races.loc[(races["season"] == SEASON) & races["completed"], "round"].astype(int))
    tune = [r for r in rounds if r <= TUNE_LAST]
    rules = load_rules(SEASON)

    base = lambda s, r: baseline_mu(prices, points, races, s, r, 5)
    grid = {(t, w): mae(lambda s, r, t=t, w=w: robust_mu(prices, points, races, s, r, t, w), tune, points)
            for t, w in itertools.product(TRIMS, WEIGHTS)}
    trim, weight = min(grid, key=grid.get)
    best = lambda s, r: robust_mu(prices, points, races, s, r, trim, weight)

    rows = []
    for name, f in (("rolling-5 baseline", base), (f"robust trim={trim} prior_weight={weight}", best)):
        result = run_season(SEASON, tables, rules, f)
        rows.append((name, mae(f, tune, points), mae(f, rounds, points), result.total))
    lines = [f"# Phase 4 base: robust form ({SEASON})", "",
             f"Tuned on rounds 1-{TUNE_LAST} by MAE; reported over rounds {rounds[0]}-{rounds[-1]}.", "",
             "| Predictor | MAE r1-10 | MAE all | Season total |", "|---|---|---|---|"]
    lines += [f"| {n} | {a:.2f} | {b:.2f} | {t:.0f} |" for n, a, b, t in rows]
    lines += ["", "Grid (MAE rounds 1-10):", "", "| trim | prior_weight | MAE |", "|---|---|---|"]
    lines += [f"| {t} | {w} | {m:.2f} |" for (t, w), m in sorted(grid.items())]
    Path("reports/phase4_form.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:8]))


if __name__ == "__main__":
    main()
