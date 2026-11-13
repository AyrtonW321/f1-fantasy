"""Aggregate walk-forward prediction and team-score metrics."""

from collections.abc import Callable

import pandas as pd

from src.backtest.walkforward import SeasonResult


def season_metrics(result: SeasonResult, actual_points: pd.DataFrame,
                   predict: Callable[[int, int], pd.DataFrame]) -> dict[str, float]:
    """Return asset MAE, picked-team totals and mean per-round Spearman correlation."""
    errors, correlations = [], []
    rounds = [item.round for item in result.rounds]
    for round_ in rounds:
        actual = actual_points.loc[(actual_points["season"] == result.season)
                                   & (actual_points["round"] == round_),
                                   ["asset_id", "kind", "total"]]
        predicted = predict(result.season, round_)[["asset_id", "kind", "mu"]]
        joined = predicted.merge(actual, on=["asset_id", "kind"], validate="one_to_one")
        errors.append((joined["mu"] - joined["total"]).abs())
        correlations.append(joined["mu"].corr(joined["total"], method="spearman"))
    by_round = {item.round: item.actual_points for item in result.rounds}
    return {
        "mae": float(pd.concat(errors).mean()),
        "season_total": float(result.total),
        "from_round_5": float(result.total_from_round_5),
        "rounds_1_4": float(sum(points for round_, points in by_round.items() if round_ <= 4)),
        "spearman": float(pd.Series(correlations).mean()),
    }
