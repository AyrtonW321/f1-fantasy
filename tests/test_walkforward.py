import pandas as pd
import pytest

from src.backtest.walkforward import SeasonResult, run_season, write_report
from src.features.rolling import baseline_mu
from src.sim.scoring import _rule, load_rules

SEASON = 2026
ROUNDS = [1, 2, 3, 4, 5, 6]
DRIVERS = [f"D{i}" for i in range(1, 11)]
CONSTRUCTORS = ["C1", "C2", "C3"]


@pytest.fixture
def rules():
    return load_rules(2026)


def _kind(asset_id):
    return "driver" if asset_id.startswith("D") else "constructor"


def _prices(r):
    # Drivers 9.0-12.0 (cycled), constructors 8-10. Every price rises 0.5 from round 2 on.
    base = {d: 9.0 + 0.5 * (i % 7) for i, d in enumerate(DRIVERS)}
    base.update({"C1": 10.0, "C2": 9.0, "C3": 8.0})
    bump = 0.5 if r >= 2 else 0.0
    return {a: p + bump for a, p in base.items()}


def _mus(r):
    # Round 1 favours D1-D5 (boost D1). Round 2 on favours D6-D10 (boost D6). C1 and C2 always win.
    if r == 1:
        drivers = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    else:
        drivers = [1, 2, 3, 4, 5, 100, 99, 98, 97, 96]
    mus = dict(zip(DRIVERS, map(float, drivers)))
    mus.update({"C1": 50.0, "C2": 40.0, "C3": 30.0})
    return mus


def _total(r, asset_id):
    # Actual fantasy points: integers, distinct per asset and round.
    return float(10 * r + int(asset_id[1:]) + (50 if asset_id.startswith("C") else 0))


def _frame(r):
    prices, mus = _prices(r), _mus(r)
    return pd.DataFrame([{"asset_id": a, "kind": _kind(a), "price": prices[a], "mu": mus[a]}
                         for a in prices])


def _tables(completed=ROUNDS):
    races = pd.DataFrame({"season": SEASON, "round": ROUNDS,
                          "completed": [r in completed for r in ROUNDS]})
    prices = pd.DataFrame([{"season": SEASON, "round": r, "asset_id": a, "kind": _kind(a), "price": p}
                           for r in ROUNDS for a, p in _prices(r).items()])
    points = pd.DataFrame([{"season": SEASON, "round": r, "asset_id": a, "kind": _kind(a),
                            "total": _total(r, a)}
                           for r in completed for a in _prices(r)])
    return {"races": races, "prices": prices, "fantasy_points": points}


def _spy():
    calls = []

    def predict(season, r):
        calls.append((season, r))
        return _frame(r)

    return calls, predict


def test_actual_points_counts_boost_and_penalty(rules):
    result = run_season(SEASON, _tables(), rules, _spy()[1])
    boost_mult = _rule(rules, "team.boost_multiplier")
    penalty = _rule(rules, "transfers.penalty")
    free = _rule(rules, "transfers.free")
    r1, r2 = result.rounds[0], result.rounds[1]

    # Round 1: no transfers. The boost driver's points are counted (boost_mult - 1) extra times.
    assert set(r1.decision.drivers) == {f"D{i}" for i in range(1, 6)}
    assert set(r1.decision.constructors) == {"C1", "C2"}
    assert r1.decision.boost == "D1"
    team1 = [*r1.decision.drivers, *r1.decision.constructors]
    assert r1.actual_points == pytest.approx(
        sum(_total(1, a) for a in team1) + (boost_mult - 1) * _total(1, "D1"))

    # Round 2: all five drivers are new, so the transfers beyond the free ones are penalised.
    assert set(r2.decision.drivers) == {f"D{i}" for i in range(6, 11)}
    assert r2.decision.boost == "D6"
    assert r2.decision.penalty_transfers == max(0, 5 - free)
    assert r2.decision.penalty_transfers > 0
    team2 = [*r2.decision.drivers, *r2.decision.constructors]
    assert r2.actual_points == pytest.approx(
        sum(_total(2, a) for a in team2) + (boost_mult - 1) * _total(2, "D6")
        - penalty * r2.decision.penalty_transfers)


def test_state_carries_between_rounds(rules):
    result = run_season(SEASON, _tables(), rules, _spy()[1])
    p1, p2 = _prices(1), _prices(2)
    team1 = [*result.rounds[0].decision.drivers, *result.rounds[0].decision.constructors]
    bank1 = _rule(rules, "team.budget") - sum(p1[a] for a in team1)
    # Round 1 team is valued at round 2 prices: 31.0 bank + 72.5 = 103.5.
    assert result.rounds[1].decision.budget == pytest.approx(bank1 + sum(p2[a] for a in team1))


