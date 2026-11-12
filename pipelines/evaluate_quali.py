"""Phase 4.4: simulator with qualifying order vs the 4.2 simulator and robust form (4.1), 2026 walk-forward.

Simulator settings tuned on rounds 1-10 by per-asset MAE; robust form settings come from config/model.yaml.
Run: uv run python pipelines/evaluate_quali.py
"""
import itertools
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipelines.evaluate_form import SEASON, TUNE_LAST, mae
from src.backtest.walkforward import run_season
from src.features.rolling import robust_mu
from src.sim.montecarlo import sim_mu
from src.sim.scoring import load_rules

L2S, SHRINKS = (0.01, 0.1, 1.0, 10.0), (5.0, 20.0, 50.0, 200.0)


def main():
    tables = {n: pd.read_parquet(f"data/processed/{n}.parquet")
              for n in ("races", "prices", "fantasy_points", "results")}
    races, prices, points, results = (tables[n] for n in ("races", "prices", "fantasy_points", "results"))
    form = yaml.safe_load(Path("config/model.yaml").read_text(encoding="utf-8"))["form"]
    rounds = sorted(races.loc[(races["season"] == SEASON) & races["completed"], "round"].astype(int))
    tune = [r for r in rounds if r <= TUNE_LAST]
    rules = load_rules(SEASON)

    sim = lambda l2, k, q=True: (lambda s, r: sim_mu(prices, points, results, races, s, r, rules, l2=l2, dnf_shrink=k, quali=q, **form))
    grid = {(l2, k): mae(sim(l2, k), tune, points) for l2, k in itertools.product(L2S, SHRINKS)}
    l2, shrink = min(grid, key=grid.get)

    start = time.perf_counter()
    for r in rounds:
        sim(l2, shrink)(SEASON, r)
    per_round = (time.perf_counter() - start) / len(rounds)

    rows = []
    for name, f in ((f"robust form (4.1) trim={form['trim']} prior_weight={form['prior_weight']}",
                     lambda s, r: robust_mu(prices, points, races, s, r, **form)),
                    (f"simulator 4.2 l2=0.01 dnf_shrink=200.0", sim(0.01, 200.0, False)),
                    (f"simulator + qualifying l2={l2} dnf_shrink={shrink}", sim(l2, shrink))):
        rows.append((name, mae(f, tune, points), mae(f, rounds, points), run_season(SEASON, tables, rules, f).total))
    beats = all(rows[2][2] < r[2] and rows[2][3] > r[3] for r in rows[:2])
    lines = [f"# Phase 4.4: simulator with qualifying order ({SEASON})", "",
             f"Tuned on rounds 1-{TUNE_LAST} by MAE; reported over rounds {rounds[0]}-{rounds[-1]}. "
             f"2000 draws, seed 0. Rounds with fewer than 3 earlier races use robust form.", "",
             "| Predictor | MAE r1-10 | MAE all | Season total |", "|---|---|---|---|"]
    lines += [f"| {n} | {a:.2f} | {b:.2f} | {t:.0f} |" for n, a, b, t in rows]
    lines += ["", f"Qualifying simulator beats 4.1 and 4.2 on both MAE (all rounds) and season total: {'yes' if beats else 'no'}",
              f"Simulator runtime: {per_round:.2f} s per round", "",
              "Grid (MAE rounds 1-10):", "", "| l2 | dnf_shrink | MAE |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {m:.2f} |" for (a, b), m in sorted(grid.items())]
    Path("reports/phase4_quali.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:11]))


if __name__ == "__main__":
    main()
