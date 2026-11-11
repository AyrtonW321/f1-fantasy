"""Sequential additive Kalman filter for constructor, driver and circuit strength."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class KalmanConfig:
    car_process_noise: float = 0.12
    driver_process_noise: float = 0.004
    track_process_noise: float = 0.001
    observation_noise: float = 0.35
    car_prior_variance: float = 1.0
    driver_prior_variance: float = 0.7
    track_prior_variance: float = 0.3
    previous_year_prior_weight: float = 0.12
    previous_year_prior_rounds: int = 3

    def __post_init__(self):
        if min(self.car_process_noise, self.driver_process_noise, self.track_process_noise,
               self.observation_noise, self.car_prior_variance, self.driver_prior_variance,
               self.track_prior_variance) <= 0:
            raise ValueError("Kalman variances/noise values must be positive")
        if not 0 <= self.previous_year_prior_weight <= 1:
            raise ValueError("previous_year_prior_weight must be between 0 and 1")


PREDICTION_COLUMNS = [
    "season", "round", "driver_code", "constructor_id", "track_id", "predicted_strength",
    "actual_position", "known_at",
]


class _Filter:
    def __init__(self, config: KalmanConfig):
        self.config = config
        self.keys: list[tuple[str, str]] = []
        self.index: dict[tuple[str, str], int] = {}
        self.mean = np.zeros(0, dtype=float)
        self.cov = np.zeros((0, 0), dtype=float)

    def ensure(self, kind: str, identity: str, prior_mean: float = 0.0) -> int:
        key = (kind, identity)
        if key in self.index:
            return self.index[key]
        old = len(self.keys)
        prior_variance = {
            "car": self.config.car_prior_variance,
            "driver": self.config.driver_prior_variance,
            "track": self.config.track_prior_variance,
        }[kind]
        self.keys.append(key)
        self.index[key] = old
        self.mean = np.append(self.mean, prior_mean)
        self.cov = np.pad(self.cov, ((0, 1), (0, 1)))
        self.cov[old, old] = prior_variance
        return old

    def transition(self) -> None:
        for key, i in self.index.items():
            q = {"car": self.config.car_process_noise,
                 "driver": self.config.driver_process_noise,
                 "track": self.config.track_process_noise}[key[0]]
            self.cov[i, i] += q

    def reset_cars_for_season(self, priors: dict[str, float]) -> None:
        car_indices = [i for (kind, _), i in self.index.items() if kind == "car"]
        for i in car_indices:
            identity = self.keys[i][1]
            self.mean[i] = priors.get(identity, 0.0) * self.config.previous_year_prior_weight
            self.cov[i, :] = 0.0
            self.cov[:, i] = 0.0
            self.cov[i, i] = self.config.car_prior_variance

    def score(self, constructor: str, driver: str, track: str, car_prior: float = 0.0) -> float:
        ids = [self.ensure("car", constructor, car_prior * self.config.previous_year_prior_weight),
               self.ensure("driver", driver), self.ensure("track", track)]
        return float(self.mean[ids].sum())

    def update(self, constructor: str, driver: str, track: str, observation: float,
               car_prior: float = 0.0) -> None:
        ids = [self.ensure("car", constructor, car_prior * self.config.previous_year_prior_weight),
               self.ensure("driver", driver), self.ensure("track", track)]
        h = np.zeros(len(self.keys), dtype=float)
        h[ids] = 1.0
        projected = self.cov @ h
        innovation_var = float(h @ projected + self.config.observation_noise)
        gain = projected / innovation_var
        residual = observation - float(h @ self.mean)
        self.mean += gain * residual
        self.cov -= np.outer(gain, projected)
        self.cov = (self.cov + self.cov.T) / 2

    def center_effects(self) -> None:
        """Impose zero-sum constraints separately on car, driver and track effects."""
        if not self.keys:
            return
        transform = np.eye(len(self.keys))
        for kind in ("car", "driver", "track"):
            indices = [i for (state_kind, _), i in self.index.items() if state_kind == kind]
            if len(indices) < 2:
                continue
            count = len(indices)
            transform[np.ix_(indices, indices)] = np.eye(count) - np.ones((count, count)) / count
        self.mean = transform @ self.mean
        self.cov = transform @ self.cov @ transform.T
        self.cov = (self.cov + self.cov.T) / 2


def _constructor_prior(results: pd.DataFrame, season: int) -> dict[str, float]:
    if results.empty or "constructor_id" not in results:
        return {}
    previous = results.loc[(results["season"] == season) & (results["session"] == "race")].copy()
    previous["position"] = pd.to_numeric(previous["position"], errors="coerce")
    previous = previous.dropna(subset=["constructor_id", "position"])
    if previous.empty:
        return {}
    mean = previous.groupby("constructor_id")["position"].mean()
    scale = mean.std(ddof=0)
    if not scale or not np.isfinite(scale):
        return {str(k): 0.0 for k in mean.index}
    return {str(k): float(-(v - mean.mean()) / scale) for k, v in mean.items()}


def walkforward_strength(
    results: pd.DataFrame,
    races: pd.DataFrame,
    track_metadata: pd.DataFrame,
    *,
    config: KalmanConfig = KalmanConfig(),
) -> pd.DataFrame:
    """Predict each race's order using only earlier completed races, then update the filter.

    Race position is converted to within-round standardized performance. The current
    race's results are used only after its predictions have been emitted.
    """
    if results.empty:
        return pd.DataFrame(columns=PREDICTION_COLUMNS)
    race_results = results.loc[results["session"].eq("race")].copy()
    race_results["position"] = pd.to_numeric(race_results["position"], errors="coerce")
    track_map = track_metadata[["season", "round", "track_id"]].drop_duplicates(
        ["season", "round"]).set_index(["season", "round"])["track_id"].to_dict()
    filter_ = _Filter(config)
    output = []
    seasons = sorted(races["season"].dropna().unique())
    for season in seasons:
        prior = _constructor_prior(race_results, int(season) - 1)
        if int(season) != seasons[0]:
            filter_.reset_cars_for_season(prior)
        season_races = races.loc[(races["season"] == season) & races["completed"]].sort_values("round")
        for event in season_races.itertuples(index=False):
            field = race_results.loc[(race_results["season"] == season)
                                     & (race_results["round"] == event.round)].copy()
            field = field.dropna(subset=["driver_code", "constructor_id", "position"])
            if field.empty:
                continue
            track_id = str(track_map.get((int(season), int(event.round)), f"unknown-{season}-{event.round}"))
            filter_.transition()
            event_prior = prior if int(event.round) <= config.previous_year_prior_rounds else {}
            for row in field.sort_values("driver_code").itertuples(index=False):
                driver, constructor = str(row.driver_code), str(row.constructor_id)
                output.append({
                    "season": int(season), "round": int(event.round), "driver_code": driver,
                    "constructor_id": constructor, "track_id": track_id,
                    "predicted_strength": filter_.score(constructor, driver, track_id,
                                                         event_prior.get(constructor, 0.0)),
                    "actual_position": float(row.position), "known_at": pd.to_datetime(event.lock_utc, utc=True),
                })
            positions = field["position"].astype(float)
            scale = float(positions.std(ddof=0)) or 1.0
            center = float(positions.mean())
            for row in field.sort_values("driver_code").itertuples(index=False):
                performance = -(float(row.position) - center) / scale
                constructor, driver = str(row.constructor_id), str(row.driver_code)
                filter_.update(constructor, driver, track_id, performance, event_prior.get(constructor, 0.0))
            filter_.center_effects()
    return pd.DataFrame(output, columns=PREDICTION_COLUMNS)


def last_race_order_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Attach the previous completed race's order score for a matched comparison."""
    output = predictions.copy()
    output["last_race_strength"] = np.nan
    for season, frame in output.groupby("season", sort=True):
        rounds = sorted(frame["round"].unique())
        previous_by_driver: dict[str, float] = {}
        for round_no in rounds:
            current = frame[frame["round"] == round_no]
            for idx, row in current.iterrows():
                output.loc[idx, "last_race_strength"] = previous_by_driver.get(row.driver_code, np.nan)
            previous_by_driver = {
                row.driver_code: -float(row.actual_position)
                for row in current.itertuples(index=False)
            }
    return output


def compare_order_predictions(predictions: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Compare per-round Spearman rank correlation against last race's order."""
    frame = last_race_order_predictions(predictions)
    metrics = []
    for (season, round_no), group in frame.groupby(["season", "round"], sort=True):
        group = group.dropna(subset=["last_race_strength", "predicted_strength", "actual_position"])
        if len(group) < 3:
            continue
        actual_rank = group["actual_position"].rank(method="average").to_numpy()
        kalman_rank = (-group["predicted_strength"]).rank(method="average").to_numpy()
        prior_rank = (-group["last_race_strength"]).rank(method="average").to_numpy()
        metrics.append({
            "season": int(season), "round": int(round_no), "drivers": len(group),
            "kalman_spearman": float(np.corrcoef(actual_rank, kalman_rank)[0, 1]),
            "last_race_spearman": float(np.corrcoef(actual_rank, prior_rank)[0, 1]),
        })
    per_round = pd.DataFrame(metrics)
    summary = {}
    if not per_round.empty:
        summary = {
            "kalman_mean_spearman": float(per_round["kalman_spearman"].mean()),
            "last_race_mean_spearman": float(per_round["last_race_spearman"].mean()),
            "rounds_compared": int(len(per_round)),
        }
    return per_round, summary
