"""Team-file logic for the Streamlit app (Phase 8.4). The app holds no game logic; it calls these.

Paths are project-relative to ROOT so the app works from any start folder. Writes always back up the
old team file to config/backup/ first. History (config/history/team_N.csv) is what the timeline reads.
"""
import csv
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from pipelines.pick_team import exclude as _exclude
from pipelines.pick_team import load_team
from src.backtest.walkforward import _actual_points
from src.features.rolling import robust_mu
from src.optimize.chip_history import replay_gain
from src.optimize.chips import estimate_chip
from src.optimize.ilp import Asset, Decision, InfeasibleTeam, TeamState, next_state, optimize
from src.sim.scoring import _rule, load_rules

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
DATA = ROOT / "data" / "processed"
HISTORY_COLS = ["season", "round", "drivers", "constructors", "boost", "boost3", "chip",
                "transfers_in", "penalty_transfers", "bank", "team_value", "source", "official_points"]
# source: app, edit, snapshot. official_points: the game's score for the round, overrides the computed one


def _tables() -> dict[str, pd.DataFrame]:
    return {n: pd.read_parquet(DATA / f"{n}.parquet") for n in ("races", "prices", "fantasy_points")}


def team_path(n: int) -> Path:
    return CONFIG / f"my_team_{n}.yaml"


def history_path(n: int) -> Path:
    return CONFIG / "history" / f"team_{n}.csv"


def load(n: int) -> dict:
    return yaml.safe_load(team_path(n).read_text(encoding="utf-8"))


def next_round(tables=None) -> tuple[int, int]:
    """(season, round) of the first round not yet completed, as pick_team uses."""
    races = (tables or _tables())["races"]
    left = races[~races["completed"]].sort_values(["season", "round"])
    if left.empty:
        raise ValueError("no upcoming round in the race table; update data once the next season is listed")
    return int(left["season"].iloc[0]), int(left["round"].iloc[0])


def team_state(n: int, tables=None) -> TeamState:
    """Team n at the next round's prices. ValueError when that round has no prices or no round is left."""
    t = tables or _tables()
    season, round_ = next_round(t)
    now = t["prices"][(t["prices"]["season"] == season) & (t["prices"]["round"] == round_)]
    return load_team(team_path(n), dict(zip(now["asset_id"], now["price"].astype(float))))


def assets(season: int, round_: int, exclude=(), tables=None) -> list[Asset]:
    """This round's assets with robust_mu (config/model.yaml form); excluded ids get mu -1000."""
    t = tables or _tables()
    form = yaml.safe_load((CONFIG / "model.yaml").read_text(encoding="utf-8"))["form"]
    mu = robust_mu(t["prices"], t["fantasy_points"], t["races"], season, round_, form["trim"], form["prior_weight"])
    if mu.empty:
        raise ValueError(f"no prices for {season} round {round_}; update data first")
    mu = _exclude(mu, list(exclude))
    return [Asset(r.asset_id, r.kind, float(r.price), float(r.mu)) for r in mu.itertuples()]


def validate(team: dict, season: int | None = None, tables=None) -> list[str]:
    """Error messages for a team dict (team-file keys); empty when valid. Counts and chips from the rules."""
    t = tables or _tables()
    season = season or next_round(t)[0]
    rules = load_rules(season)
    prices = t["prices"][t["prices"]["season"] == season]
    known = {k: set(prices.loc[prices["kind"] == k, "asset_id"]) for k in ("driver", "constructor")}
    errors = []
    for key, kind, count in (("drivers", "driver", _rule(rules, "team.drivers")),
                             ("constructors", "constructor", _rule(rules, "team.constructors"))):
        ids = list(team.get(key) or [])
        if len(ids) != count or len(set(ids)) != count:
            errors.append(f"{key}: need {count} different, got {len(set(ids))}")
        if unknown := sorted(set(ids) - known[kind]):
            errors.append(f"{key}: unknown {kind} ids {unknown}")
    try:
        if float(team.get("bank")) < 0:
            errors.append("bank: cannot be negative")
    except (TypeError, ValueError):
        errors.append("bank: must be a number")
    free = team.get("free_transfers")
    if not isinstance(free, int) or not 0 <= free <= _rule(rules, "transfers.max_free"):
        errors.append(f"free_transfers: whole number 0 to {_rule(rules, 'transfers.max_free')}")
    if bad := sorted(set(team.get("chips_left") or []) - set(rules["chips"])):
        errors.append(f"chips_left: unknown chips {bad}")
    if bad := sorted(set(team.get("exclude") or []) - known["driver"] - known["constructor"]):
        errors.append(f"exclude: unknown ids {bad}")
    return errors


