"""Build the auditable FP2 pace feature table from normalized FastF1 data."""

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.pace import fp2_longrun_pace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, action="append", dest="seasons",
                        help="season to include; defaults to 2025 and 2026")
    args = parser.parse_args()
    seasons = args.seasons or [2025, 2026]
    root = Path("data/processed")
    laps = pd.read_parquet(root / "laps.parquet")
    sessions = pd.read_parquet(root / "sessions.parquet")
    races = pd.read_parquet(root / "races.parquet")
    results = pd.read_parquet(root / "results.parquet")
    races = races.loc[races["season"].isin(seasons)].copy()
    results = results.loc[results["season"].isin(seasons)].copy()
    sessions = sessions.loc[sessions["season"].isin(seasons)].copy()
    laps = laps.loc[laps["season"].isin(seasons)].copy()
    inventory_path = root / "fastf1_session_inventory.parquet"
    expected_sessions = pd.read_parquet(inventory_path) if inventory_path.exists() else None
    if expected_sessions is not None:
        expected_sessions = expected_sessions.loc[expected_sessions["season"].isin(seasons)].copy()
    pace = fp2_longrun_pace(laps, sessions, races, results, expected_sessions=expected_sessions)
    root.mkdir(parents=True, exist_ok=True)
    pace.to_parquet(root / "pace.parquet", index=False)
    counts = pace.groupby(["season", "fit_status"], dropna=False).size().to_dict()
    print(f"wrote {len(pace)} pace/status rows; counts={counts}")

    coverage = pace.pivot_table(index=["season", "round"], columns="fit_status", values="driver_code",
                                aggfunc="count", fill_value=0)
    usable = pace.groupby(["season", "round"])["usable_prelock"].sum().rename("usable_prelock")
    entrants = pace.groupby(["season", "round"])["driver_code"].nunique().rename("entrants")
    coverage = coverage.join([usable, entrants]).fillna(0).astype(int).reset_index()
    report = [
        "# FP2 long-run pace coverage", "",
        "Counts only; driver-level pace values remain in the ignored processed Parquet table.", "",
        "## Status counts by season", "",
        "| Season | Status | Entrants |", "|---:|---|---:|",
    ]
    report.extend(f"| {season} | {status} | {int(count)} |"
                  for (season, status), count in sorted(counts.items()))
    estimates = pace.loc[pace["pace_seconds"].notna()]
    fp2_expected = pace.loc[~pace["fit_status"].eq("no_fp2_session")]
    report += ["", "## Fit diagnostics", "",
               "Estimates with `rank_deficient` status retain the centered reference pace; their unidentified slopes are null. `low sample` counts estimates based on fewer than eight laps.", "",
               "| Season | FP2 entrant rows | Pre-lock estimates | Coverage | RMSE median / p95 / max (s) | RMSE > 5s | Low sample | Slow laps removed |",
               "|---:|---:|---:|---:|---|---:|---:|---:|"]
    for season in sorted(pace["season"].unique()):
        expected_season = fp2_expected.loc[fp2_expected["season"].eq(season)]
        fitted = estimates.loc[estimates["season"].eq(season)]
        usable_count = int(expected_season["usable_prelock"].sum())
        expected_count = len(expected_season)
        coverage_pct = 100 * usable_count / expected_count if expected_count else 0.0
        if fitted.empty:
            rmse = "—"
        else:
            rmse = " / ".join(f"{fitted['rmse_seconds'].quantile(q):.2f}" for q in (0.5, 0.95, 1.0))
        report.append(
            f"| {int(season)} | {expected_count} | {usable_count} | {coverage_pct:.1f}% | {rmse} | "
            f"{int(fitted['rmse_seconds'].gt(5).sum())} | {int(fitted['observations'].lt(8).sum())} | "
            f"{int(expected_season['outlier_laps'].sum())} |"
        )
    report += ["", "## Coverage by round", "",
               "`usable_prelock` counts estimates whose FP2 data was available by the current lineup-lock cutoff.", "",
               "| Season | Round | Entrants | Usable pre-lock | Status counts |",
               "|---:|---:|---:|---:|---|"]
    status_columns = [column for column in coverage.columns
                      if column not in {"season", "round", "usable_prelock", "entrants"}]
    report.extend(
        f"| {int(row.season)} | {int(row.round)} | {int(row.entrants)} | {int(row.usable_prelock)} | "
        + ", ".join(f"{column}: {int(getattr(row, column))}" for column in status_columns if getattr(row, column))
        + " |"
        for row in coverage.itertuples(index=False)
    )
    Path("reports").mkdir(exist_ok=True)
    Path("reports/phase3_pace_coverage.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("wrote reports/phase3_pace_coverage.md")


if __name__ == "__main__":
    main()
