"""Scoring gate and cross-checks: hand-built raw trees (unit) and real raw data (marker data)."""
import json
from pathlib import Path

import pandas as pd
import pytest

from src.ingest.crosscheck import finish_mismatches, gate_mismatches, totals_mismatches
from src.sim.scoring import load_rules

# Known genuine source inconsistencies, as (season, slug, session, asset). Evidence, not a rule change:
# 2025 Spanish GP race, AST. TI's constructor row total is -5 = ALO 13 + pit 2 - 20, where the -20 is the
# not-classified line of STR, a WD driver who is not in Jolpica's race results. The 2023 Azerbaijan sprint WIL row
# has the same shape (a WD driver's -20 under a constructor) and TI excludes it there. The scoring and participation
# rules stay as they are; the gate must reproduce exactly these keys and no others.
KNOWN_SOURCE_EXCEPTIONS = {(2025, "spanish-grand-prix", "race", "AST")}


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def write_jolpica(raw: Path, season: int, *, race, quali, sprint=None, round_no: int = 1) -> None:
    """race, quali and sprint are lists of (driver code, finishing position)."""
    folder = raw / "jolpica" / str(season)
    base = {"round": str(round_no), "raceName": "Test Grand Prix", "date": "2025-03-16", "time": "04:00:00Z"}

    def results(pairs):
        return [{"position": str(pos), "Driver": {"code": code}} for code, pos in pairs]

    _write(folder / "races.json", [{**base, "Qualifying": {"date": "2025-03-15", "time": "08:00:00Z"}}])
    _write(folder / "results.json", [{**base, "Results": results(race)}])
    _write(folder / "qualifying.json", [{**base, "QualifyingResults": results(quali)}])
    if sprint is not None:
        _write(folder / "sprint.json", [{**base, "SprintResults": results(sprint)}])


def ti_driver(code: str, team: str, session: str, position, total: int, *, nc: int = 0) -> dict:
    """position may be an int, a TI code such as "WD", or None (no position). nc adds a not-classified line."""
    row = {
        "type": "driver",
        "abbreviation": code,
        "constructorId": team,
        f"{session}Position": None if position is None else str(position),
        "sessionResult": {"totalPoints": {"points": total}},
    }
    if nc:
        row["sessionResult"]["notClassifiedPoints"] = {"points": nc}
    return row


def ti_team(team: str, total: int, *, teamwork: str | None = None, pit: str | None = None) -> dict:
    result = {"totalPoints": {"points": total}}
    if teamwork is not None:
        result["teamworkPoints"] = {"points": 0, "text": teamwork}
    if pit is not None:
        result["fastestPitStopPoints"] = {"points": 0, "text": pit}
    return {"type": "constructor", "id": team, "abbreviation": team, "sessionResult": result}


def write_ti(raw: Path, season: int, *, quali: list, race: list, sprint: list | None = None) -> None:
    folder = raw / "tracinginsights" / str(season) / "test-grand-prix"
    _write(folder / "qualifying_all.json", quali)
    _write(folder / "race_all.json", race)
    if sprint is not None:
        _write(folder / "sprint_all.json", sprint)


def write_official(raw: Path, season: int, round_no: int, values: list) -> None:
    _write(raw / "official" / str(season) / "drivers" / f"{round_no}.json", {"Data": {"Value": values}})


def official_row(kind: str, tla: str, quali: str, sprint: str, race: str, gameday: str) -> dict:
    return {
        "PositionName": kind,
        "DriverTLA": tla,
        "QualifyingPoints": quali,
        "SprintPoints": sprint,
        "RacePoints": race,
        "GamedayPoints": gameday,
    }


