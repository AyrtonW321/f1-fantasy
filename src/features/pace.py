from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.features.guard import assert_known_before_lock

MODEL_CONFIG = Path(__file__).resolve().parents[2] / "config" / "model.yaml"
REQUIRED = ("long_run_min_laps", "slow_lap_cutoff", "race_clean_laps_min")
PRACTICE = ["FP1", "FP2", "FP3"]
PRACTICE_COLS = [
    "season", "round", "driver_code", "constructor_id", "long_run_alpha_s",
    "long_run_gap_pct", "long_run_laps", "short_run_gap_pct", "known_at",
]
RACE_COLS = ["driver_code", "constructor_id", "race_gap_pct", "clean_laps", "known_at"]
QUALI_COLS = ["driver_code", "constructor_id", "quali_gap_pct", "known_at"]


def _params(params: dict | None) -> dict:
    """Pace parameters: config/model.yaml `pace` block, overridden by `params`. A missing or null value raises."""
    config = yaml.safe_load(MODEL_CONFIG.read_text(encoding="utf-8")).get("pace") or {}
    merged = {**config, **(params or {})}
    bad = [k for k in REQUIRED if merged.get(k) is None]
    if bad:
        raise ValueError(f"pace parameter(s) missing or null in config/model.yaml: {bad}")
    return merged


def _green_clean_mask(laps: pd.DataFrame) -> pd.Series:
    return (~laps["in_lap"].astype(bool)
            & ~laps["out_lap"].astype(bool)
            & laps["track_status"].astype(str).eq("1")
            & laps["lap_time_s"].notna())


