"""Build normalized Parquet tables from data/raw into data/processed. Run from the project folder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src.ingest.build_tables import build_all  # noqa: E402


def main() -> None:
    out_dir = Path("data/processed")
    build_all(Path("data/raw"), out_dir, [2023, 2024, 2025, 2026])
    for name in ("races", "prices", "fantasy_points", "results"):
        print(f"{name}: {len(pd.read_parquet(out_dir / f'{name}.parquet'))} rows")


if __name__ == "__main__":
    main()
