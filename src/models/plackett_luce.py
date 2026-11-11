"""Regularized Plackett-Luce over finishing orders. Log-strength of an entrant = features @ beta."""
import numpy as np


def fit(orders: list[np.ndarray], l2: float = 1.0, iters: int = 50) -> np.ndarray:
    """Penalized maximum likelihood by Newton steps (the log likelihood is concave in beta).

    orders: one feature matrix (entrants, k) per race, rows sorted winner first.
    """
    k = orders[0].shape[1]
    beta = np.zeros(k)
    for _ in range(iters):
        grad, hess = -l2 * beta, -l2 * np.eye(k)
        for x in orders:
            s = x @ beta
            for j in range(len(x) - 1):  # stage j: entrant j picked from those still left
                w = np.exp(s[j:] - s[j:].max())
                p = w / w.sum()
                mean = p @ x[j:]
                grad += x[j] - mean
                hess -= (x[j:] * p[:, None]).T @ x[j:] - np.outer(mean, mean)
        step = np.linalg.solve(hess, grad)
        beta -= step
        if np.abs(step).max() < 1e-9:
            break
    return beta


def sample(log_strength: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """n full orders (entrant indices, winner first). Gumbel-max: argsort of log-strength + Gumbel noise is
    an exact Plackett-Luce draw. log_strength may be (m,) or (n, m); -inf entries sort last."""
    shape = np.broadcast_shapes((n, np.shape(log_strength)[-1]), np.shape(log_strength))
    return np.argsort(-(log_strength + rng.gumbel(size=shape)), axis=1, kind="stable")
