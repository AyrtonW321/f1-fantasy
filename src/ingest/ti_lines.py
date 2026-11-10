"""TracingInsights driver and constructor rows turned into scoring inputs (src/sim/scoring.py)."""
import json
import re
from pathlib import Path

from src.ingest.codes import driver_code
from src.sim.scoring import DriverLine, PitResult, Session

_SECONDS = re.compile(r"of ([\d.]+)s")
_RANK_TOKENS = re.compile(r"Fastest|2nd fastest|3rd fastest")
_RANK_OF_TOKEN = {"Fastest": 1, "2nd fastest": 2, "3rd fastest": 3}
_TEAMWORK = {
    "Neither driver reached Q2": "neither_q2",
    "One driver reached Q2": "one_q2",
    "Both drivers reached Q2": "both_q2",
    "One driver reached Q3": "one_q3",
    "Both drivers reached Q3": "both_q3",
}
# Jolpica file name -> key of the result list inside each Race dict
_JOLPICA_RESULTS = {"results": "Results", "qualifying": "QualifyingResults", "sprint": "SprintResults"}


def _points(session_result: dict, key: str) -> int:
    return (session_result.get(key) or {}).get("points", 0)


def _position(value: str | None) -> int | None:
    # TI stores finishing positions as strings; codes such as NC, DQ, WD, NT, RT carry no position points.
    return int(value) if value is not None and value.isdigit() else None


def parse_pit(row: dict) -> PitResult:
    session_result = row.get("sessionResult") or {}
    text = (session_result.get("fastestPitStopPoints") or {}).get("text") or ""
    seconds = None
    ranks: tuple[int, ...] = ()
    if " of " in text:
        # time text, e.g. "Fastest pit stop of 2.19s": seconds only, no rank tokens
        match = _SECONDS.search(text)
        seconds = float(match.group(1)) if match else None
    elif text and text != "Fastest pit stop time":
        ranks = tuple(_RANK_OF_TOKEN[token] for token in _RANK_TOKENS.findall(text))
    return PitResult(
        ranks=ranks,
        seconds=seconds,
        overall_fastest=bool(row.get("raceOverallFastestPitStop")),
        world_record=_points(session_result, "worldRecordPitStopPoints") != 0,
    )


def parse_teamwork(text: str) -> str | None:
    if not text:
        return None
    if text not in _TEAMWORK:
        raise ValueError(f"unknown teamwork text: {text}")
    return _TEAMWORK[text]


def driver_line(row: dict, session: Session) -> DriverLine:
    session_result = row.get("sessionResult") or {}
    racing = session in ("sprint", "race")
    return DriverLine(
        code=row["abbreviation"],
        session=session,
        position=_position(row.get(f"{session}Position")),
        gained=(row.get(f"{session}PositionsGained") or 0) if racing else 0,
        overtakes=(row.get(f"{session}Overtakes") or 0) if racing else 0,
        fastest_lap=bool(row.get(f"{session}FastestLap")) if racing else False,
        dotd=bool(row.get("raceDriverOfTheDay")) if session == "race" else False,
        not_classified=_points(session_result, "notClassifiedPoints") != 0,
        disqualified=_points(session_result, "disqualifiedPoints") != 0,
    )


def weekend_entrants(season: int, round_: int, raw_dir: Path) -> set[str]:
    codes: set[str] = set()
    for name, key in _JOLPICA_RESULTS.items():
        path = raw_dir / "jolpica" / str(season) / f"{name}.json"
        if not path.exists():
            continue
        for race in json.loads(path.read_text(encoding="utf-8")):
            if int(race["round"]) != round_:
                continue
            codes.update(driver_code(result["Driver"]) for result in race.get(key, []))
    return codes
