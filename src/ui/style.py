"""Team colours and readable text colour for the app's asset cards."""
from pathlib import Path

import pandas as pd
import yaml

COLORS = Path(__file__).resolve().parents[2] / "config" / "team_colors.yaml"
GREY = "#5A5F66"  # driver with no known team


def team_colors() -> dict[str, dict]:
    return yaml.safe_load(COLORS.read_text(encoding="utf-8"))


def text_color(hex_: str) -> str:
    """Black or white, whichever reads better on hex_ (WCAG relative luminance)."""
    rgb = [int(hex_.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return "#FFFFFF" if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.4 else "#000000"


def driver_teams(results: pd.DataFrame, season: int) -> dict[str, str]:
    """Driver code to constructor asset id, from each driver's latest result up to `season`."""
    to_asset = {v["results_id"]: k for k, v in team_colors().items()}
    latest = (results.loc[results["season"] <= season].sort_values(["season", "round"])
              .drop_duplicates("driver_code", keep="last"))
    return {d: to_asset[c] for d, c in zip(latest["driver_code"], latest["constructor_id"]) if c in to_asset}