def save_team(n: int, team: dict, season: int | None = None, tables=None) -> None:
    """Validate, back up the old file to config/backup/, write config/my_team_{n}.yaml."""
    if errors := validate(team, season, tables):
        raise ValueError("; ".join(errors))
    path = team_path(n)
    if path.exists():
        backup = CONFIG / "backup" / f"my_team_{n}_{datetime.now():%Y%m%d-%H%M%S}.yaml"
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(path.read_bytes())
    keys = ["exclude", "drivers", "constructors", "bank", "free_transfers", "chips_left"]
    clean = {k: team.get(k, []) for k in keys}
    clean["bank"] = round(float(clean["bank"]), 1)
    path.write_text(yaml.safe_dump(clean, sort_keys=False, default_flow_style=None), encoding="utf-8")


def _log(n: int, row: dict) -> None:
    """Append (or replace) this round's history row."""
    path = history_path(n)
    path.parent.mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame(columns=HISTORY_COLS)
    keep = old[~((old["season"] == str(row["season"])) & (old["round"] == str(row["round"])))]
    new = {k: "" if pd.isna(v := row.get(k, "")) else v for k in HISTORY_COLS}
    out = pd.concat([keep, pd.DataFrame([new]).astype(str)])
    out.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def apply_transfers(n: int, decision: Decision, chip: str | None = None, tables=None) -> dict:
    """'I made these transfers': write the decision as team n for the next round and log the round.

    bank = budget - cost; free transfers from next_state (chips with unlimited transfers use none);
    the played chip leaves chips_left; a chip with team_reverts_next_round keeps the old team and bank.
    Returns the new team dict.
    """
    t = tables or _tables()
    season, round_ = next_round(t)
    rules = load_rules(season)
    team = load(n)
    state = team_state(n, t)
    chip_rules = rules["chips"].get(chip, {}) if chip else {}
    if chip and chip not in (team.get("chips_left") or []):
        raise ValueError(f"chip {chip} not in chips_left")
    counted = replace(decision, transfers_in=()) if chip_rules.get("free_transfers") == "unlimited" else decision
    nxt = next_state(state, counted, rules)
    new = dict(team, free_transfers=int(nxt.free_transfers),
               chips_left=[c for c in team.get("chips_left") or [] if c != chip])
    if not chip_rules.get("team_reverts_next_round"):
        new.update(drivers=list(decision.drivers), constructors=list(decision.constructors),
                   bank=round(decision.budget - decision.cost, 1))
    save_team(n, new, season, t)
    penalty = 0 if counted is not decision else decision.penalty_transfers
    _log(n, {"season": season, "round": round_, "drivers": "|".join(decision.drivers),
             "constructors": "|".join(decision.constructors), "boost": decision.boost,
             "boost3": decision.boost3 or "", "chip": chip or "", "transfers_in": "|".join(decision.transfers_in),
             "penalty_transfers": penalty, "bank": round(decision.budget - decision.cost, 1),
             "team_value": decision.cost, "source": "app"})
    return new


def record_round(n: int, season: int, round_: int, drivers, constructors, boost: str, chip: str = "",
                 boost3: str = "", source: str = "edit", tables=None, official_points: float | None = None) -> None:
    """Log the lineup team n played in a round (replaces that round's row). Penalty unknown: logged 0.
    transfers_in is the diff against the latest earlier logged round."""
    t = tables or _tables()
    prices = t["prices"][(t["prices"]["season"] == season) & (t["prices"]["round"] == round_)]
    price = dict(zip(prices["asset_id"], prices["price"].astype(float)))
    lineup = [*drivers, *constructors]
    h = _history(n)
    before = h[(h["si"] < season) | ((h["si"] == season) & (h["ri"] < round_))]
    prev = [*before["drivers"].iloc[-1].split("|"), *before["constructors"].iloc[-1].split("|")] if len(before) else lineup
    team = load(n)
    _log(n, {"season": season, "round": round_, "drivers": "|".join(drivers), "constructors": "|".join(constructors),
             "boost": boost, "boost3": boost3, "chip": chip,
             "transfers_in": "|".join(a for a in lineup if a not in prev), "penalty_transfers": 0,
             "bank": team.get("bank", ""), "team_value": round(sum(price.get(a, 0.0) for a in lineup), 1),
             "source": source, "official_points": "" if official_points is None else official_points})


