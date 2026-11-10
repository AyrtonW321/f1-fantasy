import json
from pathlib import Path

import pandas as pd
import pytest

from src.ingest.build_tables import (
    build_all,
    build_prices_points,
    build_races,
    build_results,
    slugify,
)


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def schedule(rnd, name, date, time, **sessions):
    race = {"season": "2026", "round": str(rnd), "raceName": name, "date": date, "time": time}
    for key, (d, t) in sessions.items():
        race[key] = {"date": d, "time": t}
    return race


def write_jolpica(raw, season, races, results=None, qualifying=None, sprint=None):
    base = raw / "jolpica" / str(season)
    _write(base / "races.json", races)
    _write(base / "results.json", [{"round": str(r), "Results": rows} for r, rows in (results or {}).items()])
    _write(base / "qualifying.json", [{"round": str(r), "QualifyingResults": rows} for r, rows in (qualifying or {}).items()])
    _write(base / "sprint.json", [{"round": str(r), "SprintResults": rows} for r, rows in (sprint or {}).items()])


def jrow(code, team, position, grid=1, status="Finished"):
    return {
        "position": str(position),
        "grid": str(grid),
        "status": status,
        "Driver": {"code": code, "familyName": code.title()},
        "Constructor": {"constructorId": team},
    }


def _ti_total(points):
    return {"totalPoints": {"points": points, "nnPoints": points, "text": ""}}


def ti_driver(team, abbr, price, points, position=None):
    return {
        "type": "driver",
        "id": f"{team}_{abbr}",
        "abbreviation": abbr,
        "price": price,
        "racePosition": position,
        "qualifyingPosition": None,
        "sprintPosition": None,
        "sessionResult": _ti_total(points),
    }


def ti_constructor(code, price, points):
    return {"type": "constructor", "id": code, "abbreviation": code, "price": price, "sessionResult": _ti_total(points)}


def write_ti(raw, season, slug, round_number, race_all=None, qualifying_all=None, sprint_all=None):
    base = raw / "tracinginsights" / str(season) / slug
    _write(base / "race.json", {"name": slug, "roundNumber": round_number, "sprint": sprint_all is not None})
    for name, rows in (("race_all.json", race_all), ("qualifying_all.json", qualifying_all), ("sprint_all.json", sprint_all)):
        if rows is not None:
            _write(base / name, rows)


def off_row(tla, position_name, price, quali="0", sprint="0", race="0", gameday=None, is_active="1"):
    value = float(gameday) if gameday is not None else sum(float(p) for p in (quali, sprint, race) if p)
    return {
        "DriverTLA": tla,
        "PositionName": position_name,
        "Value": price,
        "QualifyingPoints": quali,
        "SprintPoints": sprint,
        "RacePoints": race,
        "GamedayPoints": f"{value:.2f}",
        "IsActive": is_active,
    }


def write_official(raw, season, gameday, rows):
    _write(raw / "official" / str(season) / "drivers" / f"{gameday}.json", {"Data": {"Value": rows}})


def test_slugify_strips_accents():
    assert slugify("São Paulo Grand Prix") == "sao-paulo-grand-prix"


def test_ti_2023_round_offset_joins_on_slug(tmp_path):
    write_jolpica(tmp_path, 2023, [
        schedule(6, "Monaco Grand Prix", "2023-05-28", "13:00:00Z", Qualifying=("2023-05-27", "14:00:00Z")),
    ], results={6: []})
    write_ti(tmp_path, 2023, "monaco-grand-prix", 7, race_all=[ti_driver("MCL", "NOR", 20.0, 10)])
    races = build_races(2023, tmp_path)
    prices, _ = build_prices_points(2023, races, tmp_path)
    assert races.loc[0, "ti_slug_round"] == 7
    assert set(prices["round"]) == {6}


def test_slug_aliases_join(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(16, "Bahrain Grand Prix in Malaysia", "2026-10-04", "07:00:00Z", Qualifying=("2026-10-03", "15:00:00Z")),
        schedule(20, "Brazilian Grand Prix", "2026-11-08", "17:00:00Z", Qualifying=("2026-11-07", "17:00:00Z")),
    ], results={})
    write_ti(tmp_path, 2026, "bahrain-grand-prix", 16)
    write_ti(tmp_path, 2026, "sao-paulo-grand-prix", 20)
    races = build_races(2026, tmp_path).set_index("round")
    assert races.loc[16, "slug"] == "bahrain-grand-prix"
    assert races.loc[20, "slug"] == "sao-paulo-grand-prix"
    assert races.loc[20, "ti_slug_round"] == 20


