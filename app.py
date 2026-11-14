"""Local Streamlit dashboard for the F1 Fantasy teams and weekly update."""
import contextlib
import io
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pipelines.pick_team import load_team
from pipelines.weekly_update import stale_warning, unsealed
from src.optimize.ilp import TeamState
from src.ui.logic import apply_transfers, history_points, next_round, save_team, top_teams, validate


def _inputs_stamp():
    """Modified times of everything top_teams reads besides its arguments: data, model and rules files."""
    files = [*(ROOT / "data" / "processed").glob("*.parquet"), ROOT / "config" / "model.yaml",
             *(ROOT / "config").glob("rules_*.yaml")]
    return tuple(sorted((p.name, p.stat().st_mtime_ns) for p in files if p.exists()))


@st.cache_data(show_spinner="Solving teams...", max_entries=64)
def _top(owned, bank, free, budget, exclude, chip, stamp):
    """Cached top_teams: each ILP solve costs ~0.2 s, so only re-solve when the team, chip or input files change."""
    state = TeamState(dict(owned), bank, free) if owned is not None else None
    return top_teams(state, budget, n=5, exclude=list(exclude), chip=chip)


def _cached_top(state, budget=100.0, exclude=(), chip=None):
    owned = tuple(sorted(state.owned.items())) if state is not None else None
    bank, free = (state.bank, state.free_transfers) if state is not None else (None, None)
    return _top(owned, bank, free, budget, tuple(exclude), chip, _inputs_stamp())


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
             "Boost": d.boost, "3x boost": getattr(d, "boost3", None) or "—",
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
                                      {"field": "lineup"}, {"field": "transfers"}, {"field": "chip"}]}},
            {"transform": [{"filter": "datum.transfer_marker"}],
             "mark": {"type": "point", "filled": True, "size": 80},
             "encoding": {"x": {"field": "round", "type": "quantitative"},
                          "y": {"field": "Value", "type": "quantitative"},
                          "color": {"field": "Series", "type": "nominal",
                                    "scale": {"domain": ["points", "cumulative", "team_value"],
                                              "range": ["#E10600", "#F2F3F4", "#54C9A6"]}},
                          "tooltip": [{"field": "round"}, {"field": "lineup"},
                                      {"field": "transfers"}, {"field": "chip"}]}}
        ],
        "resolve": {"scale": {"y": "independent"}},
        "height": 300,
    }
    st.vega_lite_chart(spec, width="stretch")


