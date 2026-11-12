"""Tune and evaluate the Phase 4.6 sprint term on 2026 walk-forward data."""
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipelines.evaluate_form import SEASON, TUNE_LAST, mae
from src.backtest.walkforward import run_season
from src.features.rolling import robust_mu
from src.features.sprint import sprint_mu
from src.sim.scoring import load_rules

SPRINT_WEIGHTS = (0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0)


def main():
    tables = {n: pd.read_parquet(f"data/processed/{n}.parquet")
              for n in ("races", "prices", "fantasy_points")}
    races, prices, points = (tables[n] for n in ("races", "prices", "fantasy_points"))
    form = yaml.safe_load(Path("config/model.yaml").read_text(encoding="utf-8"))["form"]
    rounds = sorted(races.loc[(races["season"] == SEASON) & races["completed"], "round"].astype(int))
    sprint_rounds = sorted(races.loc[(races["season"] == SEASON) & races["completed"] & races["sprint"], "round"].astype(int))
    tune = [r for r in rounds if r <= TUNE_LAST]
    base = lambda s, r: robust_mu(prices, points, races, s, r, **form)
    grid = {w: mae(lambda s, r, w=w: sprint_mu(prices, points, races, s, r, sprint_weight=w, **form),
                    tune, points) for w in SPRINT_WEIGHTS}
    weight = min(grid, key=grid.get)
    candidate = lambda s, r: sprint_mu(prices, points, races, s, r, sprint_weight=weight, **form)
    rules = load_rules(SEASON)
    base_season = run_season(SEASON, tables, rules, base)
    cand_season = run_season(SEASON, tables, rules, candidate)
    actual = points[points["season"] == SEASON]

    def result_row(label, f, run, selected):
        selected = list(selected)
        metric_mae = mae(f, selected, points)
        round_results = {r.round: r.actual_points for r in run.rounds}
        total = sum(round_results[r] for r in selected)
        return (label, metric_mae, total)

    rows = [result_row("4.1 robust_mu", base, base_season, sprint_rounds),
            result_row(f"4.6 sprint_mu (weight={weight})", candidate, cand_season, sprint_rounds)]
    all_rows = [result_row("4.1 robust_mu", base, base_season, rounds),
                result_row(f"4.6 sprint_mu (weight={weight})", candidate, cand_season, rounds)]
    anecdotal = []
    for r in (12, 17):
        anecdotal.extend([result_row(f"4.1 round {r}", base, base_season, [r]),
                          result_row(f"4.6 round {r}", candidate, cand_season, [r])])
    passes = rows[1][1] < rows[0][1] and rows[1][2] > rows[0][2] \
        and all_rows[1][1] <= all_rows[0][1] and all_rows[1][2] >= all_rows[0][2]
    lines = [f"# Phase 4.6: sprint weekends ({SEASON})", "",
             f"Tuned sprint_weight on rounds 1-{TUNE_LAST} by per-asset MAE; form trim={form['trim']}, "
             f"prior_weight={form['prior_weight']}. Sprint rounds: {', '.join(map(str, sprint_rounds))}.", "",
             "| Scope | Predictor | Per-asset MAE | Picked-team points |", "|---|---|---:|---:|"]
    lines += [f"| Six sprint rounds | {n} | {m:.2f} | {t:.0f} |" for n, m, t in rows]
    lines += [f"| All completed rounds | {n} | {m:.2f} | {t:.0f} |" for n, m, t in all_rows]
    lines += [f"| Anecdotal round | {n} | {m:.2f} | {t:.0f} |" for n, m, t in anecdotal]
    lines += ["", f"Pass bar (sprint MAE and total improve; all-round MAE and total no worse): {'PASS' if passes else 'FAIL'}.",
              f"Sprint predictor is {'enabled for evaluation only' if passes else 'disabled and not wired into pick_team.py'}.",
              "", "Sprint-weight tuning grid (rounds 1-10 MAE):", "", "| sprint_weight | MAE |", "|---:|---:|"]
    lines += [f"| {w} | {m:.2f} |" for w, m in sorted(grid.items())]
    Path("reports/phase4_sprint.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
