import pandas as pd

from src.features.rolling import robust_mu
from src.features.sprint import sprint_mu


def test_sprint_term_only_on_sprint_round_and_is_prelock():
    lock = pd.Timestamp("2026-03-01T00:00:00Z")
    races = pd.DataFrame({"season": [2026, 2026, 2026], "round": [1, 2, 3],
                          "sprint": [True, True, False], "lock_utc": [lock] * 3})
    assets = [(a, k) for a, k in (("AAA", "driver"), ("BBB", "driver"))]
    prices = pd.DataFrame([{"season": 2026, "round": r, "asset_id": a, "kind": k,
                            "price": 10.0, "known_at": lock}
                           for r in (1, 2, 3) for a, k in assets])
    points = pd.DataFrame([{"season": 2026, "round": r, "asset_id": a, "kind": k,
                            "total": total, "sprint": spr, "known_at": lock - pd.Timedelta(days=1)}
                           for r, a, k, total, spr in ((1, "AAA", "driver", 10.0, 8.0),
                                                        (1, "BBB", "driver", 10.0, 0.0),
                                                        (2, "AAA", "driver", 20.0, 10.0),
                                                        (2, "BBB", "driver", 10.0, 0.0))])
    sprint = sprint_mu(prices, points, races, 2026, 2, trim=0.0, prior_weight=1.0, sprint_weight=1.0)
    normal = sprint_mu(prices, points, races, 2026, 3, trim=0.0, prior_weight=1.0, sprint_weight=1.0)
    residual = points.copy()
    residual["total"] -= residual["sprint"]
    baseline_sprint = robust_mu(prices, residual, races, 2026, 2, trim=0.0, prior_weight=1.0)
    baseline_normal = robust_mu(prices, residual, races, 2026, 3, trim=0.0, prior_weight=1.0)
    assert sprint.set_index("asset_id").loc["AAA", "mu"] > baseline_sprint.set_index("asset_id").loc["AAA", "mu"]
    pd.testing.assert_series_equal(normal["mu"], baseline_normal["mu"])
    late_points = points.copy()
    late_points.loc[late_points["round"] == 1, "known_at"] = lock + pd.Timedelta(seconds=1)
    late_points.loc[late_points["round"] == 1, "sprint"] = 1000.0
    pd.testing.assert_frame_equal(sprint, sprint_mu(prices, late_points, races, 2026, 2,
                                                    trim=0.0, prior_weight=1.0, sprint_weight=1.0))
    assert (sprint["known_at"] <= lock).all() and (normal["known_at"] <= lock).all()
    assert sprint.columns.tolist() == ["season", "round", "asset_id", "kind", "price", "mu", "known_at"]
