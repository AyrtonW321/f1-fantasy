"""Replay-based chip values for chips that expected points cannot rank (autopilot, no_negative).

Each earlier round: take the team you would field, score what the chip would have added with that round's
actual session points, and average. Rounds are grouped by sprint weekend or not, since sprint weekends add a
session. All values come from the rules dict, so it works for any season whose chip rules are filled in.
final_fix needs the qualifying result and is not replayed.
"""
from collections.abc import Callable, Sequence

import pandas as pd

from src.sim.scoring import _rule

SESSIONS = ("qualifying", "sprint", "race")


def replay_gain(chip: str, rules: dict, drivers: Sequence[str], constructors: Sequence[str], boost: str,
                points: pd.DataFrame, mu: pd.DataFrame) -> float | None:
    """Points the chip would have added in one past round (points and mu already cut to that round)."""
    mult = _rule(rules, "team.boost_multiplier")
    if chip == "autopilot":
        _rule(rules, "chips.autopilot.boost_to")  # must be configured; only highest_scoring_driver is replayed
        if rules["chips"]["autopilot"]["boost_to"] != "highest_scoring_driver":
            return None
        tot = points[(points["kind"] == "driver") & points["asset_id"].isin(drivers)].set_index("asset_id")["total"]
        pred = mu[(mu["kind"] == "driver") & mu["asset_id"].isin(tot.index)].set_index("asset_id")["mu"]
        if pred.empty:
            return None
        return (mult - 1) * float(tot.max() - tot[pred.idxmax()])  # the boost it replaces: best predicted driver
    if chip == "no_negative":
        floor = _rule(rules, "chips.no_negative.session_floor")
        rows = points[points["asset_id"].isin([*drivers, *constructors])]
        saved = (floor - rows[list(SESSIONS)]).clip(lower=0).sum(axis=1)  # NaN session (not run) adds 0
        weight = rows["asset_id"].map(lambda a: mult if a == boost else 1)
        return float((saved * weight).sum()) if len(rows) else None
    return None


def historical_value(chip: str, rules: dict, drivers, constructors, boost: str, points: pd.DataFrame,
                     races: pd.DataFrame, predictor: Callable[[int, int], pd.DataFrame],
                     season: int, round_: int, min_rounds: int = 3) -> float | None:
    """Mean replay gain over earlier completed rounds, sprint weekends vs normal ones kept apart when possible.

    Uses the target season's earlier rounds; with fewer than min_rounds of them, the previous season is added.
    """
    lock = races.loc[(races["season"] == season) & (races["round"] == round_), "lock_utc"].iloc[0]
    sprint = bool(races.loc[(races["season"] == season) & (races["round"] == round_), "sprint"].iloc[0])
    seen = races[races["completed"] & (races["lock_utc"] < lock) & races["season"].isin([season, season - 1])]
    if (seen["season"] == season).sum() >= min_rounds:
        seen = seen[seen["season"] == season]
    gains = []
    for r in seen.itertuples():
        pts = points[(points["season"] == r.season) & (points["round"] == r.round) & (points["known_at"] <= lock)]
        g = replay_gain(chip, rules, drivers, constructors, boost, pts, predictor(r.season, r.round))
        if g is not None:
            gains.append((bool(r.sprint), g))
    same = [g for s, g in gains if s == sprint]
    use = same if len(same) >= 2 else [g for _, g in gains]
    return sum(use) / len(use) if use else None