def snapshot_next(n: int, tables=None) -> bool:
    """Log team n's saved file as its lineup for the next round unless that round already has a row.
    Boost on the best expected driver. True if a row was written."""
    t = tables or _tables()
    season, round_ = next_round(t)
    h = _history(n)
    if ((h["si"] == season) & (h["ri"] == round_)).any() or not team_path(n).exists():
        return False
    team = load(n)
    _, boost = saved_xpts(team, asset_mu(season, round_, t), load_rules(season), None)
    record_round(n, season, round_, team["drivers"], team["constructors"], boost or "", source="snapshot", tables=t)
    return True


def top_teams(state: TeamState | None, budget: float = 100.0, n: int = 5, exclude=(),
              season: int | None = None, round_: int | None = None, tables=None,
              chip: str | None = None, leads=((), ())) -> list[Decision]:
    """Best n distinct teams for the next round, best first. state=None: overall best under `budget`
    (no transfer limits); otherwise teams reachable from state (its own budget, transfer penalties).
    chip (with a state): the one best team for that chip (limitless, wildcard, x3_boost with boost3 set);
    a chip that does not change the team (autopilot, no_negative, final_fix) gives the normal list.
    leads: (boosted ids, priciest ids) of other teams (taken_leads); neither may lead this team."""
    t = tables or _tables()
    if season is None or round_ is None:
        season, round_ = next_round(t)
    rules = load_rules(season)
    if state is None:
        rules = {**rules, "team": {**rules["team"], "budget": budget}}
    pool = assets(season, round_, exclude, t)
    if chip and state is not None:
        team = {"drivers": list(state.owned), "constructors": [], "bank": state.bank,
                "free_transfers": state.free_transfers}
        _, d, _ = estimate_chip(pool, team, rules, chip, no_boost=leads[0], not_priciest=leads[1])
        if d is not None:  # shortcut: one team per chip, not top n; add forbid loops if alternatives are wanted
            return [replace(d, transfers_in=tuple(a for a in (*d.drivers, *d.constructors) if a not in state.owned))]
    found: list[Decision] = []
    for _ in range(n):
        try:
            found.append(optimize(pool, state, rules, forbid=[[*d.drivers, *d.constructors] for d in found],
                                  no_boost=leads[0], not_priciest=leads[1]))
        except InfeasibleTeam:
            break
    return found