def test_unmatched_race_raises_with_name(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z", Qualifying=("2026-03-07", "05:00:00Z")),
    ], results={})
    write_ti(tmp_path, 2026, "mystery-grand-prix", 1)
    with pytest.raises(ValueError, match="mystery-grand-prix"):
        build_races(2026, tmp_path)


def test_lock_is_earliest_competitive_session(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(2, "Chinese Grand Prix", "2026-03-15", "07:00:00Z",
                 FirstPractice=("2026-03-13", "16:30:00Z"),
                 SprintQualifying=("2026-03-13", "20:30:00Z"),
                 Sprint=("2026-03-14", "16:00:00Z"),
                 Qualifying=("2026-03-14", "20:00:00Z")),
    ], results={})
    races = build_races(2026, tmp_path)
    assert races.loc[0, "lock_utc"] == pd.Timestamp("2026-03-13T20:30:00Z")


def test_lock_handles_2023_shootout(tmp_path):
    write_jolpica(tmp_path, 2023, [
        schedule(4, "Azerbaijan Grand Prix", "2023-04-30", "11:00:00Z",
                 Qualifying=("2023-04-28", "12:00:00Z"),
                 SprintShootout=("2023-04-29", "15:00:00Z"),
                 Sprint=("2023-04-29", "11:00:00Z")),
    ], results={})
    races = build_races(2023, tmp_path)
    assert races.loc[0, "lock_utc"] == pd.Timestamp("2023-04-28T12:00:00Z")


def test_race_without_lock_session_raises(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z", FirstPractice=("2026-03-06", "01:30:00Z")),
    ], results={})
    with pytest.raises(ValueError, match="round 1"):
        build_races(2026, tmp_path)


def test_unplayed_round_has_no_points_rows(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(1, "Bahrain Grand Prix", "2026-04-12", "15:00:00Z", Qualifying=("2026-04-11", "15:00:00Z")),
        schedule(2, "Saudi Arabian Grand Prix", "2026-04-19", "17:00:00Z", Qualifying=("2026-04-18", "17:00:00Z")),
        schedule(3, "Japanese Grand Prix", "2026-03-29", "05:00:00Z", Qualifying=("2026-03-28", "06:00:00Z")),
    ], results={1: []})
    write_ti(tmp_path, 2026, "bahrain-grand-prix", 1, race_all=[ti_driver("RED", "VER", 20.0, 25)])
    write_ti(tmp_path, 2026, "saudi-arabian-grand-prix", 2, race_all=[ti_driver("RED", "VER", 20.0, 0)])
    races = build_races(2026, tmp_path)
    prices, points = build_prices_points(2026, races, tmp_path)
    by_round = races.set_index("round")
    assert by_round["completed"].to_dict() == {1: True, 2: False, 3: False}
    assert pd.isna(by_round.loc[3, "ti_slug_round"])
    assert set(prices["round"]) == {1, 2}
    assert set(points["round"]) == {1}


def test_team_change_is_one_asset(tmp_path):
    write_jolpica(tmp_path, 2025, [
        schedule(2, "Chinese Grand Prix", "2025-03-23", "07:00:00Z", Qualifying=("2025-03-22", "07:00:00Z")),
        schedule(3, "Japanese Grand Prix", "2025-04-06", "05:00:00Z", Qualifying=("2025-04-05", "06:00:00Z")),
    ], results={2: [], 3: []})
    write_ti(tmp_path, 2025, "chinese-grand-prix", 2, race_all=[ti_driver("RED", "LAW", 7.8, 4)])
    write_ti(tmp_path, 2025, "japanese-grand-prix", 3, race_all=[ti_driver("VRB", "LAW", 7.8, 6)])
    races = build_races(2025, tmp_path)
    prices, points = build_prices_points(2025, races, tmp_path)
    assert set(prices["asset_id"]) == {"LAW"}
    assert points["round"].tolist() == [2, 3]
    assert set(points["asset_id"]) == {"LAW"}


def test_duplicate_driver_keeps_row_with_points(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(5, "Miami Grand Prix", "2026-05-03", "20:00:00Z", Qualifying=("2026-05-02", "20:00:00Z")),
    ], results={5: []})
    write_ti(tmp_path, 2026, "miami-grand-prix", 5, race_all=[
        ti_driver("FER", "BEA", 5.0, 0),
        ti_driver("HAA", "BEA", 5.5, 12),
    ])
    races = build_races(2026, tmp_path)
    prices, points = build_prices_points(2026, races, tmp_path)
    bea = points[points["asset_id"] == "BEA"]
    assert len(bea) == 1
    assert bea["total"].tolist() == [12.0]
    assert prices.loc[prices["asset_id"] == "BEA", "price"].tolist() == [5.5]


