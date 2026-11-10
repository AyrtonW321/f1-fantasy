"""Kalman strength filter: constructor strength (theta) and driver skill (phi).

State x = [theta_c for each constructor, phi_d for each driver]. A driver d with
constructor c gives y = theta_c + phi_d + eps, eps ~ N(0, sigma_kind^2), where
y = -gap_pct (larger is faster). Process noise: q_car on theta, q_driver on phi.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.guard import assert_known_before_lock

STATE_COLUMNS = ["driver_code", "constructor_id", "theta", "phi", "strength", "var"]
OUTPUT_COLUMNS = [
    "season",
    "round",
    "driver_code",
    "constructor_id",
    "theta",
    "phi",
    "strength",
    "var",
    "known_at",
]


class StrengthFilter:
    def __init__(self, params: dict):
        self.params = params
        self._labels: list[tuple[str, str]] = []  # ("c", constructor_id) or ("d", driver_code)
        self._pos: dict[tuple[str, str], int] = {}
        self._x = np.zeros(0)
        self._P = np.zeros((0, 0))
        self._is_car = np.zeros(0, dtype=bool)
        self._last_constructor: dict[str, str] = {}

    def _prior_mean(self, constructor: str) -> float:
        weight = self.params.get("prior_2025_weight")
        prior = self.params.get("prior_theta")
        if weight is None or prior is None or constructor not in prior:
            return 0.0
        return float(weight) * float(prior[constructor])

    def add_entities(self, constructors, drivers) -> None:
        """Add unseen entities with the prior mean and p0 variance. Existing ones are untouched."""
        labels, means, variances, is_car = [], [], [], []
        seen: set[tuple[str, str]] = set()
        for c in constructors:
            key = ("c", c)
            if key in self._pos or key in seen:
                continue
            seen.add(key)
            labels.append(key)
            means.append(self._prior_mean(c))
            variances.append(float(self.params["p0_car"]))
            is_car.append(True)
        for d in drivers:
            key = ("d", d)
            if key in self._pos or key in seen:
                continue
            seen.add(key)
            labels.append(key)
            means.append(0.0)
            variances.append(float(self.params["p0_driver"]))
            is_car.append(False)
        if not labels:
            return
        n = len(self._labels)
        k = len(labels)
        P = np.zeros((n + k, n + k))
        P[:n, :n] = self._P
        P[n:, n:] = np.diag(variances)
        self._P = P
        self._x = np.concatenate([self._x, np.asarray(means, dtype=float)])
        self._is_car = np.concatenate([self._is_car, np.asarray(is_car, dtype=bool)])
        for i, key in enumerate(labels):
            self._pos[key] = n + i
        self._labels.extend(labels)

    def predict_step(self, q_multiplier: float = 1.0) -> None:
        """Random-walk step: add Q to the covariance. The car part is scaled by q_multiplier."""
        q = np.where(
            self._is_car,
            float(self.params["q_car"]) * float(q_multiplier),
            float(self.params["q_driver"]),
        )
        self._P = self._P + np.diag(q)

    def update(self, obs: pd.DataFrame) -> None:
        """One batch update with diagonal R. Rows with NaN y are skipped."""
        obs = obs[obs["y"].notna()]
        if obs.empty:
            return
        self.add_entities(obs["constructor_id"].tolist(), obs["driver_code"].tolist())
        m = len(obs)
        n = len(self._labels)
        rows = np.arange(m)
        c_idx = [self._pos[("c", c)] for c in obs["constructor_id"]]
        d_idx = [self._pos[("d", d)] for d in obs["driver_code"]]
        H = np.zeros((m, n))
        H[rows, c_idx] = 1.0
        H[rows, d_idx] = 1.0
        y = obs["y"].to_numpy(dtype=float)
        sigma = self.params["sigma"]
        R = np.diag([float(sigma[kind]) ** 2 for kind in obs["kind"]])

        P = self._P
        S = H @ P @ H.T + R
        K = np.linalg.solve(S, H @ P).T
        innovation = y - H @ self._x
        self._x = self._x + K @ innovation
        A = np.eye(n) - K @ H
        P = A @ P @ A.T + K @ R @ K.T  # Joseph form
        self._P = 0.5 * (P + P.T)

        for d, c in zip(obs["driver_code"], obs["constructor_id"]):
            self._last_constructor[d] = c

    def state(self) -> pd.DataFrame:
        """One row per driver observed so far, with the latest seen constructor."""
        rows = []
        P = self._P
        for d, c in self._last_constructor.items():
            ti = self._pos[("c", c)]
            di = self._pos[("d", d)]
            theta = float(self._x[ti])
            phi = float(self._x[di])
            rows.append(
                {
                    "driver_code": d,
                    "constructor_id": c,
                    "theta": theta,
                    "phi": phi,
                    "strength": theta + phi,
                    "var": float(P[ti, ti] + P[di, di] + 2 * P[ti, di]),
                }
            )
        return pd.DataFrame(rows, columns=STATE_COLUMNS)

    def entities(self) -> list[tuple[str, str]]:
        return list(self._labels)

    def mean(self) -> np.ndarray:
        return self._x.copy()

    def covariance(self) -> np.ndarray:
        return self._P.copy()


def _apply_grouped(filt: StrengthFilter, obs: pd.DataFrame, mask: np.ndarray, applied: np.ndarray) -> None:
    """Apply the masked, not-yet-applied rows: one batch per (weekend round, kind), in known_at order."""
    selected = obs[mask]
    if selected.empty:
        return
    applied |= mask
    selected = selected.sort_values("known_at", kind="mergesort")
    for _, group in selected.groupby(["round", "kind"], sort=False):
        filt.update(group)


def run_season(season, observations: pd.DataFrame, races: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Run a fresh filter over one season and snapshot the state at each round's lock."""
    filt = StrengthFilter(params)
    season_races = races[races["season"] == season].sort_values("round")
    rounds = sorted(season_races["round"].unique())
    locks = dict(zip(season_races["round"], season_races["lock_utc"]))
    obs = (
        observations[observations["season"] == season]
        .sort_values("known_at", kind="mergesort")
        .reset_index(drop=True)
    )
    applied = np.zeros(len(obs), dtype=bool)
    q_first = float(params["q_first_round_multiplier"])
    snapshots = []
    for i, r in enumerate(rounds):
        lock = locks[r]
        known_by_lock = (obs["known_at"] <= lock).to_numpy()
        # (a) earlier weekends' observations that became known before this lock, at their own time
        earlier = ~applied & (obs["round"] < r).to_numpy() & known_by_lock
        _apply_grouped(filt, obs, earlier, applied)
        # (b) advance to this round
        filt.predict_step(q_multiplier=q_first if i == 0 else 1.0)
        # (c) this weekend's observations known before lock
        current = ~applied & (obs["round"] == r).to_numpy() & known_by_lock
        _apply_grouped(filt, obs, current, applied)
        # (d) snapshot
        snap = filt.state()
        if not snap.empty:
            snap["season"] = season
            snap["round"] = r
            snap["known_at"] = lock
            snapshots.append(snap[OUTPUT_COLUMNS])
    if snapshots:
        result = pd.concat(snapshots, ignore_index=True)
    else:
        result = pd.DataFrame(columns=OUTPUT_COLUMNS)
    assert_known_before_lock(result, races)
    return result
