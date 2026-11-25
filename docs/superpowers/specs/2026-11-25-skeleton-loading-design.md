# Skeleton loading (Phase 8.11) — short design

Date: 2026-11-25. Source: the user's "Skeleton Loading UI: Design Spec" (Nov 25, 2026), applied to the Streamlit app. Approved in chat.

## Why

A cold start is ~7 s of blank page and a "Solving teams..." spinner (tables 3.7 s, team solves 0.4-1.0 s each, Best Teams 1.0 s, Timeline 0.5 s). Skeletons show the layout at once; failures get a message and Retry instead of a traceback.

## Design

- **First screen:** header and tabs render normally. Before any slow work, `main()` puts a skeleton into an `st.empty()` slot per data area: each My Team row, Best Teams, Timeline. Then each slot is filled in turn. Only on the session's first run; later full reruns keep the old content (spec: never replace real content with grey).
- **Boxes:** one per real container, no fake text. My Team row: card box | select bar + 3x2 52 px squares | four expander bars, on the same 5:2:4 grid. Best Teams: 8 row boxes. Timeline: caption bar + 300 px chart box. Colour `#262B31` (60% divider `#30363D` over card `#171B20`), same radii as the real cards.
- **Motion:** opacity 1 to 0.45 and back, 1.6 s, ease-in-out, infinite; none under `prefers-reduced-motion: reduce`.
- **Refresh:** Streamlit's stale grey-out is turned off so old content stays at full opacity during reruns.
- **Errors:** each area catches exceptions (inside its fragment, so fragment reruns are covered too) and shows one `role="alert"` line "Couldn't load <thing>. Is the data built? Try Update." plus a primary Retry button. Retry reruns that fragment only. The traceback goes to the server log, not the page.
- **Accessibility:** skeleton wrapper `role="status" aria-busy="true" aria-label="Loading"`, boxes `aria-hidden="true"`.

## Not applicable in Streamlit

The 150 ms delay and load tickets: Streamlit stops stale runs itself, and fragment reruns keep the old content. The pre-script first frame: closest is the skeleton as the first output of the run. The 15 s timeout: loads are local.

## Approaches

- **Chosen:** `st.empty()` slots with skeleton HTML from `src/ui/cards.py`, filled in place. No dependency.
- `st.spinner` only: no layout, which the spec rules out.
- A custom component with JS: true first frame, but adds a build step. Rejected.

## Plan

1. `cards.py`: `SKELETON_CSS` (in `CSS`), `team_skeleton()`, `best_skeleton(rows=8)`, `timeline_skeleton()`, `load_error(thing)`. Tests in `tests/test_ui_cards.py`: busy wrapper, box counts, `aria-hidden`, reduced-motion rule, error has `role="alert"` and no exception text.
2. `app.py`: first-run skeleton slots in `main()`, try/except in `_team_row`, `_best_tab`, `_timeline_tab` with Retry, stale fade off in CSS.
3. Browser check: cold start shows skeletons, content replaces them, a forced failure shows the message and Retry works, reduced motion stops the pulse.
