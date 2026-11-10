"""Walk-forward baseline backtest: predict, optimize and score each completed round in order.

No chips. Game values come from load_rules(season); window and seasons from config/model.yaml.
Run from the project folder: uv run python -m src.backtest.walkforward --season 2024
"""
import argparse
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

from src.features.rolling import baseline_mu
from src.optimize.ilp import Asset, Decision, next_state, optimize
from src.sim.scoring import _rule, load_rules

Predictor = Callable[[int, int], pd.DataFrame]


@dataclass(frozen=True)
class RoundResult:
    round: int
    decision: Decision
    actual_points: float
    solve_seconds: float


@dataclass(frozen=True)
class SeasonResult:
    season: int
    rounds: list[RoundResult]
    total: float
    total_from_round_5: float
    assumptions: list[str]


def _actual_points(season: int, round_: int, decision: Decision, points: pd.DataFrame, rules: dict) -> float:
    rows = points[(points["season"] == season) & (points["round"] == round_)]
    # Keyed by (asset, kind) so a driver and a constructor with the same id never share a row.
    totals = {(a, k): float(t) for a, k, t in zip(rows["asset_id"], rows["kind"], rows["total"])}
    picked = [(a, "driver") for a in decision.drivers] + [(a, "constructor") for a in decision.constructors]
    score = sum(totals.get(key, 0.0) for key in picked)  # no points row scores 0.0
    score += (_rule(rules, "team.boost_multiplier") - 1) * totals.get((decision.boost, "driver"), 0.0)
    score -= _rule(rules, "transfers.penalty") * decision.penalty_transfers
    return score


def run_season(season: int, tables: dict[str, pd.DataFrame], rules: dict, predict: Predictor) -> SeasonResult:
    races = tables["races"]
    points = tables["fantasy_points"]
    rounds = sorted(int(r) for r in races.loc[(races["season"] == season) & races["completed"], "round"])

    state = None
    results: list[RoundResult] = []
    for round_ in rounds:
        frame = predict(season, round_)
        assets = [Asset(id=row.asset_id, kind=row.kind, price=float(row.price), mu=float(row.mu))
                  for row in frame.itertuples(index=False)]
        start = time.perf_counter()
        decision = optimize(assets, state, rules)
        solve_seconds = time.perf_counter() - start
        actual = _actual_points(season, round_, decision, points, rules)
        results.append(RoundResult(round_, decision, actual, solve_seconds))
        state = next_state(state, decision, rules)

    total = sum((r.actual_points for r in results), 0.0)
    total_from_5 = sum((r.actual_points for r in results if r.round >= 5), 0.0)
    return SeasonResult(season, results, total, total_from_5, list(rules.get("assumed", [])))


def _max_solve(result: SeasonResult) -> float:
    return max((r.solve_seconds for r in result.rounds), default=0.0)


def write_report(result: SeasonResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    assumed = ", ".join(result.assumptions) or "none"
    lines = [
        f"# Baseline walk-forward {result.season}",
        "",
        f"Assumed rules: {assumed}",
        "",
        f"Total points: {result.total:.1f}",
        f"Total points from round 5: {result.total_from_round_5:.1f}",
        f"Max solve seconds: {_max_solve(result):.3f}",
        "",
        "| Round | Drivers | Constructors | Boost | Transfers in | Penalty transfers | Points | Solve seconds |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in result.rounds:
        d = r.decision
        lines.append(
            f"| {r.round} | {', '.join(d.drivers)} | {', '.join(d.constructors)} | {d.boost} "
            f"| {', '.join(d.transfers_in) or '-'} | {d.penalty_transfers} "
            f"| {r.actual_points:.1f} | {r.solve_seconds:.3f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    model = yaml.safe_load(Path("config/model.yaml").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description="Walk-forward baseline backtest.")
    parser.add_argument("--season", type=int, action="append",
                        help="season to run; repeat for several (default: all backtest seasons)")
    args = parser.parse_args(argv)
    seasons = args.season or model["backtest"]["seasons"]
    window = model["baseline"]["rolling_window"]

    processed = Path("data/processed")
    tables = {name: pd.read_parquet(processed / f"{name}.parquet")
              for name in ("races", "prices", "fantasy_points")}
    predict = lambda s, r: baseline_mu(tables["prices"], tables["fantasy_points"], tables["races"], s, r, window)

    for season in seasons:
        result = run_season(season, tables, load_rules(season), predict)
        write_report(result, Path("reports") / f"baseline_{season}.md")
        print(f"{season} {result.total:.1f} {result.total_from_round_5:.1f} "
              f"{len(result.rounds)} {_max_solve(result):.3f}")


if __name__ == "__main__":
    main()
