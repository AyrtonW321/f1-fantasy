import pandas as pd
import pytest
from datetime import timedelta

from src.ingest.fastf1_pull import (
    FastF1IngestError,
    _available_sessions,
    _convert_laps,
    _inventory_one,
    _session_code,
    configure_cache,
    pull_sessions,
    require_archive_auth,
)


def test_cache_requires_explicit_external_location(tmp_path, monkeypatch):
    monkeypatch.delenv("FASTF1_CACHE_DIR", raising=False)
    with pytest.raises(FastF1IngestError, match="FASTF1_CACHE_DIR"):
        configure_cache(tmp_path / "repo")


def test_cache_rejects_repository_and_onedrive_paths(tmp_path):
    repo = tmp_path / "OneDrive" / "project"
    with pytest.raises(FastF1IngestError, match="outside the repository"):
        configure_cache(repo, repo / ".cache")
    with pytest.raises(FastF1IngestError, match="outside OneDrive"):
        configure_cache(repo, tmp_path / "OneDrive" / "cache")


@pytest.mark.parametrize(
    "session,code",
    [("Practice 1", "FP1"), ("Practice 2", "FP2"), ("Sprint Qualifying", "SQ"),
     ("Sprint Shootout", "SS"), ("Qualifying", "Q"), ("Sprint", "S"), ("Race", "R")],
)
def test_session_name_maps_to_fastf1_code(session, code):
    assert _session_code(session) == code


def test_schedule_session_inventory_ignores_testing_round_zero():
    schedule = pd.DataFrame([{
        "RoundNumber": 0, "EventName": "Pre-Season Testing", "Session1": "Practice 1",
    }, {
        "RoundNumber": 1, "EventName": "Bahrain Grand Prix", "Session1": "Practice 1",
        "Session2": "Practice 2", "Session3": "Practice 3", "Session4": "Qualifying", "Session5": "Race",
    }])
    races = pd.DataFrame([{"season": 2023, "round": 1, "slug": "bahrain-grand-prix"}])
    inventory = _inventory_one(2023, races, schedule)
    assert inventory.loc[0, "name_match"]
    assert inventory.loc[0, "sessions"] == "FP1,FP2,FP3,Q,R"


def test_event_name_mismatch_is_reported_for_review():
    schedule = pd.DataFrame([{"RoundNumber": 1, "EventName": "Different GP", "Session1": "Practice 1"}])
    races = pd.DataFrame([{"season": 2023, "round": 1, "slug": "bahrain-grand-prix"}])
    inventory = _inventory_one(2023, races, schedule)
    assert not inventory.loc[0, "name_match"]


def test_laps_normalize_timing_and_tyre_fields():
    laps = pd.DataFrame({
        "Driver": ["1"], "LapNumber": [2], "Time": [pd.Timedelta(seconds=123)],
        "LapTime": [pd.Timedelta(seconds=90.5)], "Sector1Time": [pd.Timedelta(seconds=30)],
        "Compound": ["SOFT"], "TyreLife": [2], "Stint": [1], "PitInTime": [pd.NaT],
        "IsAccurate": [True], "TrackStatus": ["1"],
    })
    normalized = _convert_laps(laps)
    assert normalized.loc[0, "driver_code"] == "1"
    assert normalized.loc[0, "lap_time_s"] == 90.5
    assert normalized.loc[0, "session_time"] == 123
    assert normalized.loc[0, "compound"] == "SOFT"
    assert pd.isna(normalized.loc[0, "pit_in_time"])


def test_seconds_supports_python_timedelta_values():
    from src.ingest.fastf1_pull import _seconds

    assert _seconds(timedelta(seconds=12.5)) == 12.5


def test_archive_auth_fails_clearly_without_credentials_or_token(monkeypatch):
    monkeypatch.delenv("F1_USERNAME", raising=False)
    monkeypatch.delenv("F1_PASSWORD", raising=False)
    # The test environment must not already have an authenticated FastF1 token.
    from fastf1.internals.f1account import token_manager

    monkeypatch.setattr(token_manager, "get_stored", lambda: None)
    with pytest.raises(FastF1IngestError, match="F1 TV Access/Pro/Premium"):
        require_archive_auth()


