"""Weekly round report: pull data, rebuild tables, pick every team, plan chips, write the report.

Task Scheduler runs this daily (Phase 7). It skips unless the next lock is under 48 hours away
and no successful report exists for that round; --force always runs and rewrites the report.
Output: reports/round_{season}_{round:02d}.md and reports/weekly_update.log.
Never touches the data key: data/raw stays plaintext locally and sealing stays manual.
Run: uv run python -m pipelines.weekly_update [--force]
"""
import argparse
import contextlib
import io
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipelines import build_data, pick_team, plan_chips  # noqa: E402
from src.ingest.community_pull import pull_mzafram, pull_tracing_insights  # noqa: E402
from src.ingest.fantasy_scrape import snapshot_official  # noqa: E402
from src.ingest.jolpica_pull import pull_jolpica  # noqa: E402
from src.ui import logic  # noqa: E402

WINDOW = timedelta(hours=48)
REPORTS = Path("reports")
RAW = Path("data/raw")
TI_TAGS = "https://api.github.com/repos/TracingInsights/fantasy/tags?per_page=20"
log = logging.getLogger("weekly_update")


def report_path(season: int, round_: int, reports: Path = REPORTS) -> Path:
    return reports / f"round_{season}_{round_:02d}.md"


def due(races: pd.DataFrame, now: pd.Timestamp, force: bool, reports: Path = REPORTS):
    """The next round's races row when a report should be written now, else None."""
    left = races[~races["completed"]].sort_values(["season", "round"])
    if left.empty:
        return None
    nxt = left.iloc[0]
    if force:
        return nxt
    path = report_path(int(nxt["season"]), int(nxt["round"]), reports)
    done = path.exists() and "FAILED at" not in path.read_text(encoding="utf-8")
    return nxt if now < nxt["lock_utc"] <= now + WINDOW and not done else None


def stale_warning(team_file: Path, races: pd.DataFrame, season: int, round_: int) -> str | None:
    """Warn when the team file was last edited before the previous round's race (transfers may be missing)."""
    prev = races[(races["season"] == season) & (races["round"] < round_) & races["completed"]]
    if prev.empty:
        return None
    last = prev.sort_values("round").iloc[-1]
    edited = pd.Timestamp(team_file.stat().st_mtime, unit="s", tz="UTC")
    if edited >= last["race_utc"]:
        return None
    return (f"WARNING: {team_file.name} last edited {_local(edited)}, before the round {int(last['round'])} race. "
            "Update it if you made transfers, then rerun with --force.")


def unsealed(raw: Path = RAW, archive: Path = Path("data/raw.tar.gz.enc")) -> int:
    """Raw files newer than the sealed archive (all of them when there is no archive)."""
    cutoff = archive.stat().st_mtime if archive.exists() else 0.0
    return sum(1 for p in raw.rglob("*") if p.is_file() and p.stat().st_mtime > cutoff)


def _local(ts) -> str:
    return pd.Timestamp(ts).tz_convert(datetime.now().astimezone().tzinfo).strftime("%a %Y-%m-%d %H:%M %Z")


def _capture(fn, *args) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args)
    return buf.getvalue().rstrip()


def _http() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "f1-fantasy-snapshot"
    return session


def latest_ti_tag(http: requests.Session) -> str:
    response = http.get(TI_TAGS, timeout=30)
    response.raise_for_status()
    tags = [t["name"] for t in response.json() if t["name"].startswith("data-sync-")]
    if not tags:
        raise RuntimeError("no TracingInsights data-sync tag found")
    return max(tags)  # names are data-sync-YYYYMMDD-HHMMSS, so the max is the newest


def default_steps(season: int):
    """(name, fn) pairs; each fn returns report text or None."""
    http = _http()
    steps = [
        ("official snapshot", lambda: snapshot_official(RAW, http) and None),
        ("jolpica", lambda: pull_jolpica(season, RAW, http) and None),
        ("tracinginsights", lambda: pull_tracing_insights(latest_ti_tag(http), RAW, http) and None),
        ("mzafram", lambda: pull_mzafram(RAW, http) and None),
        ("rebuild tables", lambda: _capture(build_data.main) and None),
    ]
    for team in sorted(Path("config").glob("my_team_[0-9].yaml")):
        n = team.stem.rsplit("_", 1)[1]
        steps.append((f"team {n} pick", lambda n=n: _capture(pick_team.main, ["--team", n])))
        steps.append((f"team {n} chips", lambda n=n: _capture(plan_chips.main, ["--team", n])))
        steps.append((f"team {n} snapshot", lambda n=n: logic.snapshot_next(int(n)) and None))
    return steps


def execute(header: str, steps, path: Path) -> bool:
    """Run steps in order; write the report, or a FAILED report at the first failing step."""
    parts = [header]
    for name, fn in steps:
        log.info("step: %s", name)
        try:
            text = fn()
        except (Exception, SystemExit) as exc:  # pick_team raises SystemExit when prices are missing
            log.error("failed at %s\n%s", name, traceback.format_exc())
            last = (str(exc) or type(exc).__name__).strip().splitlines()[-1]
            path.write_text(f"# FAILED at {name}\n\n{header.splitlines()[0][2:]}\n\n`{last}`\n\n"
                            f"Full trace: reports/weekly_update.log. The next daily run retries.\n",
                            encoding="utf-8")
            return False
        if text:
            parts.append(f"### {name}\n\n```text\n{text}\n```")
    path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return True


def main(argv=None) -> int:
    os.chdir(ROOT)  # Task Scheduler may start elsewhere; every path here is project-relative
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="run now and rewrite the report")
    args = parser.parse_args(argv)
    REPORTS.mkdir(exist_ok=True)
    logging.basicConfig(filename=REPORTS / "weekly_update.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    races = pd.read_parquet("data/processed/races.parquet")
    now = pd.Timestamp(datetime.now(timezone.utc))
    nxt = due(races, now, args.force)
    if nxt is None:
        log.info("skip: no lock within %s or report already written", WINDOW)
        return 0
    season, round_ = int(nxt["season"]), int(nxt["round"])
    path = report_path(season, round_)
    header = (f"# {season} round {round_} ({nxt['slug']})\n\n"
              f"Lock: {_local(nxt['lock_utc'])}. Generated: {_local(now)}.")

    steps = default_steps(season)
    ok = execute(header, steps, path)
    if ok:
        races = pd.read_parquet("data/processed/races.parquet")  # rebuilt
        prices = pd.read_parquet("data/processed/prices.parquet")
        latest = int(prices.loc[prices["season"] == season, "round"].max())
        notes = [stale_warning(t, races, season, round_) for t in sorted(Path("config").glob("my_team_[0-9].yaml"))]
        notes = [n for n in notes if n]
        if latest < round_:
            notes.append(f"WARNING: round {round_} prices not published yet (latest round {latest}).")
        notes.append(f"Unsealed raw files: {unsealed()}. Seal with `uv run python -m src.ingest.vault seal` "
                     "when convenient (needs the key in that terminal only).")
        with path.open("a", encoding="utf-8") as f:
            f.write("\n## Checks\n\n" + "\n".join(f"- {n}" for n in notes) + "\n")
    log.info("%s %s", "wrote" if ok else "FAILED report", path)
    print(f"{'wrote' if ok else 'FAILED, see'} {path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
