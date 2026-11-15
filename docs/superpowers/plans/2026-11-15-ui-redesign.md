# UI Redesign Implementation Plan (Phase 8.9)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the per-team tabs with a My Team | Best Teams | Update layout of team-coloured asset cards, chip badges and swap strips.

**Architecture:** Pure helpers (colours, contrast, per-asset xPts, swaps log, chip state) go in `src/ui/style.py` and `src/ui/logic.py`. HTML building goes in `src/ui/cards.py`, which returns strings and is tested without Streamlit. `app.py` only lays out tabs and widgets and calls `st.html` with those strings.

**Tech Stack:** Python 3.14, Streamlit 1.67 (`st.html`, `st.popover`, `st.expander`, `st.fragment`), pandas, pytest, uv.

**Spec:** `docs/superpowers/specs/2026-11-14-ui-redesign-design.md`

## Global Constraints

- No new dependency. Everything here uses Streamlit, pandas, PyYAML and the stdlib.
- Game numbers (boost multiplier, x3 multiplier, chip list) come from `load_rules(season)`, never literals in code.
- Never read TracingInsights `priceChange`. No xΔ$ column.
- Work on branch `ui-redesign` in `C:\Users\ayrto_kuqm8yg\OneDrive\Documents\Coding\f1-fantasy`. Commit per task. Do not push.
- Before exploring code, run `graphify query "<question>"`. After code changes, run `graphify update .`.
- Keep every current function: chip advice, recompute chips, alternatives with "Use this one", "I made these transfers", edit form, stale-team warning, update log, and the missing-file and missing-data warnings.
- Run tests with `uv run pytest -q`. Baseline: 219 passed, 8 skipped.

## Review Focus

1. Missing price or mu for an owned asset (benched HIR, or a round with no prices yet): the card shows "—" and nothing crashes. Test in Task 3.
2. A driver with no `results.parquet` row (HIR, or a new 2027 driver) gets a grey card with readable text. Test in Task 1.
3. The first logged history row has no previous lineup, so its swap entry shows only INs. Test in Task 2.
4. Chip advice is missing, or says `none` for the next round, so the selector defaults to "None". Test in Task 2.
5. A team with no chips left, or with a chip played this round, shows correct badges and locks the selector. Test in Task 2 (state) and Task 3 (render).

---

### Task 1: Team colours and contrast

**Files:**
- Create: `config/team_colors.yaml`
- Create: `src/ui/style.py`
- Test: `tests/test_ui_style.py`

**Interfaces:**
- Produces:
  - `team_colors() -> dict[str, dict]`: constructor asset id to `{"color": "#RRGGBB", "results_id": str}`.
  - `text_color(hex_: str) -> str`: returns `"#000000"` or `"#FFFFFF"`.
  - `driver_teams(results: pd.DataFrame, season: int) -> dict[str, str]`: driver code to constructor asset id, from each driver's latest row with `season <= season`. Drivers not found are left out.
  - `GREY = "#5A5F66"`.

- [ ] **Step 1: Write `config/team_colors.yaml`.** These starting values are the builder's call, and the user may edit them:

```yaml
# constructor asset id -> livery colour and the id results.parquet uses
MER: {color: "#27F4D2", results_id: mercedes}
FER: {color: "#E80020", results_id: ferrari}
MCL: {color: "#FF8000", results_id: mclaren}
RED: {color: "#3671C6", results_id: red_bull}
AST: {color: "#229971", results_id: aston_martin}
ALP: {color: "#0093CC", results_id: alpine}
WIL: {color: "#1868DB", results_id: williams}
HAA: {color: "#FFFFFF", results_id: haas}
VRB: {color: "#6692FF", results_id: rb}
AUD: {color: "#F50537", results_id: audi}
CAD: {color: "#1E1E1E", results_id: cadillac}
```

- [ ] **Step 2: Write the failing tests**

```python
def test_text_color_contrast():
    assert style.text_color("#FFFFFF") == "#000000"   # Haas white
    assert style.text_color("#1E1E1E") == "#FFFFFF"   # dark
    assert style.text_color("#27F4D2") == "#000000"   # Mercedes teal
    assert style.text_color("#3671C6") == "#FFFFFF"   # Red Bull blue
    assert style.text_color(style.GREY) == "#FFFFFF"

def test_team_colors_cover_every_2026_constructor(tables):  # reuse fixture pattern from test_ui_logic
    ids = set(tables["prices"].query("season == 2026 and kind == 'constructor'")["asset_id"])
    assert ids <= set(style.team_colors())

def test_driver_teams_latest_row_and_missing():
    results = pd.DataFrame({"season": [2026, 2026, 2026], "round": [1, 2, 2],
                            "driver_code": ["BEA", "BEA", "OCO"], "constructor_id": ["ferrari", "haas", "haas"]})
    assert style.driver_teams(results, 2026) == {"BEA": "HAA", "OCO": "HAA"}
    assert "HIR" not in style.driver_teams(results, 2026)
```

