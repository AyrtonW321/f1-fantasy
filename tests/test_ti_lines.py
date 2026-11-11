import json

import pytest

from src.ingest.ti_lines import driver_line, parse_pit, parse_teamwork, weekend_entrants
from src.sim.scoring import DriverLine, PitResult


def pit_row(text=None, *, overall=False, world_record=0):
    """TI constructor race row. text=None means the fastestPitStopPoints key is absent."""
    session_result = {
        "worldRecordPitStopPoints": {"points": world_record, "nnPoints": world_record, "text": "World record pit stop"},
    }
    if text is not None:
        session_result["fastestPitStopPoints"] = {"points": 0, "nnPoints": 0, "text": text}
    return {"type": "constructor", "raceOverallFastestPitStop": overall, "sessionResult": session_result}


@pytest.mark.parametrize("text,ranks", [
    ("Fastest pit stop", (1,)),
    ("2nd fastest & 3rd fastest pit stop", (2, 3)),
    ("Fastest, 2nd fastest & 3rd fastest pit stop", (1, 2, 3)),
    ("Fastest & 2nd fastest pit stop", (1, 2)),
    ("", ()),
    ("Fastest pit stop time", ()),
])
def test_parse_pit_ranks(text, ranks):
    assert parse_pit(pit_row(text)).ranks == ranks


def test_parse_pit_seconds():
    assert parse_pit(pit_row("Fastest pit stop of 2.19s")).seconds == 2.19
    assert parse_pit(pit_row("Fastest pit stop of 2s")).seconds == 2.0


def test_parse_pit_missing_breakdown_is_empty():
    # qualifying and sprint constructor rows have no fastestPitStopPoints key
    assert parse_pit({"type": "constructor", "sessionResult": {}}) == PitResult()


def test_parse_pit_flags_and_world_record():
    result = parse_pit(pit_row("", overall=True, world_record=-10))
    assert result.overall_fastest is True
    assert result.world_record is True


@pytest.mark.parametrize("text,expected", [
    ("Neither driver reached Q2", "neither_q2"),
    ("One driver reached Q2", "one_q2"),
    ("Both drivers reached Q2", "both_q2"),
    ("One driver reached Q3", "one_q3"),
    ("Both drivers reached Q3", "both_q3"),
    ("", None),
])
def test_parse_teamwork_maps_known_text(text, expected):
    assert parse_teamwork(text) == expected


def test_parse_teamwork_unknown_raises():
    with pytest.raises(ValueError, match="Both drivers reached Q1"):
        parse_teamwork("Both drivers reached Q1")


def test_flags_come_from_breakdown_lines():
    def line(nc=0, dsq=0):
        row = {
            "type": "driver",
            "abbreviation": "GAS",
            "racePosition": "NC",
            "sessionResult": {
                "notClassifiedPoints": {"points": nc, "nnPoints": nc, "text": "Not Classified"},
                "disqualifiedPoints": {"points": dsq, "nnPoints": dsq, "text": "Disqualified"},
            },
        }
        return driver_line(row, "race")

    assert line(nc=-20).not_classified is True
    assert line(nc=0).not_classified is False
    assert line(dsq=-20).disqualified is True
    assert line(dsq=0).disqualified is False


@pytest.mark.parametrize("session,code", [
    ("race", "NC"), ("race", "DQ"), ("race", "WD"), ("qualifying", "NT"), ("qualifying", "RT"),
])
def test_non_numeric_position_is_none(session, code):
    # TI position codes other than digits carry no position points in the real data
    row = {"type": "driver", "abbreviation": "GAS", f"{session}Position": code, "sessionResult": {}}
    assert driver_line(row, session).position is None


def test_qualifying_line_has_no_race_fields():
    row = {
        "type": "driver",
        "abbreviation": "VER",
        "qualifyingPosition": "1",
        "racePosition": "1",
        "racePositionsGained": 3,
        "raceOvertakes": 5,
        "raceFastestLap": True,
        "raceDriverOfTheDay": True,
        "sessionResult": {},
    }
    assert driver_line(row, "qualifying") == DriverLine(code="VER", session="qualifying", position=1)


def test_driver_line_real_shaped_race_row():
    # Subset of a real 2024 Bahrain race driver row (GAS, 18th, 2 positions gained, 4 overtakes).
    row = {
        "type": "driver",
        "abbreviation": "GAS",
        "constructorId": "ALP",
        "qualifyingPosition": "20",
        "racePosition": "18",
        "racePositionsGained": 2,
        "raceOvertakes": 4,
        "raceFastestLap": False,
        "raceDriverOfTheDay": False,
        "sessionResult": {
            "positionPoints": {"points": 0, "nnPoints": 0, "text": "18th place"},
            "positionsGained": {"points": 2, "nnPoints": 2, "text": "2 positions gained"},
            "overtakes": {"points": 4, "nnPoints": 4, "text": "4 overtakes made"},
            "notClassifiedPoints": {"points": 0, "nnPoints": 0, "text": "Not Classified"},
            "disqualifiedPoints": {"points": 0, "nnPoints": 0, "text": "Disqualified"},
        },
    }
    assert driver_line(row, "race") == DriverLine(
        code="GAS", session="race", position=18, gained=2, overtakes=4,
        fastest_lap=False, dotd=False, not_classified=False, disqualified=False,
    )


def write_jolpica(raw_dir, season, name, races):
    folder = raw_dir / "jolpica" / str(season)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(races), encoding="utf-8")


def test_entrant_filter_drops_listed_non_participant(tmp_path):
    write_jolpica(tmp_path, 2024, "results", [
        {"round": "1", "Results": [{"Driver": {"code": "VER"}}, {"Driver": {"code": "LAW"}}]},
        {"round": "2", "Results": [{"Driver": {"code": "TSU"}}]},
    ])
    write_jolpica(tmp_path, 2024, "qualifying", [
        {"round": "1", "QualifyingResults": [{"Driver": {"code": "LIN"}}, {"Driver": {"code": "VER"}}]},
    ])
    codes = weekend_entrants(2024, 1, tmp_path)
    assert codes == {"VER", "LAW", "LIN"}
    assert "TSU" not in codes


def test_entrants_include_driver_only_in_race_results(tmp_path):
    write_jolpica(tmp_path, 2024, "results", [
        {"round": "3", "Results": [{"Driver": {"code": "HAM"}}, {"Driver": {"familyName": "Bortoleto"}}]},
    ])
    write_jolpica(tmp_path, 2024, "qualifying", [
        {"round": "3", "QualifyingResults": [{"Driver": {"code": "HAM"}}]},
    ])
    # BOR has no code in the fixture, so driver_code falls back to familyName[:3].upper()
    assert weekend_entrants(2024, 3, tmp_path) == {"HAM", "BOR"}


def test_bonus_points_scores_fastest_lap_dotd_and_pit_via_engine():
    from src.ingest.ti_lines import bonus_points
    from src.sim.scoring import load_rules
    rules = load_rules(2026)
    driver = {"type": "driver", "abbreviation": "VER", "raceFastestLap": True, "raceDriverOfTheDay": True,
              "sprintFastestLap": True}
    assert bonus_points(driver, rules) == 10 + 10 + 5
    team = {"type": "constructor", "id": "RED", "raceFastestLap": True,
            "sessionResult": {"fastestPitStopPoints": {"text": "Fastest pit stop of 2.19s"}}}
    assert bonus_points(team, rules) == 10 + 10  # FL counts for constructors; 2.19s is in the 10-point band
