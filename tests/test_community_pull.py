import io
import json
import zipfile

import pytest

from src.ingest.community_pull import pull_mzafram, pull_tracing_insights

TI_URL = "https://github.com/TracingInsights/fantasy/archive/refs/tags/{tag}.zip"
MZ_URL = "https://raw.githubusercontent.com/mzafram2001/f1-fantasy/main/data/{year}/round_{nn:02d}.json"


class FakeResponse:
    def __init__(self, status_code, body=b""):
        self.status_code = status_code
        self.content = body

    def json(self):
        return json.loads(self.content)


class FakeSession:
    """Maps full URL to a FakeResponse. Unknown URLs answer 404."""

    def __init__(self, routes):
        self.routes = routes

    def get(self, url, timeout):
        return self.routes.get(url, FakeResponse(404))


def body(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


def make_zip(members) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_ti_extracts_only_season_json(tmp_path):
    raw = tmp_path / "raw"
    zip_bytes = make_zip({
        "fantasy-x/data/transformed/2024/a-gp/race_all.json": body({"rows": 1}),
        "fantasy-x/data/transformed/2024/a-gp/race_all.csv": b"a,b",
        "fantasy-x/data/raw/2024/x.json": body({"raw": 1}),
    })
    http = FakeSession({TI_URL.format(tag="t1"): FakeResponse(200, zip_bytes)})

    out = pull_tracing_insights("t1", raw, http)

    assert out == raw / "tracinginsights"
    files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
    assert files == ["2024/a-gp/race_all.json", "SOURCE.json"]
    assert json.loads((out / "2024" / "a-gp" / "race_all.json").read_text(encoding="utf-8")) == {"rows": 1}
    assert json.loads((out / "SOURCE.json").read_text(encoding="utf-8")) == {"tag": "t1"}


def test_ti_drops_circuit_map(tmp_path):
    raw = tmp_path / "raw"
    zip_bytes = make_zip({
        "fantasy-x/data/transformed/2024/a-gp/race.json": body(
            {"circuitMapUrl": "data:image/png;base64,AAAA", "winner": "VER", "round": 1}
        ),
    })
    http = FakeSession({TI_URL.format(tag="t1"): FakeResponse(200, zip_bytes)})

    out = pull_tracing_insights("t1", raw, http)

    race = json.loads((out / "2024" / "a-gp" / "race.json").read_text(encoding="utf-8"))
    assert race == {"winner": "VER", "round": 1}


def test_ti_rejects_path_traversal(tmp_path):
    raw = tmp_path / "raw"
    zip_bytes = make_zip({
        "fantasy-x/data/transformed/2024/../../../evil.json": body({"x": 1}),
    })
    http = FakeSession({TI_URL.format(tag="t1"): FakeResponse(200, zip_bytes)})

    with pytest.raises(ValueError):
        pull_tracing_insights("t1", raw, http)

    outside = [p for p in tmp_path.rglob("*") if p.is_file() and raw not in p.parents]
    assert outside == []


def test_mzafram_ignores_missing_rounds(tmp_path):
    raw = tmp_path / "raw"
    http = FakeSession({
        MZ_URL.format(year=2024, nn=5): FakeResponse(200, body({"round": 5})),
        MZ_URL.format(year=2024, nn=6): FakeResponse(404),
        MZ_URL.format(year=2024, nn=7): FakeResponse(200, body({"round": 7})),
    })

    written = pull_mzafram(raw, http)

    expected = [
        raw / "mzafram" / "2024" / "round_05.json",
        raw / "mzafram" / "2024" / "round_07.json",
    ]
    assert sorted(written) == sorted(expected)
    assert sorted(p for p in raw.rglob("*") if p.is_file()) == sorted(expected)
