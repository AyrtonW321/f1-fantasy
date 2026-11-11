import pandas as pd

from src.models.kalman import (
    KalmanConfig,
    compare_order_predictions,
    walkforward_strength,
)


def sample_data():
    results = []
    for round_no, order in [(1, ["AAA", "BBB", "CCC", "DDD"]),
                            (2, ["AAA", "BBB", "CCC", "DDD"]),
                            (3, ["AAA", "BBB", "CCC", "DDD"])]:
        for position, driver in enumerate(order, 1):
            constructor = "TEAM_X" if driver in {"AAA", "BBB"} else "TEAM_Y"
            results.append({"season": 2025, "round": round_no, "session": "race", "driver_code": driver,
                            "constructor_id": constructor, "position": position})
    races = pd.DataFrame([{"season": 2025, "round": r, "completed": True,
                            "lock_utc": pd.Timestamp(f"2025-03-{r:02d}T10:00:00Z")} for r in [1, 2, 3]])
    tracks = pd.DataFrame([{"season": 2025, "round": r, "track_id": f"track-{r}"} for r in [1, 2, 3]])
    return pd.DataFrame(results), races, tracks


def test_walkforward_prediction_does_not_consume_current_or_future_race():
    results, races, tracks = sample_data()
    base = walkforward_strength(results, races, tracks)
    changed = results.copy()
    changed.loc[changed["round"].eq(2), "position"] = changed.loc[changed["round"].eq(2), "position"].map(
        {1: 4, 2: 3, 3: 2, 4: 1})
    changed.loc[changed["round"].eq(3), "position"] = changed.loc[changed["round"].eq(3), "position"].map(
        {1: 3, 2: 4, 3: 1, 4: 2})
    altered = walkforward_strength(changed, races, tracks)
    r2_base = base.loc[base["round"].eq(2), "predicted_strength"].to_list()
    r2_altered = altered.loc[altered["round"].eq(2), "predicted_strength"].to_list()
    assert r2_base == r2_altered
    r1 = base.loc[base["round"].eq(1)]
    assert r1["predicted_strength"].eq(0).all()


def test_results_row_order_does_not_change_predictions():
    results, races, tracks = sample_data()
    expected = walkforward_strength(results, races, tracks)
    actual = walkforward_strength(results.sample(frac=1, random_state=8), races, tracks.sample(frac=1))
    pd.testing.assert_frame_equal(expected, actual)


def test_predictions_carry_lock_time_and_cover_race_drivers():
    results, races, tracks = sample_data()
    predictions = walkforward_strength(results, races, tracks)
    assert len(predictions) == len(results)
    assert (predictions["known_at"] <= predictions.merge(races, on=["season", "round"])["lock_utc"]).all()


def test_order_comparison_uses_only_matched_last_race_entrants():
    results, races, tracks = sample_data()
    predictions = walkforward_strength(results, races, tracks, config=KalmanConfig())
    per_round, summary = compare_order_predictions(predictions)
    assert per_round["round"].tolist() == [2, 3]
    assert per_round["drivers"].eq(4).all()
    assert "kalman_mean_spearman" in summary
    assert "last_race_mean_spearman" in summary