If the real-data `tables` fixture is skipped when data is absent, mark `test_team_colors_cover_every_2026_constructor` the same way as the existing real-data tests.

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_ui_style.py -q`. Expected: fail with `ModuleNotFoundError: src.ui.style`.

- [ ] **Step 4: Implement `src/ui/style.py`.** `text_color` uses WCAG relative luminance (sRGB linearised) and returns white when luminance is below 0.4, else black. `driver_teams` sorts by season and round, keeps the last row per driver, and maps `constructor_id` through the inverse of `results_id`.

- [ ] **Step 5: Run tests to verify they pass.** Run `uv run pytest tests/test_ui_style.py -q`.

- [ ] **Step 6: Commit** with `git add config/team_colors.yaml src/ui/style.py tests/test_ui_style.py`, message `feat: team colours and contrast helper`.

---

### Task 2: Row data helpers in logic

**Files:**
- Modify: `src/ui/logic.py` (add functions after `history_points`)
- Test: `tests/test_ui_logic.py`

**Interfaces:**
- Consumes: the existing `assets(season, round_, exclude, tables)`, `load_rules`, `history_path`, `next_round`, `_tables`.
- Produces:
  - `asset_mu(season: int, round_: int, tables=None) -> dict[str, float]`: asset id to mu, with no exclusions.
  - `saved_xpts(team: dict, mu: dict[str, float], rules: dict, chip: str | None) -> tuple[float | None, str | None]`: returns `(xpts, x2_driver)`.
    - The x2 driver is the highest-mu driver.
    - xpts = the sum of the 7 assets' mu plus `(boost_multiplier - 1) * top1`.
    - With `chip == "x3_boost"`: top1 counts at `extra_multiplier` and top2 gets the normal boost.
    - If any asset is missing from `mu`, it returns `(None, highest-mu known driver or None)`.
  - `swaps_log(n: int) -> list[dict]`: one dict per logged row, sorted, with keys `season, round, out, in, chip`.
    - `out` and `in` are lists of asset ids, computed as differences between this row's drivers+constructors and the previous row's.
    - The first row has `out=[]` and `in=transfers_in` split on `|`.
    - An empty list is returned when no history file exists.
  - `round_chip(n: int, season: int, round_: int) -> str | None`: the chip logged for that round, or None (also None for an empty string).
  - `advised_chip(advice: str | None, round_: int) -> str | None`: parses the line `Round {round_}: <chip>;`. Returns None when advice is None, the line is missing, or the chip is `none`.

- [ ] **Step 1: Write the failing tests**

```python
def test_saved_xpts_boost_and_x3():
    rules = {"team": {"boost_multiplier": 2}, "chips": {"x3_boost": {"extra_multiplier": 3}}}
    team = {"drivers": ["A", "B", "C", "D", "E"], "constructors": ["X", "Y"]}
    mu = {"A": 10, "B": 8, "C": 1, "D": 1, "E": 1, "X": 5, "Y": 5}
    assert logic.saved_xpts(team, mu, rules, None) == (41.0, "A")       # 31 + 10
    assert logic.saved_xpts(team, mu, rules, "x3_boost") == (59.0, "A")  # 31 + 2*10 + 8
    assert logic.saved_xpts(team, {k: v for k, v in mu.items() if k != "C"}, rules, None) == (None, "A")

def test_swaps_log_diffs_rows(cfg):
    # write config/history/team_1.csv with two rows in the apply_transfers column layout:
    # R21 drivers A|B|C|D|E constructors X|Y transfers_in A ; R22 drivers A|B|C|D|F constructors X|Z
    log = logic.swaps_log(1)
    assert log[0]["out"] == [] and log[0]["in"] == ["A"]
    assert sorted(log[1]["out"]) == ["E", "Y"] and sorted(log[1]["in"]) == ["F", "Z"]

def test_swaps_log_no_file(cfg):
    assert logic.swaps_log(9) == []

def test_round_chip(cfg):
    # same history file; R22 row has chip "wildcard"
    assert logic.round_chip(1, 2026, 22) == "wildcard"
    assert logic.round_chip(1, 2026, 21) is None
    assert logic.round_chip(1, 2026, 23) is None

