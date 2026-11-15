# UI redesign (Phase 8.9)

Date: 2026-11-14. Branch: `ui-redesign`. Status: approved in conversation, awaiting doc approval.

## Intent

The app works but reads as a stack of default Streamlit tables, and the weekly action (what to change for each team) is buried among setup controls. Goal: one glance shows all three teams, their recommended swaps, prices, expected points and chip state, in a look close to the reference team-calculator screenshot (team-coloured asset cards).

## Goals

- Tabs: **My Team | Best Teams | Update** (no per-team tabs).
- My Team: all teams (one per `config/my_team_[0-9].yaml`) stacked as rows.
- Team-coloured asset cards; price and xPts under every card.
- Chip badges per team: crossed out (played earlier), checkmarked (this weekend), plain (left).
- Each weekend's swaps visible: this weekend's recommendation plus a past-swaps log.
- Looks professional: consistent spacing, alignment, readable contrast.

## Non-goals

- No price-change forecast (the reference's xΔ$ column is dropped; model has none, by earlier decision).
- No change to scoring, optimizer or prediction logic.
- No new frontend stack, no new dependency.

## Anti-goals

- Text unreadable on a team colour (white on Haas white, black on Red Bull navy).
- Losing any current function: chip advice, recompute chips, alternatives, apply transfers, edit form, stale-team warning, update log, missing-file and missing-data warnings.
- Slower than today (cached rerun ~0.2 s).

## Approaches

| Approach | Trade-off | Picked |
|---|---|---|
| A. Streamlit + custom HTML/CSS cards (`st.html`), native widgets for actions | No rewrite, no new deps; cards themselves not clickable, so actions sit beside them | **Yes** (user) |
| B. New React frontend + small Python API | Full control of look and interaction; rewrite, new deps, two processes | No |

## Decisions (user)

1. **Tabs**: My Team | Best Teams | Update. Update = today's Data tab restyled as metric tiles (next round, lock time, latest price round, unsealed files) plus the Update button and log.
2. **My Team row** shows the team **as currently saved** (not the recommendation). Columns:
   `Team | CR | x2 | DR | $ | xPts | Chips`
   - CR: 2 constructor cards. x2: the boosted driver card in its own column. DR: the other 4 driver cards (2x2 grid like the reference).
   - $: team cost; bank and free transfers on lines under it.
   - xPts: expected points this weekend for the saved team (boost and chip applied, transfer penalty if any).
   - Chips: badge per chip in the season's rules.
3. **Cards**: constructor = outlined in team colour; driver = whole container filled with team colour. Text black or white by background luminance. Under each card: price, then xPts.
4. **Swaps**: under each row, a strip `OUT HUL → IN BEA` for this weekend's selected recommendation, plus a collapsed per-weekend log of past swaps (`R21: HUL → BEA`), derived by diffing consecutive lineups in `config/history/team_{n}.csv`. The log replaces the lineup column of today's season timeline (points/cumulative/value stay).
5. **Chips**:
   - Crossed out: not in `chips_left` and not this round's logged chip (played earlier).
   - Checkmark: the chip picked for this weekend. Per-team selector defaults to the chip advice's recommendation; the swap strip follows the selected chip's lineup. Once "I made these transfers" is applied, the logged chip for the round stays checked and the selector locks until the round completes.
   - Plain: still available, not selected.
6. **Expanders under each row**: swap strip (visible, not collapsed), alternatives (top 5 for the selected chip) with "Use this one" and "I made these transfers", chip advice + recompute, edit form, past-swaps log / timeline.
7. **Best Teams**: same row component, top **10**, no chips column. Budget and exclude in a **Filters** `st.popover`, same defaults as today (budget 100, union of team `exclude` lists).

## Builder calls (Claude, correctable)

- **Colours**: new `config/team_colors.yaml`, keyed by constructor asset id (`MER`, `FER`, ...), each with `color` (2026 livery hex) and `results_id` (`mercedes`, `ferrari`, ...) because `results.parquet` uses different ids than `prices.parquet`. Not game rules, so config is fine.
- **Driver → team**: driver's constructor in their latest `results.parquet` row (season ≤ next round). No result (e.g. HIR) → neutral grey.
- **Text colour**: WCAG relative luminance; white if luminance < 0.4 else black. One small assert-based check covers a dark, a light and a mid colour.
- **Per-asset xPts**: `mu` from `logic.assets(season, round_)` (already computed for the solve; cache it the same way as `_cached_top`).
- **Row xPts for the saved team**: sum of the 7 cards' mu plus the x2 boost on the highest-mu driver (that driver goes in the x2 column), x3 on `boost3` when x3_boost is the checked chip. No transfers, so no penalty. Builder checks this matches the optimizer's objective for a zero-transfer team.
- **"Locked" chip state** needs this round's logged chip: read the latest history row for (season, next round).
- **Rendering**: one `_row_html(...)` function returning a string, styles in one `<style>` block injected once. Widgets per row use `st.columns` / `st.expander` under the HTML.
- **Missing data**: rows still render with "—" for missing price/xPts; existing warnings kept.

## Left to the builder

Exact CSS (sizes, radii, fonts), badge labels/abbreviations, expander titles, column widths, mobile behaviour (not a goal; must not crash).

## Acceptance

- Headless run on real data: all three tabs render; three team rows; Best Teams shows 10 rows; Filters change results.
- Contrast check passes; Haas, Williams, Red Bull cards readable by eye in a screenshot.
- Every function in the anti-goal list still works (headless: apply transfers on a data copy, edit/save, update refresh).
- Full test suite passes; cached rerun stays under ~0.5 s.
