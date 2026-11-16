"""Local Streamlit dashboard for the F1 Fantasy teams and weekly update."""
import contextlib
import io
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pipelines.weekly_update import stale_warning, unsealed
from src.optimize.ilp import TeamState
from src.sim.scoring import load_rules
from src.ui.cards import CSS, HEADER, asset_card, chip_grid, header_row, swap_strip, team_card, team_row
from src.ui.logic import (advised_chip, apply_transfers, asset_mu, history_points, load, next_round,
                          round_chip, save_team, saved_xpts, swaps_log, team_path, team_state, top_teams,
                          validate)
from src.ui.style import driver_teams, team_colors


def _inputs_stamp():
    """Modified times of everything top_teams reads besides its arguments: data, model and rules files."""
    files = [*(ROOT / "data" / "processed").glob("*.parquet"), ROOT / "config" / "model.yaml",
             *(ROOT / "config").glob("rules_*.yaml")]
    return tuple(sorted((p.name, p.stat().st_mtime_ns) for p in files if p.exists()))


@st.cache_data(show_spinner="Solving teams...", max_entries=64)
def _top(owned, bank, free, budget, exclude, chip, n, stamp):
    """Cached top_teams: each ILP solve costs ~0.2 s, so only re-solve when the team, chip or input files change."""
    state = TeamState(dict(owned), bank, free) if owned is not None else None
    return top_teams(state, budget, n=n, exclude=list(exclude), chip=chip)


def _cached_top(state, budget=100.0, exclude=(), chip=None, n=5):
    owned = tuple(sorted(state.owned.items())) if state is not None else None
    bank, free = (state.bank, state.free_transfers) if state is not None else (None, None)
    return _top(owned, bank, free, budget, tuple(exclude), chip, n, _inputs_stamp())


@st.cache_data(show_spinner=False)
def _mu(season, round_, stamp):
    return asset_mu(season, round_)


def _cards(ids, season, round_):
    """asset_card HTML per id: team colour, current price and this round's xPts."""
    prices = _prices(season, round_)
    kinds = dict(zip(prices["asset_id"], prices["kind"])) if not prices.empty else {}
    price = dict(zip(prices["asset_id"], prices["price"])) if not prices.empty else {}
    try:
        mu = _mu(season, round_, _inputs_stamp()) if round_ is not None else {}
    except ValueError:
        mu = {}
    colors = team_colors()
    results = _table("results")
    teams = driver_teams(results, season) if not results.empty else {}
    out = {}
    for a in ids:
        kind = kinds.get(a, "constructor" if a in colors else "driver")
        team = a if kind == "constructor" else teams.get(a)
        color = colors.get(team, {}).get("color")
        out[a] = asset_card(a, kind, color, price.get(a), mu.get(a))
    return out


@st.cache_data
def _table(name):
    path = ROOT / "data" / "processed" / f"{name}.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def _round_info():
    races = _table("races")
    if races.empty:
        return None, races, "processed race schedule is unavailable"
    try:
        return next_round({"races": races}), races, None
    except ValueError as exc:
        return None, races, str(exc)


def _prices(season, round_):
    prices = _table("prices")
    if prices.empty:
        return prices
    options = prices.loc[prices["season"] == season]
    if round_ is not None and (options["round"] == round_).any():
        options = options.loc[options["round"] == round_]
    elif not options.empty:
        options = options.loc[options["round"] == options["round"].max()]
    return options.drop_duplicates(["asset_id", "kind"], keep="last")


