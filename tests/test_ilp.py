"""Tests for the ILP team optimizer (src/optimize/ilp.py)."""
import time

import pytest

from src.optimize.ilp import Asset, Decision, InfeasibleTeam, TeamState, next_state, optimize
from src.sim.scoring import load_rules


def make_field(n_drivers: int = 22, n_constructors: int = 11) -> list[Asset]:
    """Synthetic field. Driver i has mu 30 - i, constructor j has mu 20 - j.
    Top-5 drivers D00..D04 cost 45.0; top-2 constructors C00, C01 cost 20.5 (team 65.5)."""
    drivers = [Asset(f"D{i:02d}", "driver", 8.0 + (i % 5) * 0.5, 30.0 - i) for i in range(n_drivers)]
    constructors = [Asset(f"C{j:02d}", "constructor", 10.0 + (j % 4) * 0.5, 20.0 - j)
                    for j in range(n_constructors)]
    return drivers + constructors


def _dec(n_in: int) -> Decision:
    return Decision(drivers=(), constructors=(), boost="",
                    transfers_in=tuple(f"X{i}" for i in range(n_in)),
                    penalty_transfers=0, cost=0.0, budget=0.0, expected_points=0.0)


def test_counts_and_boost():
    d = optimize(make_field(), None, load_rules(2026))
    assert d.drivers == ("D00", "D01", "D02", "D03", "D04")
    assert d.constructors == ("C00", "C01")
    assert d.boost == "D00"  # highest-mu picked driver
    # picks 140 + 39, boost extra 30 (multiplier 2 on D00)
    assert d.expected_points == pytest.approx(209.0)


def test_budget_respected():
    field = [Asset(f"H{i}", "driver", 25.0, 30.0 - i) for i in range(5)]
    field += [Asset(f"L{i}", "driver", 5.0, 10.0 - i) for i in range(5)]
    field += [Asset("K0", "constructor", 5.0, 5.0), Asset("K1", "constructor", 5.0, 4.0)]
    d = optimize(field, None, load_rules(2026))
    # Top-5 drivers cost 125.0 (over budget). Best legal team: H0-H2 + L0-L1, cost 95.0.
    assert d.drivers == ("H0", "H1", "H2", "L0", "L1")
    assert d.cost == pytest.approx(95.0)


def test_exact_budget_allowed():
    # Top team costs exactly 100.0 in tenths (1000). A float running sum gives 100.00000000000001.
    field = [Asset("T0", "driver", 20.2, 30.0), Asset("T1", "driver", 19.8, 29.0),
             Asset("T2", "driver", 17.7, 28.0), Asset("T3", "driver", 16.6, 27.0),
             Asset("T4", "driver", 6.7, 26.0)]
    field += [Asset(f"F{i}", "driver", 1.0, 1.0) for i in range(3)]
    field += [Asset("K0", "constructor", 11.7, 20.0), Asset("K1", "constructor", 7.3, 19.0),
              Asset("K2", "constructor", 1.0, 1.0)]
    d = optimize(field, None, load_rules(2026))
    assert d.drivers == ("T0", "T1", "T2", "T3", "T4")
    assert d.constructors == ("K0", "K1")
    assert d.cost == pytest.approx(100.0)


def test_boost_is_driver_only():
    field = make_field() + [Asset("CTOP", "constructor", 10.0, 99.0)]  # highest mu overall
    d = optimize(field, None, load_rules(2026))
    assert d.constructors == ("C00", "CTOP")
    assert d.boost == "D00"
    assert d.boost in d.drivers


def test_budget_grows_with_prices():
    field = [Asset(f"A{i}", "driver", 15.0, 30.0 - i) for i in range(5)]  # current 75.0
    field += [Asset(f"F{i}", "driver", 5.0, 1.0) for i in range(3)]
    field += [Asset("K0", "constructor", 14.5, 20.0), Asset("K1", "constructor", 14.5, 19.0),
              Asset("Z", "constructor", 5.0, 1.0)]  # current 29.0; team total 104.0
    # Last known prices sum to 96.0, so a budget from those prices would not fit the 104.0 team.
    owned = {"A0": 13.0, "A1": 13.0, "A2": 13.0, "A3": 13.0, "A4": 13.0, "K0": 15.5, "K1": 15.5}
    state = TeamState(owned=owned, bank=0.0, free_transfers=2)
    d = optimize(field, state, load_rules(2026))
    assert d.budget == pytest.approx(104.0)
    assert d.drivers == ("A0", "A1", "A2", "A3", "A4")
    assert d.constructors == ("K0", "K1")
    assert d.transfers_in == ()


def test_first_round_has_no_penalty():
    d = optimize(make_field(), None, load_rules(2026))
    assert d.penalty_transfers == 0
    assert d.transfers_in == ()
    assert d.budget == pytest.approx(100.0)


def test_within_free_no_penalty():
    field = make_field()
    prices = {a.id: a.price for a in field}
    owned = {k: prices[k] for k in ["D00", "D01", "D02", "D07", "D08", "C00", "C01"]}
    state = TeamState(owned=owned, bank=10.0, free_transfers=2)  # budget 74.5
    # Penalty 4 is live under 2023 rules, but 2 transfers fit inside the 2 free ones.
    d = optimize(field, state, load_rules(2023))
    assert d.transfers_in == ("D03", "D04")
    assert d.penalty_transfers == 0
    assert d.expected_points == pytest.approx(209.0)


