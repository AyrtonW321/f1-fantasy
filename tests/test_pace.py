import numpy as np
import pandas as pd
import pytest

from src.features.pace import fp2_longrun_pace


def make_rows():
    rows = []
    for stint, compound, lapnums, ages, gamma in [
        (1, "SOFT", [1, 2, 3, 4], [3, 4, 5, 6], 0.05),
        (2, "MEDIUM", [6, 7, 8, 9, 10], [1, 2, 3, 4, 5], 0.07),
    ]:
        for lap, age in zip(lapnums, ages):
            time = 100 + 0.2 * (lap - 6.0) + gamma * (age - (4.5 if compound == "SOFT" else 3.0))
            rows.append({
                "season": 2025, "round": 1, "session_code": "FP2", "driver_code": "AAA",
                "lap_number": lap, "lap_time_s": time, "compound": compound, "tyre_age": age,
                "stint": stint, "pit_in_time": np.nan, "pit_out_time": np.nan,
                "is_accurate": True, "deleted": False, "session_time": lap * 100,
            })
    rows.append({
        "season": 2025, "round": 1, "session_code": "FP2", "driver_code": "BBB",
        "lap_number": 1, "lap_time_s": 95.0, "compound": "SOFT", "tyre_age": 1,
        "stint": 1, "pit_in_time": np.nan, "pit_out_time": np.nan,
        "is_accurate": True, "deleted": False, "session_time": 100,
    })
    return pd.DataFrame(rows)


def tables(lock="2025-03-01T15:00:00Z", fp2=True, end=7200):
    races = pd.DataFrame([{
        "season": 2025, "round": 1, "lock_utc": pd.Timestamp(lock),
    }])
    sessions = pd.DataFrame([{
        "season": 2025, "round": 1, "session_code": "FP2", "scheduled_start_utc": pd.Timestamp("2025-03-01T12:00:00Z"),
        "session_end_time": end,
    }]) if fp2 else pd.DataFrame(columns=["season", "round", "session_code", "scheduled_start_utc", "session_end_time"])
    results = pd.DataFrame({"season": [2025, 2025], "round": [1, 1], "session": ["race", "race"],
                            "driver_code": ["AAA", "BBB"]})
    return races, sessions, results


def test_pace_recovers_centered_reference_pace_and_records_fit_diagnostics():
    races, sessions, results = tables()
    out = fp2_longrun_pace(make_rows(), sessions, races, results)
    aaa = out.loc[out.driver_code.eq("AAA")].iloc[0]
    assert aaa.fit_status == "fit"
    assert aaa.pace_seconds == pytest.approx(100, abs=1e-8)
    assert aaa.beta_seconds_per_lap == pytest.approx(0.2, abs=1e-8)
    assert aaa.stint_count == 2
    assert aaa.compounds == "MEDIUM,SOFT"
    assert aaa.usable_prelock
    assert aaa.known_at <= races.loc[0, "lock_utc"]


def test_emits_every_expected_driver_and_marks_short_stint_missing():
    races, sessions, results = tables()
    out = fp2_longrun_pace(make_rows(), sessions, races, results)
    assert set(out.driver_code) == {"AAA", "BBB"}
    assert out.loc[out.driver_code.eq("BBB"), "fit_status"].iloc[0] == "no_usable_longrun"
    assert pd.isna(out.loc[out.driver_code.eq("BBB"), "pace_seconds"].iloc[0])


def test_missing_fp2_emits_explicit_status_rows():
    races, sessions, results = tables(fp2=False)
    out = fp2_longrun_pace(pd.DataFrame(), sessions, races, results)
    assert len(out) == 2
    assert set(out.fit_status) == {"no_fp2_session"}
    assert not out.usable_prelock.any()
    assert out.known_at.isna().all()


def test_expected_but_unloaded_fp2_is_not_misreported_as_no_session():
    races, sessions, results = tables(fp2=False)
    expected = pd.DataFrame([{"season": 2025, "round": 1, "session_code": "FP2", "status": "not_loaded"}])
    out = fp2_longrun_pace(pd.DataFrame(), sessions, races, results, expected_sessions=expected)
    assert set(out.fit_status) == {"session_not_loaded"}


def test_post_lock_fp2_estimate_is_retained_but_not_usable_prelock():
    races, sessions, results = tables(lock="2025-03-01T13:00:00Z")
    out = fp2_longrun_pace(make_rows(), sessions, races, results)
    aaa = out.loc[out.driver_code.eq("AAA")].iloc[0]
    assert aaa.fit_status == "after_lock"
    assert not aaa.usable_prelock
    assert aaa.pace_seconds == pytest.approx(100, abs=1e-8)


def test_invalid_and_pit_laps_are_excluded():
    races, sessions, results = tables()
    laps = make_rows()
    laps.loc[0, "is_accurate"] = False
    laps.loc[1, "pit_out_time"] = 0.0
    out = fp2_longrun_pace(laps, sessions, races, results)
    aaa = out.loc[out.driver_code.eq("AAA")].iloc[0]
    assert aaa.observations == 5

