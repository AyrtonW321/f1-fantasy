"""Build normalized Parquet tables from data/raw into data/processed. Run from the project folder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from src.ingest.build_tables import _load, build_all  # noqa: E402
from src.ingest.ti_lines import bonus_points  # noqa: E402
from src.sim.scoring import load_rules  # noqa: E402

BONUS_SEASONS = [2026]  # Phase 4 uses 2026 only


def build_bonus(raw_dir: Path, out_dir: Path) -> None:
    """Per-asset bonus points per round (fastest lap, DotD, pit stop) for assets in fantasy_points."""
    races = pd.read_parquet(out_dir / "races.parquet")
    points = pd.read_parquet(out_dir / "fantasy_points.parquet")
    rows = []
    for season in BONUS_SEASONS:
        rules = load_rules(season)
        for race in races[(races["season"] == season) & races["completed"]].itertuples():
            path = raw_dir / "tracinginsights" / str(season) / race.slug / "race_all.json"
            for row in _load(path):
                kind = row["type"]
                rows.append({"season": season, "round": int(race.round), "kind": kind,
                             "asset_id": row["abbreviation"] if kind == "driver" else row["id"],
                             "bonus": bonus_points(row, rules)})
    bonus = pd.DataFrame(rows).drop_duplicates(["season", "round", "asset_id", "kind"])
    # Inner join drops TI phantom rows and carries each asset-round's known_at.
    keys = ["season", "round", "asset_id", "kind"]
    bonus = points[keys + ["known_at"]].merge(bonus, on=keys)
    bonus.to_parquet(out_dir / "bonus.parquet", index=False)


def build_overtakes(raw_dir: Path, out_dir: Path) -> None:
    """Race overtakes and positions gained per driver-round, 2023-2026 (TI raceOvertakes, racePositionsGained)."""
    races = pd.read_parquet(out_dir / "races.parquet")
    points = pd.read_parquet(out_dir / "fantasy_points.parquet")
    rows = []
    for race in races[races["completed"]].itertuples():
        for row in _load(raw_dir / "tracinginsights" / str(race.season) / race.slug / "race_all.json"):
            if row["type"] == "driver":
                rows.append({"season": race.season, "round": int(race.round), "asset_id": row["abbreviation"],
                             "overtakes": row["raceOvertakes"] or 0, "gained": row["racePositionsGained"] or 0})
    ot = pd.DataFrame(rows).drop_duplicates(["season", "round", "asset_id"])
    keys = ["season", "round", "asset_id"]
    ot = points[points["kind"] == "driver"][keys + ["known_at"]].merge(ot, on=keys)
    ot.to_parquet(out_dir / "overtakes.parquet", index=False)


def main() -> None:
    out_dir = Path("data/processed")
    build_all(Path("data/raw"), out_dir, [2023, 2024, 2025, 2026])
    build_bonus(Path("data/raw"), out_dir)
    build_overtakes(Path("data/raw"), out_dir)
    for name in ("races", "prices", "price_changes", "fantasy_points", "results", "bonus", "overtakes"):
        print(f"{name}: {len(pd.read_parquet(out_dir / f'{name}.parquet'))} rows")


if __name__ == "__main__":
    main()
