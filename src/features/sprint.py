"""Expected points for sprint weekends, using pre-lock sprint history."""

import pandas as pd

from src.features.guard import assert_known_before_lock
from src.features.rolling import ASSET, OUT_COLS, robust_mu


def sprint_mu(prices: pd.DataFrame, points: pd.DataFrame, races: pd.DataFrame,
              season: int, round_: int, trim: float = 0.3, prior_weight: float = 2.0,
              sprint_weight: float = 2.0) -> pd.DataFrame:
    """Robust non-sprint form plus a shrunk mean of earlier sprint session points."""
    residual = points.copy()
    residual["total"] = residual["total"] - residual["sprint"]
    out = robust_mu(prices, residual, races, season, round_, trim, prior_weight)
    target_sprint = races.loc[(races["season"] == season) & (races["round"] == round_), "sprint"]
    if len(target_sprint) and bool(target_sprint.iloc[0]):
        lock = out["known_at"].iloc[0] if len(out) else pd.NaT
        sprint_rounds = races.loc[(races["season"] == season) & races["sprint"], "round"]
        history = points.loc[(points["season"] == season) & points["round"].isin(sprint_rounds)
                             & (points["round"] < round_) & (points["known_at"] <= lock)]
        field_mean = float(history["sprint"].mean()) if len(history) else 0.0
        means = history.groupby(ASSET)["sprint"].agg(["sum", "count"]).reset_index()
        out = out.merge(means, on=ASSET, how="left")
        out[["sum", "count"]] = out[["sum", "count"]].fillna(0.0)
        if sprint_weight == 0:
            shrunk = out["sum"] / out["count"].replace(0, 1)
            shrunk = shrunk.where(out["count"] > 0, field_mean)
        else:
            shrunk = (out["sum"] + sprint_weight * field_mean) / (out["count"] + sprint_weight)
        out["mu"] += shrunk
        out = out[OUT_COLS].reset_index(drop=True)
    assert_known_before_lock(out, races)
    return out
