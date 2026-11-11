"""Plan 2026 chips for rounds 21-23 from config/my_team.yaml.

The team file uses drivers, constructors, bank and free_transfers; add a
``chips_left: [limitless, wildcard, extra_drs, no_negative, autopilot, final_fix]``
list containing only chips still available. If the private file is absent, the
example team is used and the output is clearly marked as illustrative.
"""
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.features.rolling import robust_mu
from src.optimize.chips import plan_chips
from src.sim.scoring import load_rules


ROOT = Path(__file__).resolve().parents[1]


def main():
    config = ROOT / "config"
    team_path = config / "my_team.yaml"
    example = not team_path.exists()
    team_path = config / "my_team.example.yaml" if example else team_path
    team = yaml.safe_load(team_path.read_text(encoding="utf-8"))
    rules = load_rules(2026)
    if example:
        team.setdefault("chips_left", list(rules["chips"]))
    elif "chips_left" not in team:
        raise SystemExit(f"{team_path} must include chips_left: [chip ids still available]")
    tables = {n: pd.read_parquet(ROOT / f"data/processed/{n}.parquet")
              for n in ("races", "prices", "fantasy_points")}
    form = yaml.safe_load((config / "model.yaml").read_text(encoding="utf-8"))["form"]
    price_rounds = tables["prices"].loc[tables["prices"]["season"] == 2026, "round"]
    price_source = {r: r if r in set(price_rounds) else int(price_rounds.max()) for r in (21, 22, 23)}

    def predictor(season, round_):
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

    plan = plan_chips(predictor, team, rules, [21, 22, 23])
    print("ILLUSTRATIVE: config/my_team.example.yaml" if example else "Team: config/my_team.yaml")
    stale = sorted({source for round_, source in price_source.items() if source != round_})
    if stale:
        print(f"Market prices are proxied from latest available 2026 round {max(stale)}.")
    for row in plan:
        d = row["decision"]
        print(f"Round {row['round']}: {row['chip'] or 'none'}; expected gain {row['gain']:.1f}; "
              f"drivers {', '.join(d.drivers)}; constructors {', '.join(d.constructors)}; "
              f"boost {d.boost}")


if __name__ == "__main__":
    main()
