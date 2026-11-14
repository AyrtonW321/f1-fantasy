"""Team-file logic for the Streamlit app (Phase 8.4). The app holds no game logic; it calls these.

Paths are project-relative to ROOT so the app works from any start folder. Writes always back up the
old team file to config/backup/ first. History (config/history/team_N.csv) is what the timeline reads.
"""
import csv
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
from src.optimize.ilp import Asset, Decision, InfeasibleTeam, TeamState, next_state, optimize
from src.sim.scoring import _rule, load_rules

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
DATA = ROOT / "data" / "processed"
HISTORY_COLS = ["season", "round", "drivers", "constructors", "boost", "boost3", "chip",
                "transfers_in", "penalty_transfers", "bank", "team_value"]


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
    return int(left["season"].iloc[0]), int(left["round"].iloc[0])


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
    out = pd.concat([keep, pd.DataFrame([{k: row.get(k, "") for k in HISTORY_COLS}]).astype(str)])
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
    now = t["prices"][(t["prices"]["season"] == season) & (t["prices"]["round"] == round_)]
    prices = dict(zip(now["asset_id"], now["price"].astype(float)))
    state = load_team(team_path(n), prices)
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
             "team_value": decision.cost})
    return new


def top_teams(state: TeamState | None, budget: float = 100.0, n: int = 5, exclude=(),
              season: int | None = None, round_: int | None = None, tables=None) -> list[Decision]:
    """Best n distinct teams for the next round, best first. state=None: overall best under `budget`
    (no transfer limits); otherwise teams reachable from state (its own budget, transfer penalties)."""
    t = tables or _tables()
    if season is None or round_ is None:
        season, round_ = next_round(t)
    rules = load_rules(season)
    if state is None:
        rules = {**rules, "team": {**rules["team"], "budget": budget}}
    pool = assets(season, round_, exclude, t)
    found: list[Decision] = []
    for _ in range(n):
        try:
            found.append(optimize(pool, state, rules, forbid=[[*d.drivers, *d.constructors] for d in found]))
        except InfeasibleTeam:
            break
    return found


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
        rows.append({"season": season, "round": round_, "points": score, "team_value": float(r.team_value),
                     "transfers": r.transfers_in.replace("|", ", "), "chip": r.chip,
                     "lineup": f"{', '.join(d.drivers)} | {', '.join(d.constructors)} | boost {d.boost}"})
    out = pd.DataFrame(rows).sort_values(["season", "round"]).reset_index(drop=True)
    out["cumulative"] = out.groupby("season")["points"].cumsum()
    return out[cols]
