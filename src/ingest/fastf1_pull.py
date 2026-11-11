"""Restartable FastF1 session and lap ingestion.

The FastF1 HTTP cache is deliberately opt-in and must live outside OneDrive and
the repository. Set ``FASTF1_CACHE_DIR`` before running this module.
"""

from __future__ import annotations

import argparse
import os
import re
import unicodedata
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd


SESSION_FIELDS = ("Session1", "Session2", "Session3", "Session4", "Session5")
SESSION_CODES = {
    "practice 1": "FP1",
    "practice 2": "FP2",
    "practice 3": "FP3",
    "qualifying": "Q",
    "sprint qualifying": "SQ",
    "sprint shootout": "SS",
    "sprint": "S",
    "race": "R",
}
LAP_FIELDS = {
    "Driver": "driver_code",
    "LapNumber": "lap_number",
    "Time": "session_time",
    "LapTime": "lap_time_s",
    "Sector1Time": "sector1_s",
    "Sector2Time": "sector2_s",
    "Sector3Time": "sector3_s",
    "Stint": "stint",
    "Compound": "compound",
    "TyreLife": "tyre_age",
    "PitInTime": "pit_in_time",
    "PitOutTime": "pit_out_time",
    "LapStartTime": "lap_start_time",
    "LapStartDate": "lap_start_utc",
    "IsAccurate": "is_accurate",
    "Deleted": "deleted",
    "TrackStatus": "track_status",
}
LAP_COLUMNS = ["season", "round", "event_name", "session_code", "session_name", *LAP_FIELDS.values()]
SESSION_COLUMNS = [
    "season", "round", "event_name", "session_code", "session_name", "scheduled_start_utc",
    "session_start_time", "session_end_time", "status", "driver_count", "lap_count",
    "weather_observations", "track_status_observations",
]
WEATHER_FIELDS = ("AirTemp", "Humidity", "Pressure", "Rainfall", "TrackTemp", "WindDirection", "WindSpeed")
INVENTORY_COLUMNS = ["season", "round", "session_code", "session_name", "status"]


class FastF1IngestError(RuntimeError):
    """Raised when schedules or session data cannot be joined safely."""


def _slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def configure_cache(repo_root: Path, cache_dir: str | Path | None = None) -> Path:
    """Set up FastF1 cache and reject paths in the checkout or any OneDrive tree."""
    raw = cache_dir if cache_dir is not None else os.environ.get("FASTF1_CACHE_DIR")
    if not raw:
        raise FastF1IngestError("Set FASTF1_CACHE_DIR to a writable directory outside OneDrive before ingesting.")
    root = repo_root.resolve()
    cache = Path(raw).expanduser().resolve()
    if cache == root or root in cache.parents:
        raise FastF1IngestError(f"FastF1 cache must be outside the repository: {cache}")
    if any(part.casefold().startswith("onedrive") for part in cache.parts):
        raise FastF1IngestError(f"FastF1 cache must be outside OneDrive: {cache}")
    cache.mkdir(parents=True, exist_ok=True)
    try:
        import fastf1
    except ImportError as exc:
        raise FastF1IngestError("FastF1 is not installed; install project dependencies with `uv sync`.") from exc
    fastf1.Cache.configure(cache_dir=str(cache))
    return cache


def require_archive_auth() -> None:
    """Fail early instead of allowing FastF1's interactive prompt in a batch pull."""
    if os.environ.get("F1_USERNAME") and os.environ.get("F1_PASSWORD"):
        return
    try:
        from fastf1.internals.f1account import token_manager

        token = token_manager.get_stored()
        if token is not None and token.is_valid():
            return
    except Exception:
        pass
    raise FastF1IngestError(
        "FastF1 archive access requires an F1 TV Access/Pro/Premium login. Set F1_USERNAME and "
        "F1_PASSWORD in the local environment, or authenticate once with "
        "`uv run python -m fastf1 auth f1tv --authenticate`; do not add credentials to the repository."
    )


def _session_code(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return SESSION_CODES.get(value.strip().casefold())


def _seconds(value: Any) -> float | None:
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timedelta, timedelta)):
        return value.total_seconds()
    return float(value)


def _available_sessions(event: pd.Series) -> list[tuple[str, str]]:
    found = []
    for field in SESSION_FIELDS:
        name = event.get(field)
        code = _session_code(name)
        if code:
            found.append((code, str(name)))
    return found


