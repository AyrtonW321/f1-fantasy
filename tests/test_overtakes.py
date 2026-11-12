import numpy as np
import pandas as pd

from src.features.overtakes import expected
from src.models import poisson


def test_poisson_fit_recovers_log_rate_and_shrunk_rate_limits():
    rng = np.random.default_rng(0)
    X = np.column_stack([np.ones(4000), rng.integers(0, 2, 4000)])
    y = rng.poisson(np.exp(X @ np.array([1.0, 0.7])))
    assert np.allclose(poisson.fit(X, y, l2=0.0), [1.0, 0.7], atol=0.1)
    assert poisson.shrunk_rate(0, 0, 3.0, 5.0) == 3.0  # no data -> prior
    assert abs(poisson.shrunk_rate(1000, 500, 3.0, 1.0) - 2.0) < 0.01  # lots of data -> own rate


def test_expected_uses_only_earlier_rounds_and_track_effect():
    tracks = pd.DataFrame({"season": [2025, 2026, 2026, 2026], "round": [1, 1, 2, 3],
                           "overtaking_difficulty": ["low", "low", "low", "high"]})
    ot = pd.DataFrame({"season": [2025, 2025, 2026, 2026, 2026], "round": [1, 1, 1, 1, 3],
                       "asset_id": ["A", "B", "A", "B", "A"], "overtakes": [2, 2, 8, 0, 99], "gained": [0, 0, 2, -2, 99]})
    e = expected(ot, tracks, 2026, 2, ["A", "B"], w_o=0.1, w_g=0.1)  # round 3 row must be ignored
    assert e["ov"][0] > e["ov"][1] and e["ov"][0] < 9 and e["gained"][0] > 0 > e["gained"][1]
    assert expected(ot, tracks, 2026, 1, ["A"], 1.0, 1.0) is None
