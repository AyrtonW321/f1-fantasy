"""Observed race-to-race fantasy price changes derived from official price snapshots."""

import pandas as pd


PRICE_CHANGE_COLUMNS = [
    "season", "round", "asset_id", "kind", "previous_round", "previous_price", "price",
    "price_change", "known_at",
]


def realized_price_changes(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate observed price changes only between adjacent round snapshots.

    The change is associated with the later round and becomes known at that
    round's pre-lock price snapshot. No source ``priceChange`` field is read.
    """
    required = {"season", "round", "asset_id", "kind", "price", "known_at"}
    missing = sorted(required - set(prices.columns))
    if missing:
        raise ValueError(f"prices missing columns: {missing}")
    if prices.empty:
        return pd.DataFrame(columns=PRICE_CHANGE_COLUMNS)
    keys = ["season", "round", "asset_id", "kind"]
    if prices.duplicated(keys).any():
        raise ValueError("prices must contain one snapshot per season, round and asset")
    current = prices[keys + ["price", "known_at"]].copy()
    prior = current.rename(columns={"round": "previous_round", "price": "previous_price"})
    joined = current.merge(prior, on=["season", "asset_id", "kind"], how="inner", suffixes=("", "_previous"))
    joined = joined.loc[joined["round"].eq(joined["previous_round"] + 1)].copy()
    joined["price_change"] = pd.to_numeric(joined["price"], errors="coerce") - pd.to_numeric(
        joined["previous_price"], errors="coerce")
    return joined[PRICE_CHANGE_COLUMNS].sort_values(keys).reset_index(drop=True)
