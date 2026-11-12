"""Phase 4.5: expected race overtakes (Poisson) and positions gained (shrunk mean) as extra form points.

Track effect: Poisson regression on earlier seasons (documented exception to the 2026-only rule), on
overtaking_difficulty dummies. Driver rate: current-season overtakes per unit of track effect, shrunk toward
the field rate. Gained can be negative, so it is a plain mean shrunk toward 0. Race session only.
"""
import numpy as np
import pandas as pd

from src.features.guard import assert_known_before_lock
from src.features.rolling import ASSET, OUT_COLS, robust_mu
from src.models import poisson
from src.sim.montecarlo import CONSTRUCTOR_CODE
from src.sim.scoring import DriverLine, score_driver


def _design(df: pd.DataFrame, tracks: pd.DataFrame) -> np.ndarray:
    level = df[["season", "round"]].merge(tracks[["season", "round", "overtaking_difficulty"]], how="left")
    d = level["overtaking_difficulty"]
    return np.column_stack([np.ones(len(df)), d.eq("medium"), d.eq("high")]).astype(float)


def expected(ot: pd.DataFrame, tracks: pd.DataFrame, season: int, round_: int, drivers: list[str],
             w_o: float, w_g: float, track: bool = True) -> pd.DataFrame | None:
    """Expected overtakes and gained per driver for a race; None without earlier current-season rows.
    ot must already be cut to rows known before the target lock."""
    cur = ot[(ot["season"] == season) & (ot["round"] < round_)]
    if cur.empty:
        return None
    old = ot[ot["season"] < season]
    beta = poisson.fit(_design(old, tracks), old["overtakes"].to_numpy(float)) if track and len(old) else np.zeros(3)
    eff = lambda df: np.exp(_design(df, tracks)[:, 1:] @ beta[1:])
    cur = cur.assign(e=eff(cur))
    prior = cur["overtakes"].sum() / cur["e"].sum()
    per = cur.groupby("asset_id").agg(o=("overtakes", "sum"), e=("e", "sum"), g=("gained", "sum"),
                                      n=("gained", "size")).reindex(drivers).fillna(0.0)
    target = eff(pd.DataFrame({"season": [season], "round": [round_]}))[0]
    return pd.DataFrame({"driver": drivers, "ov": poisson.shrunk_rate(per["o"], per["e"], prior, w_o).to_numpy() * target,
                         "gained": (per["g"] / (per["n"] + w_g)).to_numpy()})


def overtakes_mu(prices: pd.DataFrame, points: pd.DataFrame, ot: pd.DataFrame, tracks: pd.DataFrame,
                 results: pd.DataFrame, races: pd.DataFrame, season: int, round_: int, rules: dict, *,
                 trim: float, prior_weight: float, w_o: float, w_g: float,
                 use_ov: bool = True, use_g: bool = True) -> pd.DataFrame:
    """robust_mu of points minus actual overtake/gained points, plus expected overtake/gained points."""
    lock = races.loc[(races["season"] == season) & (races["round"] == round_), "lock_utc"].iloc[0]
    ot = ot[ot["known_at"] <= lock]
    base = robust_mu(prices, points, races, season, round_, trim, prior_weight)
    drivers = prices[(prices["season"] == season) & (prices["round"] == round_) & (prices["kind"] == "driver")]["asset_id"].tolist()
    exp = expected(ot, tracks, season, round_, drivers, w_o, w_g)
    if exp is None:
        return base
    p_o = score_driver(rules, DriverLine("X", "race", overtakes=1))
    p_g = score_driver(rules, DriverLine("X", "race", gained=1))
    cur = ot[(ot["season"] == season) & (ot["round"] < round_)]
    cur = cur.assign(core=cur["overtakes"] * p_o * use_ov + cur["gained"] * p_g * use_g)
    race = results[(results["season"] == season) & (results["session"] == "race") & (results["round"] < round_)]
    team = race.merge(cur[["round", "asset_id", "core"]], left_on=["round", "driver_code"], right_on=["round", "asset_id"])
    team["asset_id"] = team["constructor_id"].map(CONSTRUCTOR_CODE)
    core = pd.concat([cur[["round", "asset_id", "core"]].assign(kind="driver"),
                      team.groupby(["round", "asset_id"], as_index=False)["core"].sum().assign(kind="constructor")])
    resid = points[(points["season"] == season) & (points["round"] < round_)].merge(core, on=["round", *ASSET], how="left")
    resid["total"] -= resid["core"].fillna(0.0)
    rest = robust_mu(prices, resid.drop(columns="core"), races, season, round_, trim, prior_weight)
    add = exp["ov"] * p_o * use_ov + exp["gained"] * p_g * use_g
    last = race[race["round"] == race["round"].max()].set_index("driver_code")["constructor_id"].map(CONSTRUCTOR_CODE)
    drv = pd.Series(add.to_numpy(), index=exp["driver"])
    con = drv.groupby(last.reindex(drv.index).to_numpy()).sum()
    gain = pd.concat([drv.rename_axis("asset_id").reset_index(name="add").assign(kind="driver"),
                      con.rename_axis("asset_id").reset_index(name="add").assign(kind="constructor")])
    out = rest.merge(gain, on=ASSET, how="left")
    out["mu"] = out["mu"] + out["add"].fillna(0.0)
    out = out[OUT_COLS]
    assert_known_before_lock(out, races)
    return out
