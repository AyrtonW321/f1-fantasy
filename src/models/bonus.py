"""Empirical bonus-event samplers. History is limited to pre-lock completed rounds."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BonusOutcome:
    status: str
    fastest_lap_driver: str | None = None
    driver_of_the_day: str | None = None
    constructor_pit_points: dict[str, float] | None = None


def _eligible_history(history: pd.DataFrame, target_round: int, drivers: set[str],
                      constructors: set[str], target_lock: pd.Timestamp | str,
                      target_season: int = 2026) -> pd.DataFrame:
    required = {"season", "round", "known_at"}
    if not required <= set(history.columns):
        return history.iloc[0:0]
    h = history[(history["season"] == target_season) & (history["round"] < target_round)].copy()
    h["known_at"] = pd.to_datetime(h.known_at, utc=True, errors="coerce")
    cutoff = pd.to_datetime(target_lock, utc=True)
    return h[h.known_at.notna() & (h.known_at <= cutoff)]


def _sample_rate(history: pd.DataFrame, event: str, order: list[str], rng: np.random.Generator,
                 min_rows: int) -> str | None:
    field = set(order)
    if event not in history or "driver_code" not in history or len(history) < min_rows:
        return None
    h = history[history.driver_code.isin(field) & history[event].notna()]
    if len(h) < min_rows:
        return None
    rates = h.groupby("driver_code")[event].mean().reindex(order, fill_value=0).to_numpy(float)
    # Beta(1, 1) shrinkage toward the race-field rate prevents sparse perfect rates.
    field_rate = float(h[event].mean())
    counts = h.groupby("driver_code")[event].count().reindex(order, fill_value=0).to_numpy(float)
    shrunk = (counts * rates + 2.0 * field_rate) / (counts + 2.0)
    probabilities = shrunk / shrunk.sum() if shrunk.sum() else np.full(len(order), 1 / len(order))
    return str(rng.choice(order, p=probabilities))


def sample_bonus(history: pd.DataFrame, target_round: int, race_order: list[str],
                 driver_constructors: dict[str, str], constructors: list[str], *,
                 target_lock: pd.Timestamp | str, seed: int = 0, season: int = 2026,
                 min_history: int = 8) -> BonusOutcome:
    """Sample supported labels from prior-round history; unknown feeds return explicit unsupported."""
    drivers = set(race_order)
    teams = set(constructors)
    h = _eligible_history(history, target_round, drivers, teams, target_lock, season)
    if h.empty or not race_order:
        return BonusOutcome("unsupported")
    rng = np.random.default_rng(seed)
    fastest = _sample_rate(h, "fastest_lap", race_order, rng, min_history)
    dotd = _sample_rate(h, "dotd", race_order, rng, min_history)
    pit = None
    if {"constructor_id", "pit_points"} <= set(h.columns):
        p = h[h.constructor_id.isin(teams) & h.pit_points.notna()]
        if len(p) >= min_history:
            pit = {}
            field_values = p.pit_points.astype(float).to_numpy()
            for team in constructors:
                vals = p.loc[p.constructor_id == team, "pit_points"].astype(float)
                # A two-observation field prior shrinks thin team histories toward the field.
                use_field = not len(vals) or rng.random() < 2 / (len(vals) + 2)
                pit[team] = float(rng.choice(field_values if use_field else vals.to_numpy()))
    if fastest is None and dotd is None and pit is None:
        return BonusOutcome("unsupported")
    return BonusOutcome("supported", fastest, dotd, pit)
