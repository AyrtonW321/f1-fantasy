from types import SimpleNamespace

import pandas as pd

from src.backtest.metrics import season_metrics
from src.backtest.walkforward import SeasonResult


def test_season_metrics_aggregates_asset_error_team_totals_and_rank():
    actual = pd.DataFrame({"season": [2024] * 6, "round": [1] * 3 + [5] * 3,
                           "asset_id": list("ABC") * 2, "kind": ["driver"] * 6,
                           "total": [1, 2, 3, 1, 2, 3]})
    predicted = {
        1: [1, 2, 3],
        5: [3, 2, 1],
    }

    def predict(season, round_):
        return pd.DataFrame({"asset_id": list("ABC"), "kind": ["driver"] * 3,
                             "mu": predicted[round_]})

    result = SeasonResult(2024, [SimpleNamespace(round=1, actual_points=15),
                                 SimpleNamespace(round=5, actual_points=25)], 40, 25, [])
    metrics = season_metrics(result, actual, predict)
    assert metrics == {"mae": 2 / 3, "season_total": 40.0, "from_round_5": 25.0,
                       "rounds_1_4": 15.0, "spearman": 0.0}
