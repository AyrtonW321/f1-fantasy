"""Snapshot Jolpica (Ergast-compatible) race data to {raw_dir}/jolpica/{season}/."""

import time
from collections.abc import Callable
from pathlib import Path

import requests

from src.ingest.fantasy_scrape import _write

BASE = "https://api.jolpi.ca/ergast/f1/"
# endpoint -> key holding the per-race rows (None: races has no rows)
ENDPOINTS = {
    "races": None,
    "results": "Results",
    "qualifying": "QualifyingResults",
    "sprint": "SprintResults",
}
PAGE = 100
RETRIES = 3


def _get_page(http: requests.Session, url: str, sleep: Callable[[float], None]) -> dict:
    """Parsed JSON of one page. A 429 waits 5s and retries, up to RETRIES times."""
    response = http.get(url, timeout=30)
    for _ in range(RETRIES):
        if response.status_code != 429:
            break
        sleep(5)
        response = http.get(url, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Jolpica HTTP {response.status_code} for {url}")
    return response.json()


def _fetch(season: int, endpoint: str, key: str | None, http: requests.Session,
           sleep: Callable[[float], None]) -> list[dict]:
    """All races of one endpoint; pages merged by round, sorted by round."""
    races = {}
    offset = 0
    while True:
        url = f"{BASE}{season}/{endpoint}.json?limit={PAGE}&offset={offset}"
        data = _get_page(http, url, sleep)["MRData"]
        for race in data["RaceTable"]["Races"]:
            rnd = int(race["round"])
            if rnd not in races:
                races[rnd] = {**race, key: []} if key else dict(race)
            if key:
                races[rnd][key].extend(race.get(key, []))
        offset += PAGE
        if offset >= int(data["total"]):
            break
        sleep(0.5)
    return [races[rnd] for rnd in sorted(races)]


def pull_jolpica(season: int, raw_dir: Path, http: requests.Session,
                 sleep: Callable[[float], None] = time.sleep) -> list[Path]:
    out = raw_dir / "jolpica" / str(season)
    return [
        _write(out / f"{endpoint}.json", _fetch(season, endpoint, key, http, sleep))
        for endpoint, key in ENDPOINTS.items()
    ]


if __name__ == "__main__":
    session = requests.Session()
    session.headers["User-Agent"] = "f1-fantasy-snapshot"
    for season in range(2023, 2027):
        written = pull_jolpica(season, Path("data/raw"), session)
        print(f"{season}: wrote {len(written)} files")
