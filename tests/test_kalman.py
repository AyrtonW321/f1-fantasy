import numpy as np
import pandas as pd
import pytest

from src.models.kalman import StrengthFilter, run_season

SEASON = 2025
OBS_COLUMNS = ["season", "round", "driver_code", "constructor_id", "y", "kind", "known_at"]


def make_params(**overrides):
    params = {
        "q_car": 0.0225,
        "q_driver": 0.0001,
        "q_first_round_multiplier": 1.0,
        "p0_car": 1.0,
        "p0_driver": 0.04,
        "sigma": {
            "race": 0.1,
            "qualifying": 0.2,
            "practice_long_run": 0.5,
            "practice_short_run": 0.6,
        },
        "prior_2025_weight": 0.0,
    }
    params.update(overrides)
    return params


def make_races(n_rounds, season=SEASON):
    rows = []
    for k in range(1, n_rounds + 1):
        lock = (
            pd.Timestamp(f"{season}-03-01", tz="UTC")
            + pd.Timedelta(days=7 * (k - 1))
            + pd.Timedelta(hours=12)
        )
        rows.append({"season": season, "round": k, "lock_utc": lock})
    return pd.DataFrame(rows)


def lock_of(races, r):
    return races.loc[races["round"] == r, "lock_utc"].iloc[0]


def race_row(races, r, driver, constructor, y, season=SEASON, delay_hours=30):
    """Race of weekend r. Known 30h after its lock: after round r's lock, before round r+1's."""
    return {
        "season": season,
        "round": r,
        "driver_code": driver,
        "constructor_id": constructor,
        "y": y,
        "kind": "race",
        "known_at": lock_of(races, r) + pd.Timedelta(hours=delay_hours),
    }


def obs_frame(rows):
    return pd.DataFrame(rows, columns=OBS_COLUMNS)


def state_row(f, driver):
    return f.state().set_index("driver_code").loc[driver]


def entity_var(f, constructor, driver):
    ents = f.entities()
    P = f.covariance()
    ic = ents.index(("c", constructor))
    idr = ents.index(("d", driver))
    return P[ic, ic] + P[idr, idr] + 2 * P[ic, idr]


DRIVERS = {"A1": "A", "A2": "A", "B1": "B", "B2": "B"}


def test_recovers_known_strengths():
    rng = np.random.default_rng(0)
    races = make_races(11)
    truth = {"A": 1.0, "B": 0.0}
    rows = []
    for r in range(1, 11):
        for driver, constructor in DRIVERS.items():
            y = truth[constructor] + rng.normal(0.0, 0.1)
            rows.append(race_row(races, r, driver, constructor, y))
    out = run_season(SEASON, obs_frame(rows), races, make_params())
    final = out[out["round"] == 11]
    theta = final.groupby("constructor_id")["theta"].first()
    assert abs((theta["A"] - theta["B"]) - 1.0) < 0.15
    strength = final.set_index("driver_code")["strength"]
    a_mean = strength[["A1", "A2"]].mean()
    b_mean = strength[["B1", "B2"]].mean()
    assert a_mean > b_mean


def test_tracks_step_change_faster_with_larger_q():
    rng = np.random.default_rng(0)
    races = make_races(8)
    rows = []
    for r in range(1, 8):
        jump = 1.0 if r >= 6 else 0.0
        for driver, constructor in DRIVERS.items():
            level = jump if constructor == "A" else 0.0
            rows.append(race_row(races, r, driver, constructor, level + rng.normal(0.0, 0.1)))
    obs = obs_frame(rows)

    def theta_a_at_round_8(q_car):
        out = run_season(SEASON, obs, races, make_params(q_car=q_car))
        final = out[out["round"] == 8]
        return final.loc[final["constructor_id"] == "A", "theta"].iloc[0]

    theta_fast = theta_a_at_round_8(0.0225)
    theta_slow = theta_a_at_round_8(1e-8)
    assert abs(theta_fast - 1.0) < abs(theta_slow - 1.0)


def test_unobserved_driver_keeps_mean_and_variance_grows():
    params = make_params()
    f = StrengthFilter(params)
    f.update(obs_frame([
        {"season": SEASON, "round": 1, "driver_code": "D1", "constructor_id": "A", "y": 0.7, "kind": "race", "known_at": 0},
        {"season": SEASON, "round": 1, "driver_code": "D2", "constructor_id": "B", "y": -0.3, "kind": "race", "known_at": 0},
    ]))
    before = state_row(f, "D1").copy()
    var_before = before["var"]
    for _ in range(3):
        f.predict_step()
        f.update(pd.DataFrame([
            {"driver_code": "D2", "constructor_id": "B", "y": -0.3, "kind": "race"},
        ]))
    after = state_row(f, "D1")
    assert after["theta"] == pytest.approx(before["theta"], abs=1e-12)
    assert after["phi"] == pytest.approx(before["phi"], abs=1e-12)
    assert after["var"] - var_before == pytest.approx(3 * (params["q_car"] + params["q_driver"]), rel=1e-9)


