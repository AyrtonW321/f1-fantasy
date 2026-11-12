"""Monte Carlo race simulator: sample DNFs, then a Plackett-Luce order of the survivors; score each draw
with src/sim/scoring.py. Output is a predictor frame (OUT_COLS) for run_season.

Split, so nothing counts twice: the simulator gives race finish-position points and the not-classified
penalty (drivers; constructors as the sum of their two drivers' lines). Everything else (qualifying,
sprint, positions gained, overtakes, fastest lap, DotD, pit stops, teamwork) is robust_mu fitted on each
asset's past totals minus its actual position/DNF points (and, with quali=True, qualifying points). Assets the simulator cannot place (first
rounds, drivers absent from the last race, constructors without two entrants) keep plain robust_mu.

quali=True (Phase 4.4) also samples a qualifying order per draw (Plackett-Luce on car strength + qualifying
form), scores it (driver positions, constructor positions + Q2/Q3 teamwork) and feeds it to the race order
as a grid feature, so a driver who qualifies badly in a draw also races worse in that draw.
"""
import numpy as np
import pandas as pd

from src.features.guard import assert_known_before_lock
from src.features.rolling import ASSET, OUT_COLS, _trimmed_mean, robust_mu
from src.models import plackett_luce
from src.models.dnf import DNF_STATUSES, dnf_probability
from src.models.kalman import walkforward_strength
from src.sim.scoring import DriverLine, score_constructor, score_driver

# Jolpica constructor_id -> fantasy asset_id (2026 grid).
CONSTRUCTOR_CODE = {"alpine": "ALP", "aston_martin": "AST", "audi": "AUD", "cadillac": "CAD", "ferrari": "FER",
                    "haas": "HAA", "mclaren": "MCL", "mercedes": "MER", "rb": "VRB", "red_bull": "RED",
                    "williams": "WIL"}
NO_TRACKS = pd.DataFrame(columns=["season", "round", "track_id"])


def race_line(position: int | None, dnf: bool) -> DriverLine:
    return DriverLine("X", "race", position=None if dnf else position, not_classified=dnf)


