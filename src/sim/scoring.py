"""Official F1 Fantasy scoring. Game values come from config/rules_{season}.yaml, never from this file."""
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml


class UnknownRuleError(Exception):
    """A rule needed for this score is null (never observed) or not defined."""


Session = Literal["qualifying", "sprint", "race"]


@dataclass(frozen=True)
class DriverLine:
    code: str
    session: Session
    position: int | None = None
    gained: int = 0
    overtakes: int = 0
    fastest_lap: bool = False
    dotd: bool = False
    not_classified: bool = False
    disqualified: bool = False


@dataclass(frozen=True)
class PitResult:
    ranks: tuple[int, ...] = ()
    seconds: float | None = None
    overall_fastest: bool = False
    world_record: bool = False


def load_rules(season: int, config_dir: Path = Path("config")) -> dict:
    with open(config_dir / f"rules_{season}.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _rule(rules: dict, path: str):
    node = rules
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            raise UnknownRuleError(f"{path} is not defined in the rules file")
        node = node[key]
    if node is None:
        raise UnknownRuleError(f"{path} is null for this season (never observed); not guessing")
    return node


def _driver_points(rules: dict, line: DriverLine, *, as_constructor: bool) -> int:
    session = line.session
    total = 0
    positions = rules["driver"][session]["position"]
    if line.position is not None and 1 <= line.position <= len(positions):
        total += positions[line.position - 1]
    if session in ("sprint", "race"):
        if line.gained:
            total += line.gained * _rule(rules, f"driver.{session}.gained")
        if line.overtakes:
            total += line.overtakes * _rule(rules, f"driver.{session}.overtake")
        if line.fastest_lap:
            total += _rule(rules, f"driver.{session}.fastest_lap")
    if line.dotd and session == "race" and not as_constructor:
        total += _rule(rules, "driver.race.driver_of_the_day")
    if line.not_classified:
        total += _rule(rules, f"driver.{session}.not_classified")
    if line.disqualified:
        if as_constructor:
            total += _rule(rules, f"constructor.disqualified.{session}")
        else:
            total += _rule(rules, f"driver.{session}.disqualified")
    return total


def _pit_points(rules: dict, pit: PitResult) -> int:
    c = rules["constructor"]
    if c["pit_scoring"] not in ("rank", "time_bands"):
        raise UnknownRuleError(f"constructor.pit_scoring {c['pit_scoring']!r} is not rank or time_bands")
    total = 0
    if c["pit_scoring"] == "rank":
        # Ranks outside the table (4th and lower) score 0.
        total += sum(c["pit_ranks"].get(r, 0) for r in pit.ranks)
    elif c["pit_scoring"] == "time_bands" and pit.seconds is not None:
        for upper, points in c["pit_bands"]:
            if pit.seconds < upper:
                total += points
                break
    if pit.overall_fastest:
        total += _rule(rules, "constructor.overall_fastest_stop")
    if pit.world_record:
        total += _rule(rules, "constructor.world_record_stop")
    return total


def score_driver(rules: dict, line: DriverLine) -> int:
    return round(_driver_points(rules, line, as_constructor=False))


def score_constructor(rules: dict, lines: Sequence[DriverLine],
                      teamwork: str | None = None, pit: PitResult = PitResult()) -> int:
    total = sum(_driver_points(rules, line, as_constructor=True) for line in lines)
    if teamwork is not None:
        total += _rule(rules, f"constructor.teamwork.{teamwork}")
    if any(line.session == "race" for line in lines):
        total += _pit_points(rules, pit)
    return round(total)
