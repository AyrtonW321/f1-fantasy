"""Tune the strength filter on 2023-2025, then evaluate 2026 once as a holdout."""

from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.tracks import load_track_metadata
from src.models.kalman import KalmanConfig, compare_order_predictions, walkforward_strength


def _summary_for(predictions: pd.DataFrame, seasons: set[int]) -> tuple[pd.DataFrame, dict[str, float]]:
    subset = predictions.loc[predictions["season"].isin(seasons)]
    return compare_order_predictions(subset)


def _format_metrics(metrics: dict[str, float]) -> str:
    if not metrics:
        return "No rounds had enough matched drivers for rank comparison."
    return (f"Kalman mean Spearman: {metrics['kalman_mean_spearman']:.4f}; "
            f"last-race-order mean Spearman: {metrics['last_race_mean_spearman']:.4f}; "
            f"rounds: {metrics['rounds_compared']}")


def main() -> None:
    data_dir = Path("data/processed")
    results = pd.read_parquet(data_dir / "results.parquet")
    races = pd.read_parquet(data_dir / "races.parquet")
    tracks = load_track_metadata(Path("data/static/tracks.csv"), races)

    training_seasons = {2023, 2024, 2025}
    train_results = results.loc[results["season"].isin(training_seasons)]
    train_races = races.loc[races["season"].isin(training_seasons)]
    train_tracks = tracks.loc[tracks["season"].isin(training_seasons)]
    candidates = []
    for car_q in (0.04, 0.12, 0.30):
        for driver_q in (0.001, 0.004, 0.015):
            for track_q in (0.0005, 0.002):
                for observation_noise in (0.2, 0.5):
                    for prior_weight in (0.0, 0.12):
                        for prior_rounds in (2, 3):
                            config = KalmanConfig(
                                car_process_noise=car_q, driver_process_noise=driver_q,
                                track_process_noise=track_q, observation_noise=observation_noise,
                                previous_year_prior_weight=prior_weight,
                                previous_year_prior_rounds=prior_rounds,
                            )
                            preds = walkforward_strength(train_results, train_races, train_tracks, config=config)
                            per_round, summary = compare_order_predictions(preds)
                            if summary:
                                candidates.append((summary["kalman_mean_spearman"], config, summary, per_round))
    if not candidates:
        raise RuntimeError("No training rounds have enough comparable drivers to tune the Kalman model")
    candidates.sort(key=lambda item: (item[0], -item[1].car_process_noise, -item[1].driver_process_noise), reverse=True)
    _, chosen, train_metrics, train_rounds = candidates[0]

    # Freeze settings selected on 2023-2025, then perform the 2026 holdout run once.
    all_predictions = walkforward_strength(results, races, tracks, config=chosen)
    round_metrics, all_metrics = compare_order_predictions(all_predictions)
    holdout = round_metrics.loc[round_metrics["season"].eq(2026)]
    holdout_metrics = {}
    if not holdout.empty:
        holdout_metrics = {
            "kalman_mean_spearman": float(holdout["kalman_spearman"].mean()),
            "last_race_mean_spearman": float(holdout["last_race_spearman"].mean()),
            "rounds_compared": int(len(holdout)),
        }

    report = [
        "# Phase 3 Kalman evaluation",
        "",
        "Walk-forward predictions use only results from earlier rounds. The model observation is within-race standardized finishing order; current-race results are applied only after prediction.",
        "",
        "## Tuning (2023-2025)",
        "",
        f"Selected car process noise: `{chosen.car_process_noise}`",
        f"Selected driver process noise: `{chosen.driver_process_noise}`",
        f"Selected track process noise: `{chosen.track_process_noise}`",
        f"Selected observation noise: `{chosen.observation_noise}`",
        f"Selected previous-season prior weight: `{chosen.previous_year_prior_weight}` for up to `{chosen.previous_year_prior_rounds}` initial rounds.",
        "The grid includes a no-prior variant (`prior weight = 0`). Car, driver, and track effects are centered to sum to zero after each race update.",
        _format_metrics(train_metrics),
        "",
        "| car Q | driver Q | track Q | obs noise | prior weight | prior rounds | Kalman Spearman | last-race Spearman | rounds |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, config, metrics, _ in sorted(candidates, key=lambda item: item[1].car_process_noise + item[1].driver_process_noise):
        report.append(f"| {config.car_process_noise} | {config.driver_process_noise} | {config.track_process_noise} | "
                      f"{config.observation_noise} | {config.previous_year_prior_weight} | "
                      f"{config.previous_year_prior_rounds} | {metrics['kalman_mean_spearman']:.4f} | "
                      f"{metrics['last_race_mean_spearman']:.4f} | "
                      f"{metrics['rounds_compared']} |")
    report += ["", "## 2026 held-out evaluation", "", _format_metrics(holdout_metrics), "",
               "Acceptance: Kalman mean Spearman must exceed the matched last-race-order baseline. No 2026 metric was used to choose parameters.", ""]
    Path("reports").mkdir(exist_ok=True)
    Path("reports/phase3_kalman.md").write_text("\n".join(report), encoding="utf-8")

    holdout_log = Path("reports/holdout_2026_log.md")
    entry = (f"\n## Phase 3 Kalman evaluation ({pd.Timestamp.utcnow().date()})\n\n"
             f"Training window: 2023-2025. Parameters: car Q={chosen.car_process_noise}, "
             f"driver Q={chosen.driver_process_noise}, track Q={chosen.track_process_noise}, "
             f"observation variance={chosen.observation_noise}, prior weight={chosen.previous_year_prior_weight}, "
             f"prior rounds={chosen.previous_year_prior_rounds}. State effects centered after each round.\n\n"
             f"2026 result: {_format_metrics(holdout_metrics)}\n")
    with holdout_log.open("a", encoding="utf-8") as f:
        f.write(entry)
    print(_format_metrics(train_metrics))
    print("2026 holdout: " + _format_metrics(holdout_metrics))
    print(f"selected car Q={chosen.car_process_noise}, driver Q={chosen.driver_process_noise}")
    print(f"wrote reports/phase3_kalman.md and appended reports/holdout_2026_log.md")


if __name__ == "__main__":
    main()
