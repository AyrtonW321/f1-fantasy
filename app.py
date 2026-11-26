"""Local Streamlit dashboard for the F1 Fantasy teams and weekly update."""
import contextlib
import io
import re
import subprocess
import sys
import traceback
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pipelines.weekly_update import lagging_sources, stale_warning, unsealed
from src.optimize.ilp import TeamState
from src.sim.scoring import load_rules
from src.ui.cards import (CSS, HEADER, asset_card, best_skeleton, load_error, team_skeleton, timeline_skeleton, chip_grid, header_row, swap_strip, team_card, team_row)
from src.ui.logic import (advised_chip, apply_transfers, asset_mu, confirm_round, final_fix, load, next_round, race_review,
                          record_round, round_source,
                          round_chip, save_team, saved_xpts, swaps_log, taken_leads, team_path, team_state, top_teams,
                          validate)
from src.ui.timeline import timeline_frame, timeline_spec
from src.ui.style import driver_teams, team_colors


def _inputs_stamp():
    """Modified times of everything top_teams reads besides its arguments: data, model and rules files."""
    files = [*(ROOT / "data" / "processed").glob("*.parquet"), ROOT / "config" / "model.yaml",
             *(ROOT / "config").glob("rules_*.yaml")]
    return tuple(sorted((p.name, p.stat().st_mtime_ns) for p in files if p.exists()))


@st.cache_data(show_spinner=False, max_entries=64)  # skeletons show the wait
def _top(owned, bank, free, budget, exclude, chip, n, stamp, leads=((), ())):
    """Cached top_teams: each ILP solve costs ~0.2 s, so only re-solve when the team, chip or input files change."""
    state = TeamState(dict(owned), bank, free) if owned is not None else None
    return top_teams(state, budget, n=n, exclude=list(exclude), chip=chip, leads=leads)


def _cached_top(state, budget=100.0, exclude=(), chip=None, n=5, leads=((), ())):
    owned = tuple(sorted(state.owned.items())) if state is not None else None
    bank, free = (state.bank, state.free_transfers) if state is not None else (None, None)
    return _top(owned, bank, free, budget, tuple(exclude), chip, n, _inputs_stamp(), leads)


@st.cache_data(show_spinner=False, max_entries=16)
def _leads(n, stamp, teams):
    """Cached taken_leads; teams = mtimes of team and history files, so a saved or applied team re-solves."""
    return taken_leads(n)


def _team_stamp():
    files = [*(ROOT / "config").glob("my_team_[0-9].yaml"), *(ROOT / "config" / "history").glob("team_*.csv")]
    return tuple(sorted((p.name, p.stat().st_mtime_ns) for p in files))


@st.cache_data(show_spinner=False)
def _mu(season, round_, stamp):
    return asset_mu(season, round_)


@st.cache_data(show_spinner=False, max_entries=16)
def _review(n, season, round_, stamp, history_mtime):
    return race_review(n, season, round_)


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


def _guard(thing, key, body, *args):
    """Run one data area; on failure show a message and Retry in its place (the spec's error state)."""
    box = st.empty()
    try:
        with box.container():
            body(*args)
    except Exception:
        traceback.print_exc()  # details go to the server log, not the page
        with box.container():
            st.html(load_error(thing))
            st.columns([2, 1, 2])[1].button("Retry", key=key, type="primary", width="stretch")  # reruns this fragment


def _area(first, skeleton):
    """First run: a slot showing the skeleton until filled. Later runs: a plain container, so old content stays."""
    if not first:
        return st.container()
    slot = st.empty()
    slot.html(skeleton)
    return slot.container


@st.fragment
def _timeline_tab(numbers):
    _guard("the timeline", "retry_timeline", _timeline_body, numbers)


def _timeline_body(numbers):
    frame = timeline_frame(numbers)
    if frame.empty:
        st.info("No scored round yet this season.")
        return
    st.caption("Solid = real points. Dashed = expected points for the current best pick. Hover a race for transfers.")
    st.vega_lite_chart(timeline_spec(frame), width="stretch")


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
    """True once 'I made these transfers' logged this round (with or without a chip); snapshots do not count."""
    return any(r["season"] == season and r["round"] == round_ and r["source"] != "snapshot" for r in swaps_log(n))


def _picks(n, team, state, chip):
    """Top choices for the chip; returns (choices, session key of the chosen index)."""
    choices = []
    if state is not None:
        try:
            choices = _cached_top(state, exclude=team.get("exclude", []), chip=chip,
                                  leads=_leads(n, _inputs_stamp(), _team_stamp()))
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


