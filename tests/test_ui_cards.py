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


CHIPS = ["limitless", "wildcard", "x3_boost", "no_negative", "autopilot", "final_fix"]


def test_chip_grid_tiles_and_states():
    html = cards.chip_grid(CHIPS, ["limitless", "x3_boost", "no_negative"], "x3_boost", None)
    assert html.count('class="chip-tile') == 6 and 'class="chip-grid"' in html
    assert 'chip-tile used' in html and html.count("chip-tile gone") == 3
    assert ">X3<" in html and ">NN<" in html and 'title="no_negative"' in html


def test_team_card_has_every_asset_once():
    ids = ["MER", "FER", "ANT", "HUL", "BEA", "ALB", "CAM"]
    card = cards.team_card(["MER", "FER"], "ANT", ["HUL", "BEA", "ALB", "CAM"], 112.7, ["bank 0.3", "2 FT"],
                           207.1, {a: f"<i>{a}</i>" for a in ids})
    assert all(card.count(f"<i>{a}</i>") == 1 for a in ids)
    assert "112.7" in card and "207.1" in card and "2 FT" in card


def test_skeletons_are_busy_and_hidden_boxes():
    team = cards.team_skeleton()
    assert 'aria-busy="true"' in team and 'role="status"' in team
    assert team.count('class="sk sk-chip"') == 6 and team.count('class="sk sk-bar"') == 4
    assert cards.best_skeleton().count('class="sk sk-row"') == 8
    assert 'class="sk sk-chart"' in cards.timeline_skeleton()
    assert all('aria-hidden="true"' in s for s in (team, cards.best_skeleton(), cards.timeline_skeleton()))
    assert "prefers-reduced-motion" in cards.CSS and "1.6s" in cards.CSS


def test_load_error_is_alert_without_details():
    html = cards.load_error("Team 1")
    assert "role='alert'" in html and "Couldn't load Team 1." in html