def test_duplicate_tie_keeps_last_row(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(5, "Miami Grand Prix", "2026-05-03", "20:00:00Z", Qualifying=("2026-05-02", "20:00:00Z")),
    ], results={5: []})
    write_ti(tmp_path, 2026, "miami-grand-prix", 5, race_all=[
        ti_driver("RED", "XXX", 4.0, 5),
        ti_driver("VRB", "XXX", 6.0, 5),
    ])
    races = build_races(2026, tmp_path)
    prices, points = build_prices_points(2026, races, tmp_path)
    assert prices["price"].tolist() == [6.0]
    assert points["total"].tolist() == [5.0]


def test_phantom_row_loses_to_participating_row(tmp_path):
    # 2025 Bahrain shape: RED_LAW is a phantom (-25, no positions); VRB_LAW raced (11, P16).
    write_jolpica(tmp_path, 2025, [
        schedule(4, "Bahrain Grand Prix", "2025-04-13", "15:00:00Z", Qualifying=("2025-04-12", "15:00:00Z")),
    ], results={4: []})
    write_ti(tmp_path, 2025, "bahrain-grand-prix", 4, race_all=[
        ti_driver("RED", "LAW", 16.8, -25),
        ti_driver("VRB", "LAW", 7.8, 11, position="16"),
    ])
    races = build_races(2025, tmp_path)
    prices, points = build_prices_points(2025, races, tmp_path)
    law = points.set_index("asset_id").loc["LAW"]
    assert law["total"] == 11.0
    assert law["source"] == "tracinginsights"
    assert prices["price"].tolist() == [7.8]


def test_official_active_row_wins_unplayed_duplicate(tmp_path):
    # Round 21 shape: both LAW rows total 0. The active row (IsActive "1") must win over the last row.
    write_jolpica(tmp_path, 2026, [
        schedule(21, "Las Vegas Grand Prix", "2026-11-22", "04:00:00Z", Qualifying=("2026-11-21", "04:00:00Z")),
    ], results={})
    write_official(tmp_path, 2026, 21, [
        off_row("LAW", "DRIVER", 11.7, quali="", sprint="", race="", is_active="1"),
        off_row("LAW", "DRIVER", 15.1, quali="", sprint="", race="", is_active="0"),
    ])
    races = build_races(2026, tmp_path)
    prices, _ = build_prices_points(2026, races, tmp_path)
    assert prices["price"].tolist() == [11.7]


def test_official_inconsistency_uses_agreeing_tracinginsights_row(tmp_path):
    # Round 6 shape: official components do not sum to its own GamedayPoints.
    # GAS: TI row sums to GamedayPoints, so TI wins. ALB: TI also disagrees, so official stays.
    write_jolpica(tmp_path, 2026, [
        schedule(6, "Monaco Grand Prix", "2026-06-07", "13:00:00Z", Qualifying=("2026-06-06", "13:00:00Z")),
    ], results={6: []})
    write_ti(tmp_path, 2026, "monaco-grand-prix", 6,
             race_all=[ti_driver("ALP", "GAS", 12.5, 10), ti_driver("WIL", "ALB", 4.0, 10)],
             qualifying_all=[ti_driver("ALP", "GAS", 12.5, 2)])
    write_official(tmp_path, 2026, 6, [
        off_row("GAS", "DRIVER", 12.8, quali="2", race="23", gameday="12"),
        off_row("ALB", "DRIVER", 4.0, quali="2", race="23", gameday="12"),
    ])
    races = build_races(2026, tmp_path)
    prices, points = build_prices_points(2026, races, tmp_path)
    pts = points.set_index("asset_id")
    assert pts.loc["GAS", "total"] == 12.0
    assert pts.loc["GAS", "source"] == "tracinginsights"
    assert prices.set_index("asset_id").loc["GAS", "price"] == 12.5
    assert pts.loc["ALB", "total"] == 25.0
    assert pts.loc["ALB", "source"] == "official"


