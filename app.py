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

try:
    from src.ui.logic import apply_transfers, history_points, save_team, top_teams, validate
    STUBS = False
except ModuleNotFoundError as exc:
    if exc.name not in {"src.ui", "src.ui.logic"}:
        raise
    from app_stubs import apply_transfers, history_points, save_team, top_teams, validate
    STUBS = True


@st.cache_data
def _table(name):
    path = ROOT / "data" / "processed" / f"{name}.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def _round_info():
    races = _table("races")
    if races.empty:
        return None, races
    remaining = races.loc[~races["completed"]].sort_values(["season", "round"])
    return (remaining.iloc[0] if not remaining.empty else None), races


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
             "Boost": d.boost, "Transfers in": ", ".join(d.transfers_in) or "—",
             "Penalty transfers": d.penalty_transfers, "Cost": d.cost,
             "Expected points": d.expected_points} for d in decisions]


def _timeline(n):
    history = history_points(n)
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


def _team_tab(n, next_round, races):
    config_path = ROOT / "config" / f"my_team_{n}.yaml"
    if not config_path.exists():
        st.warning(f"Missing {config_path.relative_to(ROOT)}. Add this team file to use its controls.")
        return
    team = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    season = int(next_round["season"]) if next_round is not None else int(races["season"].max()) if not races.empty else 2026
    round_ = int(next_round["round"]) if next_round is not None else None
    prices = _prices(season, round_)
    price_map = dict(zip(prices["asset_id"], prices["price"])) if not prices.empty else {}
    team_state = load_team(config_path, price_map) if all(a in price_map for a in team.get("drivers", []) + team.get("constructors", [])) else None

    st.subheader(f"Team {n}")
    st.dataframe(pd.DataFrame([{"Kind": kind, "Asset": asset, "Price": price_map.get(asset)}
                               for kind, field in (("Driver", "drivers"), ("Constructor", "constructors"))
                               for asset in team.get(field, [])]), hide_index=True, width="stretch")
    choices = top_teams(team_state, 100.0, n=5) if team_state is not None else []
    if team_state is None:
        st.info("Current prices are unavailable for this team, so its live pick cannot be loaded yet.")
    else:
        if choices:
            st.markdown("#### Live best pick")
            st.dataframe(pd.DataFrame(_decision_rows(choices[:1])), hide_index=True, width="stretch")
            if f"choice_{n}" not in st.session_state:
                st.session_state[f"choice_{n}"] = 0
        else:
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
            if st.button(f"Use this one · {i + 1}", key=f"use_{n}_{i}"):
                st.session_state[f"choice_{n}"] = i
    else:
        st.caption("No alternative lineups are available.")

    selected = choices[min(st.session_state.get(f"choice_{n}", 0), len(choices) - 1)] if choices else None
    chips = list(team.get("chips_left", []))
    chip_choice = st.selectbox("Chip to play", ["None", *chips], key=f"chip_{n}")
    if st.button("I made these transfers", key=f"apply_{n}", disabled=selected is None):
        try:
            apply_transfers(n, selected, None if chip_choice == "None" else chip_choice)
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
        selected_chips = st.multiselect("Chips remaining", chip_options, default=chip_options)
        excluded = st.multiselect("Exclude from picks", sorted(set(drivers + constructors)),
                                  default=[x for x in team.get("exclude", []) if x in drivers + constructors])
        save = st.form_submit_button("Validate and save")
    edited = {"drivers": chosen_drivers, "constructors": chosen_constructors, "bank": bank,
              "free_transfers": free_transfers, "chips_left": selected_chips, "exclude": excluded}
    errors = validate(edited)
    if save:
        if errors:
            for error in errors:
                st.error(error)
        else:
            try:
                save_team(n, edited)
                st.success("Team saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.markdown("#### Season timeline")
    _timeline(n)


def _data_tab(next_round):
    st.subheader("Data status")
    if next_round is None:
        st.info("No upcoming round is available in the processed race schedule.")
    else:
        lock = pd.Timestamp(next_round["lock_utc"]).to_pydatetime().astimezone().strftime("%A %Y-%m-%d %H:%M %Z")
        st.write(f"Next round: {int(next_round['season'])} round {int(next_round['round'])}")
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
                st.success("Update finished.")
            else:
                st.error(f"Update exited with code {code}.")
        except Exception as exc:
            st.error(f"Could not start update: {exc}")


def main():
    st.set_page_config(page_title="F1 Fantasy", layout="wide")
    st.title("F1 Fantasy")
    if STUBS:
        st.info("The 8.4 team logic is not merged yet; team actions are temporarily stubbed.")
    next_round, races = _round_info()
    team_files = sorted((ROOT / "config").glob("my_team_[0-9].yaml"), key=lambda p: int(p.stem.rsplit("_", 1)[1]))
    team_tabs = [f"Team {p.stem.rsplit('_', 1)[1]}" for p in team_files]
    tabs = st.tabs([*team_tabs, "Best teams", "Data"])
    for i, path in enumerate(team_files):
        n = int(path.stem.rsplit("_", 1)[1])
        with tabs[i]:
            _team_tab(n, next_round, races)
    best_index = len(team_tabs)
    with tabs[best_index]:
        st.subheader("Best teams")
        budget = st.number_input("Budget", min_value=0.0, value=100.0, step=0.1, format="%.1f")
        best = top_teams(None, budget, n=5)
        if best:
            st.dataframe(pd.DataFrame(_decision_rows(best)), hide_index=True, width="stretch")
        else:
            st.info("No best-team results are available yet.")
    with tabs[best_index + 1]:
        _data_tab(next_round)


if __name__ == "__main__":
    main()
