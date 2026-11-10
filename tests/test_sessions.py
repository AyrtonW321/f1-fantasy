import json
from pathlib import Path

import pandas as pd
import pytest

from src.ingest.build_tables import build_sessions

DELAYS = {"practice": 120, "qualifying": 120, "sprint": 120, "race": 360}


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def schedule(rnd, name, date, time, **sessions):
    race = {"season": "2026", "round": str(rnd), "raceName": name, "date": date, "time": time}
    for key, (d, t) in sessions.items():
        race[key] = {"date": d, "time": t}
    return race


def write_races(raw, season, races):
    _write(raw / "jolpica" / str(season) / "races.json", races)


def by_code(df):
    return {row["session"]: row for _, row in df.iterrows()}


def test_standard_weekend_has_fp1_fp2_fp3_q_r(tmp_path):
    write_races(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z",
                 FirstPractice=("2026-03-06", "01:30:00Z"),
                 SecondPractice=("2026-03-06", "05:00:00Z"),
                 ThirdPractice=("2026-03-07", "01:30:00Z"),
                 Qualifying=("2026-03-07", "05:00:00Z")),
    ])
    sessions = build_sessions(2026, tmp_path, delays=DELAYS)
    assert set(sessions["session"]) == {"FP1", "FP2", "FP3", "Q", "R"}
    assert len(sessions) == 5


def test_sprint_weekend_has_fp1_sq_s_q_r_and_no_fp2(tmp_path):
    write_races(tmp_path, 2026, [
        schedule(2, "Chinese Grand Prix", "2026-03-15", "07:00:00Z",
                 FirstPractice=("2026-03-13", "03:30:00Z"),
                 SprintQualifying=("2026-03-13", "07:30:00Z"),
                 Sprint=("2026-03-14", "03:00:00Z"),
                 Qualifying=("2026-03-14", "07:00:00Z")),
    ])
    sessions = build_sessions(2026, tmp_path, delays=DELAYS)
    assert set(sessions["session"]) == {"FP1", "SQ", "S", "Q", "R"}
    assert "FP2" not in set(sessions["session"])


def test_known_at_is_start_plus_configured_delay(tmp_path):
    write_races(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z",
                 SecondPractice=("2026-03-06", "15:00:00Z"),
                 Qualifying=("2026-03-07", "05:00:00Z")),
    ])
    sessions = build_sessions(2026, tmp_path, delays=DELAYS)
    rows = by_code(sessions)
    assert rows["FP2"]["start_utc"] == pd.Timestamp("2026-03-06T15:00:00Z")
    assert rows["FP2"]["known_at"] == pd.Timestamp("2026-03-06T17:00:00Z")
    assert rows["R"]["known_at"] == pd.Timestamp("2026-03-08T10:00:00Z")


def test_known_at_uses_config_delays_when_not_passed(tmp_path):
    # Default delays come from config/model.yaml: practice 120 min, race 360 min.
    write_races(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z",
                 SecondPractice=("2026-03-06", "15:00:00Z"),
                 Qualifying=("2026-03-07", "05:00:00Z")),
    ])
    rows = by_code(build_sessions(2026, tmp_path))
    assert rows["FP2"]["known_at"] == pd.Timestamp("2026-03-06T17:00:00Z")
    assert rows["R"]["known_at"] == pd.Timestamp("2026-03-08T10:00:00Z")


def test_practice_after_lock_not_usable(tmp_path):
    # Lock is Qualifying at 05:00Z on Saturday. FP3 starts at 06:00Z, after the lock.
    write_races(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z",
                 FirstPractice=("2026-03-06", "01:30:00Z"),
                 ThirdPractice=("2026-03-07", "06:00:00Z"),
                 Qualifying=("2026-03-07", "05:00:00Z")),
    ])
    rows = by_code(build_sessions(2026, tmp_path, delays=DELAYS))
    assert rows["FP3"]["usable_pre_lock"] == False  # noqa: E712
    assert rows["FP1"]["usable_pre_lock"] == True  # noqa: E712


def test_fp1_before_sprint_qualifying_is_usable(tmp_path):
    write_races(tmp_path, 2026, [
        schedule(2, "Chinese Grand Prix", "2026-03-15", "07:00:00Z",
                 FirstPractice=("2026-03-13", "03:30:00Z"),
                 SprintQualifying=("2026-03-13", "07:30:00Z"),
                 Sprint=("2026-03-14", "03:00:00Z"),
                 Qualifying=("2026-03-14", "07:00:00Z")),
    ])
    rows = by_code(build_sessions(2026, tmp_path, delays=DELAYS))
    assert rows["FP1"]["usable_pre_lock"] == True  # noqa: E712
    # SQ is the lock session itself, so its known_at (start + 2h) is after the lock.
    assert rows["SQ"]["usable_pre_lock"] == False  # noqa: E712


def test_missing_time_raises_value_error_naming_round(tmp_path):
    race = schedule(3, "Japanese Grand Prix", "2026-03-29", "05:00:00Z",
                    Qualifying=("2026-03-28", "06:00:00Z"))
    race["FirstPractice"] = {"date": "2026-03-27"}
    write_races(tmp_path, 2026, [race])
    with pytest.raises(ValueError, match="2026 round 3") as excinfo:
        build_sessions(2026, tmp_path, delays=DELAYS)
    assert "FirstPractice" in str(excinfo.value)


def test_sprint_shootout_maps_to_sq(tmp_path):
    write_races(tmp_path, 2023, [
        schedule(4, "Azerbaijan Grand Prix", "2023-04-30", "11:00:00Z",
                 Qualifying=("2023-04-28", "12:00:00Z"),
                 SprintShootout=("2023-04-29", "15:00:00Z"),
                 Sprint=("2023-04-29", "11:00:00Z")),
    ])
    sessions = build_sessions(2023, tmp_path, delays=DELAYS)
    assert set(sessions["session"]) == {"SQ", "S", "Q", "R"}
    assert "SprintShootout" not in set(sessions["session"])


def test_output_columns_and_season(tmp_path):
    write_races(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z",
                 Qualifying=("2026-03-07", "05:00:00Z")),
    ])
    sessions = build_sessions(2026, tmp_path, delays=DELAYS)
    assert list(sessions.columns) == ["season", "round", "session", "start_utc", "known_at", "usable_pre_lock"]
    assert sessions["season"].tolist() == [2026, 2026]
    assert sessions["usable_pre_lock"].dtype == bool