def test_official_overrides_2026_and_maps_constructors(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z", Qualifying=("2026-03-07", "05:00:00Z")),
    ], results={1: []})
    write_ti(tmp_path, 2026, "australian-grand-prix", 1, race_all=[
        ti_driver("ALP", "GAS", 12.0, 0),
        ti_constructor("RED", 10.0, 0),
        ti_constructor("VRB", 4.0, 0),
    ])
    write_official(tmp_path, 2026, 1, [
        off_row("GAS", "DRIVER", 12.8, quali="0", sprint="3", race="13"),
        off_row("ALB", "DRIVER", 4.0, quali="2", sprint="", race="5"),
        off_row("RBR", "CONSTRUCTOR", 11.5, quali="3", sprint="", race="20"),
        off_row("RBS", "CONSTRUCTOR", 4.5, quali="0", sprint="", race="1"),
    ])
    races = build_races(2026, tmp_path)
    prices, points = build_prices_points(2026, races, tmp_path)
    pts = points.set_index("asset_id")
    assert pts.loc["GAS", ["qualifying", "sprint", "race", "total"]].tolist() == [0.0, 3.0, 13.0, 16.0]
    assert pts.loc["GAS", "source"] == "official"
    assert pts.loc["ALB", ["sprint", "total"]].tolist() == [0.0, 7.0]
    assert pts.loc["RED", "kind"] == "constructor"
    assert pts.loc["RED", "source"] == "official"
    assert prices.set_index("asset_id").loc["RED", "price"] == 11.5
    assert prices.set_index("asset_id").loc["VRB", "price"] == 4.5
    assert not {"RBR", "RBS"} & set(pts.index)


def test_price_known_at_equals_lock_and_points_after_race(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z", Qualifying=("2026-03-07", "05:00:00Z")),
    ], results={1: []})
    write_ti(tmp_path, 2026, "australian-grand-prix", 1, race_all=[ti_driver("MER", "RUS", 30.0, 25)])
    races = build_races(2026, tmp_path)
    prices, points = build_prices_points(2026, races, tmp_path)
    assert prices["known_at"].iloc[0] == pd.Timestamp("2026-03-07T05:00:00Z")
    assert points["known_at"].iloc[0] == pd.Timestamp("2026-03-08T10:00:00Z")


def test_absent_session_rows_score_zero(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z", Qualifying=("2026-03-07", "05:00:00Z")),
    ], results={1: []})
    write_ti(tmp_path, 2026, "australian-grand-prix", 1,
             race_all=[ti_driver("MER", "RUS", 30.0, 25)],
             qualifying_all=[ti_driver("MER", "ANT", 20.0, 9)])
    races = build_races(2026, tmp_path)
    _, points = build_prices_points(2026, races, tmp_path)
    rus = points.set_index("asset_id").loc["RUS"]
    assert [rus["qualifying"], rus["sprint"], rus["race"], rus["total"]] == [0.0, 0.0, 25.0, 25.0]


def test_results_rows_map_session_fields(tmp_path):
    write_jolpica(tmp_path, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z", Qualifying=("2026-03-07", "05:00:00Z")),
    ], results={1: [jrow("ANT", "mercedes", 2, grid=2),
                    {"position": "3", "grid": "0", "status": "Retired",
                     "Driver": {"familyName": "Camara"}, "Constructor": {"constructorId": "alpine"}}]},
       qualifying={1: [jrow("ANT", "mercedes", 1)]})
    res = build_results(2026, tmp_path)
    race = res[res["session"] == "race"].set_index("driver_code")
    assert race.loc["ANT", "position"] == 2
    assert race.loc["ANT", "grid"] == 2
    assert race.loc["CAM", "constructor_id"] == "alpine"
    assert race.loc["CAM", "status"] == "Retired"
    quali = res[res["session"] == "qualifying"].iloc[0]
    assert pd.isna(quali["grid"]) and pd.isna(quali["status"])
    assert res["known_at"].iloc[0] == pd.Timestamp("2026-03-08T10:00:00Z")


def test_build_all_writes_four_tables(tmp_path):
    raw = tmp_path / "raw"
    write_jolpica(raw, 2026, [
        schedule(1, "Australian Grand Prix", "2026-03-08", "04:00:00Z", Qualifying=("2026-03-07", "05:00:00Z")),
    ], results={1: [jrow("RUS", "mercedes", 1)]}, qualifying={1: [jrow("RUS", "mercedes", 1)]})
    write_ti(raw, 2026, "australian-grand-prix", 1, race_all=[ti_driver("MER", "RUS", 30.0, 25)])
    out = tmp_path / "processed"
    build_all(raw, out, [2026])
    for name in ("races", "prices", "fantasy_points", "results"):
        assert (out / f"{name}.parquet").exists()
    assert len(pd.read_parquet(out / "races.parquet")) == 1
    assert pd.read_parquet(out / "fantasy_points.parquet")["total"].tolist() == [25.0]
