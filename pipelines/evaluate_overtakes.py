"""Phase 4.5: overtakes (Poisson) and positions gained (shrunk mean), 2026 walk-forward, two gates.

Gate 1 (count check, rounds 11-20): Poisson overtakes beat a flat field mean on deviance; shrunk gained beats flat 0
on squared error. Shrinkage weights tuned on rounds 1-10 by the same metric. Failing parts drop out.
Gate 2 (fantasy): the surviving term added to robust form must beat 4.1 on MAE and season total.
Run: uv run python pipelines/evaluate_overtakes.py
"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipelines.evaluate_form import SEASON, TUNE_LAST, mae
from src.backtest.walkforward import run_season
from src.features.overtakes import expected, overtakes_mu
from src.features.rolling import robust_mu
from src.features.tracks import load_track_metadata
from src.models import poisson
from src.sim.scoring import load_rules

W_O, W_G = (0.5, 1.0, 3.0, 10.0, 30.0), (1.0, 3.0, 10.0, 30.0, 100.0)


def count_scores(ot, tracks, rounds, w_o, w_g, track=True):
    """(overtake deviance of model, of flat mean; gained SSE of model, of flat 0) over the given rounds."""
    y, mu, flat, g, gh = [], [], [], [], []
    for r in rounds:
        act = ot[(ot["season"] == SEASON) & (ot["round"] == r)]
        e = expected(ot[ot["round"].lt(r) | ot["season"].ne(SEASON)], tracks, SEASON, r, act["asset_id"].tolist(), w_o, w_g, track)
        if e is None:
            continue
        past = ot[(ot["season"] == SEASON) & (ot["round"] < r)]
        y += act["overtakes"].tolist(); mu += e["ov"].tolist(); flat += [past["overtakes"].mean()] * len(act)
        g += act["gained"].tolist(); gh += e["gained"].tolist()
    g, gh = np.array(g, float), np.array(gh)
    return (poisson.deviance(y, np.maximum(mu, 1e-6)), poisson.deviance(y, np.maximum(flat, 1e-6)),
            float(((g - gh) ** 2).mean()), float((g ** 2).mean()))


def main():
    tables = {n: pd.read_parquet(f"data/processed/{n}.parquet")
              for n in ("races", "prices", "fantasy_points", "results", "overtakes")}
    races, prices, points, results, ot = (tables[n] for n in ("races", "prices", "fantasy_points", "results", "overtakes"))
    tracks = load_track_metadata(Path("data/static/tracks.csv"))
    form = yaml.safe_load(Path("config/model.yaml").read_text(encoding="utf-8"))["form"]
    rounds = sorted(races.loc[(races["season"] == SEASON) & races["completed"], "round"].astype(int))
    tune, hold = [r for r in rounds if r <= TUNE_LAST], [r for r in rounds if r > TUNE_LAST]
    rules = load_rules(SEASON)

    w_o = min(W_O, key=lambda w: count_scores(ot, tracks, tune, w, 1.0)[0])
    w_g = min(W_G, key=lambda w: count_scores(ot, tracks, tune, 1.0, w)[2])
    dev, dev_flat, sse, sse_flat = count_scores(ot, tracks, hold, w_o, w_g)
    dev_nt = count_scores(ot, tracks, hold, w_o, w_g, track=False)[0]
    use_ov, use_g = dev < dev_flat, sse < sse_flat
    lines = [f"# Phase 4.5: overtakes and positions gained ({SEASON})", "",
             f"Weights tuned on rounds 1-{TUNE_LAST}: w_o={w_o}, w_g={w_g}. Gate 1 on rounds {hold[0]}-{hold[-1]}.", "",
             "## Gate 1: count check", "", "| Target | Model | Baseline | Pass |", "|---|---|---|---|",
             f"| Overtakes, Poisson deviance (track effect) | {dev:.3f} | {dev_flat:.3f} (flat field mean) | {'yes' if use_ov else 'no'} |",
             f"| Overtakes, Poisson deviance (no track effect) | {dev_nt:.3f} | {dev_flat:.3f} (flat field mean) | info |",
             f"| Gained, squared error | {sse:.3f} | {sse_flat:.3f} (flat 0) | {'yes' if use_g else 'no'} |", ""]
    if use_ov or use_g:
        pred = lambda s, r: overtakes_mu(prices, points, ot, tracks, results, races, s, r, rules, **form,
                                         w_o=w_o, w_g=w_g, use_ov=use_ov, use_g=use_g)
        rows = []
        for name, f in ((f"robust form (4.1) trim={form['trim']} prior_weight={form['prior_weight']}",
                         lambda s, r: robust_mu(prices, points, races, s, r, **form)),
                        (f"form + overtakes={use_ov} gained={use_g}", pred)):
            rows.append((name, mae(f, tune, points), mae(f, rounds, points), run_season(SEASON, tables, rules, f).total))
        beats = rows[1][2] < rows[0][2] and rows[1][3] > rows[0][3]
        lines += ["## Gate 2: fantasy points", "", "| Predictor | MAE r1-10 | MAE all | Season total |", "|---|---|---|---|"]
        lines += [f"| {n} | {a:.2f} | {b:.2f} | {t:.0f} |" for n, a, b, t in rows]
        lines += ["", f"Beats 4.1 on both MAE (all rounds) and season total: {'yes' if beats else 'no'}"]
    else:
        lines += ["Both parts fail gate 1; gate 2 not run."]
    Path("reports/phase4_overtakes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