def test_predictor_gets_no_future_points(rules):
    calls, predict = _spy()
    run_season(SEASON, _tables(), rules, predict)
    assert calls == [(SEASON, r) for r in ROUNDS]


def test_incomplete_rounds_skipped(rules):
    calls, predict = _spy()
    result = run_season(SEASON, _tables(completed=[1, 2, 3, 5, 6]), rules, predict)
    assert calls == [(SEASON, r) for r in [1, 2, 3, 5, 6]]
    assert [r.round for r in result.rounds] == [1, 2, 3, 5, 6]


def test_asset_without_points_row_scores_zero(rules):
    full = run_season(SEASON, _tables(), rules, _spy()[1])
    assert "D3" in full.rounds[0].decision.drivers

    tables = _tables()
    fp = tables["fantasy_points"]
    tables["fantasy_points"] = fp[~((fp["round"] == 1) & (fp["asset_id"] == "D3") & (fp["kind"] == "driver"))]
    missing = run_season(SEASON, tables, rules, _spy()[1])

    assert missing.rounds[0].decision == full.rounds[0].decision
    assert missing.rounds[0].actual_points == pytest.approx(
        full.rounds[0].actual_points - _total(1, "D3"))


def test_totals_overall_and_from_round_five(rules):
    result = run_season(SEASON, _tables(), rules, _spy()[1])
    actual = [r.actual_points for r in result.rounds]
    assert len(actual) == 6
    assert result.total == pytest.approx(sum(actual))
    assert result.total_from_round_5 == pytest.approx(actual[4] + actual[5])
    assert result.assumptions == list(rules.get("assumed", []))


def test_report_prints_assumptions(tmp_path):
    assumed = load_rules(2023)["assumed"]
    assert assumed  # rules_2023 lists at least one assumed rule
    result = SeasonResult(season=2023, rounds=[], total=0.0, total_from_round_5=0.0,
                          assumptions=list(assumed))
    path = tmp_path / "reports" / "baseline_2023.md"
    write_report(result, path)
    text = path.read_text(encoding="utf-8")
    assert "Assumed rules:" in text
    for rule in assumed:
        assert rule in text


WINDOW = 5
LOCK_0 = pd.Timestamp("2026-03-01T12:00:00Z")


def _lock(r):
    return LOCK_0 + pd.Timedelta(days=7 * (r - 1))


def _full_tables():
    # Every round completed. Points are known one day after each lock, so they are
    # known before the next round's lock only.
    races = pd.DataFrame({"season": SEASON, "round": ROUNDS, "completed": True,
                          "lock_utc": [_lock(r) for r in ROUNDS]})
    prices = pd.DataFrame([{"season": SEASON, "round": r, "asset_id": a, "kind": _kind(a), "price": p}
                           for r in ROUNDS for a, p in _prices(r).items()])
    points = pd.DataFrame([{"season": SEASON, "round": r, "asset_id": a, "kind": _kind(a),
                            "total": _total(r, a), "known_at": _lock(r) + pd.Timedelta(days=1)}
                           for r in ROUNDS for a in _prices(r)])
    return {"races": races, "prices": prices, "fantasy_points": points}


def test_earlier_decisions_ignore_later_data(rules):
    def predictor(tables):
        return lambda season, r: baseline_mu(tables["prices"], tables["fantasy_points"],
                                             tables["races"], season, r, WINDOW)

    tables = _full_tables()
    first = run_season(SEASON, tables, rules, predictor(tables))

    # Wild round-5 values: points for a driver picked in round 5, and a price for another driver.
    scored = first.rounds[4].decision.drivers[0]
    priced = next(d for d in DRIVERS if d != scored)
    changed = _full_tables()
    fp = changed["fantasy_points"]
    fp.loc[(fp["round"] == 5) & (fp["asset_id"] == scored), "total"] = 9999.0
    pr = changed["prices"]
    pr.loc[(pr["round"] == 5) & (pr["asset_id"] == priced), "price"] = 999.0
    second = run_season(SEASON, changed, rules, predictor(changed))

    for before, after in zip(first.rounds[:4], second.rounds[:4]):
        assert after.round == before.round
        assert after.decision == before.decision
        assert after.actual_points == before.actual_points
    # The wild values reached round 5, so the comparison above is not vacuous.
    assert ((second.rounds[4].decision, second.rounds[4].actual_points)
            != (first.rounds[4].decision, first.rounds[4].actual_points))
