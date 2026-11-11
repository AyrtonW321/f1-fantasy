import numpy as np

from src.models import plackett_luce


def test_sample_orders_hold_every_entrant_once_and_repeat_with_seed():
    s = np.array([2.0, 1.0, 0.0, -1.0, -3.0])
    a = plackett_luce.sample(s, 500, np.random.default_rng(7))
    b = plackett_luce.sample(s, 500, np.random.default_rng(7))
    assert (np.sort(a, axis=1) == np.arange(5)).all()
    assert (a == b).all()
    win = np.bincount(a[:, 0], minlength=5) / 500
    assert win[0] > win[1] > win[4]  # strongest wins most
    assert abs(win[0] - np.exp(2) / np.exp(s).sum()) < 0.06  # P(win) = w_i / sum w


def test_fit_recovers_strength_weights():
    rng = np.random.default_rng(0)
    true = np.array([1.5, -0.5])
    orders = []
    for _ in range(60):
        x = rng.normal(size=(12, 2))
        orders.append(x[plackett_luce.sample(x @ true, 1, rng)[0]])
    beta = plackett_luce.fit(orders, l2=0.01)
    assert np.allclose(beta, true, atol=0.3)
