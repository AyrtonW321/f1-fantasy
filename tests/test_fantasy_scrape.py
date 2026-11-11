import json
from pathlib import Path

from src.ingest.fantasy_scrape import snapshot_official

BASE = "https://fantasy.formula1.com/feeds/"


def url(path: str) -> str:
    return BASE + path


def raceday(*gamedays: int, season: str = "2026") -> dict:
    return {"Data": {"Value": [{"GamedayId": g, "Season": season} for g in gamedays]}}


def drivers(*player_ids: int) -> dict:
    return {"Data": {"Value": [{"PlayerId": p} for p in player_ids]}}


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    """Maps full URL to (status, payload). Unknown URLs answer 404."""

    def __init__(self, routes):
        self.routes = routes

    def get(self, url, timeout):
        status, payload = self.routes.get(url, (404, {}))
        return FakeResponse(status, payload)


def seed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_snapshot_writes_every_gameday(tmp_path):
    http = FakeSession({
        url("schedule/raceday_en.json"): (200, raceday(1, 2)),
        url("limits/constraints.json"): (200, {"Data": {"Value": {"budget": 100}}}),
        url("apps/web_config.json"): (200, {"Data": {"Value": {"x": 1}}}),
        url("drivers/1_en.json"): (200, drivers(101)),
        url("drivers/2_en.json"): (200, drivers(101, 102)),
        url("popup/playerstats_101.json"): (200, {"Data": {"Value": {"p": 101}}}),
        url("popup/playerstats_102.json"): (200, {"Data": {"Value": {"p": 102}}}),
    })
    written = snapshot_official(tmp_path, http)
    season = tmp_path / "official" / "2026"
    expected = [season / p for p in [
        "raceday.json",
        "constraints.json",
        "web_config.json",
        "drivers/1.json",
        "drivers/2.json",
        "playerstats/101.json",
        "playerstats/102.json",
    ]]
    assert sorted(written) == sorted(expected)
    assert all(p.exists() for p in expected)


def test_failed_fetch_keeps_existing_file(tmp_path):
    existing = tmp_path / "official" / "2026" / "drivers" / "1.json"
    seed(existing, '{"good": 1}')
    http = FakeSession({
        url("schedule/raceday_en.json"): (200, raceday(1)),
        url("drivers/1_en.json"): (403, drivers(101)),
    })
    written = snapshot_official(tmp_path, http)
    assert existing.read_text(encoding="utf-8") == '{"good": 1}'
    assert existing not in written


def test_empty_driver_feed_keeps_existing_file(tmp_path):
    existing = tmp_path / "official" / "2026" / "drivers" / "1.json"
    seed(existing, '{"good": 1}')
    http = FakeSession({
        url("schedule/raceday_en.json"): (200, raceday(1)),
        url("drivers/1_en.json"): (200, {"Data": {"Value": []}}),
    })
    written = snapshot_official(tmp_path, http)
    assert existing.read_text(encoding="utf-8") == '{"good": 1}'
    assert existing not in written


def test_schedule_404_raises_and_writes_nothing(tmp_path):
    http = FakeSession({})
    try:
        snapshot_official(tmp_path, http)
    except RuntimeError as e:
        assert "schedule feed could not be fetched" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


def test_schedule_empty_value_raises(tmp_path):
    http = FakeSession({
        url("schedule/raceday_en.json"): (200, {"Data": {"Value": []}}),
    })
    try:
        snapshot_official(tmp_path, http)
    except RuntimeError as e:
        assert "schedule feed could not be fetched" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
    assert not any(p.is_file() for p in tmp_path.rglob("*"))