def test_mid_season_team_move_keeps_phi_joins_new_theta():
    f = StrengthFilter(make_params())
    # Establish theta_A about 1.0 with D1 phi about 0.5, and theta_B about 0.0 with D3, D4.
    batch = pd.DataFrame([
        {"driver_code": "D1", "constructor_id": "A", "y": 1.5, "kind": "race"},
        {"driver_code": "D2", "constructor_id": "A", "y": 1.0, "kind": "race"},
        {"driver_code": "D3", "constructor_id": "B", "y": 0.0, "kind": "race"},
        {"driver_code": "D4", "constructor_id": "B", "y": 0.0, "kind": "race"},
    ])
    for _ in range(8):
        f.update(batch)
    # Only the within-team difference of phi is identified (about 0.5), so phi_D1 sits near 0.25 to 0.3.
    phi_before = state_row(f, "D1")["phi"]
    assert phi_before > 0.1

    # D1 moves to B. Observation says B's strength for him is about 0.8.
    f.update(pd.DataFrame([{"driver_code": "D1", "constructor_id": "B", "y": 0.8, "kind": "race"}]))
    after = state_row(f, "D1")
    assert after["constructor_id"] == "B"
    assert len(f.state()) == 4
    assert after["phi"] > 0.1          # phi kept, not reset to the prior of 0
    theta_b = f.state().set_index("driver_code").loc["D3", "theta"]
    assert theta_b > 0.05              # new constructor's theta is updated by D1's observation


def test_nan_observation_skipped():
    f = StrengthFilter(make_params())
    f.update(pd.DataFrame([
        {"driver_code": "D1", "constructor_id": "A", "y": 0.5, "kind": "race"},
        {"driver_code": "D2", "constructor_id": "B", "y": -0.2, "kind": "race"},
    ]))
    state_before = f.state()
    cov_before = f.covariance()
    entities_before = f.entities()
    f.update(pd.DataFrame([
        {"driver_code": "D1", "constructor_id": "A", "y": np.nan, "kind": "race"},
        {"driver_code": "D9", "constructor_id": "C", "y": np.nan, "kind": "race"},
    ]))
    pd.testing.assert_frame_equal(f.state(), state_before)
    np.testing.assert_array_equal(f.covariance(), cov_before)
    assert f.entities() == entities_before


def test_covariance_stays_symmetric_and_psd():
    rng = np.random.default_rng(1)
    params = make_params()
    f = StrengthFilter(params)
    constructors = ["A", "B", "C"]
    drivers = [f"D{i}" for i in range(6)]
    kinds = list(params["sigma"])
    for i in range(200):
        rows = []
        for _ in range(int(rng.integers(1, 5))):
            j = int(rng.integers(6))
            rows.append({
                "driver_code": drivers[j],
                "constructor_id": constructors[j % 3],
                "y": float(rng.normal()),
                "kind": kinds[int(rng.integers(4))],
            })
        f.update(pd.DataFrame(rows))
        if i % 5 == 0:
            f.predict_step(q_multiplier=float(rng.uniform(0.5, 2.0)))
    P = f.covariance()
    np.testing.assert_allclose(P, P.T, atol=1e-12)
    assert np.linalg.eigvalsh(P).min() > -1e-10


def test_observation_after_lock_never_used():
    rng = np.random.default_rng(2)
    races = make_races(5)
    rows = []
    for r in range(1, 5):
        for driver, constructor in DRIVERS.items():
            rows.append(race_row(races, r, driver, constructor, constructor_level(constructor) + rng.normal(0.0, 0.1)))
    # Weekend 2 race is known after lock of round 2 and before lock of round 3.
    post_lock = [i for i, row in enumerate(rows) if row["round"] == 2][0]
    assert rows[post_lock]["known_at"] > lock_of(races, 2)

    out = run_season(SEASON, obs_frame(rows), races, make_params())
    mutated = [dict(row) for row in rows]
    mutated[post_lock]["y"] = mutated[post_lock]["y"] + 5.0
    out_mut = run_season(SEASON, obs_frame(mutated), races, make_params())

    pd.testing.assert_frame_equal(
        out[out["round"] == 2].reset_index(drop=True),
        out_mut[out_mut["round"] == 2].reset_index(drop=True),
    )
    round3 = out[out["round"] == 3].reset_index(drop=True)
    round3_mut = out_mut[out_mut["round"] == 3].reset_index(drop=True)
    assert not np.allclose(round3["strength"].to_numpy(), round3_mut["strength"].to_numpy())


