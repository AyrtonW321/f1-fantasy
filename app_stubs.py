"""Temporary UI contract stubs; replace with src.ui.logic when task 8.4 merges."""

import pandas as pd


def validate(team: dict) -> list[str]:
    errors = []
    if len(team.get("drivers", [])) != 5:
        errors.append("Select exactly five drivers.")
    if len(team.get("constructors", [])) != 2:
        errors.append("Select exactly two constructors.")
    return errors


def save_team(n: int, team: dict) -> None:
    errors = validate(team)
    if errors:
        raise ValueError("\n".join(errors))
    raise NotImplementedError("Team saving is unavailable until task 8.4 is merged.")


def apply_transfers(n: int, decision, chip: str | None = None) -> None:
    raise NotImplementedError("Transfer saving is unavailable until task 8.4 is merged.")


def top_teams(state, budget: float, n: int = 5) -> list:
    return []


def history_points(n: int) -> pd.DataFrame:
    return pd.DataFrame(columns=["round", "points", "cumulative", "team_value", "transfers", "chip", "lineup"])
