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


def _trimmed_mean(values: pd.Series, trim: float) -> float:
    v = values.sort_values().to_numpy()
    cut = int(len(v) * trim)
    return float(v[cut:len(v) - cut].mean())


def robust_mu(prices: pd.DataFrame, points: pd.DataFrame, races: pd.DataFrame,
              season: int, round_: int, trim: float = 0.2, prior_weight: float = 3.0) -> pd.DataFrame:
    """Season-to-date trimmed mean per asset, shrunk toward the price prior.

    Uses every earlier round of the season, so one or two outlier weekends move it little.
    mu = (k * trimmed_mean + prior_weight * price * m) / (k + prior_weight).
    """
    base = baseline_mu(prices, points, races, season, round_, window=1)  # reuse target rows, lock, guard
    lock = base["known_at"].iloc[0] if len(base) else None
    history = points[(points["season"] == season) & (points["round"] < round_) & (points["known_at"] <= lock)]
    priced = history.merge(prices[["season", "round", *ASSET, "price"]], on=["season", "round", *ASSET])
    ratios = (priced["total"] / priced["price"]).dropna()
    m = float(ratios.median()) if len(ratios) else 1.0
    form = (history.groupby(ASSET)["total"]
            .agg(center=lambda s: _trimmed_mean(s, trim), k="count").reset_index())
    out = base.drop(columns="mu").merge(form, on=ASSET, how="left")
    out["k"] = out["k"].fillna(0)
    out["center"] = out["center"].fillna(0.0)
    out["mu"] = (out["k"] * out["center"] + prior_weight * out["price"] * m) / (out["k"] + prior_weight)
    out = out[OUT_COLS].reset_index(drop=True)
    assert_known_before_lock(out, races)
    return out


def bonus_mu(prices: pd.DataFrame, points: pd.DataFrame, bonus: pd.DataFrame, races: pd.DataFrame,
             season: int, round_: int, trim: float = 0.3, prior_weight: float = 2.0,
             bonus_weight: float = 2.0) -> pd.DataFrame:
    """robust_mu of non-bonus points plus each asset's mean bonus points, shrunk toward its kind's field mean.

    Bonus points (fastest lap, DotD, pit stop) are rare spikes that trimming would cut, so they get a plain
    shrunk mean instead. Expected values only: the optimizer uses means, so no per-draw sampling here.
    """
    keys = ["season", "round", *ASSET]
    resid = points.merge(bonus[keys + ["bonus"]], on=keys, how="left")
    resid["total"] = resid["total"] - resid["bonus"].fillna(0.0)
    out = robust_mu(prices, resid.drop(columns="bonus"), races, season, round_, trim, prior_weight)
    lock = out["known_at"].iloc[0] if len(out) else None
    hist = bonus[(bonus["season"] == season) & (bonus["round"] < round_) & (bonus["known_at"] <= lock)]
    field = hist.groupby("kind")["bonus"].mean()
    stats = hist.groupby(ASSET)["bonus"].agg(["sum", "count"]).reset_index()
    out = out.merge(stats, on=ASSET, how="left").fillna({"sum": 0.0, "count": 0.0})
    prior = out["kind"].map(field).fillna(0.0)
    out["mu"] = out["mu"] + (out["sum"] + bonus_weight * prior) / (out["count"] + bonus_weight)
    out = out[OUT_COLS].reset_index(drop=True)
    assert_known_before_lock(out, races)
    return out