def _inventory_one(season: int, races: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    if "RoundNumber" not in schedule.columns:
        raise FastF1IngestError(f"FastF1 schedule for {season} has no RoundNumber column")
    schedule = schedule[pd.to_numeric(schedule["RoundNumber"], errors="coerce").fillna(0) > 0]
    schedule = schedule.drop_duplicates("RoundNumber", keep="last")
    expected = races.loc[races["season"].eq(season)]
    by_round = {int(row.RoundNumber): row for row in schedule.itertuples(index=False)}
    rows = []
    for race in expected.itertuples(index=False):
        event = by_round.get(int(race.round))
        if event is None:
            raise FastF1IngestError(f"FastF1 schedule missing {season} round {race.round} ({race.slug})")
        event_name = str(getattr(event, "EventName", ""))
        # Round numbers are canonical; names are a diagnostic to flag an alias for human review.
        sessions = [(code, name) for code, name in _available_sessions(pd.Series(event._asdict()).rename(lambda x: x))]
        rows.append({
            "season": season,
            "round": int(race.round),
            "canonical_slug": race.slug,
            "fastf1_event": event_name,
            "fastf1_slug": _slug(event_name),
            "name_match": _slug(event_name) == race.slug,
            "sessions": ",".join(code for code, _ in sessions),
            "session_names": ",".join(name for _, name in sessions),
        })
    return pd.DataFrame(rows)


def event_inventory(races: pd.DataFrame, seasons: list[int], *, fastf1_api: Any = None) -> pd.DataFrame:
    """Compare FastF1's event/session schedule against canonical Jolpica rounds."""
    if fastf1_api is None:
        import fastf1 as fastf1_api
    frames = []
    for season in seasons:
        schedule = fastf1_api.get_event_schedule(season, include_testing=False)
        frames.append(_inventory_one(season, races, schedule))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _convert_laps(laps: pd.DataFrame) -> pd.DataFrame:
    keep = {source: target for source, target in LAP_FIELDS.items() if source in laps.columns}
    out = laps[list(keep)].rename(columns=keep).copy()
    for column in ("lap_time_s", "sector1_s", "sector2_s", "sector3_s"):
        if column in out:
            out[column] = out[column].map(_seconds)
    for column in ("session_time", "lap_start_time", "pit_in_time", "pit_out_time"):
        if column in out:
            out[column] = out[column].map(_seconds)
    if "lap_start_utc" in out:
        out["lap_start_utc"] = pd.to_datetime(out["lap_start_utc"], utc=True, errors="coerce")
    return out


def _session_weather(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    out = frame.copy()
    if "Time" in out:
        out = out.rename(columns={"Time": "session_time"})
        out["session_time"] = out["session_time"].map(_seconds)
    for name in WEATHER_FIELDS:
        if name not in out:
            out[name] = pd.NA
    return out[[c for c in ("session_time", *WEATHER_FIELDS) if c in out.columns]]


def _session_track_status(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["session_time", "track_status"])
    out = frame.copy()
    if "Time" in out:
        out = out.rename(columns={"Time": "session_time"})
        out["session_time"] = out["session_time"].map(_seconds)
    status_col = "Status" if "Status" in out else "TrackStatus" if "TrackStatus" in out else None
    if status_col is None:
        return pd.DataFrame(columns=["session_time", "track_status"])
    return out[[c for c in ("session_time", status_col) if c in out]].rename(columns={status_col: "track_status"})


def _load_session(fastf1_api: Any, season: int, round_no: int, code: str):
    session = fastf1_api.get_session(season, round_no, code)
    # Race-control messages are needed for FastF1's Deleted lap flag. Without
    # them, session.laps can mark deleted times as accurate and contaminate pace fits.
    session.load(laps=True, telemetry=False, weather=True, messages=True)
    try:
        laps = session.laps
    except Exception as exc:
        raise FastF1IngestError(
            f"{season} round {round_no} {code} did not load lap timing; check F1 TV authentication "
            "and whether FastF1 has published the session archive."
        ) from exc
    if laps is None or laps.empty:
        raise FastF1IngestError(
            f"{season} round {round_no} {code} returned no laps; check authentication and source availability."
        )
    return session


def _existing(path: Path, columns: list[str]) -> pd.DataFrame:
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame(columns=columns)


def _merge_write(path: Path, previous: pd.DataFrame, rows: pd.DataFrame, keys: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if rows.empty:
        return
    replace_keys = rows[keys].drop_duplicates()
    if not previous.empty:
        marker = previous.merge(replace_keys, on=keys, how="left", indicator=True)
        previous = marker.loc[marker["_merge"].eq("left_only"), previous.columns]
    result = rows.copy() if previous.empty else pd.concat([previous, rows], ignore_index=True)
    result = result.drop_duplicates(keys, keep="last")
    result.to_parquet(path, index=False)


def pull_sessions(
    races: pd.DataFrame,
    out_dir: Path,
    seasons: list[int],
    *,
    rounds: list[int] | None = None,
    include_incomplete: bool = False,
    fastf1_api: Any = None,
) -> dict[str, Any]:
    """Pull selected seasons and replace matching sessions in normalized Parquet tables."""
    if fastf1_api is None:
        import fastf1 as fastf1_api
    session_path, lap_path, weather_path, status_path = (
        out_dir / "sessions.parquet", out_dir / "laps.parquet",
        out_dir / "weather.parquet", out_dir / "track_status.parquet",
    )
    inventory_path = out_dir / "fastf1_session_inventory.parquet"
    old_sessions = _existing(session_path, SESSION_COLUMNS)
    old_laps = _existing(lap_path, LAP_COLUMNS)
    old_weather = _existing(weather_path, ["season", "round", "session_code", "session_time", *WEATHER_FIELDS])
    old_status = _existing(status_path, ["season", "round", "session_code", "session_time", "track_status"])
    old_inventory = _existing(inventory_path, INVENTORY_COLUMNS)
    session_rows, lap_rows, weather_rows, status_rows, inventory_rows, warnings = [], [], [], [], [], []
    expected_session_keys: set[tuple[int, int, str]] = set()
    event_rows = event_inventory(races, seasons, fastf1_api=fastf1_api)
    mismatches = event_rows.loc[~event_rows["name_match"]]
    if not mismatches.empty:
        details = mismatches[["season", "round", "canonical_slug", "fastf1_event"]].to_dict("records")
        raise FastF1IngestError(f"Unreviewed FastF1 event-name mismatches; add explicit aliases first: {details}")
    session_tasks = []
    for event in event_rows.itertuples(index=False):
        if rounds is not None and int(event.round) not in rounds:
            continue
        event_row = races.loc[(races["season"] == event.season) & (races["round"] == event.round)].iloc[0]
        if not include_incomplete and not bool(event_row.get("completed", False)):
            continue
        session_pairs = zip(event.sessions.split(","), event.session_names.split(",")) if event.sessions else []
        for code, session_name in session_pairs:
            expected_session_keys.add((int(event.season), int(event.round), code))
            inventory_rows.append({"season": int(event.season), "round": int(event.round),
                                   "session_code": code, "session_name": session_name, "status": "expected"})
            session_tasks.append((event, code, session_name))
    for event, code, session_name in session_tasks:
        try:
            session = _load_session(fastf1_api, event.season, int(event.round), code)
            laps = _convert_laps(session.laps)
            laps.insert(0, "session_name", session_name)
            laps.insert(0, "session_code", code)
            laps.insert(0, "event_name", event.fastf1_event)
            laps.insert(0, "round", int(event.round))
            laps.insert(0, "season", int(event.season))
            lap_rows.append(laps.reindex(columns=LAP_COLUMNS))
            weather = _session_weather(getattr(session, "weather_data", pd.DataFrame()))
            if not weather.empty:
                weather.insert(0, "session_code", code)
                weather.insert(0, "round", int(event.round))
                weather.insert(0, "season", int(event.season))
                weather_rows.append(weather)
            track = _session_track_status(getattr(session, "track_status", pd.DataFrame()))
            if not track.empty:
                track.insert(0, "session_code", code)
                track.insert(0, "round", int(event.round))
                track.insert(0, "season", int(event.season))
                status_rows.append(track)
            start = getattr(session, "session_start_time", pd.NaT)
            end = getattr(session, "session_end_time", pd.NaT)
            session_rows.append({
                "season": int(event.season), "round": int(event.round), "event_name": event.fastf1_event,
                "session_code": code, "session_name": session_name,
                "scheduled_start_utc": pd.to_datetime(getattr(session, "date", pd.NaT), utc=True, errors="coerce"),
                "session_start_time": _seconds(start), "session_end_time": _seconds(end),
                "status": "loaded", "driver_count": int(laps["driver_code"].nunique()) if "driver_code" in laps else 0,
                "lap_count": len(laps), "weather_observations": len(weather),
                "track_status_observations": len(track),
            })
        except Exception as exc:  # preserve partial pulls and report each unavailable session
            warnings.append({"season": int(event.season), "round": int(event.round), "session": code,
                             "event": event.fastf1_event,
                             "error": f"{type(exc).__name__}; check F1 TV auth/API and local logs"})
            if type(exc).__name__ == "RateLimitExceededError":
                break
    sessions = pd.DataFrame(session_rows, columns=SESSION_COLUMNS)
    laps = pd.concat(lap_rows, ignore_index=True) if lap_rows else pd.DataFrame(columns=LAP_COLUMNS)
    weather = pd.concat(weather_rows, ignore_index=True) if weather_rows else pd.DataFrame(
        columns=["season", "round", "session_code", "session_time", *WEATHER_FIELDS])
    track_status = pd.concat(status_rows, ignore_index=True) if status_rows else pd.DataFrame(
        columns=["season", "round", "session_code", "session_time", "track_status"])
    _merge_write(session_path, old_sessions, sessions, ["season", "round", "session_code"])
    _merge_write(lap_path, old_laps, laps, ["season", "round", "session_code", "driver_code", "lap_number", "stint"])
    _merge_write(weather_path, old_weather, weather, ["season", "round", "session_code", "session_time"])
    _merge_write(status_path, old_status, track_status, ["season", "round", "session_code", "session_time"])
    loaded_session_keys = {(int(row["season"]), int(row["round"]), str(row["session_code"]))
                           for row in session_rows}
    missing_sessions = sorted(expected_session_keys - loaded_session_keys)
    session_inventory = pd.DataFrame(inventory_rows, columns=INVENTORY_COLUMNS)
    if not session_inventory.empty:
        session_inventory["status"] = session_inventory.apply(
            lambda row: "loaded" if (int(row["season"]), int(row["round"]), str(row["session_code"])) in loaded_session_keys
            else "not_loaded", axis=1,
        )
    _merge_write(inventory_path, old_inventory, session_inventory, ["season", "round", "session_code"])
    return {
        "sessions_loaded": len(sessions), "laps_loaded": len(laps), "weather_rows": len(weather),
        "track_status_rows": len(track_status), "warnings": warnings,
        "inventory_path": str(inventory_path),
        "expected_sessions": len(expected_session_keys), "loaded_session_keys": sorted(loaded_session_keys),
        "missing_sessions": [{"season": s, "round": r, "session": code}
                             for s, r, code in missing_sessions],
        "name_mismatches": event_rows.loc[~event_rows["name_match"],
                                          ["season", "round", "canonical_slug", "fastf1_event"]].to_dict("records"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, action="append", dest="seasons")
    parser.add_argument("--round", type=int, action="append", dest="rounds")
    parser.add_argument("--include-incomplete", action="store_true",
                        help="also attempt sessions for rounds without Jolpica race results")
    parser.add_argument("--allow-partial", action="store_true",
                        help="write available sessions and exit successfully despite missing sessions")
    parser.add_argument("--inventory", action="store_true",
                        help="print the FastF1/Jolpica event and session inventory without downloading laps")
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    configure_cache(repo_root)
    races = pd.read_parquet(args.data_dir / "races.parquet")
    available_seasons = set(races["season"].dropna().astype(int).tolist())
    seasons = args.seasons or [season for season in (2025, 2026) if season in available_seasons]
    if args.inventory:
        inventory = event_inventory(races, seasons)
        print(inventory.to_string(index=False))
        if not inventory["name_match"].all():
            raise FastF1IngestError("Event-name mismatches need explicit aliases before a pull.")
        return
    require_archive_auth()
    result = pull_sessions(races, args.data_dir, seasons, rounds=args.rounds,
                           include_incomplete=args.include_incomplete)
    report_path = Path("reports/fastf1_ingest_summary.md")
    report_path.parent.mkdir(exist_ok=True)
    report = [
        "# FastF1 ingest summary", "",
        f"Sessions loaded: {result['sessions_loaded']}",
        f"Expected sessions: {result['expected_sessions']}",
        f"Missing sessions: {len(result['missing_sessions'])}",
        f"Laps loaded: {result['laps_loaded']}",
        f"Weather observations: {result['weather_rows']}",
        f"Track-status observations: {result['track_status_rows']}",
        f"Warnings: {len(result['warnings'])}",
        f"Event-name mismatches: {len(result['name_mismatches'])}",
        "",
        "| Season | Round | Session | Event | Issue |",
        "|---:|---:|---|---|---|",
    ]
    report.extend(f"| {row['season']} | {row['round']} | {row['session']} | — | missing expected session |"
                  for row in result["missing_sessions"])
    report.extend(f"| {row['season']} | {row['round']} | {row['session']} | {row['event']} | {row['error']} |"
                  for row in result["warnings"])
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wrote local ingest summary to {report_path}")
    if result["sessions_loaded"] == 0:
        raise FastF1IngestError("FastF1 loaded zero sessions; check requested rounds and archive authentication.")
    if (result["missing_sessions"] or result["warnings"]) and not args.allow_partial:
        raise FastF1IngestError(
            f"FastF1 pull incomplete: {len(result['missing_sessions'])} missing sessions; "
            f"summary: {report_path}. Re-run with --allow-partial only for an intentional recovery pull."
        )
    print(f"loaded {result['sessions_loaded']} sessions and {result['laps_loaded']} laps")
    if result["name_mismatches"]:
        print(f"event name variants to review: {len(result['name_mismatches'])}")
    for warning in result["warnings"]:
        print(f"warning: {warning}")


if __name__ == "__main__":
    main()
