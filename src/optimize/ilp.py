"""ILP team optimizer: best legal team under the budget, counts and transfer rules.

Formulation: spec Layer 4 (docs/superpowers/specs/2026-11-09-f1-fantasy-optimizer.md).
Game values come from the rules dict (config/rules_{season}.yaml); _rule raises
UnknownRuleError for a null value.
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

import pulp

from src.sim.scoring import _rule


@dataclass(frozen=True)
class Asset:
    id: str
    kind: Literal["driver", "constructor"]
    price: float
    mu: float


@dataclass(frozen=True)
class TeamState:
    owned: Mapping[str, float]  # asset id to last known price
    bank: float
    free_transfers: int


@dataclass(frozen=True)
class Decision:
    drivers: tuple[str, ...]
    constructors: tuple[str, ...]
    boost: str
    transfers_in: tuple[str, ...]
    penalty_transfers: int
    cost: float
    budget: float
    expected_points: float
    prices: Mapping[str, float] = field(default_factory=dict)  # picked asset id to current price


class InfeasibleTeam(Exception):
    """No legal team fits the budget and counts."""


def _tenths(value: float) -> int:
    # Integer tenths avoid float error at exact budgets, e.g. 12.1 * 5 + 19.7 + 19.8 == 100.0.
    return round(value * 10)


def optimize(assets: Sequence[Asset], state: TeamState | None, rules: dict) -> Decision:
    assets = sorted(assets, key=lambda a: a.id)  # fixed order: repeatable results
    n_drivers = _rule(rules, "team.drivers")
    n_constructors = _rule(rules, "team.constructors")
    boost_mult = _rule(rules, "team.boost_multiplier")

    if state is None:
        budget = _rule(rules, "team.budget")
        penalty = 0
    else:
        current = {a.id: a.price for a in assets}
        budget = state.bank + sum(current.get(k, last) for k, last in state.owned.items())
        penalty = _rule(rules, "transfers.penalty")

    prob = pulp.LpProblem("f1_team", pulp.LpMaximize)
    pick = [pulp.LpVariable(f"p{i}", cat="Binary") for i in range(len(assets))]
    drv = [i for i, a in enumerate(assets) if a.kind == "driver"]
    con = [i for i, a in enumerate(assets) if a.kind == "constructor"]
    boost = {i: pulp.LpVariable(f"b{i}", cat="Binary") for i in drv}

    prob += pulp.lpSum(pick[i] for i in drv) == n_drivers
    prob += pulp.lpSum(pick[i] for i in con) == n_constructors
    prob += pulp.lpSum(boost.values()) == 1
    for i in drv:
        prob += boost[i] <= pick[i]
    prob += pulp.lpSum(_tenths(a.price) * pick[i] for i, a in enumerate(assets)) <= _tenths(budget)

    obj = pulp.lpSum(a.mu * pick[i] for i, a in enumerate(assets))
    obj += pulp.lpSum(assets[i].mu * (boost_mult - 1) * boost[i] for i in drv)

    if state is not None:
        s = [pulp.LpVariable(f"s{i}", cat="Binary") for i in range(len(assets))]
        e = pulp.LpVariable("e", lowBound=0)
        for i, a in enumerate(assets):
            prob += s[i] >= pick[i] - (1 if a.id in state.owned else 0)
        prob += e >= pulp.lpSum(s) - state.free_transfers
        obj -= penalty * e
    prob += obj

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        raise InfeasibleTeam(f"no legal team: solver status {status}")

    chosen = [assets[i] for i in range(len(assets)) if pick[i].value() > 0.5]
    boosted = assets[next(i for i in drv if boost[i].value() > 0.5)]
    drivers = tuple(a.id for a in chosen if a.kind == "driver")
    constructors = tuple(a.id for a in chosen if a.kind == "constructor")
    if state is None:
        transfers_in: tuple[str, ...] = ()
        penalty_transfers = 0
    else:
        transfers_in = tuple(a.id for a in chosen if a.id not in state.owned)
        penalty_transfers = max(0, len(transfers_in) - state.free_transfers)

    return Decision(
        drivers=drivers,
        constructors=constructors,
        boost=boosted.id,
        transfers_in=transfers_in,
        penalty_transfers=penalty_transfers,
        cost=round(sum(a.price for a in chosen), 1),
        budget=budget,
        expected_points=(sum(a.mu for a in chosen) + (boost_mult - 1) * boosted.mu
                         - penalty * penalty_transfers),
        prices={a.id: a.price for a in chosen},
    )


def next_state(state: TeamState | None, decision: Decision, rules: dict) -> TeamState:
    bank = decision.budget - decision.cost
    base_free = _rule(rules, "transfers.free")
    if state is None:
        free = base_free
    else:
        unused = max(state.free_transfers - len(decision.transfers_in), 0)
        carry = min(_rule(rules, "transfers.carry_max"), unused)
        free = min(_rule(rules, "transfers.max_free"), base_free + carry)
    return TeamState(owned=decision.prices, bank=bank, free_transfers=free)
