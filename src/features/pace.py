"""Pre-lock FP2 long-run pace estimates with explicit coverage and fit diagnostics."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.features.guard import assert_known_before_lock


PACE_COLUMNS = [
    "season", "round", "driver_code", "pace_seconds", "observations", "stint_count", "compounds",
    "tyre_age_min", "tyre_age_max", "beta_seconds_per_lap", "gamma_by_compound", "rmse_seconds",
    "lap_reference", "tyre_age_reference", "outlier_laps", "fit_status", "known_at", "usable_prelock",
]


def _valid_laps(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty:
        columns = set(laps.columns) | {
            "season", "round", "driver_code", "lap_time_s", "compound", "tyre_age", "lap_number", "stint",
        }
        return pd.DataFrame(columns=sorted(columns))
    data = laps.copy()
    data = data.loc[pd.to_numeric(data.get("lap_time_s"), errors="coerce").between(40, 200)]
    if "is_accurate" in data:
        data = data.loc[data["is_accurate"].fillna(False).astype(bool)]
    if "deleted" in data:
        data = data.loc[~data["deleted"].astype("boolean").fillna(False)]
    if "track_status" in data:
        status = data["track_status"].astype("string")
        green = status.isna() | status.str.fullmatch(r"1+").fillna(False)
        data = data.loc[green]
    for pit in ("pit_in_time", "pit_out_time"):
        if pit in data:
            data = data.loc[data[pit].isna()]
    data = data.loc[data["compound"].notna() & data["tyre_age"].notna() & data["lap_number"].notna()]
    data["lap_time_s"] = pd.to_numeric(data["lap_time_s"], errors="coerce")
    data["tyre_age"] = pd.to_numeric(data["tyre_age"], errors="coerce")
    data["lap_number"] = pd.to_numeric(data["lap_number"], errors="coerce")
    return data.dropna(subset=["lap_time_s", "tyre_age", "lap_number"])


def _fit_driver(driver_laps: pd.DataFrame, min_laps: int) -> dict:
    eligible = []
    outlier_laps = 0
    for _, stint in driver_laps.groupby("stint", dropna=False, sort=True):
        stint = stint.drop_duplicates("lap_number").sort_values("lap_number")
        lap_times = stint["lap_time_s"].to_numpy(dtype=float)
        median = float(np.median(lap_times))
        mad = float(np.median(np.abs(lap_times - median)))
        # A handful of accurate-but-very-slow laps can inflate MAD enough to
        # keep red-flag/traffic laps in the fit. Anchor the upper cutoff on the
        # faster half of the stint and cap the MAD allowance at ten seconds.
        lower_half = np.sort(lap_times)[: max(2, int(np.ceil(len(lap_times) / 2)))]
        baseline = float(np.median(lower_half))
        threshold = max(3.0, min(4.5 * 1.4826 * mad, 10.0))
        inliers = stint["lap_time_s"] <= baseline + threshold
        outlier_laps += int((~inliers).sum())
        stint = stint.loc[inliers]
        if len(stint) >= min_laps:
            eligible.append(stint)
    if not eligible:
        return {"fit_status": "no_usable_longrun", "outlier_laps": outlier_laps}
    data = pd.concat(eligible, ignore_index=True)
    compounds = sorted(data["compound"].astype(str).unique())
    lap_center = float(data["lap_number"].median())
    data["lap_centered"] = data["lap_number"] - lap_center
    centered_ages = {}
    columns = [np.ones(len(data)), data["lap_centered"].to_numpy(dtype=float)]
    for compound in compounds:
        mask = data["compound"].astype(str).eq(compound)
        center = float(data.loc[mask, "tyre_age"].median())
        centered_ages[compound] = center
        age_effect = np.zeros(len(data), dtype=float)
        age_effect[mask.to_numpy()] = data.loc[mask, "tyre_age"].to_numpy(dtype=float) - center
        columns.append(age_effect)
    matrix = np.column_stack(columns)
    y = data["lap_time_s"].to_numpy(dtype=float)
    coefficients, _, rank, _ = np.linalg.lstsq(matrix, y, rcond=None)
    residuals = y - matrix @ coefficients
    status = "fit" if rank == matrix.shape[1] else "rank_deficient"
    # When lap number and tyre age are collinear, the reference-condition pace (intercept)
    # remains estimable; report the unidentified slopes as diagnostics rather than inventing them.
    gammas = {compound: float(coefficients[i + 2]) if rank == matrix.shape[1] else None
              for i, compound in enumerate(compounds)}
    return {
        "fit_status": status,
        "pace_seconds": float(coefficients[0]),
        "observations": int(len(data)),
        "stint_count": int(len(eligible)),
        "compounds": ",".join(compounds),
        "tyre_age_min": float(data["tyre_age"].min()),
        "tyre_age_max": float(data["tyre_age"].max()),
        "beta_seconds_per_lap": float(coefficients[1]) if rank == matrix.shape[1] else None,
        "gamma_by_compound": json.dumps(gammas, sort_keys=True),
        "rmse_seconds": float(np.sqrt(np.mean(residuals ** 2))),
        "lap_reference": lap_center,
        "tyre_age_reference": json.dumps(centered_ages, sort_keys=True),
        "outlier_laps": outlier_laps,
    }


def _known_at(session: pd.Series, session_laps: pd.DataFrame) -> pd.Timestamp:
    start = pd.to_datetime(session.get("scheduled_start_utc"), utc=True, errors="coerce")
    end_seconds = pd.to_numeric(pd.Series([session.get("session_end_time")]), errors="coerce").iloc[0]
    if pd.isna(end_seconds) and not session_laps.empty and "session_time" in session_laps:
        end_seconds = pd.to_numeric(session_laps["session_time"], errors="coerce").max()
    if pd.isna(start) or pd.isna(end_seconds):
        return pd.NaT
    return start + pd.to_timedelta(float(end_seconds), unit="s")


def fp2_longrun_pace(
    laps: pd.DataFrame,
    sessions: pd.DataFrame,
    races: pd.DataFrame,
    results: pd.DataFrame | None = None,
    *,
    min_laps: int = 4,
    enforce_prelock: bool = True,
    expected_sessions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return one FP2 pace/status row per expected race entrant and weekend.

    Estimates with ``known_at`` after the fantasy lock are retained for coverage
    diagnostics but marked unusable as pre-lock predictors.
    """
    if min_laps < 2:
        raise ValueError("min_laps must be at least 2")
    fp2 = laps.loc[laps["session_code"].eq("FP2")].copy() if not laps.empty else laps.copy()
    valid = _valid_laps(fp2)
    fp2_sessions = sessions.loc[sessions["session_code"].eq("FP2")].copy() if not sessions.empty else sessions.copy()
    if results is None:
        expected = valid[["season", "round", "driver_code"]].drop_duplicates() if not valid.empty else pd.DataFrame(
            columns=["season", "round", "driver_code"])
    else:
        expected = results.loc[results["session"].eq("race"), ["season", "round", "driver_code"]].drop_duplicates()
    rows = []
    for event in races.itertuples(index=False):
        entrants = expected.loc[(expected["season"] == event.season) & (expected["round"] == event.round),
                                "driver_code"].dropna().astype(str).sort_values().unique()
        session_row = fp2_sessions.loc[(fp2_sessions["season"] == event.season)
                                       & (fp2_sessions["round"] == event.round)]
        expected_fp2 = (expected_sessions.loc[
            expected_sessions["season"].eq(event.season) & expected_sessions["round"].eq(event.round)
            & expected_sessions["session_code"].eq("FP2")
        ] if expected_sessions is not None else pd.DataFrame())
        event_laps = valid.loc[(valid["season"] == event.season) & (valid["round"] == event.round)]
        known_at = _known_at(session_row.iloc[0], event_laps) if not session_row.empty else pd.NaT
        lock = pd.to_datetime(event.lock_utc, utc=True)
        for driver in entrants:
            driver_laps = event_laps.loc[event_laps["driver_code"].astype(str).eq(driver)]
            if not session_row.empty:
                fit = _fit_driver(driver_laps, min_laps)
            elif expected_sessions is not None and not expected_fp2.empty:
                fit = {"fit_status": "session_not_loaded"}
            else:
                fit = {"fit_status": "no_fp2_session"}
            status = fit["fit_status"]
            usable = status in {"fit", "rank_deficient"} and not pd.isna(known_at) and known_at <= lock
            if status in {"fit", "rank_deficient"} and not usable:
                status = "after_lock" if not pd.isna(known_at) and known_at > lock else "unknown_availability"
            rows.append({
                "season": int(event.season), "round": int(event.round), "driver_code": driver,
                "pace_seconds": fit.get("pace_seconds"), "observations": fit.get("observations", 0),
                "stint_count": fit.get("stint_count", 0), "compounds": fit.get("compounds", ""),
                "tyre_age_min": fit.get("tyre_age_min"), "tyre_age_max": fit.get("tyre_age_max"),
                "beta_seconds_per_lap": fit.get("beta_seconds_per_lap"),
                "gamma_by_compound": fit.get("gamma_by_compound", "{}"),
                "rmse_seconds": fit.get("rmse_seconds"), "lap_reference": fit.get("lap_reference"),
                "tyre_age_reference": fit.get("tyre_age_reference", "{}"),
                "outlier_laps": fit.get("outlier_laps", 0), "fit_status": status,
                # NaT when FP2 timing unknown; stamping lock_utc would pass the leakage guard falsely.
                "known_at": known_at,
                "usable_prelock": bool(usable),
            })
    output = pd.DataFrame(rows, columns=PACE_COLUMNS)
    output["known_at"] = pd.to_datetime(output["known_at"], utc=True, errors="coerce")
    if enforce_prelock and not output.empty:
        prelock = output.loc[output["usable_prelock"]]
        assert_known_before_lock(prelock, races)
    return output
