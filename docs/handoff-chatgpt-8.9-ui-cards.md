# Handoff: Phase 8.9 Task 3 (HTML cards) for ChatGPT

Work **only** in the git worktree `C:\Users\ayrto_kuqm8yg\OneDrive\Documents\Coding\f1-fantasy-ui-cards` on branch `ui-cards`. Claude is editing `src/ui/logic.py` and `app.py` at the same time in the main folder, so never touch that folder or those two files. Commit on `ui-cards`. Do not merge, push or switch branches.

## Read first

- `CLAUDE.md` (project rules)
- `docs/superpowers/specs/2026-11-14-ui-redesign-design.md` (design)
- `docs/superpowers/plans/2026-11-15-ui-redesign.md`, **Task 3** (your task; follow its interfaces and tests exactly)
- `src/ui/style.py` (already merged: `text_color(hex_)`, `GREY`)
- `.streamlit/config.toml` (dark theme colours to match)
- If `graphify-out/graph.json` exists, run `graphify query "<question>"` before grepping or reading source files.

## Deliverable

Create `src/ui/cards.py` and `tests/test_ui_cards.py`:

- `CSS`
- `asset_card`
- `chip_badges`
- `team_row` (outer element `<div class="row">`)
- `swap_strip`

The exact signatures and test assertions are in plan Task 3. Rules:

- Pure functions that return HTML strings. No Streamlit import, no new dependency.
- Escape asset ids with `html.escape`.
- Driver card: filled with the team colour, text `text_color(color)`. Constructor card: `border:2px solid <color>`, dark fill, light text. `color=None` means `GREY`.
- The two lines under each card are price, then xPts, each shown as `—` when None.
- Chip badges:
  - `✓` for `played_now or selected`, class `chip used`
  - `<s>` for chips not in `chips_left`, class `chip gone`
  - plain `chip` for everything else
- Look: compact, like a team-calculator table on a dark background. Cards about 56px wide.

## Done when

- `uv run pytest -q` passes, at the same count as before plus the 6 new tests.
- Commit on `ui-cards` with message `feat: HTML cards, chip badges, team row`.
- Reply with the commit hash and any choices you made that the plan left open.
