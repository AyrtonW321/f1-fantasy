"""Scoring gate and source cross-checks. Reports mismatches; never edits rows or rules."""
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from src.ingest.build_tables import build_races
from src.ingest.codes import driver_code
from src.ingest.ti_lines import driver_line, parse_pit, parse_teamwork, weekend_entrants
from src.sim.scoring import PitResult, score_constructor, score_driver

OFFICIAL_SEASON = 2026
# Official constructor code -> TracingInsights constructor id
CONSTRUCTOR_ALIASES = {"RBR": "RED", "RBS": "VRB"}
PIT_RETRY = 0.049  # TI pit text rounds the seconds, so a stop near a band edge can land one band off
TOLERANCE = 0.01
_TI_FILES = {"qualifying": "qualifying_all.json", "sprint": "sprint_all.json", "race": "race_all.json"}
_OFFICIAL_POINTS = {"qualifying": "QualifyingPoints", "sprint": "SprintPoints", "race": "RacePoints"}
_JOLPICA = {
    "qualifying": ("qualifying.json", "QualifyingResults"),
    "sprint": ("sprint.json", "SprintResults"),
    "race": ("results.json", "Results"),
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _blank_zero(value: str) -> float:
    # The official feed leaves blanks for sessions with no points.
    return float(value) if value.strip() else 0.0


def _text(section: dict, key: str) -> str:
    return (section.get(key) or {}).get("text") or ""


def _session_result(row: dict) -> dict:
    return row.get("sessionResult") or {}


def _ti_total(row: dict) -> float:
    return float(_session_result(row)["totalPoints"]["points"])


def _ti_sessions(ti_dir: Path) -> dict[str, list[dict]]:
    """Session name -> TI rows in qualifying, sprint, race order. Sprint exists only on sprint weekends."""
    out = {"qualifying": _load(ti_dir / _TI_FILES["qualifying"])}
    if (ti_dir / _TI_FILES["sprint"]).exists():
        out["sprint"] = _load(ti_dir / _TI_FILES["sprint"])
    out["race"] = _load(ti_dir / _TI_FILES["race"])
    return out


def _official_parts(value: dict) -> dict[str, float]:
    return {session: _blank_zero(value[key]) for session, key in _OFFICIAL_POINTS.items()}


def _official_rank(value: dict) -> tuple[bool, float]:
    # build_tables policy: an active row beats an inactive duplicate, then the larger absolute total wins.
    return str(value.get("IsActive")) == "1", abs(sum(_official_parts(value).values()))


def _official_index(raw_dir: Path, season: int, round_no: int) -> dict[tuple[str, str], dict]:
    """(kind, asset id) -> official row for one gameday. Kind is 'driver' or 'constructor'.
    Duplicate rows for one asset: the active row wins, then the larger absolute total, then the last row."""
    path = raw_dir / "official" / str(season) / "drivers" / f"{round_no}.json"
    if not path.exists():
        return {}
    best: dict[tuple[str, str], tuple[tuple[bool, float], dict]] = {}
    for value in _load(path)["Data"]["Value"]:
        kind = {"DRIVER": "driver", "CONSTRUCTOR": "constructor"}[value["PositionName"]]
        tla = value["DriverTLA"]
        key = (kind, CONSTRUCTOR_ALIASES.get(tla, tla) if kind == "constructor" else tla)
        rank = _official_rank(value)
        if key not in best or rank >= best[key][0]:
            best[key] = (rank, value)
    return {key: value for key, (_, value) in best.items()}


def _official_inconsistent(value: dict) -> bool:
    return abs(sum(_official_parts(value).values()) - _blank_zero(value["GamedayPoints"])) > TOLERANCE


def _participates(row: dict, session: str, entrants: set[str]) -> bool:
    # Listed in Jolpica's results for this weekend and given a TI position. WD and a missing position do not take part.
    position = row.get(f"{session}Position")
    return row["abbreviation"] in entrants and position is not None and position != "WD"


def _skip_reason(row: dict, session: str, entrants: set[str]) -> str:
    if row["abbreviation"] not in entrants:
        return "not in Jolpica weekend results"
    if row.get(f"{session}Position") is None:
        return "no TI position"
    return "withdrew (WD)"


def _constructor_lines(team_id: str, participants: list[dict], session: str) -> list:
    return [driver_line(row, session) for row in participants if row.get("constructorId") == team_id]


def _pit_retry_accepted(rules: dict, lines: list, teamwork: str | None, pit: PitResult, expected: float) -> bool:
    return any(
        score_constructor(rules, lines, teamwork=teamwork, pit=replace(pit, seconds=pit.seconds + shift)) == expected
        for shift in (-PIT_RETRY, PIT_RETRY)
    )


def _round_gate(season: int, race: dict, raw_dir: Path, rules: dict,
                ambiguous: list | None, anomalies: list | None, skipped: list | None) -> list[dict]:
    slug, round_no = race["slug"], int(race["round"])
    sessions = _ti_sessions(raw_dir / "tracinginsights" / str(season) / slug)
    entrants = weekend_entrants(season, round_no, raw_dir)
    official = _official_index(raw_dir, season, round_no) if season == OFFICIAL_SEASON else None
    inconsistent = {key for key, value in (official or {}).items() if _official_inconsistent(value)}
    ti_totals: dict[tuple[str, str], dict[str, float]] = {}
    mismatches: list[dict] = []

    for session, rows in sessions.items():
        participants = [row for row in rows if row["type"] == "driver" and _participates(row, session, entrants)]
        participating_codes = {row["abbreviation"] for row in participants}
        for row in rows:
            kind = row["type"]
            asset = row["abbreviation"] if kind == "driver" else row["id"]
            if kind == "driver" and not _participates(row, session, entrants):
                if skipped is not None:
                    skipped.append({"season": season, "slug": slug, "session": session, "driver": asset,
                                    "reason": _skip_reason(row, session, entrants)})
                # Skipped rows are not scored. In 2026 the official session must be 0, unless this driver takes part in the
                # same session under his real team: then the official points belong to that row, compared on its own.
                if official is not None and asset not in participating_codes and (kind, asset) in official:
                    official_points = _official_parts(official[(kind, asset)])[session]
                    if official_points != 0:
                        mismatches.append({"season": season, "slug": slug, "session": session, "asset": asset,
                                           "expected": official_points, "actual": 0})
                continue

            ti_total = _ti_total(row)
            ti_totals.setdefault((kind, asset), {})[session] = ti_total

            if official is None:
                expected = ti_total
            elif (kind, asset) not in official:
                expected = None
            elif (kind, asset) in inconsistent:
                expected = ti_total
            else:
                expected = _official_parts(official[(kind, asset)])[session]

            lines, teamwork, pit = None, None, None
            if kind == "driver":
                actual = score_driver(rules, driver_line(row, session))
            else:
                lines = _constructor_lines(asset, participants, session)
                teamwork = parse_teamwork(_text(_session_result(row), "teamworkPoints")) if session == "qualifying" else None
                pit = parse_pit(row) if session == "race" else PitResult()
                actual = score_constructor(rules, lines, teamwork=teamwork, pit=pit)

            if expected is not None and actual == expected:
                continue
            if (kind == "constructor" and session == "race" and pit.seconds is not None
                    and expected is not None and _pit_retry_accepted(rules, lines, teamwork, pit, expected)):
                if ambiguous is not None:
                    ambiguous.append({"season": season, "slug": slug, "asset": asset,
                                      "seconds": pit.seconds, "expected": expected})
                continue
            mismatches.append({"season": season, "slug": slug, "session": session, "asset": asset,
                               "expected": expected, "actual": actual})

    if anomalies is not None and official is not None:
        for key in sorted(inconsistent):
            if key in ti_totals:
                value = official[key]
                anomalies.append({
                    "season": season,
                    "slug": slug,
                    "asset": key[1],
                    "official_components": _official_parts(value),
                    "official_gameday": _blank_zero(value["GamedayPoints"]),
                    "ti_expected": ti_totals[key],
                })
    return mismatches


def gate_mismatches(season: int, raw_dir: Path, rules: dict, ambiguous: list | None = None,
                    anomalies: list | None = None, skipped: list | None = None) -> list[dict]:
    """Every TI row of every completed session scored with the rules, compared with the expected session points.

    A driver row takes part only if Jolpica lists him that weekend and TI gives him a position. Rows that do not
    take part are not scored or compared; they are appended to `skipped`. Constructors score only participating rows.
    In 2026, a skipped driver whose official row has non-zero points for that session is reported with actual 0.
    """
    races = build_races(season, raw_dir)
    out: list[dict] = []
    for race in races[races["completed"]].to_dict("records"):
        out.extend(_round_gate(season, race, raw_dir, rules, ambiguous, anomalies, skipped))
    return out


def _position(value) -> int | None:
    # TI positions are digit strings. NC, DQ, WD, NT, RT, blanks and 0 carry no finishing position.
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    return value if isinstance(value, int) and value > 0 else None


def _jolpica_finishes(raw_dir: Path, season: int, round_no: int, session: str) -> dict[str, int]:
    name, key = _JOLPICA[session]
    path = raw_dir / "jolpica" / str(season) / name
    finishes: dict[str, int] = {}
    if path.exists():
        for race in _load(path):
            if int(race["round"]) == round_no:
                for result in race.get(key, []):
                    finishes[driver_code(result["Driver"])] = int(result["position"])
    return finishes


def _save_season_csv(path: Path, season: int, rows: list[dict]) -> None:
    """One CSV for all seasons: this season's rows are replaced and other seasons' rows are kept.
    Written only when there are rows, or when an older file still holds this season's rows."""
    if not rows and not path.exists():
        return
    default_columns = {
        "finish_mismatches.csv": ["season", "slug", "session", "driver", "ti", "jolpica"],
        "totals_mismatches.csv": ["season", "round", "asset", "ours", "mzafram"],
    }
    columns = list(rows[0]) if rows else default_columns[path.name]
    frame = pd.DataFrame(rows, columns=columns)
    if path.exists() and path.stat().st_size:
        previous = pd.read_csv(path)
        frame = pd.concat([previous[previous["season"] != season], frame], ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def finish_mismatches(season: int, raw_dir: Path) -> list[dict]:
    """TI numeric finishing positions compared with Jolpica's, for every completed session.
    Rows are also written to data/processed/finish_mismatches.csv (raw_dir's sibling 'processed' folder)."""
    races = build_races(season, raw_dir)
    out: list[dict] = []
    for race in races[races["completed"]].to_dict("records"):
        slug, round_no = race["slug"], int(race["round"])
        for session, rows in _ti_sessions(raw_dir / "tracinginsights" / str(season) / slug).items():
            jolpica = _jolpica_finishes(raw_dir, season, round_no, session)
            for row in rows:
                if row["type"] != "driver":
                    continue
                ti = _position(row.get(f"{session}Position"))
                if ti is None:
                    continue
                code = row["abbreviation"]
                if jolpica.get(code) != ti:
                    out.append({"season": season, "slug": slug, "session": session, "driver": code,
                                "ti": ti, "jolpica": jolpica.get(code)})
    _save_season_csv(raw_dir.parent / "processed" / "finish_mismatches.csv", season, out)
    return out


def totals_mismatches(season: int, raw_dir: Path, points: pd.DataFrame, races: pd.DataFrame) -> list[dict]:
    """Report only, not a gate: our fantasy_points totals against mzafram Round_Fantasy_Points.
    mzafram files are numbered by the Jolpica round (races `round`), not by TI's roundNumber (`ti_slug_round`).
    Only this season's completed races are compared."""
    out: list[dict] = []
    for race in races[(races["season"] == season) & races["completed"]].to_dict("records"):
        round_no = int(race["round"])
        path = raw_dir / "mzafram" / str(season) / f"round_{round_no:02d}.json"
        if not path.exists():
            continue
        in_round = points[(points["season"] == season) & (points["round"] == round_no)]
        ours = {(row.kind, row.asset_id): float(row.total) for row in in_round.itertuples(index=False)}
        data = _load(path)
        theirs = {("driver", d["Driver_Code"]): d["Round_Fantasy_Points"] for d in data.get("Drivers", [])}
        theirs.update({("constructor", t["Team_Code"]): t["Round_Fantasy_Points"] for t in data.get("Teams", [])})
        for key, mz_total in theirs.items():
            if key in ours and mz_total is not None and abs(ours[key] - float(mz_total)) > TOLERANCE:
                out.append({"season": season, "round": round_no, "asset": key[1],
                            "ours": ours[key], "mzafram": float(mz_total)})
    _save_season_csv(raw_dir.parent / "processed" / "totals_mismatches.csv", season, out)
    return out
