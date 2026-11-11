import pandas as pd
import pytest

from src.features.tracks import TrackMetadataError, add_prior_safety_car_rates, load_track_metadata


def write_tracks(path, rows):
    pd.DataFrame(rows, columns=[
        "season", "round", "track_id", "track_name", "track_type", "overtaking_difficulty",
        "safety_car_rate", "safety_car_rate_races", "sprint",
    ]).to_csv(path, index=False)


def test_load_track_metadata_covers_schedule_and_allows_unknown_safety_car_rate(tmp_path):
    path = tmp_path / "tracks.csv"
    write_tracks(path, [
        [2025, 1, "albert_park", "Albert Park", "semi-permanent", "medium", None, 0, False],
        [2025, 2, "shanghai", "Shanghai", "permanent", "medium", 0.25, 4, True],
    ])
    schedule = pd.DataFrame({"season": [2025, 2025], "round": [1, 2]})
    result = load_track_metadata(path, schedule)
    assert len(result) == 2
    assert pd.isna(result.loc[0, "safety_car_rate"])
    assert bool(result.loc[1, "sprint"])


def test_load_track_metadata_rejects_missing_scheduled_event(tmp_path):
    path = tmp_path / "tracks.csv"
    write_tracks(path, [[2025, 1, "albert_park", "Albert Park", "semi-permanent", "medium", None, 0, False]])
    schedule = pd.DataFrame({"season": [2025], "round": [2]})
    with pytest.raises(TrackMetadataError, match="missing scheduled events"):
        load_track_metadata(path, schedule)


def test_load_track_metadata_rejects_duplicate_event_key(tmp_path):
    path = tmp_path / "tracks.csv"
    row = [2025, 1, "albert_park", "Albert Park", "semi-permanent", "medium", None, 0, False]
    write_tracks(path, [row, row])
    with pytest.raises(TrackMetadataError, match="one row per season and round"):
        load_track_metadata(path)


def test_load_track_metadata_requires_manual_categories(tmp_path):
    path = tmp_path / "tracks.csv"
    write_tracks(path, [[2025, 1, "albert_park", "Albert Park", None, "medium", None, 0, False]])
    with pytest.raises(TrackMetadataError, match="required for every event"):
        load_track_metadata(path)


@pytest.mark.parametrize("column", ["track_id", "track_name", "sprint"])
def test_load_track_metadata_requires_identity_and_sprint_flag(tmp_path, column):
    path = tmp_path / "tracks.csv"
    row = {"season": 2025, "round": 1, "track_id": "albert_park", "track_name": "Albert Park",
           "track_type": "semi-permanent", "overtaking_difficulty": "medium",
           "safety_car_rate": None, "safety_car_rate_races": 0, "sprint": False}
    row[column] = None
    pd.DataFrame([row]).to_csv(path, index=False)
    with pytest.raises(TrackMetadataError):
        load_track_metadata(path)


def test_load_track_metadata_checks_category_and_rate_ranges(tmp_path):
    path = tmp_path / "tracks.csv"
    write_tracks(path, [[2025, 1, "albert_park", "Albert Park", "unknown", "medium", 1.2, 5, False]])
    with pytest.raises(TrackMetadataError, match="track_type"):
        load_track_metadata(path)


def test_safety_car_rate_uses_only_prior_observed_races_at_same_track():
    tracks = pd.DataFrame({
        "season": [2024, 2025, 2025], "round": [1, 1, 2],
        "track_id": ["A", "A", "B"],
    })
    status = pd.DataFrame({
        "season": [2024, 2025, 2025], "round": [1, 1, 2], "session_code": ["R", "R", "R"],
        "track_status": ["1", "4", "1"],
    })
    output = add_prior_safety_car_rates(tracks, status)
    assert pd.isna(output.loc[0, "safety_car_rate"])
    assert output.loc[1, "safety_car_rate"] == 0
    assert output.loc[2, "safety_car_rate"] is pd.NA or pd.isna(output.loc[2, "safety_car_rate"])
