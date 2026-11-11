import pandas as pd
import pytest

from src.optimize.chips import estimate_chip, plan_chips
from src.optimize.ilp import Asset, TeamState, optimize
from src.sim.scoring import UnknownRuleError, load_rules


def field(expensive=False):
    drivers = [Asset(f"D{i}", "driver", 25 if expensive and i < 5 else 8 + i, 40 - i)
               for i in range(8)]
    constructors = [Asset(f"C{i}", "constructor", 12 + i, 20 - i) for i in range(3)]
    return drivers + constructors


def team(assets, chips=None):
    return {"drivers": [f"D{i}" for i in range(5)], "constructors": ["C0", "C1"],
            "bank": 0.0, "free_transfers": 0, "chips_left": chips or []}


def test_reads_config_rules_and_null_raises():
    rules = load_rules(2026)
    assets = field()
    t = team(assets)
    gain, _, unsupported = estimate_chip(assets, t, rules, "limitless")
    assert gain >= 0 and unsupported is None
    rules["chips"]["limitless"] = None
    with pytest.raises(UnknownRuleError):
        estimate_chip(assets, t, rules, "limitless")


def test_limitless_ignores_budget_and_wildcard_respects_it():
    rules = load_rules(2026)
    assets = field(expensive=True)
    t = team(assets)
    t["drivers"] = [f"D{i}" for i in range(3, 8)]
    t["constructors"] = ["C1", "C2"]
    base = optimize(assets, TeamState({a.id: a.price for a in assets if a.id in {*t['drivers'], *t['constructors']}}, 0, 0), rules)
    _, limitless, _ = estimate_chip(assets, t, rules, "limitless", base)
    _, wildcard, _ = estimate_chip(assets, t, rules, "wildcard", base)
    assert limitless.budget > base.budget
    assert limitless.cost <= limitless.budget
    assert wildcard.cost <= wildcard.budget


def test_unsupported_chips_are_not_recommended_and_each_used_once():
    assets = field()
    t = team(assets, ["limitless", "wildcard", "no_negative", "autopilot", "final_fix"])

    def predictor(season, round_):
        return pd.DataFrame([{"season": season, "round": round_, "asset_id": a.id, "kind": a.kind,
                              "price": a.price, "mu": a.mu, "known_at": pd.Timestamp("2026-01-01", tz="UTC")}
                             for a in assets])

    result = plan_chips(predictor, t, load_rules(2026), [21, 22, 23])
    chosen = [row["chip"] for row in result if row["chip"]]
    assert len(chosen) == len(set(chosen))
    assert len(result) == 3
    assert all(row["chip"] not in {"no_negative", "autopilot", "final_fix"} for row in result)


def test_duplicate_remaining_chip_rejected():
    with pytest.raises(ValueError, match="at most once"):
        plan_chips(lambda *_: pd.DataFrame(), {"chips_left": ["wildcard", "wildcard"]},
                   load_rules(2026), [21])
