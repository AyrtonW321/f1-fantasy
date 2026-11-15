from src.ui import cards


def test_driver_card_filled_with_contrast():
    html = cards.asset_card("BEA", "driver", "#FFFFFF", 3.4, None)
    assert "background:#FFFFFF" in html and "color:#000000" in html
    assert "3.4" in html and "—" in html


def test_constructor_card_outlined_and_grey_fallback():
    html = cards.asset_card("MER", "constructor", "#27F4D2", 71.0, 12.0)
    assert "border:2px solid #27F4D2" in html and "background:#27F4D2" not in html
    assert "#5A5F66" in cards.asset_card("HIR", "driver", None, None, None)


def test_chip_badges_states():
    html = cards.chip_badges(["limitless", "wildcard", "x3_boost"], ["limitless", "x3_boost"], "x3_boost", None)
    assert '<span class="chip gone"><s>wildcard</s>' in html
    assert 'class="chip used">✓ x3_boost' in html
    assert '<span class="chip">limitless' in html


def test_chip_badges_played_now_wins_and_none_left():
    html = cards.chip_badges(["limitless", "wildcard"], [], "limitless", "wildcard")
    assert 'class="chip used">✓ wildcard' in html and "<s>limitless</s>" in html


def test_team_row_columns_and_no_chips():
    row = cards.team_row("1", ["MER", "FER"], "ANT", ["HUL", "BEA", "ALB", "CAM"], 112.7, ["bank 0.3", "2 FT"],
                         207.1, {a: f"<i>{a}</i>" for a in ["MER", "FER", "ANT", "HUL", "BEA", "ALB", "CAM"]})
    assert row.index("<i>MER</i>") < row.index("<i>ANT</i>") < row.index("<i>HUL</i>")
    assert "112.7" in row and "bank 0.3" in row and "207.1" in row and 'class="chips"' not in row


def test_swap_strip():
    assert "OUT HUL → IN BEA" in cards.swap_strip(["HUL"], ["BEA"])
    assert "No transfers" in cards.swap_strip([], [])


def test_header_row():
    assert "Chips" in cards.header_row() and "Chips" not in cards.header_row("#", chips=False)
