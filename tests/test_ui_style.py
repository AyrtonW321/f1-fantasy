from pathlib import Path

import pandas as pd
import pytest

from src.ui import style

PRICES = Path("data/processed/prices.parquet")


def test_text_color_contrast():
    assert style.text_color("#FFFFFF") == "#000000"  # Haas white
    assert style.text_color("#1E1E1E") == "#FFFFFF"  # dark
    assert style.text_color("#27F4D2") == "#000000"  # Mercedes teal
    assert style.text_color("#3671C6") == "#FFFFFF"  # Red Bull blue
    assert style.text_color(style.GREY) == "#FFFFFF"


@pytest.mark.skipif(not PRICES.exists(), reason="real data not unpacked")
def test_team_colors_cover_every_2026_constructor():
    prices = pd.read_parquet(PRICES)
    ids = set(prices.query("season == 2026 and kind == 'constructor'")["asset_id"])
    assert ids <= set(style.team_colors())


def test_driver_teams_latest_row_and_missing():
    results = pd.DataFrame({"season": [2026, 2026, 2026], "round": [1, 2, 2],
                            "driver_code": ["BEA", "BEA", "OCO"], "constructor_id": ["ferrari", "haas", "haas"]})
    assert style.driver_teams(results, 2026) == {"BEA": "HAA", "OCO": "HAA"}
    assert "HIR" not in style.driver_teams(results, 2026)
