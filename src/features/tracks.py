"""Validated event-level circuit metadata used by pre-lock features."""

from pathlib import Path

import pandas as pd


TRACK_COLUMNS = [
    "season", "round", "track_id", "track_name", "track_type", "overtaking_difficulty",
    "safety_car_rate", "safety_car_rate_races", "sprint",
]
TRACK_TYPES = {"street", "semi-permanent", "permanent"}
OVERTAKING_LEVELS = {"low", "medium", "high"}


class TrackMetadataError(ValueError):
    """Raised when static track metadata is incomplete or invalid."""


def load_track_metadata(path: Path, schedule: pd.DataFrame | None = None) -> pd.DataFrame:
    tracks = pd.read_csv(path)
    missing = sorted(set(TRACK_COLUMNS) - set(tracks.columns))
    if missing:
        raise TrackMetadataError(f"tracks.csv missing columns: {missing}")
    if tracks[["season", "round"]].duplicated().any():
        raise TrackMetadataError("tracks.csv must have one row per season and round")
    if tracks[["track_id", "track_name"]].isna().any().any() or tracks[["track_id", "track_name"]].astype(str).apply(lambda col: col.str.strip().eq("")).any().any():
        raise TrackMetadataError("track_id and track_name are required for every event")
    if tracks[["track_type", "overtaking_difficulty"]].isna().any().any():
        raise TrackMetadataError("track_type and overtaking_difficulty are required for every event")
    if not set(tracks["track_type"].dropna()).issubset(TRACK_TYPES):
        raise TrackMetadataError(f"track_type must be one of {sorted(TRACK_TYPES)}")
    if not set(tracks["overtaking_difficulty"].dropna()).issubset(OVERTAKING_LEVELS):
        raise TrackMetadataError(f"overtaking_difficulty must be one of {sorted(OVERTAKING_LEVELS)}")
    if tracks["sprint"].isna().any() or not pd.api.types.is_bool_dtype(tracks["sprint"]):
        raise TrackMetadataError("sprint must be true or false for every event")
    rates = pd.to_numeric(tracks["safety_car_rate"], errors="coerce")
    if ((rates.dropna() < 0) | (rates.dropna() > 1)).any():
        raise TrackMetadataError("safety_car_rate must be between 0 and 1 when known")
    if schedule is not None:
        expected = schedule[["season", "round"]].drop_duplicates()
        joined = expected.merge(tracks[["season", "round"]], on=["season", "round"], how="left", indicator=True)
        missing_events = joined.loc[joined["_merge"].eq("left_only"), ["season", "round"]]
        if not missing_events.empty:
            raise TrackMetadataError(f"tracks.csv missing scheduled events: {missing_events.to_dict('records')}")
    return tracks[TRACK_COLUMNS].sort_values(["season", "round"]).reset_index(drop=True)


def add_prior_safety_car_rates(tracks: pd.DataFrame, track_status: pd.DataFrame) -> pd.DataFrame:
    """Attach each event's circuit SC rate using only earlier observed race sessions.

    A race counts as SC-affected when any race-session track-status code includes
    ``4`` (Safety Car). Virtual Safety Car codes are not counted as a physical SC.
    Events with no usable status observation are excluded from the denominator.
    """
    output = tracks.copy().sort_values(["season", "round"]).reset_index(drop=True)
    status = track_status.loc[track_status["session_code"].eq("R")].copy() if not track_status.empty else track_status.copy()
    outcomes: dict[tuple[int, int], bool] = {}
    if not status.empty:
        for (season, round_no), frame in status.groupby(["season", "round"]):
            values = frame["track_status"].dropna().astype(str)
            if not values.empty:
                outcomes[(int(season), int(round_no))] = any("4" in value for value in values)
    rates, counts = [], []
    prior_by_track: dict[str, list[bool]] = {}
    for row in output.itertuples(index=False):
        history = prior_by_track.get(str(row.track_id), [])
        rates.append(sum(history) / len(history) if history else pd.NA)
        counts.append(len(history))
        outcome = outcomes.get((int(row.season), int(row.round)))
        if outcome is not None:
            prior_by_track.setdefault(str(row.track_id), []).append(outcome)
    output["safety_car_rate"] = rates
    output["safety_car_rate_races"] = counts
    return output