def write_2025_weekend(raw: Path, *, pit: str = "Fastest pit stop of 2.19s", team_race_total: int = 50) -> None:
    # MCL: NOR P1 and PIA P3. Quali 10 + 8 + both_q3 10 = 28. Race 25 + 15 + 10 pit band (2.19s < 2.20) = 50.
    write_jolpica(raw, 2025, race=[("NOR", 1), ("PIA", 3)], quali=[("NOR", 1), ("PIA", 3)])
    write_ti(
        raw, 2025,
        quali=[
            ti_driver("NOR", "MCL", "qualifying", 1, 10),
            ti_driver("PIA", "MCL", "qualifying", 3, 8),
            ti_team("MCL", 28, teamwork="Both drivers reached Q3"),
        ],
        race=[
            ti_driver("NOR", "MCL", "race", 1, 25),
            ti_driver("PIA", "MCL", "race", 3, 15),
            ti_team("MCL", team_race_total, pit=pit),
        ],
    )


def test_constructor_scores_correctly_2025(tmp_path):
    write_2025_weekend(tmp_path)
    ambiguous, anomalies, skipped = [], [], []
    assert gate_mismatches(2025, tmp_path, load_rules(2025), ambiguous, anomalies, skipped) == []
    assert ambiguous == []
    assert anomalies == []
    assert skipped == []


def test_wrong_expected_total_gives_one_mismatch(tmp_path):
    write_2025_weekend(tmp_path, team_race_total=51)
    assert gate_mismatches(2025, tmp_path, load_rules(2025)) == [
        {"season": 2025, "slug": "test-grand-prix", "session": "race", "asset": "MCL", "expected": 51.0, "actual": 50},
    ]


def test_pit_rounding_ambiguity_accepted_and_recorded(tmp_path):
    # Text 2.2s scores the 2.20+ band (5). The true stop was 2.19s (10 points), so the -0.049 retry reproduces 50.
    write_2025_weekend(tmp_path, pit="Fastest pit stop of 2.2s")
    ambiguous = []
    assert gate_mismatches(2025, tmp_path, load_rules(2025), ambiguous) == []
    assert ambiguous == [
        {"season": 2025, "slug": "test-grand-prix", "asset": "MCL", "seconds": 2.2, "expected": 50.0},
    ]


def test_pit_retry_does_not_rescue_other_totals(tmp_path):
    # Expected 60 is not reproduced by either band, so the row stays a mismatch and nothing is recorded as ambiguous.
    write_2025_weekend(tmp_path, pit="Fastest pit stop of 2.2s", team_race_total=60)
    ambiguous = []
    assert gate_mismatches(2025, tmp_path, load_rules(2025), ambiguous) == [
        {"season": 2025, "slug": "test-grand-prix", "session": "race", "asset": "MCL", "expected": 60.0, "actual": 45},
    ]
    assert ambiguous == []


def test_2026_official_anomaly_falls_back_to_ti_and_is_recorded(tmp_path):
    # Official race 20 + quali 10 does not sum to gameday 99, so the TI totals (25 race, 10 quali) are the expected values.
    write_jolpica(tmp_path, 2026, race=[("NOR", 1)], quali=[("NOR", 1)])
    write_ti(
        tmp_path, 2026,
        quali=[ti_driver("NOR", "MCL", "qualifying", 1, 10)],
        race=[ti_driver("NOR", "MCL", "race", 1, 25)],
    )
    write_official(tmp_path, 2026, 1, [official_row("DRIVER", "NOR", "10", "", "20", "99.00")])
    ambiguous, anomalies = [], []
    assert gate_mismatches(2026, tmp_path, load_rules(2026), ambiguous, anomalies) == []
    assert anomalies == [{
        "season": 2026,
        "slug": "test-grand-prix",
        "asset": "NOR",
        "official_components": {"qualifying": 10.0, "sprint": 0.0, "race": 20.0},
        "official_gameday": 99.0,
        "ti_expected": {"qualifying": 10.0, "race": 25.0},
    }]


def test_2026_asset_missing_from_official_feed_has_none_expected(tmp_path):
    write_jolpica(tmp_path, 2026, race=[("NOR", 1), ("PIA", 3)], quali=[("NOR", 1)])
    write_ti(
        tmp_path, 2026,
        quali=[ti_driver("NOR", "MCL", "qualifying", 1, 10)],
        race=[ti_driver("NOR", "MCL", "race", 1, 25), ti_driver("PIA", "MCL", "race", 3, 15)],
    )
    write_official(tmp_path, 2026, 1, [official_row("DRIVER", "NOR", "10", "", "25", "35.00")])
    assert gate_mismatches(2026, tmp_path, load_rules(2026)) == [
        {"season": 2026, "slug": "test-grand-prix", "session": "race", "asset": "PIA", "expected": None, "actual": 15},
    ]


