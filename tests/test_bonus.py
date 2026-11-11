import pandas as pd

from src.models.bonus import sample_bonus


def history():
    rows = []
    for r in range(1, 11):
        for i, code in enumerate(["A", "B", "C"]):
            rows.append({"season": 2026, "round": r, "driver_code": code,
                         "constructor_id": f"T{i // 2}", "fastest_lap": code == "A",
                         "dotd": code == "B", "pit_points": float(i),
                         "known_at": pd.Timestamp(f"2026-03-{r:02d}", tz="UTC")})
    return pd.DataFrame(rows)


def call(hist, seed=2):
    return sample_bonus(hist, 11, ["A", "B", "C"], {"A": "T0", "B": "T0", "C": "T1"},
                        ["T0", "T1"], target_lock="2026-12-01T00:00:00Z", seed=seed, min_history=3)


def test_fixed_seed_and_valid_outcomes():
    first = call(history())
    assert first == call(history())
    assert first.status == "supported"
    assert first.fastest_lap_driver in {"A", "B", "C"}
    assert first.driver_of_the_day in {"A", "B", "C"}
    assert set(first.constructor_pit_points) <= {"T0", "T1"}


def test_no_future_round_or_post_lock_leakage():
    hist = history()
    future = hist.iloc[[0]].copy()
    future["round"] = 11
    future["fastest_lap"] = False
    late = hist.iloc[[0]].copy()
    late["known_at"] = pd.Timestamp("2027-01-01", tz="UTC")
    target_time = "2026-12-01T00:00:00Z"
    a = sample_bonus(hist, 11, ["A", "B", "C"], {}, ["T0", "T1"], target_lock=target_time,
                     seed=5, min_history=3)
    b = sample_bonus(pd.concat([hist, future, late]), 11, ["A", "B", "C"], {}, ["T0", "T1"],
                     target_lock=target_time, seed=5, min_history=3)
    assert a == b


def test_unsupported_when_sources_missing():
    outcome = sample_bonus(pd.DataFrame(), 11, ["A"], {}, ["T0"],
                           target_lock="2026-12-01T00:00:00Z")
    assert outcome.status == "unsupported"
