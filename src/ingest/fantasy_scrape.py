"""Snapshot the official F1 Fantasy feeds to {out_dir}/official/{season}/."""

import json
import os
import tempfile
from pathlib import Path

import requests

BASE = "https://fantasy.formula1.com/feeds/"


def _get(http: requests.Session, path: str):
    """Parsed JSON if the response is valid (200, parses, non-empty), else None."""
    try:
        response = http.get(BASE + path, timeout=30)
        if response.status_code != 200:
            return None
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None
    return payload if payload else None


def _rows(payload) -> list:
    """Data.Value of a feed if it is a list, else []."""
    try:
        value = payload["Data"]["Value"]
    except (KeyError, TypeError):
        return []
    return value if isinstance(value, list) else []


def _write(path: Path, payload) -> Path:
    """Atomic write: temp file in the same folder, then os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.replace(tmp, path)
    return path


def snapshot_official(out_dir: Path, http: requests.Session) -> list[Path]:
    raceday = _get(http, "schedule/raceday_en.json")
    rows = _rows(raceday)
    if not rows:
        return []
    season = max(int(r["Season"]) for r in rows)
    last_gameday = max(int(r["GamedayId"]) for r in rows)
    base = out_dir / "official" / str(season)

    written = [_write(base / "raceday.json", raceday)]
    for feed, name in [
        ("limits/constraints.json", "constraints.json"),
        ("apps/web_config.json", "web_config.json"),
    ]:
        payload = _get(http, feed)
        if payload is not None:
            written.append(_write(base / name, payload))

    # Drivers feed per gameday; the last valid one (highest gameday) lists the players.
    latest_players = []
    for g in range(1, last_gameday + 1):
        drivers = _get(http, f"drivers/{g}_en.json")
        if not _rows(drivers):
            continue
        written.append(_write(base / "drivers" / f"{g}.json", drivers))
        latest_players = _rows(drivers)

    for pid in dict.fromkeys(r["PlayerId"] for r in latest_players):
        payload = _get(http, f"popup/playerstats_{pid}.json")
        if payload is not None:
            written.append(_write(base / "playerstats" / f"{pid}.json", payload))
    return written


if __name__ == "__main__":
    session = requests.Session()
    session.headers["User-Agent"] = "f1-fantasy-snapshot"
    written = snapshot_official(Path("data/raw"), session)
    print(f"wrote {len(written)} files")
