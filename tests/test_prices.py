import pandas as pd
import pytest

from src.features.prices import realized_price_changes


def test_realized_price_changes_compare_adjacent_round_snapshots_only():
    prices = pd.DataFrame({
        "season": [2025, 2025, 2025, 2025], "round": [1, 2, 4, 5],
        "asset_id": ["AAA"] * 4, "kind": ["driver"] * 4, "price": [10.0, 10.5, 11.5, 11.0],
        "known_at": pd.to_datetime(["2025-03-01T00:00:00Z", "2025-03-08T00:00:00Z",
                                     "2025-03-22T00:00:00Z", "2025-03-29T00:00:00Z"]),
        "priceChange": [99, 99, 99, 99],  # intentionally ignored; post-race source field is forbidden
    })
    changes = realized_price_changes(prices)
    assert changes[["round", "previous_round", "price_change"]].to_dict("records") == [
        {"round": 2, "previous_round": 1, "price_change": 0.5},
        {"round": 5, "previous_round": 4, "price_change": -0.5},
    ]
    assert changes.loc[0, "known_at"] == prices.loc[1, "known_at"]


def test_realized_price_changes_reject_duplicate_snapshots():
    prices = pd.DataFrame({"season": [2025, 2025], "round": [1, 1], "asset_id": ["AAA", "AAA"],
                           "kind": ["driver", "driver"], "price": [10, 10],
                           "known_at": pd.to_datetime(["2025-03-01T00:00:00Z", "2025-03-01T00:00:00Z"])})
    with pytest.raises(ValueError, match="one snapshot"):
        realized_price_changes(prices)
