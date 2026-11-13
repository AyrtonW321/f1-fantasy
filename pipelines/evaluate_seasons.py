"""Evaluate multi-season baselines and re-tune robust form for Phase 5."""
import argparse
import importlib
import itertools
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.metrics import season_metrics
from src.backtest.walkforward import run_season
from src.features.rolling import baseline_mu, robust_mu
from src.sim.scoring import load_rules

SEASONS = (2023, 2024, 2025, 2026)
TRIMS, WEIGHTS = (0.0, 0.1, 0.2, 0.3, 0.4), (0.5, 1.0, 2.0, 3.0, 5.0)


def _external_predictors(spec, tables, model):
    module_name, function_name = spec.split(":", 1)
    factory = getattr(importlib.import_module(module_name), function_name)
    return factory(tables, model)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictor", help="optional extension factory as module:function; returns {name: (season, round) predictor}")
    args = parser.parse_args(argv)
    tables = {n: pd.read_parquet(f"data/processed/{n}.parquet")
              for n in ("races", "prices", "fantasy_points")}
    model_path = Path("config/model.yaml")
    model = yaml.safe_load(model_path.read_text(encoding="utf-8"))
    form = model["form"].copy()
    races, prices, points = tables["races"], tables["prices"], tables["fantasy_points"]

    def baseline(s, r):
        return baseline_mu(prices, points, races, s, r, model["baseline"]["rolling_window"])

    def robust(s, r, trim=form["trim"], weight=form["prior_weight"]):
        return robust_mu(prices, points, races, s, r, trim, weight)

    predictors = {"rolling-5": baseline, "robust_mu": robust}
    if args.predictor:
        predictors.update(_external_predictors(args.predictor, tables, model))

    lines = ["# Phase 5: multi-season walk-forward", "",
             "Per-asset MAE and per-round Spearman use each predictor's pre-lock asset predictions. Team totals use the season rules.",
             "", "| Predictor | Season | Asset MAE | Season total | From round 5 | Rounds 1-4 | Mean round Spearman |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    aggregate_2026 = {}
    for season in SEASONS:
        for name, predict in predictors.items():
            result = run_season(season, tables, load_rules(season), predict)
            metrics = season_metrics(result, points, predict)
            lines.append(f"| {name} | {season} | {metrics['mae']:.2f} | {metrics['season_total']:.0f} | "
                         f"{metrics['from_round_5']:.0f} | {metrics['rounds_1_4']:.0f} | {metrics['spearman']:.4f} |")
            if season == 2026:
                aggregate_2026[name] = metrics

    grid = {}
    for trim, weight in itertools.product(TRIMS, WEIGHTS):
        values = []
        for season in (2023, 2024, 2025):
            pred = lambda s, r, t=trim, w=weight: robust(s, r, t, w)
            result = run_season(season, tables, load_rules(season), pred)
            values.append((result.total, season_metrics(result, points, pred)["mae"]))
        grid[(trim, weight)] = (sum(x[0] for x in values), sum(x[1] for x in values) / len(values))
    best_trim, best_weight = max(grid, key=lambda key: grid[key][0])
    tuned = lambda s, r: robust(s, r, best_trim, best_weight)
    current_2026 = run_season(2026, tables, load_rules(2026), robust)
    best_2026 = run_season(2026, tables, load_rules(2026), tuned)
    current_metrics = season_metrics(current_2026, points, robust)
    tuned_metrics = season_metrics(best_2026, points, tuned)
    adopted = best_2026.total >= current_2026.total
    changed = (best_trim, best_weight) != (form["trim"], form["prior_weight"])
    if adopted and changed:
        model["form"].update(trim=best_trim, prior_weight=best_weight)
        model_path.write_text(yaml.safe_dump(model, sort_keys=False), encoding="utf-8")

    outcome = ("Adopted new setting" if changed and adopted else
               "Retained current setting; config/model.yaml unchanged" if adopted else
               "Not adopted; config/model.yaml unchanged")
    lines += ["", "## Task 5.2: shared 2023-2025 tuning", "",
              f"Selected by maximum combined season points: trim={best_trim}, prior_weight={best_weight}; "
              f"combined points {grid[(best_trim, best_weight)][0]:.0f}, mean season MAE {grid[(best_trim, best_weight)][1]:.2f}.",
              f"2026 check: current trim={form['trim'] if adopted else model['form']['trim']}, "
              f"prior_weight={form['prior_weight'] if adopted else model['form']['prior_weight']} total "
              f"{current_2026.total:.0f}; tuned total {best_2026.total:.0f}, MAE {tuned_metrics['mae']:.2f}. "
              f"{outcome}.", "",
              "| trim | prior_weight | Combined 2023-2025 points | Mean season MAE |",
              "|---:|---:|---:|---:|"]
    lines += [f"| {t} | {w} | {total:.0f} | {mae:.2f} |" for (t, w), (total, mae) in sorted(grid.items())]
    report = Path("reports/phase5_seasons.md")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    holdout = Path("reports/holdout_2026_log.md")
    with holdout.open("a", encoding="utf-8") as f:
        f.write("\n## Phase 5 2026 aggregate metrics (2026-11-12)\n\n")
        f.write("| Predictor | Asset MAE | Season total | From round 5 | Rounds 1-4 | Mean round Spearman |\n|---|---:|---:|---:|---:|---:|\n")
        for name, m in aggregate_2026.items():
            f.write(f"| {name} | {m['mae']:.2f} | {m['season_total']:.0f} | {m['from_round_5']:.0f} | {m['rounds_1_4']:.0f} | {m['spearman']:.4f} |\n")
        f.write(f"\n5.2 tuned check: trim={best_trim}, prior_weight={best_weight}, 2026 total {best_2026.total:.0f}, "
                f"asset MAE {tuned_metrics['mae']:.2f}; {'adopted' if adopted else 'not adopted'} against current total {current_2026.total:.0f}.\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
