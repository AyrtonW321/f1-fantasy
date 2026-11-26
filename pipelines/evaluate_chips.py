"""Hindsight chip backtest 2023-2026 (run: uv run python -m pipelines.evaluate_chips): what each chip would have added in each round, robust_mu walk-forward team.

2023-2025 chip rules are null in config, so 2026's chip section is borrowed (assumption: 2027 chips = 2026 chips).
Wildcard gain = points over the chip round plus the next 2 rounds vs. the no-chip path. Final Fix is not replayed.
"""
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.backtest.walkforward import _actual_points, run_season
from src.features.rolling import robust_mu
from src.optimize.chip_history import replay_gain
from src.optimize.chips import estimate_chip
from src.optimize.ilp import Asset, next_state, optimize
from src.sim.scoring import load_rules

T = {n: pd.read_parquet(ROOT / f"data/processed/{n}.parquet") for n in ("races", "prices", "fantasy_points")}
form = yaml.safe_load((ROOT / "config/model.yaml").read_text(encoding="utf-8"))["form"]
chips26 = load_rules(2026)["chips"]
pred = lambda s, r: robust_mu(T["prices"], T["fantasy_points"], T["races"], s, r, form["trim"], form["prior_weight"])
WC_HORIZON = 3

rows = []
for season in (2023, 2024, 2025, 2026):
    rules = load_rules(season)
    rules["chips"] = chips26
    base = run_season(season, T, rules, pred)
    races = T["races"][T["races"]["season"] == season].set_index("round")
    pts = T["fantasy_points"]
    state = None
    for i, rr in enumerate(base.rounds):
        r, d = rr.round, rr.decision
        frame = pred(season, r)
        assets = [Asset(a.asset_id, a.kind, float(a.price), float(a.mu)) for a in frame.itertuples()]
        p = pts[(pts["season"] == season) & (pts["round"] == r)]
        g = {"season": season, "round": r, "slug": races.loc[r, "slug"], "sprint": bool(races.loc[r, "sprint"]),
             "base": rr.actual_points}
        g["autopilot"] = replay_gain("autopilot", rules, d.drivers, d.constructors, d.boost, p, frame)
        g["no_negative"] = replay_gain("no_negative", rules, d.drivers, d.constructors, d.boost, p, frame)
        if state is not None and i >= 1:  # limitless/wildcard/x3 need a held team; skip round 1 (also locked there)
            owned = list(state.owned)
            tm = {"drivers": [a for a in owned if a in {x.id for x in assets if x.kind == "driver"}],
                  "constructors": [a for a in owned if a in {x.id for x in assets if x.kind == "constructor"}],
                  "bank": state.bank, "free_transfers": state.free_transfers}
            try:
                for chip in ("x3_boost", "limitless"):
                    _, cand, _ = estimate_chip(assets, tm, rules, chip, d)
                    if cand is None:
                        continue
                    act = _actual_points(season, r, cand, pts, rules)
                    if chip == "x3_boost":
                        top = p[(p["kind"] == "driver") & (p["asset_id"] == cand.boost3)]["total"].sum()
                        act += (chips26["x3_boost"]["extra_multiplier"] - 1) * float(top)
                    else:
                        act += rules["transfers"]["penalty"] * cand.penalty_transfers  # limitless: no penalty
                    g[chip] = act - rr.actual_points
                _, wc, _ = estimate_chip(assets, tm, rules, "wildcard", d)
                if wc is not None:
                    gain = _actual_points(season, r, wc, pts, rules) + rules["transfers"]["penalty"] * wc.penalty_transfers \
                        - rr.actual_points
                    st = next_state(state, wc, rules)
                    for nxt in base.rounds[i + 1:i + WC_HORIZON]:
                        fa = [Asset(a.asset_id, a.kind, float(a.price), float(a.mu)) for a in pred(season, nxt.round).itertuples()]
                        dd = optimize(fa, st, rules)
                        gain += _actual_points(season, nxt.round, dd, pts, rules) - nxt.actual_points
                        st = next_state(st, dd, rules)
                    g["wildcard"] = gain
            except Exception as exc:  # a missing asset price etc.; keep going
                g["error"] = str(exc)[:80]
        rows.append(g)
        state = next_state(state, d, rules)
    print(season, "done", flush=True)

out = pd.DataFrame(rows)
C = ["limitless", "x3_boost", "no_negative", "autopilot", "wildcard"]
md = ["# Chip backtest 2023-2026 (hindsight, robust_mu team)", "",
      "Mean points a chip would have added in a round. 2026 chip rules used for every season.",
      f"Wildcard counts its round plus the next {WC_HORIZON - 1}. Final Fix not replayed (rule backtest: +51 over 18 swaps, 2026).",
      "", "## Overall and sprint vs normal", "", "```text", out.groupby("sprint")[C].mean().round(1).to_string(), "```", "",
      "Overall: " + ", ".join(f"{c} {out[c].mean():.1f}" for c in C), "",
      "## Wildcard by round", "", "```text",
      out.groupby(pd.cut(out["round"], [0, 6, 12, 18, 25]), observed=True)["wildcard"].mean().round(1).to_string(), "```", "",
      "## Best tracks per chip (mean over seasons)", ""]
by = out.groupby("slug")[C].mean()
md += [f"- {c}: " + ", ".join(f"{k} {v:.0f}" for k, v in by[c].nlargest(6).items()) for c in C]
(ROOT / "reports" / "chip_backtest.md").write_text(chr(10).join(md) + chr(10), encoding="utf-8")
print("wrote reports/chip_backtest.md")
