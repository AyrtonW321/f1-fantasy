import numpy as np
import pandas as pd
import pytest

from src.features.guard import LeakageError
from src.features.pace import practice_pace, quali_pace, race_pace

KA = pd.Timestamp("2025-03-01T12:00:00Z")          # practice known_at (usable)
LOCK = pd.Timestamp("2025-03-02T14:00:00Z")        # lock of round 1
KA_RACE = pd.Timestamp("2025-03-02T12:00:00Z")     # race known_at (report only)

LAP_COLS = [
    "season", "round", "session", "driver_code", "constructor_id", "lap_number",
    "lap_time_s", "stint", "compound", "tyre_life", "is_accurate", "track_status",
    "in_lap", "out_lap", "known_at",
]
SESSION_COLS = ["season", "round", "session", "start_utc", "known_at", "usable_pre_lock"]
PRACTICE_COLS = [
    "season", "round", "driver_code", "constructor_id", "long_run_alpha_s",
    "long_run_gap_pct", "long_run_laps", "short_run_gap_pct", "known_at",
]
RACE_COLS = ["driver_code", "constructor_id", "race_gap_pct", "clean_laps", "known_at"]
QUALI_COLS = ["driver_code", "constructor_id", "quali_gap_pct", "known_at"]


def races_frame(lock=LOCK):
    return pd.DataFrame({"season": [2025], "round": [1], "lock_utc": [lock]})


def session_row(session, known_at=KA, usable=True):
    return {"season": 2025, "round": 1, "session": session,
            "start_utc": known_at - pd.Timedelta(hours=2),
            "known_at": known_at, "usable_pre_lock": usable}


def sessions_frame(*rows):
    return pd.DataFrame(list(rows), columns=SESSION_COLS)


def lap(driver, lap_number, t, *, session="FP2", stint=1, compound="MEDIUM",
        constructor="ferrari", in_lap=False, out_lap=False, track="1", known_at=KA):
    return {"season": 2025, "round": 1, "session": session, "driver_code": driver,
            "constructor_id": constructor, "lap_number": lap_number, "lap_time_s": t,
            "stint": stint, "compound": compound, "tyre_life": float(lap_number),
            "is_accurate": True, "track_status": track, "in_lap": in_lap,
            "out_lap": out_lap, "known_at": known_at}


def make_stint(driver, stint_no, first_lap, base, n, slope=0.0, **kw):
    """n green laps with lap_time = base + slope * k for k = 0..n-1."""
    return [lap(driver, first_lap + k, base + slope * k, stint=stint_no, **kw)
            for k in range(n)]


def laps_frame(rows):
    return pd.DataFrame(rows, columns=LAP_COLS)


def run_practice(rows, sessions=None, lock=LOCK, params=None):
    if sessions is None:
        sessions = sessions_frame(session_row("FP2"))
    return practice_pace(laps_frame(rows), sessions, races_frame(lock), 2025, 1, params=params)


def test_long_run_recovers_known_alpha():
    rows = make_stint("VER", 1, 1, 90.0, 8, slope=0.05)
    out = run_practice(rows).set_index("driver_code")
    assert out.loc["VER", "long_run_alpha_s"] == pytest.approx(90.0)
    assert out.loc["VER", "long_run_laps"] == 8


def test_stint_below_min_laps_gives_nan():
    rows = make_stint("VER", 1, 1, 90.0, 5, slope=0.05)
    out = run_practice(rows).set_index("driver_code")
    assert pd.isna(out.loc["VER", "long_run_alpha_s"])
    assert pd.isna(out.loc["VER", "long_run_laps"])


def test_stint_at_min_laps_is_fitted():
    rows = make_stint("VER", 1, 1, 90.0, 6, slope=0.05)
    out = run_practice(rows).set_index("driver_code")
    assert out.loc["VER", "long_run_alpha_s"] == pytest.approx(90.0)


def test_in_out_and_yellow_laps_excluded():
    clean = make_stint("VER", 1, 1, 90.0, 8, slope=0.05)
    # Absurd times on an out lap (first), an in lap and a yellow lap (last).
    # Boundary placement keeps the fitted laps identical to the clean run.
    noisy = clean + [
        lap("VER", 0, 150.0, out_lap=True),
        lap("VER", 9, 200.0, in_lap=True),
        lap("VER", 10, 130.0, track="4"),
    ]
    pd.testing.assert_frame_equal(run_practice(clean), run_practice(noisy))
    out = run_practice(noisy).set_index("driver_code")
    assert out.loc["VER", "long_run_laps"] == 8


