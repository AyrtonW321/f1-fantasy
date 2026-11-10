"""Pull TracingInsights season JSON and mzafram round JSON into {raw_dir}."""

import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

import requests

from src.ingest.fantasy_scrape import _write

TI_ARCHIVE = "https://github.com/TracingInsights/fantasy/archive/refs/tags/{tag}.zip"
MZAFRAM_BASE = "https://raw.githubusercontent.com/mzafram2001/f1-fantasy/main/data"
SEASONS = ("2023", "2024", "2025", "2026")


def _check_member(name: str) -> None:
    """Refuse zip members that could leave the target folder (.., absolute, drive colon)."""
    posix = name.replace("\\", "/")
    if ".." in posix.split("/") or posix.startswith("/") or ":" in posix:
        raise ValueError(f"unsafe zip member: {name!r}")


def pull_tracing_insights(tag: str, raw_dir: Path, http: requests.Session) -> Path:
    response = http.get(TI_ARCHIVE.format(tag=tag), timeout=120)
    if response.status_code != 200:
        raise RuntimeError(f"TracingInsights {tag}: HTTP {response.status_code}")
    out = raw_dir / "tracinginsights"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        members = archive.infolist()
        for info in members:
            _check_member(info.filename)
        for info in members:
            parts = PurePosixPath(info.filename).parts
            if len(parts) != 6 or parts[1:3] != ("data", "transformed") or parts[3] not in SEASONS:
                continue
            year, slug, name = parts[3], parts[4], parts[5]
            if name != "race.json" and not name.endswith("_all.json"):
                continue
            payload = json.loads(archive.read(info))
            if name == "race.json":
                payload.pop("circuitMapUrl", None)
            _write(out / year / slug / name, payload)
    _write(out / "SOURCE.json", {"tag": tag})
    return out


def pull_mzafram(raw_dir: Path, http: requests.Session) -> list[Path]:
    written = []
    for year in SEASONS:
        for nn in range(1, 31):
            try:
                response = http.get(f"{MZAFRAM_BASE}/{year}/round_{nn:02d}.json", timeout=30)
                if response.status_code != 200:
                    continue
                payload = response.json()
            except (requests.RequestException, ValueError):
                continue
            if payload:
                written.append(_write(raw_dir / "mzafram" / year / f"round_{nn:02d}.json", payload))
    return written


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m src.ingest.community_pull <tracinginsights-tag>")
    session = requests.Session()
    session.headers["User-Agent"] = "f1-fantasy-snapshot"
    raw = Path("data/raw")
    ti_dir = pull_tracing_insights(sys.argv[1], raw, session)
    ti_files = [p for p in ti_dir.rglob("*.json") if p.name != "SOURCE.json"]
    mz_files = pull_mzafram(raw, session)
    print(f"tracinginsights: {len(ti_files)} files, mzafram: {len(mz_files)} files")