class FakeSession:
    date = pd.Timestamp("2025-03-01T12:00:00Z")
    session_start_time = pd.Timedelta(minutes=1)
    session_end_time = pd.Timedelta(hours=1)
    laps = pd.DataFrame({
        "Driver": ["1"], "LapNumber": [1], "Time": [pd.Timedelta(minutes=2)],
        "LapTime": [pd.Timedelta(seconds=90)], "Sector1Time": [pd.Timedelta(seconds=30)],
        "Sector2Time": [pd.Timedelta(seconds=30)], "Sector3Time": [pd.Timedelta(seconds=30)],
        "Stint": [1], "Compound": ["SOFT"], "TyreLife": [1], "PitInTime": [pd.NaT],
        "PitOutTime": [pd.NaT], "LapStartTime": [pd.Timedelta(seconds=30)],
        "LapStartDate": [pd.Timestamp("2025-03-01T12:00:30Z")], "IsAccurate": [True],
        "Deleted": [False], "TrackStatus": ["1"],
    })
    weather_data = pd.DataFrame({"Time": [pd.Timedelta(minutes=2)], "AirTemp": [20.0]})
    track_status = pd.DataFrame({"Time": [pd.Timedelta(minutes=2)], "Status": ["1"]})

    def load(self, **kwargs):
        pass


class FakeFastF1:
    @staticmethod
    def get_event_schedule(season, include_testing=False):
        return pd.DataFrame([{
            "RoundNumber": 1, "EventName": "Bahrain Grand Prix", "Session1": "Practice 2",
            "Session2": None, "Session3": None, "Session4": None, "Session5": None,
        }])

    @staticmethod
    def get_session(season, round_no, code):
        return FakeSession()


def test_pull_sessions_writes_normalized_lap_weather_and_status_tables(tmp_path):
    races = pd.DataFrame([{
        "season": 2025, "round": 1, "slug": "bahrain-grand-prix", "completed": True,
        "lock_utc": pd.Timestamp("2025-03-01T15:00:00Z"),
    }])
    result = pull_sessions(races, tmp_path, [2025], fastf1_api=FakeFastF1)
    assert result["sessions_loaded"] == 1
    assert result["laps_loaded"] == 1
    assert result["weather_rows"] == 1
    assert result["track_status_rows"] == 1
    assert result["warnings"] == []
    laps = pd.read_parquet(tmp_path / "laps.parquet")
    assert laps.loc[0, "driver_code"] == "1"
    assert laps.loc[0, "lap_time_s"] == 90
    assert laps.loc[0, "compound"] == "SOFT"


def test_rate_limit_stops_requests_but_records_full_expected_inventory(tmp_path):
    class LimitedSession(FakeSession):
        def __init__(self, code):
            self.code = code

        def load(self, **kwargs):
            if self.code == "FP2":
                raise type("RateLimitExceededError", (RuntimeError,), {})()

    class RateLimitedFastF1(FakeFastF1):
        @staticmethod
        def get_event_schedule(season, include_testing=False):
            return pd.DataFrame([{
                "RoundNumber": 1, "EventName": "Bahrain Grand Prix",
                "Session1": "Practice 1", "Session2": "Practice 2",
            }])

        @staticmethod
        def get_session(season, round_no, code):
            return LimitedSession(code)

    races = pd.DataFrame([{
        "season": 2025, "round": 1, "slug": "bahrain-grand-prix", "completed": True,
    }])
    result = pull_sessions(races, tmp_path, [2025], fastf1_api=RateLimitedFastF1)
    assert result["expected_sessions"] == 2
    assert result["sessions_loaded"] == 1
    inventory = pd.read_parquet(tmp_path / "fastf1_session_inventory.parquet")
    assert inventory.set_index("session_code")["status"].to_dict() == {
        "FP1": "loaded", "FP2": "not_loaded",
    }


def test_pull_sessions_refuses_unreviewed_event_name_mismatch(tmp_path):
    class MismatchFastF1(FakeFastF1):
        @staticmethod
        def get_event_schedule(season, include_testing=False):
            return pd.DataFrame([{"RoundNumber": 1, "EventName": "Unknown Grand Prix", "Session1": "Practice 2"}])

    races = pd.DataFrame([{"season": 2025, "round": 1, "slug": "bahrain-grand-prix", "completed": True}])
    with pytest.raises(FastF1IngestError, match="Unreviewed FastF1 event-name mismatches"):
        pull_sessions(races, tmp_path, [2025], fastf1_api=MismatchFastF1)
