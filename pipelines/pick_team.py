"""Pick the team for the next unlocked round from robust season form.

Reads config/my_team.yaml when present (owned assets, bank, free transfers);
otherwise picks from scratch with the starting budget. Chips not handled yet.
Run: uv run python pipelines/pick_team.py [--season 2026] [--round 21]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.features.rolling import robust_mu
from src.optimize.ilp import Asset, TeamState, optimize
from src.sim.scoring import load_rules

TEAM_FILE = Path("config/my_team.yaml")


def load_team(path: Path, prices: dict[str, float]) -> TeamState:
    team = yaml.safe_load(path.read_text(encoding="utf-8"))
    owned_ids = [*team["drivers"], *team["constructors"]]
    unknown = [a for a in owned_ids if a not in prices]
    if unknown:
        raise ValueError(f"{path}: assets not in this round's prices: {unknown}")
    return TeamState(owned={a: prices[a] for a in owned_ids}, bank=float(team["bank"]),
                     free_transfers=int(team["free_transfers"]))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--round", type=int, help="default: first round not yet completed")
    args = parser.parse_args(argv)

    tables = {n: pd.read_parquet(f"data/processed/{n}.parquet") for n in ("races", "prices", "fantasy_points")}
    races = tables["races"]
    season_races = races[races["season"] == args.season]
    round_ = args.round or int(season_races.loc[~season_races["completed"], "round"].min())
    form = yaml.safe_load(Path("config/model.yaml").read_text(encoding="utf-8"))["form"]
    mu = robust_mu(tables["prices"], tables["fantasy_points"], races, args.season, round_,
                   form["trim"], form["prior_weight"])
    if mu.empty:
        raise SystemExit(f"no prices for {args.season} round {round_}; run the official snapshot first")
    assets = [Asset(id=r.asset_id, kind=r.kind, price=float(r.price), mu=float(r.mu)) for r in mu.itertuples()]
    state = load_team(TEAM_FILE, {a.id: a.price for a in assets}) if TEAM_FILE.exists() else None
    d = optimize(assets, state, load_rules(args.season))

    slug = season_races.loc[season_races["round"] == round_, "slug"].iloc[0]
    by_id = mu.set_index("asset_id")
    print(f"{args.season} round {round_} ({slug}); team from {'my_team.yaml' if state else 'scratch, budget cap'}")
    for a in [*d.drivers, *d.constructors]:
        tag = " (2x boost)" if a == d.boost else ""
        print(f"  {a:4} {by_id.loc[a, 'kind']:11} price {by_id.loc[a, 'price']:5.1f}  expected {by_id.loc[a, 'mu']:5.1f}{tag}")
    print(f"cost {d.cost:.1f} of budget {d.budget:.1f}; transfers in: {', '.join(d.transfers_in) or '-'}; "
          f"penalty transfers: {d.penalty_transfers}")


if __name__ == "__main__":
    main()