def test_advised_chip():
    text = "Round 21: no_negative; expected gain 11.8; ...\nRound 22: none; expected gain 0.0"
    assert logic.advised_chip(text, 21) == "no_negative"
    assert logic.advised_chip(text, 22) is None
    assert logic.advised_chip(text, 23) is None
    assert logic.advised_chip(None, 21) is None
```

The history CSV columns are exactly the keys `apply_transfers` passes to `_log`: `season, round, drivers, constructors, boost, boost3, chip, transfers_in, penalty_transfers, bank, team_value`.

- [ ] **Step 2: Run the new tests to verify they fail.** Run `uv run pytest tests/test_ui_logic.py -q -k "saved_xpts or swaps_log or round_chip or advised_chip"`. Expected: `AttributeError`.

- [ ] **Step 3: Implement the five functions** in `src/ui/logic.py` using the interfaces above. `asset_mu` is `{a.id: a.mu for a in assets(season, round_, (), tables)}`. Read the multipliers with the existing `_rule(rules, "team.boost_multiplier")` and `_rule(rules, "chips.x3_boost.extra_multiplier")`.

- [ ] **Step 4: Run the full suite.** Run `uv run pytest -q`. Expected: 219 + 5 new tests passed, 8 skipped.

- [ ] **Step 5: Commit** with `git add src/ui/logic.py tests/test_ui_logic.py`, message `feat: row helpers for saved xPts, swaps log, chip state`.

---

### Task 3: Card and row HTML

**Files:**
- Create: `src/ui/cards.py`
- Test: `tests/test_ui_cards.py`

**Interfaces:**
- Consumes: `style.text_color`, `style.GREY`.
- Produces:
  - `CSS: str`, a single `<style>` block covering the row grid, cards, badges and the swap strip.
  - `asset_card(asset_id: str, kind: str, color: str | None, price: float | None, xpts: float | None) -> str`.
    - A driver card is filled with `color`, and its text uses `text_color(color)`.
    - A constructor card has a 2px border in `color`, a neutral dark fill and light text.
    - `color=None` means `GREY`.
    - The card holds two sub-lines, price (`12.3`) and xPts (`8.4`), each `—` when None.
  - `chip_badges(all_chips: list[str], chips_left: list[str], selected: str | None, played_now: str | None) -> str`.
    - The checked chip is `played_now or selected` and gets `class="chip used"` plus a `✓` prefix.
    - Any other chip not in `chips_left` gets `class="chip gone"` and is struck through with `<s>`.
    - Everything else gets `class="chip"`.
  - `team_row(label: str, constructors: list[str], x2: str | None, drivers: list[str], cost: float | None, money_lines: list[str], xpts: float | None, cards: dict[str, str], chips_html: str = "") -> str`.
    - `cards` maps asset id to its `asset_card` HTML.
    - Grid columns: `label | CR | x2 | DR (2x2) | $ (cost, then money_lines) | xPts | chips`.
    - The chips column is omitted when `chips_html == ""`.
    - The outer element is `<div class="row">`, which the Task 4 headless check counts.
  - `swap_strip(out: list[str], in_: list[str]) -> str`. Renders `OUT A, B → IN C, D`, or `No transfers` when both lists are empty.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail.** Run `uv run pytest tests/test_ui_cards.py -q`. Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `src/ui/cards.py`.** Use f-strings, and escape asset ids with `html.escape`. Card size, radius and font size are the builder's choice. Aim for the reference's compact look: cards about 56px wide, a monospace-ish number line, and colours from the dark theme in `.streamlit/config.toml`.

- [ ] **Step 4: Run tests to verify they pass.** Run `uv run pytest tests/test_ui_cards.py -q`.

- [ ] **Step 5: Commit** with `git add src/ui/cards.py tests/test_ui_cards.py`, message `feat: HTML cards, chip badges, team row`.

---

### Task 4: New app layout

**Files:**
- Modify: `app.py` (`_top`, `_team_tab`, `_picks`, `_choose_and_apply`, `_best_tab`, `_data_tab`, `main`, `_timeline`)

**Interfaces:**
- Consumes: Tasks 1-3, plus the existing `_cached_top`, `_report_chip_advice`, `_capture_chips`, `_edit_form`, `_prices`, `_round_info`.
- Produces: no new public names. Private helpers are listed below.

- [ ] **Step 1: Add the `n` parameter to the solve cache.** Change `_top(..., n, stamp)` and `_cached_top(state, budget=100.0, exclude=(), chip=None, n=5)` to pass `n` through to `top_teams`.

- [ ] **Step 2: Add the shared data helpers.**
  - `_row_cards(asset_ids, kinds, season, round_) -> dict[str, str]` builds `asset_card` for each id.
    - Colour: from `team_colors()` for a constructor, or via `driver_teams(_table("results"), season)` then `team_colors()` for a driver.
    - Price: from `_prices`.
    - xPts: from `_cached_mu(season, round_, stamp)`, which wraps `asset_mu` in `@st.cache_data`.
  - Inject `cards.CSS` once per page with `st.html` in `main`.

- [ ] **Step 3: Replace `_team_tab` with the `@st.fragment` function `_team_row(n, next_round, races)`.**
  1. Missing team file: show the existing warning and return.
  2. Chip selector (`st.selectbox`, key `chip_{n}`):
     - Options are `["None", *chips_left]`.
     - The default index comes from `advised_chip(_report_chip_advice(n)[0], round_)`.
     - When `round_chip(n, season, round_)` is set, the selector is disabled and shows that chip.
  3. Header row: `st.html(team_row(f"Team {n}", ...))`.
     - It uses the saved team, with x2 and xpts from `saved_xpts(team, mu, rules, chip)`.
     - `money_lines` are `[f"bank {bank:.1f}", f"{free_transfers} FT"]`.
     - `chips_html` is `chip_badges(list(rules["chips"]), chips_left, chip, played_now)`.
  4. Stale-team warning, kept as today.
  5. `st.html(swap_strip(out, in_))`, built from the selected choice: out = owned assets not in the choice, in = `choice.transfers_in`.
  6. `st.expander("Alternatives")`: the existing table and "Use this one" buttons, then the selected summary and "I made these transfers". Keep the bodies of `_picks` and `_choose_and_apply`. `_picks` loses its own selectbox because the selector moved to item 2.
  7. `st.expander("Chip advice")`: the existing `_chip_advice(n)`.
  8. `st.expander("Edit team")`: the existing `_edit_form(n, team, prices)`.
  9. `st.expander("Past swaps")`: one line per `swaps_log(n)` entry, as `R{round}: OUT … → IN …` plus the chip if any, followed by the existing `_timeline(n)` chart. Drop `lineup` from the chart tooltip.

- [ ] **Step 4: Rewrite `_best_tab`.**
  - A `st.popover("Filters")` holds the existing budget and exclude widgets with unchanged defaults and keys.
  - `best = _cached_top(None, budget, exclude=exclude, n=10)`.
  - Each decision renders as `team_row(str(i + 1), d.constructors, d.boost, [x for x in d.drivers if x != d.boost], d.cost, [], d.expected_points, cards)` with no chips.
  - The existing empty and `ValueError` messages stay.

- [ ] **Step 5: Make `_data_tab` the Update tab.**
  - Next round, lock time, latest price round and unsealed files become four `st.metric` tiles in `st.columns(4)`.
  - The Update button and its log streaming stay unchanged.

- [ ] **Step 6: Update `main`.**
  - Tabs are `st.tabs(["My Team", "Best Teams", "Update"])`.
  - My Team loops over the team files, calling `_team_row(n, …)` with an `st.divider()` between teams.
  - The `update_output` banner stays.

- [ ] **Step 7: Run a headless check on real data.** Run this in the scratchpad:

```python
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py", default_timeout=120).run()
assert not at.exception
assert [t.label for t in at.tabs] == ["My Team", "Best Teams", "Update"]
html = "".join(h.proto.body for h in at.get("html"))
assert html.count('class="row') >= 3 + 10
```

Expected: no assertion error.

- [ ] **Step 8: Run the full suite.** Run `uv run pytest -q`. Expected: all pass, with 8 skipped.

- [ ] **Step 9: Do a visual check.**
  1. Run `uv run streamlit run app.py --server.headless true` in the background.
  2. Open it in the browser pane and screenshot the My Team and Best Teams tabs.
  3. Confirm that Haas, Williams and Red Bull cards are readable and that chip badges show all three states where they apply.
  4. Send the screenshots to the user.

- [ ] **Step 10: Commit** with `git add app.py`, message `feat: My Team / Best Teams / Update layout with team cards`.

---

### Task 5: Wrap-up

- [ ] Use `superpowers:verification-before-completion`. Re-run `uv run pytest -q`, then rerun the headless check from Task 4, Step 7.
- [ ] Time a cached rerun: run `AppTest` twice and time the second `.run()`. Expected: under 0.5 s on My Team. If it's slower, record it in `docs/known-issues.md`.
- [ ] Update `docs/progress.md` with a dated line. Add to `docs/decisions.md`: "UI stays Streamlit with HTML cards (no frontend rewrite); team colours in config/team_colors.yaml; no xΔ$ (no price forecast)."
- [ ] Run `graphify update .`, then commit the docs and graph with message `docs: UI redesign progress`.
- [ ] Ask the user before merging to main or pushing.