def _fit_stints(fp2: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Per-stint fit on FP2: driver_code, constructor_id, stint, compound, alpha, n_laps."""
    rows = []
    cand = fp2[_green_clean_mask(fp2)].sort_values("lap_number")
    for (driver, stint_no), g in cand.groupby(["driver_code", "stint"], sort=False):
        y = g["lap_time_s"].to_numpy(dtype=float)
        keep = y <= p["slow_lap_cutoff"] * np.median(y)
        y = y[keep]
        n = len(y)
        if n < p["long_run_min_laps"] or n < 2:
            continue
        # Real laps since the first kept lap, so a dropped lap does not compress the slope.
        laps_kept = g["lap_number"].to_numpy(dtype=float)[keep]
        x = laps_kept - laps_kept[0]
        design = np.column_stack([np.ones(n), x])
        if np.linalg.matrix_rank(design) < 2:
            continue
        coef = np.linalg.lstsq(design, y, rcond=None)[0]
        if not np.all(np.isfinite(coef)):
            continue
        first = g.iloc[0]
        rows.append({"driver_code": driver, "constructor_id": first["constructor_id"],
                     "stint": stint_no, "compound": first["compound"],
                     "alpha": float(coef[0]), "n_laps": n})
    return pd.DataFrame(rows, columns=["driver_code", "constructor_id", "stint",
                                       "compound", "alpha", "n_laps"])


def _compound_deltas(stints: pd.DataFrame) -> dict:
    """delta per compound relative to the reference compound (delta_ref = 0)."""
    counts = stints.groupby("compound").size()
    ref = sorted(counts.index, key=lambda c: (-counts[c], c))[0]

    per = {}  # (driver, compound) -> lap-weighted alpha
    for (driver, comp), g in stints.groupby(["driver_code", "compound"]):
        per[(driver, comp)] = float(np.average(g["alpha"], weights=g["n_laps"]))

    deltas = {ref: 0.0}
    for comp in counts.index:
        if comp == ref:
            continue
        diffs = [per[(d, comp)] - per[(d, ref)]
                 for d in {k[0] for k in per}
                 if (d, comp) in per and (d, ref) in per]
        deltas[comp] = float(np.median(diffs)) if diffs else np.nan
    return deltas


def _long_run(fp2: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Per driver: long_run_alpha_s and long_run_laps (NaN where not computable)."""
    stints = _fit_stints(fp2, p)
    empty = pd.DataFrame(columns=["driver_code", "long_run_alpha_s", "long_run_laps"])
    if stints.empty:
        return empty
    deltas = _compound_deltas(stints)
    stints = stints.assign(corr=stints["alpha"] - stints["compound"].map(deltas))
    stints = stints[np.isfinite(stints["corr"])]
    if stints.empty:
        return empty
    rows = []
    for driver, g in stints.groupby("driver_code"):
        rows.append({"driver_code": driver,
                     "long_run_alpha_s": float(np.average(g["corr"], weights=g["n_laps"])),
                     "long_run_laps": int(g["n_laps"].sum())})
    return pd.DataFrame(rows)


def _gap_pct(values: pd.Series) -> pd.Series:
    """100 * (value - field median) / field median; NaN stays NaN."""
    if values.notna().sum() == 0:
        return values.astype(float)
    med = values.median()
    return 100 * (values - med) / med


def practice_pace(laps: pd.DataFrame, sessions: pd.DataFrame, races: pd.DataFrame,
                  season: int, round_: int, params: dict | None = None) -> pd.DataFrame:
    p = _params(params)
    usable = sessions[(sessions["season"] == season) & (sessions["round"] == round_)
                      & sessions["session"].isin(PRACTICE)
                      & sessions["usable_pre_lock"].eq(True)]
    lp = laps[(laps["season"] == season) & (laps["round"] == round_)
              & laps["session"].isin(PRACTICE)]
    lp = lp.merge(usable[["season", "round", "session", "known_at"]]
                  .rename(columns={"known_at": "session_known_at"}),
                  on=["season", "round", "session"], how="inner")
    if lp.empty:
        return pd.DataFrame(columns=PRACTICE_COLS)

    drivers = sorted(lp["driver_code"].unique())
    base = pd.DataFrame(index=pd.Index(drivers, name="driver_code"))
    base["constructor_id"] = lp.groupby("driver_code")["constructor_id"].first()

    lr = _long_run(lp[lp["session"] == "FP2"], p).set_index("driver_code")
    base["long_run_alpha_s"] = lr["long_run_alpha_s"].reindex(drivers).astype(float)
    base["long_run_laps"] = lr["long_run_laps"].reindex(drivers).astype("Int64")
    base["long_run_gap_pct"] = _gap_pct(base["long_run_alpha_s"])

    valid = lp[lp["lap_time_s"].notna() & ~lp["in_lap"].astype(bool) & ~lp["out_lap"].astype(bool)]
    best = valid.groupby("driver_code")["lap_time_s"].min().reindex(drivers)
    base["short_run_gap_pct"] = 100 * (best - best.min()) / best.min() if best.notna().any() else np.nan

    # Conservative: a row is known only once every usable practice session that
    # carries this driver's laps is known.
    base["known_at"] = lp.groupby("driver_code")["session_known_at"].max().reindex(drivers)

    out = base.reset_index()
    out.insert(0, "season", season)
    out.insert(1, "round", round_)
    out = out[PRACTICE_COLS]
    assert_known_before_lock(out, races)
    return out


def race_pace(laps: pd.DataFrame, season: int, round_: int,
              params: dict | None = None) -> pd.DataFrame:
    p = _params(params)
    r = laps[(laps["season"] == season) & (laps["round"] == round_) & (laps["session"] == "R")]
    if r.empty:
        return pd.DataFrame(columns=RACE_COLS)

    drivers = sorted(r["driver_code"].unique())
    clean = r[(r["lap_number"] > 1) & _green_clean_mask(r)]
    counts = clean.groupby("driver_code").size().reindex(drivers, fill_value=0)
    med = clean.groupby("driver_code")["lap_time_s"].median().reindex(drivers)
    med = med.where(counts >= p["race_clean_laps_min"])

    out = pd.DataFrame({
        "driver_code": drivers,
        "constructor_id": r.groupby("driver_code")["constructor_id"].first().reindex(drivers).to_numpy(),
        "race_gap_pct": _gap_pct(med).to_numpy(),
        "clean_laps": counts.to_numpy(),
        "known_at": r["known_at"].max(),
    })
    return out[RACE_COLS]


def quali_pace(laps: pd.DataFrame, season: int, round_: int,
               params: dict | None = None) -> pd.DataFrame:
    q = laps[(laps["season"] == season) & (laps["round"] == round_) & (laps["session"] == "Q")]
    if q.empty:
        return pd.DataFrame(columns=QUALI_COLS)

    drivers = sorted(q["driver_code"].unique())
    best = (q[q["lap_time_s"].notna()].groupby("driver_code")["lap_time_s"].min()
            .reindex(drivers))
    pole = best.min()
    out = pd.DataFrame({
        "driver_code": drivers,
        "constructor_id": q.groupby("driver_code")["constructor_id"].first().reindex(drivers).to_numpy(),
        "quali_gap_pct": (100 * (best - pole) / pole).to_numpy(),
        "known_at": q["known_at"].max(),
    })
    return out[QUALI_COLS]