def constructor_level(constructor):
    return 1.0 if constructor == "A" else 0.0


def test_round_one_uses_prior_only_with_larger_variance():
    f = StrengthFilter(make_params())
    f.add_entities(["A"], ["D1"])
    ents = f.entities()
    assert f.mean()[ents.index(("c", "A"))] == 0.0
    assert f.mean()[ents.index(("d", "D1"))] == 0.0
    assert entity_var(f, "A", "D1") == pytest.approx(1.0 + 0.04)


def test_round_one_output_is_empty_when_only_post_lock_observations():
    races = make_races(2)
    rows = [race_row(races, 1, "A1", "A", 1.0), race_row(races, 1, "B1", "B", 0.0)]
    out = run_season(SEASON, obs_frame(rows), races, make_params())
    assert out[out["round"] == 1].empty
    assert set(out["round"]) == {2}
    assert len(out) == 2


def test_prior_2025_weight_zero_means_flat_start():
    f = StrengthFilter(make_params(prior_theta={"A": 0.5}, prior_2025_weight=0.0))
    f.add_entities(["A"], [])
    assert f.mean()[f.entities().index(("c", "A"))] == 0.0

    g = StrengthFilter(make_params(prior_theta={"A": 0.5}, prior_2025_weight=1.0))
    g.add_entities(["A"], [])
    assert g.mean()[g.entities().index(("c", "A"))] == pytest.approx(0.5)


def test_season_runner_resets_state_each_season():
    rng = np.random.default_rng(3)
    races = pd.concat([make_races(3, season=2024), make_races(3, season=SEASON)], ignore_index=True)
    rows_2024 = []
    rows_2025 = []
    for r in range(1, 3):
        for driver, constructor in DRIVERS.items():
            rows_2024.append(race_row(races, r, driver, constructor, rng.normal(), season=2024))
            rows_2025.append(race_row(races, r, driver, constructor, rng.normal(), season=SEASON))
    out_2024 = run_season(2024, obs_frame(rows_2024 + rows_2025), races, make_params())
    out_2025 = run_season(SEASON, obs_frame(rows_2024 + rows_2025), races, make_params())
    fresh = run_season(SEASON, obs_frame(rows_2025), races, make_params())
    assert not out_2024.empty
    pd.testing.assert_frame_equal(out_2025.reset_index(drop=True), fresh.reset_index(drop=True))


def test_batch_update_matches_sequential_single_updates():
    rng = np.random.default_rng(4)
    rows = [
        {"driver_code": "D1", "constructor_id": "A", "y": float(rng.normal()), "kind": "race"},
        {"driver_code": "D2", "constructor_id": "A", "y": float(rng.normal()), "kind": "qualifying"},
        {"driver_code": "D3", "constructor_id": "B", "y": float(rng.normal()), "kind": "practice_short_run"},
        {"driver_code": "D4", "constructor_id": "B", "y": float(rng.normal()), "kind": "practice_long_run"},
    ]
    df = pd.DataFrame(rows)
    batch = StrengthFilter(make_params())
    sequential = StrengthFilter(make_params())
    # Same entity layout in both filters, so the covariance matrices are comparable.
    for f in (batch, sequential):
        f.add_entities(["A", "B"], ["D1", "D2", "D3", "D4"])
    batch.update(df)
    for i in range(len(df)):
        sequential.update(df.iloc[[i]])
    pd.testing.assert_frame_equal(batch.state(), sequential.state(), atol=1e-9, rtol=0)
    np.testing.assert_allclose(batch.covariance(), sequential.covariance(), atol=1e-9, rtol=0)


def test_observation_after_lock_used_in_next_round_once_known():
    races = make_races(3)
    rows = []
    for r in range(1, 3):
        for driver, constructor in DRIVERS.items():
            rows.append(race_row(races, r, driver, constructor, constructor_level(constructor)))
    with_obs = run_season(SEASON, obs_frame(rows), races, make_params())
    # Drop the weekend-2 race: it is known only after lock of round 2.
    without = run_season(SEASON, obs_frame([row for row in rows if row["round"] == 1]), races, make_params())
    pd.testing.assert_frame_equal(
        with_obs[with_obs["round"] == 2].reset_index(drop=True),
        without[without["round"] == 2].reset_index(drop=True),
    )
    assert (with_obs.loc[with_obs["round"] == 2, "known_at"] == lock_of(races, 2)).all()
    round3_with = with_obs[with_obs["round"] == 3].set_index("driver_code")["strength"]
    round3_without = without[without["round"] == 3].set_index("driver_code")["strength"]
    assert not np.allclose(round3_with.loc[list(DRIVERS)], round3_without.loc[list(DRIVERS)])
