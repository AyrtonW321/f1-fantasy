"""Track ratings loader and template writer.

Ratings are hand-built by the user. This module never fills a blank rating.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = ["slug", "circuit_type", "overtaking_difficulty", "notes"]
CIRCUIT_TYPES = {"street", "permanent", "hybrid"}
RACES_PATH = Path("data/processed/races.parquet")
TRACKS_PATH = Path("data/static/tracks.csv")


def _clean(value: object) -> str:
    return "" if value is None or (isinstance(value, float) and np.isnan(value)) else str(value).strip()


def _parse_overtaking(slug: str, raw: str) -> float:
    if raw == "":
        return np.nan
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"overtaking_difficulty for {slug!r} is not an integer: {raw!r}") from None
    if not value.is_integer() or not 1 <= value <= 5:
        raise ValueError(f"overtaking_difficulty for {slug!r} must be an integer 1-5, got {raw!r}")
    return value


def load_tracks(path: Path, races: pd.DataFrame) -> pd.DataFrame:
    """Load tracks.csv and check it matches the distinct race slugs in `races`."""
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing_cols = [c for c in COLUMNS if c not in raw.columns]
    if missing_cols:
        raise ValueError(f"tracks file {path} is missing columns: {missing_cols}")

    slugs = [_clean(s) for s in raw["slug"]]
    seen: set[str] = set()
    for slug in slugs:
        if slug in seen:
            raise ValueError(f"duplicate slug in tracks file: {slug!r}")
        seen.add(slug)

    race_slugs = set(races["slug"].dropna().unique())
    for slug in sorted(race_slugs - seen):
        raise ValueError(f"race slug {slug!r} has no row in tracks file {path}")
    for slug in sorted(seen - race_slugs):
        raise ValueError(f"tracks file slug {slug!r} matches no race")

    out = pd.DataFrame({"slug": slugs})
    circuit = []
    for slug, raw_type in zip(slugs, raw["circuit_type"]):
        value = _clean(raw_type)
        if value and value not in CIRCUIT_TYPES:
            raise ValueError(f"circuit_type for {slug!r} must be one of {sorted(CIRCUIT_TYPES)}, got {value!r}")
        circuit.append(value if value else None)
    out["circuit_type"] = pd.Series(circuit, dtype=object)
    out["overtaking_difficulty"] = pd.Series(
        [_parse_overtaking(slug, _clean(v)) for slug, v in zip(slugs, raw["overtaking_difficulty"])],
        dtype="float64",
    )
    out["notes"] = pd.Series([_clean(v) or None for v in raw["notes"]], dtype=object)
    return out


def blank_ratings(df: pd.DataFrame) -> list[str]:
    """Slugs with any blank rating (circuit_type or overtaking_difficulty)."""
    blank = df["circuit_type"].isna() | df["overtaking_difficulty"].isna()
    return sorted(df.loc[blank, "slug"].tolist())


def write_template(races: pd.DataFrame, path: Path) -> None:
    """Write a template with every distinct race slug, sorted, ratings blank. Never overwrites."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing {path}")
    slugs = sorted(races["slug"].dropna().unique())
    template = pd.DataFrame({"slug": slugs, "circuit_type": "", "overtaking_difficulty": "", "notes": ""})
    path.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(path, index=False, columns=COLUMNS)


def main(argv: list[str] | None = None, races_path: Path = RACES_PATH, out_path: Path = TRACKS_PATH) -> int:
    parser = argparse.ArgumentParser(description="Track ratings tools")
    parser.add_argument("--template", action="store_true", help="write a blank tracks.csv template")
    args = parser.parse_args(argv)
    if not args.template:
        parser.print_help()
        return 2
    if out_path.exists():
        print(f"refusing to overwrite existing {out_path}", file=sys.stderr)
        return 1
    races = pd.read_parquet(races_path)
    write_template(races, out_path)
    print(f"wrote template with {races['slug'].nunique()} slugs to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