@pytest.mark.parametrize("active_first", [True, False])
def test_2026_duplicate_official_rows_prefer_the_active_one(tmp_path, active_first):
    # Two DRIVER rows for LAW, as in the real feed: the active row carries the points, the inactive duplicate is blank.
    # The active row must win whichever position it is in.
    write_jolpica(tmp_path, 2026, race=[("LAW", 9)], quali=[("LAW", 14)])
    write_ti(tmp_path, 2026,
             quali=[ti_driver("LAW", "VRB", "qualifying", 14, 0)],
             race=[ti_driver("LAW", "VRB", "race", 9, 2)])
    active = {**official_row("DRIVER", "LAW", "0", "", "2", "2.00"), "IsActive": "1"}
    inactive = {**official_row("DRIVER", "LAW", "", "", "", "0"), "IsActive": "0"}
    write_official(tmp_path, 2026, 1, [active, inactive] if active_first else [inactive, active])
    assert gate_mismatches(2026, tmp_path, load_rules(2026)) == []


def test_2026_skipped_driver_with_nonzero_official_points_is_reported(tmp_path):
    # Mexico shape again, but the official feed gives TSU -5 in qualifying. A skipped row is not compared, so its
    # official points must be 0. -5 is reported with actual 0.
    write_jolpica(tmp_path, 2026, race=[("HAD", 8)], quali=[("HAD", 8)])
    write_ti(tmp_path, 2026, race=[], quali=[
        ti_driver("HAD", "VRB", "qualifying", 8, 3),
        ti_driver("TSU", "VRB", "qualifying", 15, -5, nc=-5),
        ti_team("VRB", 8, teamwork="One driver reached Q3"),
    ])
    write_official(tmp_path, 2026, 1, [
        official_row("DRIVER", "HAD", "3", "", "", "3.00"),
        official_row("DRIVER", "TSU", "-5", "", "", "-5.00"),
        official_row("CONSTRUCTOR", "VRB", "8", "", "", "8.00"),
    ])
    skipped = []
    assert gate_mismatches(2026, tmp_path, load_rules(2026), skipped=skipped) == [
        {"season": 2026, "slug": "test-grand-prix", "session": "qualifying", "asset": "TSU", "expected": -5.0, "actual": 0},
    ]
    assert skipped == [
        {"season": 2026, "slug": "test-grand-prix", "session": "qualifying", "driver": "TSU",
         "reason": "not in Jolpica weekend results"},
    ]


def test_2026_phantom_row_does_not_recheck_a_driver_who_takes_part(tmp_path):
    # LAW has a phantom race row under RED (no position, -20) and takes part under VRB (P9, 2 points). The official
    # row is per driver, so its points belong to the VRB row, which is compared on its own. The phantom is not rechecked.
    write_jolpica(tmp_path, 2026, race=[("LAW", 9)], quali=[("LAW", 14)])
    write_ti(tmp_path, 2026,
             quali=[ti_driver("LAW", "VRB", "qualifying", 14, 0)],
             race=[ti_driver("LAW", "RED", "race", None, -20, nc=-20),
                   ti_driver("LAW", "VRB", "race", 9, 2)])
    write_official(tmp_path, 2026, 1, [official_row("DRIVER", "LAW", "0", "", "2", "2.00")])
    skipped = []
    assert gate_mismatches(2026, tmp_path, load_rules(2026), skipped=skipped) == []
    assert skipped == [
        {"season": 2026, "slug": "test-grand-prix", "session": "race", "driver": "LAW", "reason": "no TI position"},
    ]