def _report_chip_advice(n):
    files = sorted((ROOT / "reports").glob("round_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    heading = re.compile(rf"^### team {n} chips\s*\n\s*```text\s*\n(.*?)\n```", re.I | re.M | re.S)
    for path in files:
        match = heading.search(path.read_text(encoding="utf-8"))
        if match:
            return match.group(1), path.name
    return None, None


def _capture_chips(n):
    from pipelines.plan_chips import main

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        main(["--team", str(n)])
    return output.getvalue()


def _decision_rows(decisions):
    return [{"Drivers": ", ".join(d.drivers), "Constructors": ", ".join(d.constructors),
             "Boost": d.boost, "3x boost": d.boost3 or "—",
             "Transfers in": ", ".join(d.transfers_in) or "—",
             "Penalty transfers": d.penalty_transfers, "Cost": d.cost,
             "Expected points": d.expected_points} for d in decisions]


def _timeline(n):
    try:
        history = history_points(n)
    except ValueError as exc:
        st.warning(str(exc))
        return
    if history.empty:
        st.info("History starts at the first round saved through the app.")
        return
    frame = history.copy()
    frame["transfer_marker"] = frame["transfers"].fillna("").astype(str).str.len().gt(0) | frame["chip"].fillna("").astype(str).ne("")
    frame["lineup"] = frame["lineup"].fillna("").astype(str)
    values = frame.melt(id_vars=["round", "lineup", "transfers", "chip", "transfer_marker"],
                        value_vars=["points", "cumulative", "team_value"],
                        var_name="Series", value_name="Value")
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {"values": values.to_dict("records")},
        "layer": [
            {"mark": {"type": "line", "point": False},
             "encoding": {"x": {"field": "round", "type": "quantitative", "title": "Round"},
                          "y": {"field": "Value", "type": "quantitative", "title": "Points / team value"},
                          "color": {"field": "Series", "type": "nominal",
                                    "scale": {"domain": ["points", "cumulative", "team_value"],
                                              "range": ["#E10600", "#F2F3F4", "#54C9A6"]}},
                          "tooltip": [{"field": "round"}, {"field": "Series"}, {"field": "Value"},
                                      {"field": "transfers"}, {"field": "chip"}]}},
            {"transform": [{"filter": "datum.transfer_marker"}],
             "mark": {"type": "point", "filled": True, "size": 80},
             "encoding": {"x": {"field": "round", "type": "quantitative"},
                          "y": {"field": "Value", "type": "quantitative"},
                          "color": {"field": "Series", "type": "nominal",
                                    "scale": {"domain": ["points", "cumulative", "team_value"],
                                              "range": ["#E10600", "#F2F3F4", "#54C9A6"]}},
                          "tooltip": [{"field": "round"},
                                      {"field": "transfers"}, {"field": "chip"}]}}
        ],
        "resolve": {"scale": {"y": "independent"}},
        "height": 300,
    }
    st.vega_lite_chart(spec, width="stretch")


def _table_of(decisions):
    st.dataframe(pd.DataFrame(_decision_rows(decisions)), hide_index=True, width="stretch")


def _chip_select(n, team, season, round_):
    """Per-team chip picker: defaults to the chip advice; locked to the logged chip once applied.
    Returns (chip, played_now)."""
    played_now = round_chip(n, season, round_) if round_ is not None else None
    options = ["None", *team.get("chips_left", []), *([played_now] if played_now else [])]
    advised = advised_chip(_report_chip_advice(n)[0], round_) if round_ is not None else None
    default = played_now or (advised if advised in options else None) or "None"
    choice = st.selectbox("Chip this weekend", options, index=options.index(default), key=f"chip_{n}",
                          disabled=_applied(n, season, round_))
    return (None if choice == "None" else choice), played_now


def _applied(n, season, round_):
    """True once 'I made these transfers' logged this round (with or without a chip)."""
    return any(r["season"] == season and r["round"] == round_ for r in swaps_log(n))


def _picks(n, team, state, chip):
    """Top choices for the chip; returns (choices, session key of the chosen index)."""
    choices = []
    if state is not None:
        try:
            choices = _cached_top(state, exclude=team.get("exclude", []), chip=chip)
        except ValueError as exc:
            st.warning(str(exc))
    if not choices and state is not None:
        st.info("No live pick is available yet.")
    return choices, f"choice_{n}_{chip or 'None'}"


def _chip_advice(n):
    advice, report_name = _report_chip_advice(n)
    if advice:
        st.caption(report_name)
        st.code(advice)
    else:
        st.info("No chip advice was found in the latest round report.")
    if st.button("Recompute chips", key=f"chips_{n}"):
        try:
            st.code(_capture_chips(n))
        except Exception as exc:
            st.error(f"Could not recompute chip advice: {exc}")


def _selected(choices, choice_key):
    index = min(st.session_state.get(choice_key, 0), len(choices) - 1) if choices else None
    return index, (choices[index] if index is not None else None)


def _choose_and_apply(n, choices, chip, choice_key, applied=False):
    if not choices:
        st.caption("No alternative lineups are available.")
    else:
        _table_of(choices)
        cols = st.columns(len(choices))
        for i, col in enumerate(cols):  # on_click so the swap strip above sees the choice this run
            col.button(f"Use #{i + 1}", key=f"use_{n}_{chip or 'None'}_{i}",
                       on_click=st.session_state.__setitem__, args=(choice_key, i))
    index, selected = _selected(choices, choice_key)
    if selected is not None:
        st.write(f"Selected: #{index + 1}")
        st.write(f"Drivers: {', '.join(selected.drivers)}")
        st.write(f"Constructors: {', '.join(selected.constructors)}")
    if applied:
        st.caption("Transfers already applied for this round.")
    if st.button("I made these transfers", key=f"apply_{n}", disabled=selected is None or applied):
        try:
            apply_transfers(n, selected, chip)
            st.success("Team updated.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _edit_form(n, team, prices):
    ids = {k: prices.loc[prices["kind"] == k, "asset_id"].astype(str).tolist() if not prices.empty else team.get(f"{k}s", [])
           for k in ("driver", "constructor")}
    drivers, constructors = ids["driver"], ids["constructor"]
    with st.form(f"edit_{n}"):
        chosen_drivers = st.multiselect("Drivers (select 5)", drivers, default=[x for x in team.get("drivers", []) if x in drivers])
        chosen_constructors = st.multiselect("Constructors (select 2)", constructors,
                                             default=[x for x in team.get("constructors", []) if x in constructors])
        bank = st.number_input("Bank", min_value=0.0, value=float(team.get("bank", 0.0)), step=0.1, format="%.1f")
        free_transfers = st.number_input("Free transfers", min_value=0, value=int(team.get("free_transfers", 0)), step=1)
        chips = [c for c in team.get("chips_left", []) if st.checkbox(c, value=True, key=f"edit_chip_{n}_{c}")]
        excluded = st.multiselect("Exclude from picks", sorted(set(drivers + constructors)),
                                  default=[x for x in team.get("exclude", []) if x in drivers + constructors])
        save = st.form_submit_button("Validate and save")
    edited = {"drivers": chosen_drivers, "constructors": chosen_constructors, "bank": bank,
              "free_transfers": free_transfers, "chips_left": chips, "exclude": excluded}
    try:
        errors = validate(edited)
    except ValueError as exc:
        errors = [str(exc)]
    for error in errors:
        st.error(error)
    if save and not errors:
        try:
            save_team(n, edited)
            st.success("Team saved.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


@st.fragment  # a click inside one tab reruns only that tab
def _team_row(n, next_round, races):
    config_path = team_path(n)
    if not config_path.exists():
        st.warning(f"Missing {config_path.relative_to(ROOT)}. Add this team file to use its controls.")
        return
    team = load(n) or {}
    season = next_round[0] if next_round is not None else int(races["season"].max()) if not races.empty else 2026
    round_ = next_round[1] if next_round is not None else None
    prices = _prices(season, round_)  # falls back to the latest priced round, for display and the edit form
    try:
        state = team_state(n)
    except ValueError as exc:
        state = None
        st.warning(str(exc))
    rules = load_rules(season)

    left, mid, right = st.columns([5, 2, 4], gap="medium")
    with mid:
        chip, played_now = _chip_select(n, team, season, round_)
        st.html(chip_grid(list(rules["chips"]), team.get("chips_left", []), chip, played_now))
    drivers, constructors = team.get("drivers", []), team.get("constructors", [])
    try:
        mu = _mu(season, round_, _inputs_stamp()) if round_ is not None else {}
    except ValueError:
        mu = {}
    xpts, x2 = saved_xpts(team, mu, rules, chip)
    cost = sum(state.owned.values()) if state is not None else None
    with left:
        st.markdown(f"**Team {n}**")
        st.html(team_card(constructors, x2, [d for d in drivers if d != x2], cost,
                          [f"bank {float(team.get('bank', 0.0)):.1f}", f"{int(team.get('free_transfers', 0))} FT"],
                          xpts, _cards([*drivers, *constructors], season, round_)))
        if round_ is not None and not races.empty and (warning := stale_warning(config_path, races, season, round_)):
            st.warning(warning)
        choices, choice_key = _picks(n, team, state, chip)
        _, selected = _selected(choices, choice_key)
        if selected is not None:
            owned = [*drivers, *constructors]
            picked = [*selected.drivers, *selected.constructors]
            st.html(swap_strip([a for a in owned if a not in picked], [a for a in picked if a not in owned]))
            st.caption(f"{', '.join(selected.drivers)} | {', '.join(selected.constructors)} · x2 {selected.boost}"
                       f"{f' · x3 {selected.boost3}' if selected.boost3 else ''} · cost {selected.cost:.1f}"
                       f" · {selected.expected_points:.1f} xPts")
    with right:
        with st.expander("Alternatives"):
            _choose_and_apply(n, choices, chip, choice_key, round_ is not None and _applied(n, season, round_))
        with st.expander("Chip advice"):
            _chip_advice(n)
        with st.expander("Edit team"):
            _edit_form(n, team, prices)
        with st.expander("Past swaps"):
            log = swaps_log(n)
            if not log:
                st.caption("No swaps logged yet.")
            for r in log:
                chip_note = f" · {r['chip']}" if r["chip"] else ""
                st.text(f"R{r['round']}: OUT {', '.join(r['out']) or '—'} → IN {', '.join(r['in']) or '—'}{chip_note}")


def _data_tab(next_round, next_error):
    tiles = st.columns(4)
    if next_round is None:
        tiles[0].metric("Next round", "—")
        tiles[1].metric("Lock", "—")
        if next_error:
            st.warning(next_error)
        else:
            st.info("No upcoming round is available in the processed race schedule.")
    else:
        race = _table("races")
        race = race.loc[(race["season"] == next_round[0]) & (race["round"] == next_round[1])].iloc[0]
        lock = pd.Timestamp(race["lock_utc"]).to_pydatetime().astimezone()
        tiles[0].metric(f"Next round · {next_round[0]}", f"R{next_round[1]}")
        tiles[1].metric(f"Lock · {lock:%Y-%m-%d}", lock.strftime("%a %H:%M"))
    prices = _table("prices")
    latest = prices.sort_values(["season", "round"]).iloc[-1] if not prices.empty else None
    tiles[2].metric(f"Latest prices · {int(latest['season'])}" if latest is not None else "Latest prices",
                    f"R{int(latest['round'])}" if latest is not None else "—")
    try:
        tiles[3].metric("Unsealed raw files", unsealed(ROOT / "data" / "raw", ROOT / "data" / "raw.tar.gz.enc"))
    except Exception as exc:
        st.warning(f"Could not read the unsealed-file count: {exc}")
    if st.button("Update data", key="update_data"):
        log = st.empty()
        lines = []
        command = ["uv", "run", "python", "-m", "pipelines.weekly_update", "--force"]
        try:
            process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in process.stdout:
                lines.append(line.rstrip())
                log.code("\n".join(lines[-80:]))
            code = process.wait()
            if code == 0:
                st.cache_data.clear()
                st.session_state["update_output"] = lines
                st.rerun()
            else:
                st.error(f"Update exited with code {code}.")
        except Exception as exc:
            st.error(f"Could not start update: {exc}")


@st.fragment
def _best_tab(next_round, team_numbers):
    benched = sorted({a for n in team_numbers for a in (load(n) or {}).get("exclude") or []})
    prices = _prices(*next_round) if next_round is not None else pd.DataFrame()
    options = sorted(set(prices["asset_id"].astype(str)) | set(benched)) if not prices.empty else benched
    with st.popover("Filters"):
        budget = st.number_input("Budget", min_value=0.0, value=100.0, step=0.1, format="%.1f")
        # default: every id excluded in any team file (benched drivers)
        exclude = st.multiselect("Exclude from picks", options, default=benched, key="best_exclude")
    try:
        best = _cached_top(None, budget, exclude=exclude, n=10)
        if best:
            season, round_ = next_round if next_round is not None else (None, None)
            cards = _cards({a for d in best for a in (*d.drivers, *d.constructors)}, season, round_)
            st.html(header_row("#", chips=False) + "".join(team_row(str(i + 1), d.constructors, d.boost, [x for x in d.drivers if x != d.boost],
                                     d.cost, [], d.expected_points, cards) for i, d in enumerate(best)))
        else:
            st.info("No best-team results are available yet.")
    except ValueError as exc:
        st.warning(str(exc))


def main():
    st.set_page_config(page_title="F1 Fantasy", layout="wide")
    st.html(CSS)
    st.html(HEADER)
    if "update_output" in st.session_state:
        st.success("Update finished.")
        st.code("\n".join(st.session_state.pop("update_output")))
    next_round, races, next_error = _round_info()
    team_files = sorted((ROOT / "config").glob("my_team_[0-9].yaml"), key=lambda p: int(p.stem.rsplit("_", 1)[1]))
    numbers = [int(p.stem.rsplit("_", 1)[1]) for p in team_files]
    mine, best, timeline, update = st.tabs(["My Team", "Best Teams", "Timeline", "Update"])
    with mine:
        for i, n in enumerate(numbers):
            if i:
                st.divider()
            _team_row(n, next_round, races)
    with best:
        _best_tab(next_round, numbers)
    with timeline:
        st.info("Timeline arrives with the timeline branch.")
    with update:
        _data_tab(next_round, next_error)


if __name__ == "__main__":
    main()