def test_compound_offset_corrects_soft_vs_medium():
    rows = (make_stint("VER", 1, 1, 90.0, 6, compound="MEDIUM")
            + make_stint("VER", 2, 7, 89.0, 6, compound="SOFT")
            + make_stint("HAM", 1, 1, 89.5, 6, compound="SOFT")
            + make_stint("LEC", 1, 1, 90.0, 6, compound="MEDIUM"))
    out = run_practice(rows).set_index("driver_code")
    # MEDIUM is the reference (2 stints, tie with SOFT broken alphabetically).
    # delta_SOFT = 89.0 - 90.0 = -1.0 from VER, so HAM's SOFT stint becomes 89.5 + 1.0.
    assert out.loc["HAM", "long_run_alpha_s"] == pytest.approx(90.5)
    assert out.loc["VER", "long_run_alpha_s"] == pytest.approx(90.0)
    assert out.loc["VER", "long_run_laps"] == 12
    assert out.loc["LEC", "long_run_alpha_s"] == pytest.approx(90.0)


def test_stint_without_estimable_offset_is_dropped():
    rows = (make_stint("VER", 1, 1, 90.0, 6, compound="MEDIUM")
            + make_stint("HAM", 1, 1, 89.5, 6, compound="SOFT"))
    out = run_practice(rows).set_index("driver_code")
    assert out.loc["VER", "long_run_alpha_s"] == pytest.approx(90.0)
    assert pd.isna(out.loc["HAM", "long_run_alpha_s"])
    assert pd.isna(out.loc["HAM", "long_run_laps"])


def test_fit_is_full_rank_for_fresh_tyre_stint():
    # Fresh tyre: tyre_life rises with lap_number. The fit must still give a finite alpha.
    rows = make_stint("VER", 1, 1, 90.0, 8, slope=0.05)
    out = run_practice(rows).set_index("driver_code")
    assert np.isfinite(out.loc["VER", "long_run_alpha_s"])
    assert out.loc["VER", "long_run_alpha_s"] == pytest.approx(90.0)


def test_gap_is_percent_of_field_median():
    rows = (make_stint("VER", 1, 1, 90.0, 6)
            + make_stint("HAM", 1, 1, 91.0, 6)
            + make_stint("LEC", 1, 1, 92.0, 6))
    out = run_practice(rows).set_index("driver_code")
    assert out.loc["HAM", "long_run_gap_pct"] == pytest.approx(0.0)
    assert out.loc["VER", "long_run_gap_pct"] == pytest.approx(100 * (90.0 - 91.0) / 91.0)
    assert out.loc["LEC", "long_run_gap_pct"] == pytest.approx(100 * (92.0 - 91.0) / 91.0)


def test_sprint_weekend_has_no_long_run_values():
    # Only FP1 is usable; there is no FP2 at all.
    sessions = sessions_frame(session_row("FP1"))
    rows = (make_stint("VER", 1, 1, 91.0, 3, session="FP1")
            + make_stint("HAM", 1, 1, 92.0, 3, session="FP1"))
    out = run_practice(rows, sessions=sessions).set_index("driver_code")
    assert pd.isna(out.loc["VER", "long_run_alpha_s"])
    assert pd.isna(out.loc["VER", "long_run_gap_pct"])
    assert pd.isna(out.loc["VER", "long_run_laps"])
    assert out.loc["VER", "short_run_gap_pct"] == pytest.approx(0.0)
    assert out.loc["HAM", "short_run_gap_pct"] == pytest.approx(100 * (92.0 - 91.0) / 91.0)


def test_short_run_uses_only_pre_lock_sessions():
    sessions = sessions_frame(
        session_row("FP1", known_at=KA, usable=True),
        session_row("FP3", known_at=pd.Timestamp("2025-03-02T16:00:00Z"), usable=False),
    )
    rows = [
        lap("VER", 1, 91.0, session="FP1"),
        lap("HAM", 1, 91.5, session="FP1"),
        # FP3 is after lock: HAM is faster here, but must be ignored.
        lap("HAM", 1, 90.0, session="FP3", known_at=pd.Timestamp("2025-03-02T16:00:00Z")),
    ]
    out = run_practice(rows, sessions=sessions).set_index("driver_code")
    assert out.loc["VER", "short_run_gap_pct"] == pytest.approx(0.0)
    assert out.loc["HAM", "short_run_gap_pct"] == pytest.approx(100 * (91.5 - 91.0) / 91.0)
    assert out.loc["HAM", "known_at"] == KA


