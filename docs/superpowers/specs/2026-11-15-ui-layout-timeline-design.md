# UI layout and Timeline tab (Phase 8.10) — short design

Date: 2026-11-15. Builds on 2026-11-14-ui-redesign-design.md (Phase 8.9).

## Why

The user wants the My Team view to read like f1fantasytools.com's Best Teams panel: compact boxed team cards, not rows stretched across the page. Also a cleaner header, livelier tabs, and a view of how each team's points build up over the rest of the season.

## Goals

1. **My Team row, three columns per team** (all 3 team files):
   - Left (~45%): team card in the f1fantasytools style. Constructor boxes outlined in team colour, driver boxes filled with it (current luminance rule for text). Under each box a small dark grid with price and xPts. Team cost and total xPts in boxed cells beside the assets, x2 driver in its own column.
   - Middle: chips as square tiles (~52 px), 3x2 grid, same colours as now (grey struck = played, green ✓ = this weekend, white = left). Chip select control stays under the grid.
   - Right: Alternatives, Chip advice, Edit team, Past swaps expanders, collapsed by default. Swap strip stays under the card.
2. **Header**: title moved to the top-left, small red accent mark, smaller than `st.title`.
3. **Tabs**: My Team · Best Teams · Timeline · Update. CSS-only hover (colour fade, sliding underline) and a pill for the active tab.
4. **Timeline tab**: one line per team, cumulative points.
   - Season 2026 starts at round 20: the team in `my_team_N.yaml` scored with its real round-20 points (`_actual_points`).
   - Rounds 21-23: logged rounds use real points (from `history_points`); unlogged future rounds use the team's expected points for the current best pick, dashed line. Rounds after the next one repeat that pick (the optimizer plans one round at a time).
   - Hover: round, points, cumulative, transfers OUT → IN, chip, x2 driver, and whether it is actual or expected.
   - Past swaps expander keeps the text log; the per-team chart moves to the Timeline tab.

## Non-goals

No back-fill of rounds 1-19. No price-change forecast. No new dependency. No change to optimizer, scoring or rules files.

## Anti-goals

Game logic in `app.py`. Data after a round's lock used for that round's expected points. Breaking `apply_transfers` / history file format.

## Approaches

- **Chosen: Streamlit + `st.html` cards + CSS + `st.vega_lite_chart`.** Reuses `cards.py`, existing chart code, no build step.
- Custom React component: full control of hover, but adds a JS build and a dependency. Rejected.
- Plotly chart: nicer hover out of the box, but a new dependency for one chart. Rejected.

## Split

- **ChatGPT** (worktree `../f1-fantasy-timeline`, branch `timeline`): new `src/ui/timeline.py` with `timeline_frame(numbers, tables=None) -> DataFrame` (columns: team, season, round, points, cumulative, kind ∈ {actual, expected}, transfers, chip, boost) and `timeline_spec(frame) -> dict` (Vega-Lite), plus `tests/test_ui_timeline.py`. Touches no other file.
- **Claude** (main checkout, branch `ui-layout`): `cards.py` CSS/markup, `app.py` layout, header, tabs; wires the Timeline tab to `timeline.py` after merge.

## Left to the builder

Exact pixel sizes, colours of the three team lines (must differ from red/green chip colours), tooltip wording.
