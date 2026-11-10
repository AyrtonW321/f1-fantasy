import json
from pathlib import Path

import pytest

from src.ingest.jolpica_pull import pull_jolpica

BASE = "https://api.jolpi.ca/ergast/f1/"
ENDPOINTS = ["races", "results", "qualifying", "sprint"]


def url(season: int, endpoint: str, offset: int) -> str:
    return f"{BASE}{season}/{endpoint}.json?limit=100&offset={offset}"


def page(total: int, races: list) -> dict:
    return {"MRData": {"total": str(total), "limit": "100", "offset": "0",
                       "RaceTable": {"season": "2024", "Races": races}}}


def race(rnd: int, key=None, drivers=()) -> dict:
    """Race dict; drivers become rows under key (Results, QualifyingResults, SprintResults)."""
    out = {"season": "2024", "round": str(rnd), "raceName": f"GP {rnd}"}
    if key:
        out[key] = [{"driverId": d} for d in drivers]
    return out


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    """Maps full URL to a queue of (status, payload); the last entry repeats. Unknown URLs answer 404."""

    def __init__(self, routes):
        self.routes = routes

    def get(self, url, timeout):
        queue = self.routes.get(url, [(404, {})])
        status, payload = queue.pop(0) if len(queue) > 1 else queue[0]
        return FakeResponse(status, payload)


def empty_routes(season: int) -> dict:
    """Every endpoint answers total 0 on its first page."""
    return {url(season, ep, 0): [(200, page(0, []))] for ep in ENDPOINTS}


def read(tmp_path: Path, season: int, endpoint: str):
    path = tmp_path / "jolpica" / str(season) / f"{endpoint}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_jolpica_merges_race_split_across_pages(tmp_path):
    # Pages advance by 100 rows, so total 101 means offsets 0 and 100.
    # Round 1 is cut between the two pages.
    routes = empty_routes(2024)
    routes[url(2024, "results", 0)] = [(200, page(101, [race(1, "Results", ("ham", "ver"))]))]
    routes[url(2024, "results", 100)] = [(200, page(101, [race(1, "Results", ("lec",))]))]
    pull_jolpica(2024, tmp_path, FakeSession(routes), sleep=lambda s: None)
    races = read(tmp_path, 2024, "results")
    assert len(races) == 1
    assert [r["driverId"] for r in races[0]["Results"]] == ["ham", "ver", "lec"]


def test_jolpica_retries_429(tmp_path):
    routes = empty_routes(2024)
    routes[url(2024, "results", 0)] = [
        (429, {}),
        (200, page(1, [race(1, "Results", ("ham",))])),
    ]
    sleeps = []
    pull_jolpica(2024, tmp_path, FakeSession(routes), sleep=sleeps.append)
    assert sleeps == [5]
    assert read(tmp_path, 2024, "results")[0]["Results"][0]["driverId"] == "ham"


def test_jolpica_writes_all_endpoints_even_when_empty(tmp_path):
    # Sprint total 0 (season without sprints) still writes an empty list.
    routes = empty_routes(2024)
    routes[url(2024, "races", 0)] = [(200, page(1, [race(1)]))]
    paths = pull_jolpica(2024, tmp_path, FakeSession(routes), sleep=lambda s: None)
    assert [p.name for p in paths] == ["races.json", "results.json", "qualifying.json", "sprint.json"]
    assert all(p.exists() for p in paths)
    assert read(tmp_path, 2024, "sprint") == []


def test_jolpica_raises_after_three_429s(tmp_path):
    routes = empty_routes(2024)
    routes[url(2024, "results", 0)] = [(429, {})]
    sleeps = []
    with pytest.raises(RuntimeError):
        pull_jolpica(2024, tmp_path, FakeSession(routes), sleep=sleeps.append)
    assert sleeps == [5, 5, 5]
    assert not (tmp_path / "jolpica" / "2024" / "results.json").exists()
