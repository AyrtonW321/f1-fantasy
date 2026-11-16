# UI Layout and Timeline (Phase 8.10) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compact f1fantasytools-style team cards in three columns, square 3x2 chip tiles, nicer header and tabs, and a Timeline tab of cumulative points from round 20 to season end.

**Architecture:** Pure HTML/CSS helpers in `src/ui/cards.py`, timeline data and chart spec in new `src/ui/timeline.py`, layout only in `app.py`.

**Tech Stack:** Streamlit, pandas, Vega-Lite via `st.vega_lite_chart`, pytest.

**Spec:** `docs/superpowers/specs/2026-11-15-ui-layout-timeline-design.md`

## Global Constraints

- No new dependency. No game logic in `app.py`.
- Rules from `config/rules_{season}.yaml` only (`load_rules`).
- History file format (`HISTORY_COLS` in `src/ui/logic.py`) unchanged.
- ChatGPT works only in worktree `../f1-fantasy-timeline` (branch `timeline`); Claude in the main folder (branch `ui-layout`). Never the same files.

## Review Focus

1. Team with no history file: timeline still shows round 20 actual and expected rounds 21-23 (Task 1 test).
2. A logged round replaces the expected point for that round (Task 1 test with a temp history file).
3. Team file missing or `team_state` raises `ValueError`: timeline skips that team, others still render (Task 1 test).
4. Narrow window (<850 px): the three columns stack, chip grid stays 3x2 (Task 3 manual check).
5. Chip tile text fits a 52 px square for the longest chip name `no_negative` (Task 2 test: short labels).

---

### Task 1: Timeline data and chart (ChatGPT)

**Files:**
- Create: `src/ui/timeline.py`
- Test: `tests/test_ui_timeline.py`

**Interfaces:**
- Consumes: `src.ui.logic`: `load(n)`, `team_path(n)`, `history_points(n, tables)`, `team_state(n, tables)`, `top_teams(state, n=1, tables=tables)`, `next_round(tables)`, `asset_mu(season, round_, tables)`, `_tables()`; `src.backtest.walkforward._actual_points(season, round_, decision, points, rules)`; `src.optimize.ilp.Decision`; `src.sim.scoring.load_rules`.
- Produces:
  - `timeline_frame(numbers: list[int], tables=None) -> pd.DataFrame` with columns `team` (str, "Team N"), `season`, `round`, `points`, `cumulative`, `kind` ("actual" | "expected"), `transfers` (str, "OUT a, b → IN c, d" or ""), `chip` (str or ""), `boost` (str).
  - `timeline_spec(frame: pd.DataFrame) -> dict` (Vega-Lite v5).

Rows per team, season = `next_round(t)[0]`:
- Start round `s0` = highest round in `fantasy_points` for that season (20 now). Row from `load(n)` drivers/constructors, boost = driver with the highest `asset_mu(season, s0)`, points = `_actual_points`, kind actual, transfers "".
- Logged rounds `> s0` from `history_points(n)` with non-NaN points: kind actual, transfers and chip from history.
- Every remaining round of the season (`races` table) not covered above: kind expected, points = `top_teams(team_state(n), n=1)[0].expected_points`, transfers from that decision vs the team file on the first expected round, "" after.
- `cumulative` = cumsum of points per team, rounds ascending.
- Any `ValueError` / missing team file for one team: skip that team.

- [ ] **Step 1: Write failing tests**

