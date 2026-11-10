import pandas as pd

from src.features.guard import assert_known_before_lock

ASSET = ["asset_id", "kind"]
OUT_COLS = ["season", "round", "asset_id", "kind", "price", "mu", "known_at"]


def baseline_mu(prices: pd.DataFrame, points: pd.DataFrame, races: pd.DataFrame,
                season: int, round_: int, window: int = 5) -> pd.DataFrame:
    lock = races.loc[(races["season"] == season) & (races["round"] == round_), "lock_utc"].iloc[0]

    target = prices.loc[(prices["season"] == season) & (prices["round"] == round_),
                        ["season", "round", "asset_id", "kind", "price"]]

    # Same season, earlier rounds, known by the target lock.
    history = points[(points["season"] == season)
                     & (points["round"] < round_)
                     & (points["known_at"] <= lock)]

    # League median of total / price over the whole history set (rows without a price skipped).
    priced = history.merge(prices[["season", "round", "asset_id", "kind", "price"]],
                           on=["season", "round", *ASSET])
    ratios = (priced["total"] / priced["price"]).dropna()
    m = float(ratios.median()) if len(ratios) else 1.0

    # Latest `window` rows per asset; k may be 0.
    recent = history.sort_values("round", ascending=False).groupby(ASSET).head(window)
    form = recent.groupby(ASSET).agg(form_sum=("total", "sum"), k=("total", "count")).reset_index()

    out = target.merge(form, on=ASSET, how="left")
    out[["form_sum", "k"]] = out[["form_sum", "k"]].fillna(0)
    prior = out["price"] * m
    out["mu"] = (out["form_sum"] + (window - out["k"]) * prior) / window
    out["known_at"] = lock
    out = out[OUT_COLS].reset_index(drop=True)
    assert_known_before_lock(out, races)
    return out