def test_2025_phantom_row_under_other_team_excluded_from_constructor(tmp_path):
    # LAW is listed under RED with no position and -5, and drove for VRB. RED must score VER 10 + one_q3 5 only.
    write_jolpica(tmp_path, 2025, race=[("VER", 1), ("LAW", 14)], quali=[("VER", 1), ("LAW", 14)])
    write_ti(
        tmp_path, 2025,
        quali=[
            ti_driver("VER", "RED", "qualifying", 1, 10),
            ti_driver("LAW", "RED", "qualifying", None, -5, nc=-5),
            ti_driver("LAW", "VRB", "qualifying", 14, 0),
            ti_team("RED", 15, teamwork="One driver reached Q3"),
            ti_team("VRB", -1, teamwork="Neither driver reached Q2"),
        ],
        race=[
            ti_driver("VER", "RED", "race", 1, 25),
            ti_driver("LAW", "VRB", "race", 14, 0),
            ti_team("RED", 25),
            ti_team("VRB", 0),
        ],
    )
    skipped = []
    assert gate_mismatches(2025, tmp_path, load_rules(2025), skipped=skipped) == []
    assert skipped == [
        {"season": 2025, "slug": "test-grand-prix", "session": "qualifying", "driver": "LAW", "reason": "no TI position"},
    ]


def test_2023_sprint_withdrawal_excluded_from_constructor(tmp_path):
    # SAR is listed under WIL with sprint WD and a -20 not-classified line. The constructor total leaves him out.
    write_jolpica(tmp_path, 2023, race=[("ALB", 9), ("SAR", 20)], quali=[("ALB", 9), ("SAR", 20)],
                  sprint=[("ALB", 9), ("SAR", 20)])
    write_ti(tmp_path, 2023, quali=[], race=[], sprint=[
        ti_driver("ALB", "WIL", "sprint", 9, 0),
        ti_driver("SAR", "WIL", "sprint", "WD", -20, nc=-20),
        ti_team("WIL", 0),
    ])
    skipped = []
    assert gate_mismatches(2023, tmp_path, load_rules(2023), skipped=skipped) == []
    assert skipped == [
        {"season": 2023, "slug": "test-grand-prix", "session": "sprint", "driver": "SAR", "reason": "withdrew (WD)"},
    ]


def test_2026_driver_not_in_jolpica_excluded_from_constructor(tmp_path):
    # Mexico 2026 shape: TSU is listed under VRB with a -5 but is not in Jolpica's weekend results.
    write_jolpica(tmp_path, 2026, race=[("HAD", 8)], quali=[("HAD", 8)])
    write_ti(tmp_path, 2026, race=[], quali=[
        ti_driver("HAD", "VRB", "qualifying", 8, 3),
        ti_driver("TSU", "VRB", "qualifying", 15, -5, nc=-5),
        ti_team("VRB", 8, teamwork="One driver reached Q3"),
    ])
    write_official(tmp_path, 2026, 1, [
        official_row("DRIVER", "HAD", "3", "", "", "3.00"),
        official_row("DRIVER", "TSU", "0", "", "", "0.00"),
        official_row("CONSTRUCTOR", "VRB", "8", "", "", "8.00"),
    ])
    skipped = []
    assert gate_mismatches(2026, tmp_path, load_rules(2026), skipped=skipped) == []
    assert skipped == [
        {"season": 2026, "slug": "test-grand-prix", "session": "qualifying", "driver": "TSU",
         "reason": "not in Jolpica weekend results"},
    ]


def test_non_participant_driver_is_skipped_not_compared(tmp_path):
    # GAS is in Jolpica's race results but TI gives him no position. His TI total of -20 is neither scored nor compared.
    write_jolpica(tmp_path, 2025, race=[("NOR", 1), ("GAS", 20)], quali=[("NOR", 1)])
    write_ti(
        tmp_path, 2025,
        quali=[ti_driver("NOR", "MCL", "qualifying", 1, 10)],
        race=[ti_driver("NOR", "MCL", "race", 1, 25), ti_driver("GAS", "ALP", "race", None, -20)],
    )
    skipped = []
    assert gate_mismatches(2025, tmp_path, load_rules(2025), skipped=skipped) == []
    assert skipped == [
        {"season": 2025, "slug": "test-grand-prix", "session": "race", "driver": "GAS", "reason": "no TI position"},
    ]


