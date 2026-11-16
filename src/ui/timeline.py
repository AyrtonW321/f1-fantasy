"""Timeline data and Vega-Lite chart for a team's season points."""
import pandas as pd

from src.backtest.walkforward import _actual_points
from src.optimize.ilp import Decision
from src.sim.scoring import load_rules
from src.ui import logic


FRAME_COLUMNS = ["team", "season", "round", "points", "cumulative", "kind",
                 "transfers", "chip", "boost"]


def _transfer_text(out: list[str], incoming: list[str]) -> str:
    if not out and not incoming:
        return ""
    return f"OUT {', '.join(out)} → IN {', '.join(incoming)}"


def timeline_frame(numbers: list[int], tables=None) -> pd.DataFrame:
    """Build actual and expected point rows from the highest scored round to season end."""
    t = tables if tables is not None else logic._tables()
    season, _ = logic.next_round(t)
    points = t["fantasy_points"]
    scored = points.loc[points["season"] == season, "round"]
    if scored.empty:
        return pd.DataFrame(columns=FRAME_COLUMNS)
    start = int(scored.max())
    rounds = sorted(int(r) for r in t["races"].loc[
        (t["races"]["season"] == season) & (t["races"]["round"] >= start), "round"].unique())
    if not rounds:
        return pd.DataFrame(columns=FRAME_COLUMNS)

    rows = []
    for n in numbers:
        try:
            team = logic.load(n)
            mu = logic.asset_mu(season, start, t)
            drivers, constructors = tuple(team["drivers"]), tuple(team["constructors"])
            boost = max(drivers, key=lambda d: mu.get(d, float("-inf")))
            saved = Decision(drivers, constructors, boost, (), 0, 0.0, 0.0, 0.0)
            actual = _actual_points(season, start, saved, points, load_rules(season))

            history = logic.history_points(n, t)
            history = history[(history["season"] == season) & (history["round"] > start)]
            history = history.dropna(subset=["points"]).set_index("round")
            swaps = {(s["season"], s["round"]): s for s in logic.swaps_log(n)}

            state = logic.team_state(n, t)
            best = logic.top_teams(state, n=1, tables=t)
            choice = best[0] if best else None
            expected_transfer = ""
            if choice:
                owned = set((*team["drivers"], *team["constructors"]))
                chosen = set((*choice.drivers, *choice.constructors))
                expected_transfer = _transfer_text(sorted(owned - chosen), list(choice.transfers_in))

            team_rows = [{"team": f"Team {n}", "season": season, "round": start,
                          "points": actual, "kind": "actual", "transfers": "", "chip": "", "boost": boost}]
            for r in rounds:
                if r <= start:
                    continue
                if r in history.index:
                    h = history.loc[r]
                    sw = swaps.get((season, r), {})
                    transfers = _transfer_text(sw.get("out", []), sw.get("in", []))
                    team_rows.append({"team": f"Team {n}", "season": season, "round": r,
                                      "points": float(h["points"]), "kind": "actual", "transfers": transfers,
                                      "chip": str(h["chip"] or ""), "boost": boost})
                elif choice is not None:
                    team_rows.append({"team": f"Team {n}", "season": season, "round": r,
                                      "points": float(choice.expected_points), "kind": "expected",
                                      "transfers": expected_transfer if not any(x["kind"] == "expected" for x in team_rows) else "",
                                      "chip": "", "boost": choice.boost})
            rows.extend(team_rows)
        except (ValueError, FileNotFoundError, KeyError):
            continue

    frame = pd.DataFrame(rows, columns=FRAME_COLUMNS)
    if not frame.empty:
        frame = frame.sort_values(["team", "round"]).reset_index(drop=True)
        frame["cumulative"] = frame.groupby("team")["points"].cumsum()
    return frame


def timeline_spec(frame: pd.DataFrame) -> dict:
    """Return a dark-background Vega-Lite v5 cumulative points chart."""
    values = frame[FRAME_COLUMNS].where(pd.notna(frame[FRAME_COLUMNS]), None).to_dict("records") if not frame.empty else []
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "background": None,
        "data": {"values": values},
        "width": "container",
        "height": 300,
        "encoding": {
            "x": {"field": "round", "type": "ordinal", "sort": "ascending", "title": "Round"},
            "y": {"field": "cumulative", "type": "quantitative", "title": "Cumulative points"},
            "color": {"field": "team", "type": "nominal",
                      "scale": {"range": ["#55A7E8", "#C98CEB", "#F0C96A"]}},
            "strokeDash": {"field": "kind", "type": "nominal",
                           "scale": {"domain": ["actual", "expected"], "range": [[1, 0], [6, 4]]}},
            "tooltip": [
                {"field": "team", "type": "nominal", "title": "Team"},
                {"field": "round", "type": "ordinal", "title": "Round"},
                {"field": "points", "type": "quantitative", "title": "Points", "format": ".1f"},
                {"field": "cumulative", "type": "quantitative", "title": "Cumulative", "format": ".1f"},
                {"field": "kind", "type": "nominal", "title": "Type"},
                {"field": "transfers", "type": "nominal", "title": "Transfers"},
                {"field": "chip", "type": "nominal", "title": "Chip"},
                {"field": "boost", "type": "nominal", "title": "x2 driver"},
            ],
        },
        "mark": {"type": "line", "point": {"filled": True, "size": 60}},
        "config": {"view": {"stroke": None}, "axis": {"labelColor": "#F2F3F4", "titleColor": "#F2F3F4", "gridColor": "#30363D"},
                   "legend": {"labelColor": "#F2F3F4", "titleColor": "#F2F3F4"}},
    }
