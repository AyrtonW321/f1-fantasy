import numpy as np
import pandas as pd
import pytest

from src.features.rolling import robust_mu
from src.sim.montecarlo import point_tables, sim_mu, simulate
from src.sim.scoring import DriverLine, load_rules, score_constructor, score_driver

RULES = load_rules(2026)
TEAMS = {"ferrari": ("FER", ["LEC", "HAM"]), "mercedes": ("MER", ["RUS", "ANT"]), "mclaren": ("MCL", ["NOR", "PIA"])}


def _world(rounds=6, seed=1):
    rng = np.random.default_rng(seed)
    races = pd.DataFrame({"season": 2026, "round": range(1, rounds + 1), "completed": True,
                          "lock_utc": pd.date_range("2026-03-08", periods=rounds, freq="7D", tz="UTC")})
    results, prices, points = [], [], []
    for r, t in zip(races["round"], races["lock_utc"]):
        order = rng.permutation([(c, d) for c, (_, ds) in TEAMS.items() for d in ds])
        for pos, (c, d) in enumerate(order, 1):
            status = "Retired" if rng.random() < 0.15 else "Finished"
            results.append(dict(season=2026, round=r, session="race", driver_code=d, constructor_id=c,
                                position=pos, grid=pos, status=status, known_at=t + pd.offsets.Day(1)))
        for c, (code, ds) in TEAMS.items():
            for a, kind in [(code, "constructor"), *[(d, "driver") for d in ds]]:
                prices.append(dict(season=2026, round=r, asset_id=a, kind=kind, price=float(rng.uniform(5, 30)),
                                   known_at=t))
                points.append(dict(season=2026, round=r, asset_id=a, kind=kind, total=float(rng.integers(-20, 40)),
                                   known_at=t + pd.offsets.Day(1)))
    return races, pd.DataFrame(results), pd.DataFrame(prices), pd.DataFrame(points)


def _predict(races, results, prices, points, round_=5, seed=0):
    return sim_mu(prices, points, results, races, 2026, round_, RULES, trim=0.3, prior_weight=2.0, seed=seed)


def test_hand_built_draw_matches_scoring_engine():
    drv, con = point_tables(RULES, 4)
    rank = np.array([0, 2, 4, 1])  # P1, P3, not classified, P2
    lines = [DriverLine("A", "race", position=1), DriverLine("B", "race", position=3),
             DriverLine("C", "race", not_classified=True), DriverLine("D", "race", position=2)]
    assert drv[rank].tolist() == [score_driver(RULES, l) for l in lines] == [25, 15, -20, 18]
    # Constructor of drivers A and C: one line each, summed.
    assert con[rank[0]] + con[rank[2]] == score_constructor(RULES, [lines[0], lines[2]])


def test_simulate_every_entrant_once_and_seed_reproduces():
    s, p = np.array([1.0, 0.5, 0.0, -0.5, -1.0]), np.full(5, 0.2)
    a, b = simulate(s, p, 400, seed=3), simulate(s, p, 400, seed=3)
    assert (a == b).all()
    for row in a:
        classified = np.sort(row[row < 5])
        assert (classified == np.arange(len(classified))).all()  # survivors fill P1..Pk exactly once
    assert 0.1 < (a == 5).mean() < 0.3


def test_sim_mu_reproducible_and_uses_simulator():
    races, results, prices, points = _world()
    a = _predict(races, results, prices, points)
    pd.testing.assert_frame_equal(a, _predict(races, results, prices, points))
    base = robust_mu(prices, points, races, 2026, 5, 0.3, 2.0)
    assert len(a) == 9 and not np.allclose(a["mu"], base["mu"])


def test_sim_mu_never_reads_target_round_or_later():
    races, results, prices, points = _world()
    before = _predict(races, results, prices, points)
    late = results["round"] >= 5
    results.loc[late, "position"] = results.loc[late, "position"].to_numpy()[::-1]
    results.loc[late, "status"] = "Retired"
    points.loc[points["round"] >= 5, "total"] += 100
    prices.loc[prices["round"] >= 6, "price"] += 50
    pd.testing.assert_frame_equal(before, _predict(races, results, prices, points))


def test_early_rounds_fall_back_to_robust_form():
    races, results, prices, points = _world()
    pd.testing.assert_frame_equal(_predict(races, results, prices, points, round_=3),
                                  robust_mu(prices, points, races, 2026, 3, 0.3, 2.0))


@pytest.mark.data
def test_sim_mu_on_real_2026_round():
    from pathlib import Path
    if not Path("data/processed/results.parquet").exists():
        pytest.skip("data/processed absent")
    t = {n: pd.read_parquet(f"data/processed/{n}.parquet") for n in ("races", "prices", "fantasy_points", "results")}
    out = sim_mu(t["prices"], t["fantasy_points"], t["results"], t["races"], 2026, 12, RULES,
                 trim=0.3, prior_weight=2.0)
    assert out["mu"].notna().all() and len(out) == len(t["prices"].query("season == 2026 and round == 12"))


def test_quali_sim_reproducible_and_scores_qualifying():
    races, results, prices, points = _world()
    q = results[results["session"] == "race"].assign(session="qualifying", status=None)
    results = pd.concat([results, q], ignore_index=True)
    a = sim_mu(prices, points, results, races, 2026, 5, RULES, trim=0.3, prior_weight=2.0, quali=True, seed=0)
    b = sim_mu(prices, points, results, races, 2026, 5, RULES, trim=0.3, prior_weight=2.0, quali=True, seed=0)
    pd.testing.assert_frame_equal(a, b)
    assert not a["mu"].isna().any()