@st.fragment  # a click inside one tab reruns only that tab
def _team_tab(n, next_round, races):
    config_path = ROOT / "config" / f"my_team_{n}.yaml"
    if not config_path.exists():
        st.warning(f"Missing {config_path.relative_to(ROOT)}. Add this team file to use its controls.")
        return
    team = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    season = next_round[0] if next_round is not None else int(races["season"].max()) if not races.empty else 2026
    round_ = next_round[1] if next_round is not None else None
    prices = _prices(season, round_)
    price_map = dict(zip(prices["asset_id"], prices["price"])) if not prices.empty else {}
    team_state = load_team(config_path, price_map) if all(a in price_map for a in team.get("drivers", []) + team.get("constructors", [])) else None

    st.subheader(f"Team {n}")
    st.dataframe(pd.DataFrame([{"Kind": kind, "Asset": asset, "Price": price_map.get(asset)}
                               for kind, field in (("Driver", "drivers"), ("Constructor", "constructors"))
                               for asset in team.get(field, [])]), hide_index=True, width="stretch")
    chips = list(team.get("chips_left", []))
    chip_choice = st.selectbox("Chip to play", ["None", *chips], key=f"chip_{n}")
    chip = None if chip_choice == "None" else chip_choice
    choice_key = f"choice_{n}_{chip_choice}"
    choices = []
    if team_state is not None:
        try:
            choices = _cached_top(team_state, exclude=team.get("exclude", []), chip=chip)
        except ValueError as exc:
            st.warning(str(exc))
    else:
        st.warning("Current prices are unavailable for this team, so its live pick cannot be loaded yet.")
    if choices:
        st.markdown("#### Live best pick")
        st.dataframe(pd.DataFrame(_decision_rows(choices[:1])), hide_index=True, width="stretch")
        st.session_state.setdefault(choice_key, 0)
    elif team_state is not None:
        st.info("No live pick is available yet.")

    warning = stale_warning(config_path, races, season, round_) if round_ is not None and not races.empty else None
    if warning:
        st.warning(warning)

    advice, report_name = _report_chip_advice(n)
    if advice:
        st.markdown(f"#### Chip advice · {report_name}")
        st.code(advice)
    else:
        st.info("No chip advice was found in the latest round report.")
    if st.button("Recompute chips", key=f"chips_{n}"):
        try:
            st.code(_capture_chips(n))
        except Exception as exc:
            st.error(f"Could not recompute chip advice: {exc}")

    st.markdown("#### Other choices")
    if choices:
        st.dataframe(pd.DataFrame(_decision_rows(choices)), hide_index=True, width="stretch")
        for i, decision in enumerate(choices):
            if st.button(f"Use this one · {i + 1}", key=f"use_{n}_{chip_choice}_{i}"):
                st.session_state[choice_key] = i
    else:
        st.caption("No alternative lineups are available.")

    selected_index = min(st.session_state.get(choice_key, 0), len(choices) - 1) if choices else None
    selected = choices[selected_index] if selected_index is not None else None
    if selected is not None:
        st.write(f"Selected: #{selected_index + 1}")
        st.write(f"Drivers: {', '.join(selected.drivers)}")
        st.write(f"Constructors: {', '.join(selected.constructors)}")
    if st.button("I made these transfers", key=f"apply_{n}", disabled=selected is None):
        try:
            apply_transfers(n, selected, chip)
            st.success("Team updated.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.markdown("#### Edit team")
    drivers = prices.loc[prices["kind"] == "driver", "asset_id"].astype(str).tolist() if not prices.empty else team.get("drivers", [])
    constructors = prices.loc[prices["kind"] == "constructor", "asset_id"].astype(str).tolist() if not prices.empty else team.get("constructors", [])
    chip_options = list(team.get("chips_left", []))
    with st.form(f"edit_{n}"):
        chosen_drivers = st.multiselect("Drivers (select 5)", drivers, default=[x for x in team.get("drivers", []) if x in drivers])
        chosen_constructors = st.multiselect("Constructors (select 2)", constructors,
                                             default=[x for x in team.get("constructors", []) if x in constructors])
        bank = st.number_input("Bank", min_value=0.0, value=float(team.get("bank", 0.0)), step=0.1, format="%.1f")
        free_transfers = st.number_input("Free transfers", min_value=0, value=int(team.get("free_transfers", 0)), step=1)
        selected_chips = [chip for chip in chip_options
                          if st.checkbox(chip, value=True, key=f"edit_chip_{n}_{chip}")]
        excluded = st.multiselect("Exclude from picks", sorted(set(drivers + constructors)),
                                  default=[x for x in team.get("exclude", []) if x in drivers + constructors])
        save = st.form_submit_button("Validate and save")
    edited = {"drivers": chosen_drivers, "constructors": chosen_constructors, "bank": bank,
              "free_transfers": free_transfers, "chips_left": selected_chips, "exclude": excluded}
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

    st.markdown("#### Season timeline")
    _timeline(n)


def _data_tab(next_round, next_error):
    st.subheader("Data status")
    if next_round is None:
        if next_error:
            st.warning(next_error)
        else:
            st.info("No upcoming round is available in the processed race schedule.")
    else:
        race = _table("races")
        race = race.loc[(race["season"] == next_round[0]) & (race["round"] == next_round[1])].iloc[0]
        lock = pd.Timestamp(race["lock_utc"]).to_pydatetime().astimezone().strftime("%A %Y-%m-%d %H:%M %Z")
        st.write(f"Next round: {next_round[0]} round {next_round[1]}")
        st.write(f"Lock: {lock}")
    prices = _table("prices")
    latest = prices.sort_values(["season", "round"]).iloc[-1] if not prices.empty else None
    latest_label = f"{int(latest['season'])} round {int(latest['round'])}" if latest is not None else "unavailable"
    st.write(f"Latest price round: {latest_label}")
    try:
        st.write(f"Unsealed raw files: {unsealed(ROOT / 'data' / 'raw', ROOT / 'data' / 'raw.tar.gz.enc')}")
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
def _best_tab():
    st.subheader("Best teams")
    budget = st.number_input("Budget", min_value=0.0, value=100.0, step=0.1, format="%.1f")
    try:
        best = _cached_top(None, budget)
        if best:
            st.dataframe(pd.DataFrame(_decision_rows(best)), hide_index=True, width="stretch")
        else:
            st.info("No best-team results are available yet.")
    except ValueError as exc:
        st.warning(str(exc))


def main():
    st.set_page_config(page_title="F1 Fantasy", layout="wide")
    st.title("F1 Fantasy")
    if "update_output" in st.session_state:
        st.success("Update finished.")
        st.code("\n".join(st.session_state.pop("update_output")))
    next_round, races, next_error = _round_info()
    team_files = sorted((ROOT / "config").glob("my_team_[0-9].yaml"), key=lambda p: int(p.stem.rsplit("_", 1)[1]))
    team_tabs = [f"Team {p.stem.rsplit('_', 1)[1]}" for p in team_files]
    tabs = st.tabs([*team_tabs, "Best teams", "Data"])
    for i, path in enumerate(team_files):
        n = int(path.stem.rsplit("_", 1)[1])
        with tabs[i]:
            _team_tab(n, next_round, races)
    best_index = len(team_tabs)
    with tabs[best_index]:
        _best_tab()
    with tabs[best_index + 1]:
        _data_tab(next_round, next_error)


if __name__ == "__main__":
    main()
