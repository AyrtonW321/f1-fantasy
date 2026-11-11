"""Phase 4.7: robust form + separate bonus mean vs robust form (4.1), 2026 walk-forward.

Settings tuned on rounds 1-10 by per-asset MAE; reported over every completed round.
Run: uv run python pipelines/evaluate_bonus.py
"""
import itertools
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipelines.evaluate_form import SEASON, TUNE_LAST, mae
from src.backtest.walkforward import run_season
from src.features.rolling import bonus_mu, robust_mu
from src.sim.scoring import load_rules

TRIMS, WEIGHTS, BONUS_WEIGHTS = (0.2, 0.3), (1.0, 2.0, 3.0), (0.5, 1.0, 2.0, 5.0, 10.0)


def main():
    tables = {n: pd.read_parquet(f"data/processed/{n}.parquet") for n in ("races", "prices", "fantasy_points", "bonus")}
    races, prices, points, bonus = (tables[n] for n in ("races", "prices", "fantasy_points", "bonus"))
    form = yaml.safe_load(Path("config/model.yaml").read_text(encoding="utf-8"))["form"]
    rounds = sorted(races.loc[(races["season"] == SEASON) & races["completed"], "round"].astype(int))
    tune = [r for r in rounds if r <= TUNE_LAST]
    rules = load_rules(SEASON)

    pred = lambda t, w, b: (lambda s, r: bonus_mu(prices, points, bonus, races, s, r, t, w, b))
    grid = {k: mae(pred(*k), tune, points) for k in itertools.product(TRIMS, WEIGHTS, BONUS_WEIGHTS)}
    best = min(grid, key=grid.get)

    rows = []
    for name, f in ((f"robust form (4.1) trim={form['trim']} prior_weight={form['prior_weight']}",
                     lambda s, r: robust_mu(prices, points, races, s, r, **form)),
                    ("form + bonus trim={} prior_weight={} bonus_weight={}".format(*best), pred(*best))):
        rows.append((name, mae(f, tune, points), mae(f, rounds, points), run_season(SEASON, tables, rules, f).total))
    beats = rows[1][2] < rows[0][2] and rows[1][3] > rows[0][3]
    lines = [f"# Phase 4.7: bonus events ({SEASON})", "",
             f"Tuned on rounds 1-{TUNE_LAST} by MAE; reported over rounds {rounds[0]}-{rounds[-1]}. "
             "Bonus = fastest lap, DotD, pit stop points from raw TI rows (data/processed/bonus.parquet).", "",
             "| Predictor | MAE r1-10 | MAE all | Season total |", "|---|---|---|---|"]
    lines += [f"| {n} | {a:.2f} | {b:.2f} | {t:.0f} |" for n, a, b, t in rows]
    lines += ["", f"Beats 4.1 on both MAE (all rounds) and season total: {'yes' if beats else 'no'}", "",
              "Grid (MAE rounds 1-10):", "", "| trim | prior_weight | bonus_weight | MAE |", "|---|---|---|---|"]
    lines += [f"| {t} | {w} | {b} | {m:.2f} |" for (t, w, b), m in sorted(grid.items())]
    Path("reports/phase4_bonus.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:10]))


if __name__ == "__main__":
    main()