def test_finish_positions_match_jolpica(tmp_path):
    write_jolpica(tmp_path, 2025, race=[("NOR", 1), ("PIA", 3)], quali=[("NOR", 1), ("PIA", 3)])
    write_ti(
        tmp_path, 2025,
        # Position 0 carries no finish: skipped, not compared.
        quali=[ti_driver("NOR", "MCL", "qualifying", 1, 0), ti_driver("PIA", "MCL", "qualifying", 3, 0),
               ti_driver("LEC", "FER", "qualifying", 0, 0)],
        race=[
            ti_driver("NOR", "MCL", "race", 1, 0),
            ti_driver("PIA", "MCL", "race", 3, 0),
            # Non-numeric TI position (not classified) is skipped, not compared.
            {"type": "driver", "abbreviation": "GAS", "constructorId": "ALP", "racePosition": "NC",
             "sessionResult": {"totalPoints": {"points": -20}}},
        ],
    )
    assert finish_mismatches(2025, tmp_path) == []


def test_finish_positions_disagree_and_missing_jolpica_row(tmp_path):
    raw = tmp_path / "raw"  # the CSV goes to raw's sibling folder, processed/
    write_jolpica(raw, 2025, race=[("NOR", 1), ("PIA", 3)], quali=[("NOR", 1)])
    write_ti(
        raw, 2025,
        quali=[ti_driver("NOR", "MCL", "qualifying", 1, 0)],
        race=[ti_driver("NOR", "MCL", "race", 1, 0), ti_driver("PIA", "MCL", "race", 2, 0),
              ti_driver("LEC", "FER", "race", 5, 0)],
    )
    assert finish_mismatches(2025, raw) == [
        {"season": 2025, "slug": "test-grand-prix", "session": "race", "driver": "PIA", "ti": 2, "jolpica": 3},
        {"season": 2025, "slug": "test-grand-prix", "session": "race", "driver": "LEC", "ti": 5, "jolpica": None},
    ]
    csv = (tmp_path / "processed" / "finish_mismatches.csv").read_text(encoding="utf-8")
    assert "PIA" in csv and "LEC" in csv


def test_finish_csv_replaces_only_this_season(tmp_path):
    raw = tmp_path / "raw"
    csv = tmp_path / "processed" / "finish_mismatches.csv"
    write_jolpica(raw, 2025, race=[("PIA", 3)], quali=[("PIA", 3)])
    write_ti(raw, 2025, quali=[ti_driver("PIA", "MCL", "qualifying", 3, 0)],
             race=[ti_driver("PIA", "MCL", "race", 2, 0)])
    write_jolpica(raw, 2024, race=[("PIA", 3)], quali=[("PIA", 3)])
    write_ti(raw, 2024, quali=[ti_driver("PIA", "MCL", "qualifying", 3, 0)],
             race=[ti_driver("PIA", "MCL", "race", 4, 0)])
    finish_mismatches(2025, raw)
    finish_mismatches(2024, raw)
    assert pd.read_csv(csv)["season"].tolist() == [2025, 2024]

    # 2025 now agrees, so its rows leave the file and 2024 stays.
    write_ti(raw, 2025, quali=[ti_driver("PIA", "MCL", "qualifying", 3, 0)],
             race=[ti_driver("PIA", "MCL", "race", 3, 0)])
    assert finish_mismatches(2025, raw) == []
    assert pd.read_csv(csv)["season"].tolist() == [2024]


def _points(rows) -> pd.DataFrame:
    return pd.DataFrame([
        {"season": 2025, "round": rnd, "asset_id": asset, "kind": kind, "total": total}
        for rnd, asset, kind, total in rows
    ])


