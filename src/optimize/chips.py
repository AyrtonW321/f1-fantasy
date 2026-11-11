"""Forward chip-value estimates using the configured rules and team optimizer."""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from collections.abc import Callable, Mapping, Sequence

import pandas as pd

from src.optimize.ilp import Asset, Decision, TeamState, optimize
from src.sim.scoring import _rule


def _state(team: Mapping, prices: Mapping[str, float]) -> TeamState:
    owned = [*team["drivers"], *team["constructors"]]
    unknown = sorted(set(owned) - set(prices))
    if unknown:
        raise ValueError(f"team assets absent from predictor prices: {unknown}")
    return TeamState({asset: prices[asset] for asset in owned}, float(team["bank"]),
                     int(team["free_transfers"]))


def estimate_chip(assets: Sequence[Asset], team: Mapping, rules: dict, chip: str,
                  baseline: Decision | None = None) -> tuple[float | None, Decision | None, str | None]:
    """Return (gain, resulting team, unsupported reason); rules are read via scoring._rule."""
    chip_rules = _rule(rules, f"chips.{chip}")
    baseline = baseline or optimize(assets, _state(team, {a.id: a.price for a in assets}), rules)
    if chip == "limitless":
        if _rule(rules, f"chips.{chip}.budget_cap") is not False:
            return None, None, "configured budget behavior is not unlimited"
        if _rule(rules, f"chips.{chip}.free_transfers") != "unlimited":
            return None, None, "configured transfer behavior is not unlimited"
        _rule(rules, f"chips.{chip}.team_reverts_next_round")
        chip_assets = list(assets)
        capless = deepcopy(rules)
        capless["team"]["budget"] = sum(a.price for a in chip_assets)
        # State-less optimizer only applies configured budget; preserve team objective without transfer penalties.
        candidate = optimize(chip_assets, None, capless)
    elif chip == "wildcard":
        if _rule(rules, f"chips.{chip}.budget_cap") is not True:
            return None, None, "configured budget behavior is not capped"
        if _rule(rules, f"chips.{chip}.free_transfers") != "unlimited":
            return None, None, "configured transfer behavior is not unlimited"
        _rule(rules, f"chips.{chip}.team_reverts_next_round")
        free = deepcopy(rules)
        free["transfers"]["penalty"] = 0
        candidate = optimize(assets, _state(team, {a.id: a.price for a in assets}), free)
    elif chip == "extra_drs":
        multiplier = _rule(rules, f"chips.{chip}.extra_multiplier")
        # Try each possible 3x driver while optimize chooses the normal 2x driver.
        candidates = []
        for boosted in (a for a in assets if a.kind == "driver"):
            altered = [Asset(a.id, a.kind, a.price,
                             a.mu * (multiplier - 1) if a.id == boosted.id else a.mu)
                       for a in assets]
            d = optimize(altered, _state(team, {a.id: a.price for a in altered}), rules)
            ids = set(d.drivers)
            if boosted.id in ids and d.boost != boosted.id:
                value = sum(a.mu for a in assets if a.id in {*d.drivers, *d.constructors})
                normal = next(a for a in assets if a.id == d.boost)
                normal_multiplier = _rule(rules, "team.boost_multiplier")
                value += (normal_multiplier - 1) * normal.mu + (multiplier - 1) * boosted.mu
                value -= _rule(rules, "transfers.penalty") * d.penalty_transfers
                candidates.append((value, d))
        if not candidates:
            return None, None, "no feasible extra boost assignment"
        _, candidate = max(candidates, key=lambda x: (x[0], tuple(x[1].drivers)))
        # Expected value adjusted for the second 3x boost selected above.
        gain = max(0.0, max(v for v, _ in candidates) - baseline.expected_points)
        return gain, candidate, None
    else:
        # No-negative needs session-level downside; Autopilot needs the distribution of the maximum;
        # Final Fix needs post-qualifying observations. None are present in mu-only input.
        return None, None, "mu-only predictor does not support this chip's required estimate"
    gain = candidate.expected_points - baseline.expected_points
    return max(0.0, gain), candidate, None


def plan_chips(predictor: Callable[[int, int], pd.DataFrame], team: Mapping, rules: dict,
               rounds: Sequence[int], season: int = 2026) -> list[dict]:
    """Assign configured remaining chips to rounds for maximum nonnegative expected gain."""
    chips_left = team.get("chips_left", [])
    if len(chips_left) != len(set(chips_left)):
        raise ValueError("each chip may appear at most once in chips_left")
    chips = [str(c) for c in chips_left]
    values = {}
    decisions = {}
    for round_ in rounds:
        frame = predictor(season, round_)
        assets = [Asset(str(r.asset_id), str(r.kind), float(r.price), float(r.mu))
                  for r in frame.itertuples()]
        state = _state(team, {a.id: a.price for a in assets})
        base = optimize(assets, state, rules)
        for chip in chips:
            gain, decision, unsupported = estimate_chip(assets, team, rules, chip, base)
            values[(round_, chip)] = gain
            decisions[(round_, chip)] = (decision, unsupported)
    # Enumerate one option per round; chip indexes are unique and at most one per round.
    options = [None, *chips]
    best = None
    for assignment in product(options, repeat=len(rounds)):
        used = [c for c in assignment if c is not None]
        if len(used) != len(set(used)) or any(values[(r, c)] is None for r, c in zip(rounds, assignment) if c):
            continue
        score = sum(values[(r, c)] or 0 for r, c in zip(rounds, assignment) if c)
        key = (score, tuple("" if c is None else c for c in assignment))
        if best is None or key > best[0]:
            best = (key, assignment)
    assignment = best[1] if best else tuple(None for _ in rounds)
    output = []
    for round_, chip in zip(rounds, assignment):
        if chip is None:
            baseframe = predictor(season, round_)
            assets = [Asset(str(r.asset_id), str(r.kind), float(r.price), float(r.mu))
                      for r in baseframe.itertuples()]
            decision = optimize(assets, _state(team, {a.id: a.price for a in assets}), rules)
            output.append({"round": round_, "chip": None, "gain": 0.0, "decision": decision})
        else:
            decision, _ = decisions[(round_, chip)]
            output.append({"round": round_, "chip": chip, "gain": values[(round_, chip)], "decision": decision})
    return output