def taken_leads(n: int, tables=None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(boosted drivers, priciest drivers) other teams take next round, so team n leads with someone else.
    A team that logged this round (not a snapshot) counts with that lineup; an unlogged team counts only when
    numbered below n (its own best pick), so lower numbers choose first."""
    t = tables or _tables()
    season, round_ = next_round(t)
    now = t["prices"][(t["prices"]["season"] == season) & (t["prices"]["round"] == round_)]
    price = dict(zip(now["asset_id"], now["price"].astype(float)))
    boosts, priciest = [], []
    for m in range(1, 10):
        if m == n or not team_path(m).exists():
            continue
        h = _history(m)
        row = h[(h["si"] == season) & (h["ri"] == round_)]
        if len(row) and (row["source"].iloc[-1] or "app") != "snapshot":
            drivers, boosted = row["drivers"].iloc[-1].split("|"), [row["boost"].iloc[-1], row["boost3"].iloc[-1]]
        elif m > n:
            continue
        else:  # shortcut: plans the other team without its chip; logged lineups (chip included) win once applied
            d = top_teams(team_state(m, t), n=1, exclude=load(m).get("exclude") or [], tables=t,
                          leads=taken_leads(m, t))[0]
            drivers, boosted = d.drivers, [d.boost]
        boosts += [b for b in boosted if b]
        priciest.append(max(drivers, key=lambda a: price.get(a, 0.0)))
    return tuple(boosts), tuple(priciest)


def history_points(n: int, tables=None) -> pd.DataFrame:
    """Per logged round: points (boost, chip and penalties applied; NaN until scored), cumulative,
    team value, transfers, chip, lineup."""
    cols = ["season", "round", "points", "cumulative", "team_value", "transfers", "chip", "lineup"]
    path = history_path(n)
    if not path.exists():
        return pd.DataFrame(columns=cols)
    t = tables or _tables()
    pts = t["fantasy_points"]
    h = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = []
    for r in h.itertuples():
        season, round_ = int(r.season), int(r.round)
        rules = load_rules(season)
        d = Decision(tuple(r.drivers.split("|")), tuple(r.constructors.split("|")), r.boost, (),
                     int(r.penalty_transfers), float(r.team_value), 0.0, 0.0)
        got = pts[(pts["season"] == season) & (pts["round"] == round_)]
        score = float("nan")
        if len(got):
            score = _actual_points(season, round_, d, pts, rules)
            total = got.set_index(["asset_id", "kind"])["total"]
            if r.chip == "x3_boost" and r.boost3:
                score += (_rule(rules, "chips.x3_boost.extra_multiplier") - 1) * float(total.get((r.boost3, "driver"), 0.0))
            elif r.chip == "autopilot":
                drv = [float(total.get((a, "driver"), 0.0)) for a in d.drivers]
                score += (_rule(rules, "team.boost_multiplier") - 1) * (max(drv) - float(total.get((d.boost, "driver"), 0.0)))
            elif r.chip == "no_negative":
                score += replay_gain("no_negative", rules, d.drivers, d.constructors, d.boost, got, pd.DataFrame())
        if getattr(r, "official_points", ""):
            score = float(r.official_points)
        rows.append({"season": season, "round": round_, "points": score, "team_value": float(r.team_value),
                     "transfers": r.transfers_in.replace("|", ", "), "chip": r.chip,
                     "lineup": f"{', '.join(d.drivers)} | {', '.join(d.constructors)} | boost {d.boost}"})
    out = pd.DataFrame(rows).sort_values(["season", "round"]).reset_index(drop=True)
    out["cumulative"] = out.groupby("season")["points"].cumsum()
    return out[cols]


def asset_mu(season: int, round_: int, tables=None) -> dict[str, float]:
    """Asset id to this round's expected points (no exclusions)."""
    return {a.id: a.mu for a in assets(season, round_, (), tables)}


def saved_xpts(team: dict, mu: dict, rules: dict, chip: str | None) -> tuple[float | None, str | None]:
    """(expected points, x2 driver) for the saved team with no transfers; x2 on the best driver,
    x3_boost puts the extra multiplier on the best and x2 on the next. None if any asset has no mu."""
    known = sorted((d for d in team["drivers"] if d in mu), key=lambda d: mu[d], reverse=True)
    x3 = chip == "x3_boost" and len(known) > 1
    x2 = known[1] if x3 else known[0] if known else None
    picks = [*team["drivers"], *team["constructors"]]
    if not known or any(a not in mu for a in picks):
        return None, x2
    boost = _rule(rules, "team.boost_multiplier")
    total = sum(mu[a] for a in picks) + (boost - 1) * mu[known[0]]
    if x3:
        total += (_rule(rules, "chips.x3_boost.extra_multiplier") - boost) * mu[known[0]] + (boost - 1) * mu[known[1]]
    return float(total), x2


def _history(n: int) -> pd.DataFrame:
    path = history_path(n)
    if not path.exists():
        return pd.DataFrame(columns=[*HISTORY_COLS, "si", "ri"])
    h = pd.read_csv(path, dtype=str, keep_default_na=False)
    return h.assign(si=h["season"].astype(int), ri=h["round"].astype(int)).sort_values(["si", "ri"])


def swaps_log(n: int) -> list[dict]:
    """Per logged round: assets out and in versus the previous logged lineup (first row: its transfers_in)."""
    out, prev = [], None
    for r in _history(n).itertuples():
        now = [*r.drivers.split("|"), *r.constructors.split("|")]
        if prev is None:
            gone, came = [], [a for a in r.transfers_in.split("|") if a]
        else:
            gone, came = [a for a in prev if a not in now], [a for a in now if a not in prev]
        out.append({"season": r.si, "round": r.ri, "out": gone, "in": came, "chip": r.chip or None,
                    "source": getattr(r, "source", "") or "app"})  # rows before the source column came from the app
        if not (r.chip and load_rules(r.si)["chips"].get(r.chip, {}).get("team_reverts_next_round")):
            prev = now  # a reverting chip (limitless) leaves the old team in place
    return out


def round_source(n: int, season: int, round_: int) -> str | None:
    """How that round's lineup was logged: app, edit or snapshot; None when nothing is logged."""
    h = _history(n)
    row = h[(h["si"] == season) & (h["ri"] == round_)]
    return (row["source"].iloc[-1] if "source" in row and row["source"].iloc[-1] else "app") if len(row) else None


def confirm_round(n: int, season: int, round_: int) -> None:
    """Mark a snapshot row as confirmed by the user (source edit), lineup unchanged."""
    h = _history(n)
    row = h[(h["si"] == season) & (h["ri"] == round_)]
    if not len(row):
        raise ValueError(f"no lineup logged for round {round_}; record it with Edit team")
    _log(n, {**row.iloc[-1].to_dict(), "source": "edit"})


def race_review(n: int, season: int, round_: int, tables=None) -> dict | None:
    """Scored round review for team n: points, what the model expected for that lineup, the best
    team in hindsight under the same budget (team value + bank, no transfer limits), and the model's
    biggest misses. None when the round has no logged lineup or no points yet."""
    t = tables or _tables()
    hist = history_points(n, t)
    row = hist[(hist["season"] == season) & (hist["round"] == round_)]
    if row.empty or pd.isna(row["points"].iloc[0]):
        return None
    logged = _history(n)
    logged = logged[(logged["si"] == season) & (logged["ri"] == round_)].iloc[-1]
    rules = load_rules(season)
    pool = assets(season, round_, (), t)
    mu = {a.id: a.mu for a in pool}
    pts = t["fantasy_points"]
    actual = pts[(pts["season"] == season) & (pts["round"] == round_)].set_index("asset_id")["total"]
    lineup = [*logged["drivers"].split("|"), *logged["constructors"].split("|")]
    boost = _rule(rules, "team.boost_multiplier")
    expected = sum(mu.get(a, 0.0) for a in lineup) + (boost - 1) * mu.get(logged["boost"], 0.0)
    budget = float(logged["team_value"]) + float(logged["bank"] or 0)
    hindsight = optimize([replace(a, mu=float(actual.get(a.id, 0.0))) for a in pool], None,
                         {**rules, "team": {**rules["team"], "budget": budget}})
    misses = sorted(((a.id, a.mu, float(actual.get(a.id, 0.0))) for a in pool),
                    key=lambda m: abs(m[2] - m[1]), reverse=True)[:5]
    return {"points": float(row["points"].iloc[0]), "expected": expected, "chip": row["chip"].iloc[0],
            "best_points": hindsight.expected_points,
            "best_lineup": f"{', '.join(hindsight.drivers)} | {', '.join(hindsight.constructors)} | x2 {hindsight.boost}",
            "misses": misses}


def round_chip(n: int, season: int, round_: int) -> str | None:
    """Chip logged for that round, if any."""
    h = _history(n)
    row = h[(h["si"] == season) & (h["ri"] == round_)]
    return (row["chip"].iloc[-1] or None) if len(row) else None


def advised_chip(advice: str | None, round_: int) -> str | None:
    """Chip the plan_chips advice recommends for round_ ('Round N: <chip>;'), None for none/missing."""
    match = re.search(rf"^Round {round_}: (\w+);", advice or "", re.M)
    return match.group(1) if match and match.group(1) != "none" else None


def final_fix(n: int, results: pd.DataFrame | None = None, tables=None) -> dict | None:
    """Final Fix swap for the next round: worst-qualified owned driver out (boosted drivers kept),
    best-qualified affordable driver in. None until that round's qualifying results exist.
    Rule backtest (2026 r1-21): +51 points over 18 swaps vs no swap; a quali-aware simulator swap lost (-14).
    shortcut: drivers missing from qualifying count as last, upgrade if they turn out to be data gaps."""
    t = tables or _tables()
    season, round_ = next_round(t)
    res = results if results is not None else pd.read_parquet(DATA / "results.parquet")
    q = res[(res["season"] == season) & (res["round"] == round_) & (res["session"] == "qualifying")]
    if q.empty:
        return None
    pos = dict(zip(q["driver_code"], q["position"].astype(int)))
    team, state = load(n), team_state(n, t)
    h = _history(n)
    row = h[(h["si"] == season) & (h["ri"] == round_)]
    boosted = {*row[["boost", "boost3"]].iloc[-1]} - {""} if len(row) else set()
    now = t["prices"][(t["prices"]["season"] == season) & (t["prices"]["round"] == round_)
                      & (t["prices"]["kind"] == "driver")]
    price = dict(zip(now["asset_id"], now["price"].astype(float)))
    last = len(price) + 1
    outs = [d for d in team["drivers"] if d not in boosted]
    out = max(outs, key=lambda d: (pos.get(d, last), d))
    room = state.bank + state.owned[out]
    ins = [d for d, p in price.items() if d not in team["drivers"] and d not in (team.get("exclude") or [])
           and p <= room + 1e-9 and d in pos]
    if not ins:
        return {"round": round_, "out": out, "in": None, "quali": {d: pos.get(d) for d in team["drivers"]}}
    best = min(ins, key=lambda d: (pos[d], d))
    return {"round": round_, "out": out, "out_pos": pos.get(out), "in": best, "in_pos": pos[best],
            "in_price": price[best], "room": room, "boosted": sorted(boosted),
            "quali": {d: pos.get(d) for d in team["drivers"]}}
