"""Poisson count helpers for overtakes: log-link regression and a gamma-Poisson shrunk rate."""
import numpy as np


def fit(X: np.ndarray, y: np.ndarray, l2: float = 1.0, iters: int = 50) -> np.ndarray:
    """Penalised Newton fit of log E[y] = X @ beta. Column 0 must be the intercept (not penalised)."""
    pen = l2 * np.eye(X.shape[1])
    pen[0, 0] = 0.0
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(max(y.mean(), 1e-9))
    for _ in range(iters):
        mu = np.exp(X @ beta)
        step = np.linalg.solve((X * mu[:, None]).T @ X + pen, X.T @ (y - mu) - pen @ beta)
        beta += step
        if np.abs(step).max() < 1e-9:
            break
    return beta


def shrunk_rate(count, exposure, prior_rate: float, weight: float):
    """Posterior mean of a gamma(prior_rate*weight, weight) prior after `count` events in `exposure`."""
    return (count + weight * prior_rate) / (exposure + weight)


def deviance(y: np.ndarray, mu: np.ndarray) -> float:
    """Mean Poisson deviance; lower is better."""
    y, mu = np.asarray(y, float), np.asarray(mu, float)
    term = np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0.0)
    return float(np.mean(2 * (term - (y - mu))))