```python
def test_spec_dashes_expected_and_has_tooltip():
    frame = pd.DataFrame({"team": ["Team 1"] * 2, "season": [2026] * 2, "round": [20, 21],
                          "points": [50.0, 60.0], "cumulative": [50.0, 110.0],
                          "kind": ["actual", "expected"], "transfers": ["", "OUT GAS → IN ALO"],
                          "chip": ["", ""], "boost": ["RUS", "RUS"]})
    spec = timeline_spec(frame)
    text = json.dumps(spec)
    assert "strokeDash" in text and "transfers" in text and "cumulative" in text
    assert spec["data"]["values"][1]["kind"] == "expected"

@pytest.mark.skipif(not PRICES.exists(), reason="real data not unpacked")
def test_frame_round20_then_expected(tmp_path, monkeypatch):
    monkeypatch.setattr(logic, "history_path", lambda n: tmp_path / f"team_{n}.csv")  # no history
    f = timeline_frame([1])
    assert f["round"].tolist() == [20, 21, 22, 23]
    assert f["kind"].tolist() == ["actual", "expected", "expected", "expected"]
    assert f["cumulative"].tolist() == pytest.approx(f["points"].cumsum().tolist())

@pytest.mark.skipif(not PRICES.exists(), reason="real data not unpacked")
def test_missing_team_is_skipped():
    assert set(timeline_frame([1, 9])["team"]) == {"Team 1"}
```

Plus one test that writes a history row for round 21 into `tmp_path` and has `fantasy_points` covering round 21 (use a copy of tables with round-20 rows relabelled 21) and asserts the round-21 row is `kind == "actual"`.

- [ ] **Step 2:** `uv run pytest tests/test_ui_timeline.py -q` fails (module missing).
- [ ] **Step 3:** Implement. Spec: x round (ordinal), y cumulative, color team (three colours, none red `#E10600` or green `#2EB86A`), line `strokeDash` by kind, filled points, tooltip team, round, points, cumulative, kind, transfers, chip, boost. Dark-theme friendly (no white background: `"background": null`).
- [ ] **Step 4:** `uv run pytest -q` passes.
- [ ] **Step 5:** Commit on `timeline`: `feat: timeline frame and chart`.

### Task 2: Card and chip CSS (Claude)

**Files:** Modify `src/ui/cards.py`; Test `tests/test_ui_cards.py`.

**Interfaces:** Produces `team_card(constructors, x2, drivers, cost, money_lines, xpts, cards) -> str` (box layout like the reference: CR column, x2 column, 2x2 driver grid, boxed cost and xPts cells), `chip_grid(all_chips, chips_left, selected, played_now) -> str` (class `chip-grid`, 3 columns, square tiles, short labels X3 LL WC NN AP FF), `HEADER` HTML. `chip_badges` and `team_row` stay for Best Teams.

- [ ] Test: `chip_grid` has 6 `chip-tile` spans, `used`/`gone` classes as `chip_badges`, labels `X3` and `NN`.
- [ ] Test: `team_card` contains every asset id and the x2 id once.
- [ ] Implement CSS: `.chip-grid{display:grid;grid-template-columns:repeat(3,52px);gap:6px}`, tiles 52x52 rounded; tab CSS on `[data-baseweb="tab"]` (hover colour fade, underline transition, active pill).
- [ ] `uv run pytest -q` passes; commit `feat: team card, chip grid, header CSS`.

### Task 3: My Team layout and header (Claude)

**Files:** Modify `app.py`.

- [ ] Replace `st.title` with `st.html(HEADER)`; tabs `["My Team", "Best Teams", "Timeline", "Update"]`.
- [ ] `_team_row`: `left, mid, right = st.columns([5, 2, 4])`; card + swap strip + caption left; `chip_grid` + chip select middle; four expanders right. Past swaps keeps text log only.
- [ ] Browser check on real data at desktop and 375 px width; AppTest smoke run has no exception.
- [ ] Commit `feat: three-column team layout, header, tabs`.

### Task 4: Timeline tab (Claude, after merging `timeline`)

- [ ] Merge `timeline` into `ui-layout`; Timeline tab calls `timeline_frame(numbers)` then `st.vega_lite_chart(timeline_spec(frame), width="stretch")`, `st.info` when empty. Remove `_timeline` from `app.py`.
- [ ] Browser check: three lines, dashed after round 20, hover shows transfers.
- [ ] `uv run pytest -q`, `graphify update .`, progress/decisions docs, commit.