def point_tables(rules: dict, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Engine points for finishing index 0..n-1 (P1..Pn) and index n = not classified: (driver, constructor)."""
    lines = [race_line(p, False) for p in range(1, n + 1)] + [race_line(None, True)]
    return (np.array([score_driver(rules, l) for l in lines]),
            np.array([score_constructor(rules, [l]) for l in lines]))


def simulate(log_strength: np.ndarray, p_dnf: np.ndarray, n_draws: int, seed: int) -> np.ndarray:
    """Finishing index per draw and entrant, shape (n_draws, m); a DNF gets index m."""
    rng = np.random.default_rng(seed)
    m = np.shape(log_strength)[-1]  # log_strength: (m,) or one row per draw (n_draws, m)
    dnf = rng.random((n_draws, m)) < p_dnf
    order = plackett_luce.sample(np.where(dnf, -np.inf, log_strength), n_draws, rng)
    return np.where(dnf, m, _rank(order))


Q2_CUT, Q3_CUT = 16, 10  # 22-car field: 6 out in Q1, 6 in Q2, top 10 in Q3


def _rank(order: np.ndarray) -> np.ndarray:
    """Entrant indices winner first -> finishing index per entrant."""
    rank = np.empty_like(order)
    np.put_along_axis(rank, order, np.broadcast_to(np.arange(order.shape[1]), order.shape), axis=1)
    return rank


def _teamwork(rules: dict, a, b):
    """Constructor qualifying teamwork points for two finishing indices (0-based) or positions-1; vectorised."""
    key = lambda n: score_constructor(rules, [], n)
    best, worst = np.minimum(a, b), np.maximum(a, b)
    return np.select([worst < Q3_CUT, best < Q3_CUT, worst < Q2_CUT, best < Q2_CUT],
                     [key("both_q3"), key("one_q3"), key("both_q2"), key("one_q2")], key("neither_q2"))


def _perf(rank: np.ndarray, m: int) -> np.ndarray:
    """Standardised position score (higher = better) for 0-based finishing indices in an m-car field."""
    return -(rank - (m - 1) / 2) / np.arange(m).std()


def quali_tables(rules: dict, n: int) -> np.ndarray:
    return np.array([score_driver(rules, DriverLine("X", "qualifying", position=p)) for p in range(1, n + 1)])


def _features(race: pd.DataFrame, kalman: pd.DataFrame, round_: int, drivers: list[str], teams: list[str],
              form_trim: float) -> np.ndarray:
    """[Kalman car strength (team mean of predicted strength), driver form (trimmed mean of earlier perf)]."""
    k = kalman[kalman["round"] == round_].set_index("driver_code")["predicted_strength"].reindex(drivers)
    car = k.groupby(np.array(teams)).transform("mean").fillna(0.0).to_numpy()
    earlier = race[race["round"] < round_]
    form = (earlier.groupby("driver_code")["perf"].apply(lambda s: _trimmed_mean(s, form_trim))
            .reindex(drivers).fillna(0.0).to_numpy())
    return np.column_stack([car, form])


def sim_mu(prices: pd.DataFrame, points: pd.DataFrame, results: pd.DataFrame, races: pd.DataFrame,
           season: int, round_: int, rules: dict, *, trim: float, prior_weight: float, l2: float = 1.0,
           dnf_shrink: float = 5.0, form_trim: float = 0.3, n_draws: int = 2000, seed: int = 0,
           min_rounds: int = 3, quali: bool = False) -> pd.DataFrame:
    lock = races.loc[(races["season"] == season) & (races["round"] == round_), "lock_utc"].iloc[0]
    hist = results[(results["season"] == season) & (results["round"] < round_) & (results["known_at"] <= lock)]
    race = hist[hist["session"] == "race"].copy()
    past_points = points[(points["season"] == season) & (points["round"] < round_)]
    base = robust_mu(prices, past_points, races, season, round_, trim, prior_weight)
    if race["round"].nunique() < min_rounds:  # too little history to fit order strengths
        return base

    # Entrants: target-round priced drivers who raced the last completed round, with that round's team.
    target = prices[(prices["season"] == season) & (prices["round"] == round_) & (prices["kind"] == "driver")]
    last = race[race["round"] == race["round"].max()]
    field = last[last["driver_code"].isin(target["asset_id"])].reset_index(drop=True)
    drivers, teams = field["driver_code"].tolist(), field["constructor_id"].tolist()

    # Kalman sees history plus a placeholder target field; it emits target strengths before any update.
    placeholder = field[["driver_code", "constructor_id"]].assign(
        season=season, round=round_, session="race", position=np.arange(1, len(field) + 1))
    sched = races[(races["season"] == season) & (races["round"] <= round_)].assign(completed=True)
    kalman = walkforward_strength(pd.concat([race, placeholder], ignore_index=True), sched, NO_TRACKS)

    def add_perf(df):  # per-round standardised position score
        g = df.groupby("round")["position"]
        return df.assign(perf=-(df["position"] - g.transform("mean")) / g.transform(lambda s: s.std(ddof=0) or 1.0))

    race = add_perf(race)
    train = [_features(race, kalman, r, g["driver_code"].tolist(), g["constructor_id"].tolist(), form_trim)
             for r, g in race[~race["status"].isin(DNF_STATUSES)].sort_values("position").groupby("round")]
    x = _features(race, kalman, round_, drivers, teams, form_trim)
    m = len(drivers)
    drv_pts, con_pts = point_tables(rules, m)
    p_dnf = dnf_probability(race, drivers, dnf_shrink).to_numpy()
    if quali:
        qual = add_perf(hist[(hist["session"] == "qualifying") & hist["position"].notna()].copy())
        qtrain = [_features(qual, kalman, r, g["driver_code"].tolist(), g["constructor_id"].tolist(), form_trim)
                  for r, g in qual.sort_values("position").groupby("round")]
        qbeta = plackett_luce.fit(qtrain, l2)
        qrank = _rank(plackett_luce.sample(_features(qual, kalman, round_, drivers, teams, form_trim) @ qbeta,
                                           n_draws, np.random.default_rng(seed + 1)))
        qperf = qual.set_index(["round", "driver_code"])["perf"]
        grid = [np.array([qperf.get((r, d), 0.0) for d in g["driver_code"]]) for r, g in
                race[~race["status"].isin(DNF_STATUSES)].sort_values("position").groupby("round")]
        beta = plackett_luce.fit([np.column_stack([f, q]) for f, q in zip(train, grid)], l2)
        rank = simulate(x @ beta[:2] + _perf(qrank, m) * beta[2], p_dnf, n_draws, seed)
    else:
        beta = plackett_luce.fit(train, l2)
        rank = simulate(x @ beta, p_dnf, n_draws, seed)
    pts_d, pts_c = drv_pts[rank], con_pts[rank]
    if quali:  # constructor teamwork needs both of a team's drivers, applied below via pairs
        qd = quali_tables(rules, m)[qrank]
        pts_d = pts_d + qd
        pts_c = pts_c + qd.astype(float)
        ti = np.array(teams)
        for t in set(teams):
            i = np.flatnonzero(ti == t)
            if len(i) == 2:
                pts_c[:, i] += (_teamwork(rules, qrank[:, i[0]], qrank[:, i[1]]) / 2)[:, None]
    sim = {(d, "driver"): v for d, v in zip(drivers, pts_d.mean(axis=0))}
    con = pd.Series(pts_c.mean(axis=0), index=teams).groupby(level=0).agg(["sum", "count"])
    sim |= {(CONSTRUCTOR_CODE[t], "constructor"): s for t, (s, c) in con.iterrows() if c == 2}

    # Residual form: past totals minus each asset's actual position/DNF points.
    dnf = race["status"].isin(DNF_STATUSES)
    lines = [race_line(int(p), bool(f)) for p, f in zip(race["position"], dnf)]
    race["core_d"] = [score_driver(rules, l) for l in lines]
    race["core_c"] = [score_constructor(rules, [l]) for l in lines]
    race["team"] = race["constructor_id"].map(CONSTRUCTOR_CODE)
    if race["team"].isna().any():
        raise KeyError(f"no fantasy id for constructors {sorted(race.loc[race['team'].isna(), 'constructor_id'].unique())}")
    core = pd.concat([
        race[["round", "driver_code", "core_d"]].set_axis(["round", "asset_id", "core"], axis=1).assign(kind="driver"),
        race.groupby(["round", "team"], as_index=False)["core_c"].sum()
            .set_axis(["round", "asset_id", "core"], axis=1).assign(kind="constructor"),
    ])
    if quali:  # actual qualifying points: driver position + constructor positions and Q2/Q3 teamwork
        q = hist[(hist["session"] == "qualifying") & hist["position"].notna()].copy()
        q["team"] = q["constructor_id"].map(CONSTRUCTOR_CODE)
        q["pts"] = [score_driver(rules, DriverLine("X", "qualifying", position=int(p))) for p in q["position"]]
        qcon = q.groupby(["round", "team"]).agg(n=("pts", "size"), pts=("pts", "sum"), lo=("position", "min"),
                                                hi=("position", "max")).reset_index()
        qcon = qcon[qcon["n"] == 2]
        qcon["pts"] += _teamwork(rules, qcon["lo"].to_numpy() - 1, qcon["hi"].to_numpy() - 1)
        qcore = pd.concat([
            q[["round", "driver_code", "pts"]].set_axis(["round", "asset_id", "core"], axis=1).assign(kind="driver"),
            qcon[["round", "team", "pts"]].set_axis(["round", "asset_id", "core"], axis=1).assign(kind="constructor"),
        ])
        core = pd.concat([core, qcore]).groupby(["round", *ASSET], as_index=False)["core"].sum()
    resid = past_points.merge(core, on=["round", *ASSET], how="left")
    resid["total"] = resid["total"] - resid["core"].fillna(0.0)
    rest = robust_mu(prices, resid.drop(columns="core"), races, season, round_, trim, prior_weight)

    out = base.merge(rest[[*ASSET, "mu"]].rename(columns={"mu": "rest"}), on=ASSET)
    simmed = pd.Series([sim.get(k, np.nan) for k in zip(out["asset_id"], out["kind"])], index=out.index)
    out["mu"] = np.where(simmed.notna(), out["rest"] + simmed, out["mu"])
    out = out[OUT_COLS]
    assert_known_before_lock(out, races)
    return out
