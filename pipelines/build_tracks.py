"""Refresh pre-event safety-car rates from previously observed FastF1 race status."""

from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.tracks import add_prior_safety_car_rates, load_track_metadata


def main() -> None:
    track_path = Path("data/static/tracks.csv")
    tracks = load_track_metadata(track_path)
    status_path = Path("data/processed/track_status.parquet")
    status = pd.read_parquet(status_path) if status_path.exists() else pd.DataFrame(
        columns=["season", "round", "session_code", "track_status"])
    updated = add_prior_safety_car_rates(tracks, status)
    updated.to_csv(track_path, index=False)
    known = updated["safety_car_rate"].notna().sum()
    print(f"updated historical safety-car rates for {known}/{len(updated)} events")


if __name__ == "__main__":
    main()