def race_laps(driver, n_clean, t):
    rows = [lap(driver, 1, 200.0, session="R", known_at=KA_RACE)]  # lap 1 excluded
    rows += [lap(driver, k + 2, t, session="R", known_at=KA_RACE) for k in range(n_clean)]
    return rows


def test_race_pace_requires_clean_laps():
    rows = race_laps("VER", 20, 80.0) + race_laps("LEC", 15, 81.0) + race_laps("HAM", 14, 81.5)
    out = race_pace(laps_frame(rows), 2025, 1).set_index("driver_code")
    assert out.loc["VER", "clean_laps"] == 20
    assert out.loc["HAM", "clean_laps"] == 14
    assert pd.isna(out.loc["HAM", "race_gap_pct"])
    # Field median over VER (80.0) and LEC (81.0) = 80.5.
    assert out.loc["VER", "race_gap_pct"] == pytest.approx(100 * (80.0 - 80.5) / 80.5)
    assert out.loc["LEC", "race_gap_pct"] == pytest.approx(100 * (81.0 - 80.5) / 80.5)
    assert (out["known_at"] == KA_RACE).all()


def test_race_pace_min_clean_laps_is_a_parameter():
    rows = race_laps("VER", 20, 80.0) + race_laps("LEC", 15, 81.0) + race_laps("HAM", 14, 81.5)
    out = race_pace(laps_frame(rows), 2025, 1,
                    params={"race_clean_laps_min": 14}).set_index("driver_code")
    assert not pd.isna(out.loc["HAM", "race_gap_pct"])


def test_quali_gap_zero_for_pole():
    rows = [
        lap("VER", 1, 90.5, session="Q"),
        lap("VER", 2, 90.0, session="Q"),
        lap("HAM", 1, 90.3, session="Q"),
        lap("HAM", 2, np.nan, session="Q"),
        lap("LEC", 1, np.nan, session="Q"),
    ]
    out = quali_pace(laps_frame(rows), 2025, 1).set_index("driver_code")
    assert out.loc["VER", "quali_gap_pct"] == 0.0
    assert out.loc["HAM", "quali_gap_pct"] == pytest.approx(100 * (90.3 - 90.0) / 90.0)
    assert pd.isna(out.loc["LEC", "quali_gap_pct"])
    assert (out["known_at"] == KA).all()


def test_no_usable_practice_gives_empty_frame_with_columns():
    sessions = sessions_frame(session_row("FP2", usable=False))
    out = run_practice(make_stint("VER", 1, 1, 90.0, 8), sessions=sessions)
    assert list(out.columns) == PRACTICE_COLS
    assert len(out) == 0


def test_output_known_at_after_lock_raises_leakage_error():
    late = LOCK + pd.Timedelta(hours=1)
    sessions = sessions_frame(session_row("FP2", known_at=late, usable=True))
    rows = make_stint("VER", 1, 1, 90.0, 8, known_at=late)
    with pytest.raises(LeakageError):
        run_practice(rows, sessions=sessions)


def test_dropped_slow_laps_do_not_distort_slope():
    # lap_time = 90.0 + 0.05 * (lap_number - 1); laps 2-4 are slow traffic laps and are dropped.
    slow = {2, 3, 4}
    rows = [lap("VER", n, 90.0 + 0.05 * (n - 1) + (15.0 if n in slow else 0.0), stint=1) for n in range(1, 11)]
    out = run_practice(rows).set_index("driver_code")
    assert out.loc["VER", "long_run_alpha_s"] == pytest.approx(90.0)
    assert out.loc["VER", "long_run_laps"] == 7


def test_short_run_ignores_in_and_out_laps():
    rows = [lap("VER", 1, 95.0), lap("VER", 2, 80.0, in_lap=True), lap("VER", 3, 81.0, out_lap=True),
            lap("HAM", 1, 96.0)]
    sessions = sessions_frame(session_row("FP1"))
    rows = [{**r, "session": "FP1"} for r in rows]
    out = run_practice(rows, sessions=sessions).set_index("driver_code")
    assert out.loc["VER", "short_run_gap_pct"] == pytest.approx(0.0)
    assert out.loc["HAM", "short_run_gap_pct"] == pytest.approx(100 * (96.0 - 95.0) / 95.0)