def _edit_form(n, team, prices, season, rounds, chip_names, default_boost=None):
    """rounds: round numbers the saved lineup can be recorded as played in (next round first)."""
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
        st.caption("Played lineup (logged to history, shown in Timeline)")
        played = st.selectbox("Record as played in round", rounds, key=f"edit_round_{n}") if rounds else None
        boost = st.selectbox("x2 boost", drivers, index=drivers.index(default_boost) if default_boost in drivers else 0,
                             key=f"edit_boost_{n}")
        chip_played = st.selectbox("Chip played", ["", *chip_names], key=f"edit_chip_played_{n}")
        boost3 = st.selectbox("x3 driver (x3_boost only)", ["", *drivers], key=f"edit_boost3_{n}")
        official = st.number_input("Official score from the game (blank = compute)", value=None, step=1.0,
                                   format="%.0f", key=f"edit_official_{n}")
        save = st.form_submit_button("Validate and save")
    edited = {"drivers": chosen_drivers, "constructors": chosen_constructors, "bank": bank,
              "free_transfers": free_transfers, "chips_left": chips, "exclude": excluded}
    try:
        errors = validate(edited)
    except ValueError as exc:
        errors = [str(exc)]
    if boost not in chosen_drivers:
        errors.append("x2 boost: pick one of your drivers")
    if chip_played == "x3_boost" and (boost3 not in chosen_drivers or boost3 == boost):
        errors.append("x3 driver: pick one of your drivers other than the x2 boost")
    elif chip_played != "x3_boost" and boost3:
        errors.append("x3 driver: only with the x3_boost chip")
    for error in errors:
        st.error(error)
    if save and not errors:
        try:
            if played is not None:
                record_round(n, season, played, chosen_drivers, chosen_constructors, boost, chip_played, boost3,
                             official_points=official)
            save_team(n, edited)
            st.success("Team saved.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


@st.fragment  # a click inside one tab reruns only that tab
def _team_row(n, next_round, races):
    _guard(f"Team {n}", f"retry_team_{n}", _team_row_body, n, next_round, races)


def _team_row_body(n, next_round, races):
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
    done = races[(races["season"] == season) & races["completed"]]["round"].sort_values(ascending=False) \
        if not races.empty else pd.Series(dtype=int)
    last = int(done.iloc[0]) if len(done) else None

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
        label = f" · Round {round_} · {_race_name(races, season, round_)}" if round_ is not None else ""
        st.markdown(f"**Team {n}**{label}")
        st.html(team_card(constructors, x2, [d for d in drivers if d != x2], cost,
                          [f"bank {float(team.get('bank', 0.0)):.1f}", f"{int(team.get('free_transfers', 0))} FT"],
                          xpts, _cards([*drivers, *constructors], season, round_)))
        if round_ is not None and not races.empty and (warning := stale_warning(config_path, races, season, round_)):
            st.warning(warning)
        if last is not None and round_source(n, season, last) in (None, "snapshot"):
            _confirm_banner(n, season, last, _race_name(races, season, last))
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
        if "final_fix" in (team.get("chips_left") or []):
            with st.expander("Final Fix (after qualifying)"):
                _final_fix(n)
        if last is not None:
            with st.expander(f"Last race · R{last} {_race_name(races, season, last)}"):
                _last_race(n, season, last)
        with st.expander("Edit team"):
            rounds = ([round_] if round_ is not None else []) + [int(r) for r in done]
            _edit_form(n, team, prices, season, rounds, list(rules["chips"]), saved_xpts(team, mu, rules, None)[1])
        with st.expander("Past swaps"):
            log = swaps_log(n)
            if not log:
                st.caption("No swaps logged yet.")
            for r in log:
                chip_note = (f" · {r['chip']}" if r["chip"] else "") + (" · auto snapshot" if r["source"] == "snapshot" else "")
                st.text(f"R{r['round']}: OUT {', '.join(r['out']) or '—'} → IN {', '.join(r['in']) or '—'}{chip_note}")


def _race_name(races, season, round_):
    slug = races.loc[(races["season"] == season) & (races["round"] == round_), "slug"]
    return slug.iloc[0].removesuffix("-grand-prix").replace("-", " ").title() if len(slug) else f"Round {round_}"


def _confirm_banner(n, season, round_, name):
    """Ask the user to confirm the lineup logged for the last race (or record one if nothing is logged)."""
    source = round_source(n, season, round_)
    if source is None:
        st.warning(f"No lineup recorded for R{round_} {name}. Use Edit team, set 'Record as played in round' "
                   f"to {round_}, and save what you played.")
        return
    st.warning(f"R{round_} {name} lineup is an auto snapshot. Confirm it matches what you played, "
               "or fix it in Edit team.")
    if st.button("Confirm lineup", key=f"confirm_{n}_{round_}"):
        confirm_round(n, season, round_)
        st.rerun()


def _final_fix(n):
    try:
        ff = final_fix(n)
    except (ValueError, FileNotFoundError) as exc:
        st.caption(f"Final Fix unavailable: {exc}")
        return
    if ff is None:
        st.caption("Qualifying results not in yet. After qualifying ends, open the Update tab and run it, then check here.")
        return
    st.caption("Qualifying: " + ", ".join(f"{d} P{p}" if p else f"{d} no time" for d, p in
                                          sorted(ff["quali"].items(), key=lambda x: x[1] or 99)))
    if ff["in"] is None:
        st.caption(f"No affordable swap for {ff['out']}.")
        return
    pos = f"P{ff['out_pos']}" if ff["out_pos"] else "no time"
    st.html(swap_strip([ff["out"]], [ff["in"]]))
    st.markdown(f"Swap **{ff['out']}** ({pos}) for **{ff['in']}** (P{ff['in_pos']}, {ff['in_price']:.1f} of "
                f"{ff['room']:.1f} available).")
    st.caption("Rule: worst-qualified driver out (boosted drivers kept), best-qualified affordable driver in. "
               "Backtest 2026: +51 pts over 18 races vs no swap, but noisy (single races ranged -35 to +28). "
               "Play it when the gap is big, e.g. your driver starts from the back.")


def _last_race(n, season, round_):
    hist = ROOT / "config" / "history" / f"team_{n}.csv"
    review = _review(n, season, round_, _inputs_stamp(), hist.stat().st_mtime_ns if hist.exists() else 0)
    if review is None:
        st.caption("No points yet, or no lineup recorded for this round.")
        return
    a, b, c = st.columns(3)
    a.metric("Scored", f"{review['points']:.0f}", f"{review['points'] - review['expected']:+.0f}",
             help="Change versus expected")
    b.metric("Expected", f"{review['expected']:.0f}")
    c.metric("Best", f"{review['best_points']:.0f}", help="Best team in hindsight under the same budget")
    if review["chip"]:
        st.caption(f"Chip: {review['chip']}")
    st.caption(f"Best team in hindsight (same budget, no transfer limits): {review['best_lineup']}")
    st.caption("Biggest model misses: " + ", ".join(f"{a} {mu:.0f}→{got:.0f}" for a, mu, got in review["misses"]))


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
    if next_round is not None:
        behind = lagging_sources(_table("races"), _table("fantasy_points"), next_round[0], ROOT / "data" / "raw")
        for line in behind:
            st.warning(f"Behind: {line}")
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
    _guard("the best teams", "retry_best", _best_body, next_round, team_numbers)


def _best_body(next_round, team_numbers):
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
    first = not st.session_state.get("loaded")
    team_files = sorted((ROOT / "config").glob("my_team_[0-9].yaml"), key=lambda p: int(p.stem.rsplit("_", 1)[1]))
    numbers = [int(p.stem.rsplit("_", 1)[1]) for p in team_files]
    mine, best, timeline, update = st.tabs(["My Team", "Best Teams", "Timeline", "Update"])
    with mine:  # every skeleton goes out before any slow work starts
        slots = []
        for i, n in enumerate(numbers):
            if i:
                st.divider()
            slots.append(_area(first, team_skeleton()))
    with best:
        best_slot = _area(first, best_skeleton())
    with timeline:
        timeline_slot = _area(first, timeline_skeleton())
    next_round, races, next_error = _round_info()
    for n, slot in zip(numbers, slots):
        with (slot() if first else slot):
            _team_row(n, next_round, races)
    with (best_slot() if first else best_slot):
        _best_tab(next_round, numbers)
    with (timeline_slot() if first else timeline_slot):
        _timeline_tab(numbers)
    with update:
        _data_tab(next_round, next_error)
    st.session_state["loaded"] = True

if __name__ == "__main__":
    main()
