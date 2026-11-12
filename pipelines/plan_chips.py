"""Plan chips for the rest of the season (default: the season with unplayed rounds) from config/my_team.yaml.

The team file uses drivers, constructors, bank and free_transfers; add a
``chips_left: [limitless, wildcard, x3_boost, no_negative, autopilot, final_fix]``
list containing only chips still available. If the private file is absent, the
example team is used and the output is clearly marked as illustrative.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipelines.pick_team import exclude
from src.features.rolling import robust_mu
from src.optimize.chip_history import historical_value
from src.optimize.chips import plan_chips
from src.sim.scoring import load_rules


ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, help="default: season with rounds still to play")
    parser.add_argument("--team", type=int, help="read config/my_team_N.yaml instead of my_team.yaml")
    args = parser.parse_args(argv)
    config = ROOT / "config"
    team_path = config / (f"my_team_{args.team}.yaml" if args.team else "my_team.yaml")
    example = not team_path.exists()
    team_path = config / "my_team.example.yaml" if example else team_path
    team = yaml.safe_load(team_path.read_text(encoding="utf-8"))
    tables = {n: pd.read_parquet(ROOT / f"data/processed/{n}.parquet")
              for n in ("races", "prices", "fantasy_points")}
    races = tables["races"]
    season = args.season or int(races.loc[~races["completed"], "season"].min())
    rounds = sorted(races.loc[(races["season"] == season) & ~races["completed"], "round"].astype(int))
    if not rounds:
        raise SystemExit(f"no rounds left to play in {season}")
    rules = load_rules(season)
    if example:
        team.setdefault("chips_left", list(rules["chips"]))
    elif "chips_left" not in team:
        raise SystemExit(f"{team_path} must include chips_left: [chip ids still available]")
    form = yaml.safe_load((config / "model.yaml").read_text(encoding="utf-8"))["form"]
    price_rounds = tables["prices"].loc[tables["prices"]["season"] == season, "round"]
    price_source = {r: r if r in set(price_rounds) else int(price_rounds.max()) for r in rounds}

    def raw_predictor(season, round_):
        prices = tables["prices"]
        if not ((prices["season"] == season) & (prices["round"] == round_)).any():
            earlier = prices[(prices["season"] == season) & (prices["round"] < round_)]
            if earlier.empty:
                return pd.DataFrame(columns=["season", "round", "asset_id", "kind", "price", "mu", "known_at"])
            latest = int(earlier["round"].max())
            proxy = earlier[earlier["round"] == latest].copy()
            proxy["round"] = round_
            prices = pd.concat([prices, proxy], ignore_index=True)
        return robust_mu(prices, tables["fantasy_points"], tables["races"], season, round_,
                         form["trim"], form["prior_weight"])

    def predictor(season, round_):
        mu = raw_predictor(season, round_)
        return exclude(mu, team.get("exclude", [])) if len(mu) else mu

    replay = lambda chip, d, r: historical_value(chip, rules, d.drivers, d.constructors, d.boost,
                                                 tables["fantasy_points"], tables["races"], raw_predictor, season, r)
    plan = plan_chips(predictor, team, rules, rounds, season, replay=replay)
    print("ILLUSTRATIVE: config/my_team.example.yaml" if example else f"Team: config/{team_path.name}")
    stale = sorted({source for round_, source in price_source.items() if source != round_})
    if stale:
        print(f"Market prices are proxied from latest available {season} round {max(stale)}.")
    for row in plan:
        d = row["decision"]
        print(f"Round {row['round']}: {row['chip'] or 'none'}; expected gain {row['gain']:.1f}; "
              f"drivers {', '.join(d.drivers)}; constructors {', '.join(d.constructors)}; "
              f"boost {d.boost}")
    skipped = sorted({c for row in plan for c in row.get("unsupported", {})})
    if skipped:
        print(f"Not valued: {', '.join(skipped)}. "
              "Their gain depends on qualifying results, so the plan cannot rank them (play after qualifying).")


if __name__ == "__main__":
    main()