def _swap_field() -> list[Asset]:
    """BOSS is the boost target and is always kept. N1-N3 each beat an owned O by 6 mu.
    No other swap gains anything, so the optimum is decided only by the penalty."""
    drivers = [Asset("BOSS", "driver", 5.0, 30.0)]
    drivers += [Asset(f"O{i}", "driver", 5.0, 10.0) for i in range(1, 5)]
    drivers += [Asset(f"N{i}", "driver", 5.0, 16.0) for i in range(1, 4)]
    drivers += [Asset(f"F{i}", "driver", 5.0, 2.0) for i in range(1, 4)]
    constructors = [Asset("CA", "constructor", 5.0, 4.0), Asset("CB", "constructor", 5.0, 3.0),
                    Asset("CX", "constructor", 5.0, 2.0)]
    return drivers + constructors


def test_penalty_size_changes_choice():
    field = _swap_field()
    owned_ids = {"BOSS", "O1", "O2", "O3", "O4", "CA", "CB"}
    state = TeamState(owned={a.id: a.price for a in field if a.id in owned_ids}, bank=0.0,
                      free_transfers=2)

    # penalty 4: 3 swaps give 18 - 4 = 14, beating 2 swaps at 12
    d23 = optimize(field, state, load_rules(2023))
    assert len(d23.transfers_in) == 3
    assert d23.penalty_transfers == 1
    assert d23.expected_points == pytest.approx(121.0)  # 107 base + 18 - 4

    # penalty 10: 3 swaps give 18 - 10 = 8, losing to 2 swaps at 12
    d26 = optimize(field, state, load_rules(2026))
    assert len(d26.transfers_in) == 2
    assert d26.penalty_transfers == 0
    assert d26.expected_points == pytest.approx(119.0)  # 107 base + 12


def test_missing_owned_asset_keeps_value():
    # GHOST is owned at 10.0 but is no longer in the field. Team must be the 5 drivers
    # A0-A4 plus K0, K1, which only fits if GHOST's last known 10.0 is in the budget.
    field = [Asset(f"A{i}", "driver", 15.0, 30.0 - i) for i in range(4)]
    field += [Asset("A4", "driver", 9.0, 26.0)]
    field += [Asset("K0", "constructor", 12.0, 20.0), Asset("K1", "constructor", 12.0, 19.0)]
    owned = {"GHOST": 10.0, "A0": 15.0, "A1": 15.0, "A2": 15.0, "A3": 15.0, "K0": 12.0, "K1": 12.0}
    state = TeamState(owned=owned, bank=0.0, free_transfers=2)
    d = optimize(field, state, load_rules(2026))
    assert d.budget == pytest.approx(94.0)  # 10 + 60 + 24
    assert d.cost == pytest.approx(93.0)    # 60 + 9 + 24
    assert d.drivers == ("A0", "A1", "A2", "A3", "A4")
    assert d.transfers_in == ("A4",)


def test_carry_rules():
    rules = load_rules(2026)
    assert next_state(None, _dec(0), rules).free_transfers == 2
    assert next_state(TeamState({}, 0.0, 2), _dec(1), rules).free_transfers == 3  # 2 free, 1 used
    assert next_state(TeamState({}, 0.0, 2), _dec(0), rules).free_transfers == 3  # 2 free, 0 used
    assert next_state(TeamState({}, 0.0, 3), _dec(0), rules).free_transfers == 3  # 3 free, 0 used
    assert next_state(TeamState({}, 0.0, 3), _dec(3), rules).free_transfers == 2  # 3 free, 3 used


def test_next_state_bank_and_prices():
    field = make_field()
    rules = load_rules(2026)
    prices = {a.id: a.price for a in field}
    d = optimize(field, None, rules)  # cost 65.5 of 100.0
    nxt = next_state(None, d, rules)
    assert nxt.bank == pytest.approx(d.budget - d.cost)
    assert nxt.bank == pytest.approx(34.5)
    assert dict(nxt.owned) == {k: prices[k] for k in d.drivers + d.constructors}
    assert nxt.free_transfers == 2


def test_solves_under_two_seconds():
    field = make_field(n_drivers=22)  # 22 drivers + 11 constructors = 33 assets
    assert len(field) == 33
    prices = {a.id: a.price for a in field}
    owned = {k: prices[k] for k in ["D10", "D11", "D12", "D13", "D14", "C05", "C06"]}
    state = TeamState(owned=owned, bank=0.0, free_transfers=2)
    start = time.perf_counter()
    d = optimize(field, state, load_rules(2026))
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0
    assert len(d.drivers) == 5 and len(d.constructors) == 2


def test_infeasible_raises():
    field = [Asset(f"D{i}", "driver", 30.0, 10.0 - i) for i in range(5)]  # 150.0 > 100.0
    field += [Asset("C0", "constructor", 5.0, 1.0), Asset("C1", "constructor", 5.0, 1.0)]
    with pytest.raises(InfeasibleTeam):
        optimize(field, None, load_rules(2026))


def test_results_repeatable():
    rules = load_rules(2026)
    field = make_field()
    first = optimize(field, None, rules)
    assert optimize(field, None, rules) == first
    assert optimize(list(reversed(field)), None, rules) == first
    # Tied field: many equal optima, so the answer must come from the fixed id order alone.
    tied = [Asset(f"T{i:02d}", "driver", 8.0, 10.0) for i in range(10)]
    tied += [Asset(f"U{j:02d}", "constructor", 10.0, 5.0) for j in range(4)]
    first_tied = optimize(tied, None, rules)
    assert optimize(tied, None, rules) == first_tied
    assert optimize(list(reversed(tied)), None, rules) == first_tied