def _races(rows) -> pd.DataFrame:
    """rows are (season, round, ti_slug_round) tuples; every race is completed."""
    return pd.DataFrame({
        "season": [row[0] for row in rows],
        "round": [row[1] for row in rows],
        "ti_slug_round": pd.array([row[2] for row in rows], dtype="Int64"),
        "completed": [True] * len(rows),
    })


def write_mzafram(raw: Path, round_no: int, drivers: dict, teams: dict) -> None:
    _write(raw / "mzafram" / "2025" / f"round_{round_no:02d}.json", {
        "Meta": {"season": 2025},
        "Drivers": [{"Driver_Code": c, "Round_Fantasy_Points": v} for c, v in drivers.items()],
        "Teams": [{"Team_Code": c, "Round_Fantasy_Points": v} for c, v in teams.items()],
    })


def test_totals_difference_reported_and_written_to_csv(tmp_path):
    raw = tmp_path / "raw"
    write_mzafram(raw, 1, drivers={"NOR": 59.0}, teams={"MCL": 71.0})  # PIA has no mzafram row: skipped
    points = _points([(1, "NOR", "driver", 59.0), (1, "MCL", "constructor", 70.0), (1, "PIA", "driver", 30.0)])
    assert totals_mismatches(2025, raw, points, _races([(2025, 1, 1)])) == [
        {"season": 2025, "round": 1, "asset": "MCL", "ours": 70.0, "mzafram": 71.0},
    ]
    assert "MCL" in (tmp_path / "processed" / "totals_mismatches.csv").read_text(encoding="utf-8")


def test_totals_join_uses_jolpica_round_not_ti_slug_round(tmp_path):
    # TI's roundNumber (7) is not the file number; mzafram round_01 is the Jolpica round 1 file.
    raw = tmp_path / "raw"
    write_mzafram(raw, 1, drivers={"NOR": 50.0}, teams={})
    points = _points([(1, "NOR", "driver", 59.0)])
    assert totals_mismatches(2025, raw, points, _races([(2025, 1, 7)])) == [
        {"season": 2025, "round": 1, "asset": "NOR", "ours": 59.0, "mzafram": 50.0},
    ]


def test_totals_only_compares_races_of_the_requested_season(tmp_path):
    # A 2024 race with round 1 would map to the same 2025 file and repeat the 2025 difference if seasons were not filtered.
    raw = tmp_path / "raw"
    write_mzafram(raw, 1, drivers={"NOR": 50.0}, teams={})
    points = _points([(1, "NOR", "driver", 59.0)])
    assert totals_mismatches(2025, raw, points, _races([(2025, 1, 1), (2024, 1, 1)])) == [
        {"season": 2025, "round": 1, "asset": "NOR", "ours": 59.0, "mzafram": 50.0},
    ]


def test_totals_missing_mzafram_file_is_skipped(tmp_path):
    raw = tmp_path / "raw"
    points = _points([(2, "NOR", "driver", 59.0)])
    assert totals_mismatches(2025, raw, points, _races([(2025, 2, 2)])) == []
    assert not (tmp_path / "processed" / "totals_mismatches.csv").exists()


@pytest.mark.data
@pytest.mark.parametrize("season", [2023, 2024, 2025, 2026])
def test_scoring_reproduces_every_completed_session(raw_data, season):
    bad = gate_mismatches(season, raw_data, load_rules(season))
    found = {(m["season"], m["slug"], m["session"], m["asset"]) for m in bad}
    expected = {key for key in KNOWN_SOURCE_EXCEPTIONS if key[0] == season}
    assert found == expected, (
        f"unexpected {sorted(found - expected)}, missing {sorted(expected - found)}; "
        f"{len(bad)} mismatches, first: {bad[:20]}"
    )


@pytest.mark.data
@pytest.mark.parametrize("season", [2023, 2024, 2025, 2026])
def test_finish_positions_agree(raw_data, season):
    # Bounded sanity check: the remaining mismatches are post-race reclassifications and are written to
    # data/processed/finish_mismatches.csv. Every row is shown here, not hidden.
    bad = finish_mismatches(season, raw_data)
    assert len(bad) <= 10, f"{len(bad)} mismatches (limit 10), rows: {bad}"
