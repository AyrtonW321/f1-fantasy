"""Normalized Parquet tables from the raw Jolpica, TracingInsights and official snapshots."""

import json
import re
import unicodedata
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from src.ingest.codes import driver_code
from src.features.prices import realized_price_changes

SLUG_ALIASES = {
    "bahrain-grand-prix-in-malaysia": "bahrain-grand-prix",
    "brazilian-grand-prix": "sao-paulo-grand-prix",
}
CONSTRUCTOR_ALIASES = {"RBR": "RED", "RBS": "VRB"}
LOCK_SESSIONS = ("Qualifying", "Sprint", "SprintQualifying", "SprintShootout")
KNOWN_AT_DELAY = pd.Timedelta(hours=6)
RESULT_FILES = (
    ("results.json", "Results", "race"),
    ("qualifying.json", "QualifyingResults", "qualifying"),
    ("sprint.json", "SprintResults", "sprint"),
)
RACE_COLS = ["season", "round", "slug", "ti_slug_round", "sprint", "lock_utc", "race_utc", "completed"]
PRICE_COLS = ["season", "round", "asset_id", "kind", "price", "known_at", "source"]
POINT_COLS = ["season", "round", "asset_id", "kind", "qualifying", "sprint", "race", "total", "known_at", "source"]
RESULT_COLS = ["season", "round", "session", "driver_code", "constructor_id", "position", "grid", "status", "known_at"]
PARTICIPATION_FIELDS = ("racePosition", "qualifyingPosition", "sprintPosition")


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _utc(session: dict) -> pd.Timestamp:
    return pd.to_datetime(f"{session['date']}T{session['time']}", utc=True)


def _lock_utc(season: int, round_no: int, name: str, session: dict) -> pd.Timestamp:
    if "time" not in session:
        raise ValueError(f"{season} round {round_no} {name} has no time on the schedule")
    return _utc(session)


def _points(value: str) -> float:
    # Official blanks mark sessions with no points (inactive rows, non-sprint weekends).
    return float(value) if value.strip() else 0.0


def _ti_points(row: dict) -> float:
    return float(row["sessionResult"]["totalPoints"]["points"])


def _ti_session_points(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    return {row["id"]: _ti_points(row) for row in _load(path)}


def _asset(asset_id, kind, price, qualifying, sprint, race, source, participated) -> dict:
    return {
        "asset_id": asset_id,
        "kind": kind,
        "price": price,
        "qualifying": qualifying,
        "sprint": sprint,
        "race": race,
        "total": qualifying + sprint + race,
        "source": source,
        "participated": participated,
    }


def _dedupe(rows: list[dict]) -> dict[str, dict]:
    """One row per asset: participating row first, then larger signed total, ties go to the last row."""
    best: dict[str, dict] = {}
    for row in rows:
        key = (row["participated"], row["total"])
        kept = best.get(row["asset_id"])
        if kept is None or key >= (kept["participated"], kept["total"]):
            best[row["asset_id"]] = row
    return best


def _ti_rows(race_dir: Path) -> list[dict]:
    race_all = race_dir / "race_all.json"
    if not race_all.exists():
        return []
    quali = _ti_session_points(race_dir / "qualifying_all.json")
    sprint = _ti_session_points(race_dir / "sprint_all.json")
    rows = []
    for row in _load(race_all):
        kind = row["type"]
        asset_id = row["abbreviation"] if kind == "driver" else row["id"]
        participated = any(row.get(field) is not None for field in PARTICIPATION_FIELDS)
        rows.append(_asset(
            asset_id, kind, float(row["price"]),
            quali.get(row["id"], 0.0), sprint.get(row["id"], 0.0), _ti_points(row),
            "tracinginsights", participated,
        ))
    return rows


def _official_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for value in _load(path)["Data"]["Value"]:
        kind = {"DRIVER": "driver", "CONSTRUCTOR": "constructor"}[value["PositionName"]]
        tla = value["DriverTLA"]
        asset_id = CONSTRUCTOR_ALIASES.get(tla, tla) if kind == "constructor" else tla
        row = _asset(
            asset_id, kind, float(value["Value"]),
            _points(value["QualifyingPoints"]), _points(value["SprintPoints"]), _points(value["RacePoints"]),
            "official", value["IsActive"] == "1",
        )
        row["gameday"] = _points(value["GamedayPoints"])
        rows.append(row)
    return rows


def _round_assets(raw_dir: Path, season: int, slug: str, round_no: int) -> dict[str, dict]:
    ti_rows = _ti_rows(raw_dir / "tracinginsights" / str(season) / slug)
    official_rows = _official_rows(raw_dir / "official" / str(season) / "drivers" / f"{round_no}.json")
    assets = _dedupe(ti_rows)
    for asset_id, row in _dedupe(official_rows).items():
        if abs(row["total"] - row["gameday"]) > 1e-9:
            # Official components disagree with the feed's own GamedayPoints: use a TI row that agrees.
            agreeing = [t for t in ti_rows if t["asset_id"] == asset_id and abs(t["total"] - row["gameday"]) <= 1e-9]
            if agreeing:
                assets[asset_id] = _dedupe(agreeing)[asset_id]
                continue
        assets[asset_id] = row  # official overrides TI for the same asset
    return assets


def build_races(season: int, raw_dir: Path) -> pd.DataFrame:
    jolpica = raw_dir / "jolpica" / str(season)
    completed = {int(r["round"]) for r in _load(jolpica / "results.json")}
    ti_root = raw_dir / "tracinginsights" / str(season)
    rows = []
    for race in _load(jolpica / "races.json"):
        round_no = int(race["round"])
        base = slugify(race["raceName"])
        slug = SLUG_ALIASES.get(base, base)
        locks = [_lock_utc(season, round_no, key, race[key]) for key in LOCK_SESSIONS if key in race]
        if not locks:
            raise ValueError(f"{season} round {round_no} has no lock session on the schedule")
        if "time" not in race:
            raise ValueError(f"{season} round {round_no} race has no time on the schedule")
        ti_race = ti_root / slug / "race.json"
        rows.append({
            "season": season,
            "round": round_no,
            "slug": slug,
            "ti_slug_round": _load(ti_race)["roundNumber"] if ti_race.exists() else pd.NA,
            "sprint": "Sprint" in race,
            "lock_utc": min(locks),
            "race_utc": _utc(race),
            "completed": round_no in completed,
        })
    if ti_root.exists():
        slugs = {row["slug"] for row in rows}
        unmatched = sorted(p.name for p in ti_root.iterdir() if p.is_dir() and p.name not in slugs)
        if unmatched:
            raise ValueError(f"TracingInsights {season} dirs with no Jolpica race: {unmatched}")
    races = pd.DataFrame(rows, columns=RACE_COLS)
    return races.astype({"ti_slug_round": "Int64", "sprint": bool, "completed": bool}).assign(
        lock_utc=lambda df: pd.to_datetime(df["lock_utc"], utc=True),
        race_utc=lambda df: pd.to_datetime(df["race_utc"], utc=True),
    )


def build_prices_points(season: int, races: pd.DataFrame, raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    price_rows, point_rows = [], []
    for race in races.itertuples(index=False):
        for asset in _round_assets(raw_dir, season, race.slug, race.round).values():
            base = {"season": season, "round": race.round, "asset_id": asset["asset_id"], "kind": asset["kind"]}
            price_rows.append({**base, "price": asset["price"], "known_at": race.lock_utc, "source": asset["source"]})
            if race.completed:
                point_rows.append({
                    **base,
                    "qualifying": asset["qualifying"],
                    "sprint": asset["sprint"],
                    "race": asset["race"],
                    "total": asset["total"],
                    "known_at": race.race_utc + KNOWN_AT_DELAY,
                    "source": asset["source"],
                })
    prices = pd.DataFrame(price_rows, columns=PRICE_COLS)
    points = pd.DataFrame(point_rows, columns=POINT_COLS)
    prices["known_at"] = pd.to_datetime(prices["known_at"], utc=True)
    points["known_at"] = pd.to_datetime(points["known_at"], utc=True)
    return prices, points


def build_results(season: int, raw_dir: Path) -> pd.DataFrame:
    jolpica = raw_dir / "jolpica" / str(season)
    race_utc = {int(r["round"]): _utc(r) for r in _load(jolpica / "races.json")}
    rows = []
    for filename, key, session in RESULT_FILES:
        for race in _load(jolpica / filename):
            round_no = int(race["round"])
            for row in race[key]:
                rows.append({
                    "season": season,
                    "round": round_no,
                    "session": session,
                    "driver_code": driver_code(row["Driver"]),
                    "constructor_id": row["Constructor"]["constructorId"],
                    "position": int(row["position"]),
                    "grid": int(row["grid"]) if session == "race" else pd.NA,
                    "status": pd.NA if session == "qualifying" else row["status"],
                    "known_at": race_utc[round_no] + KNOWN_AT_DELAY,
                })
    results = pd.DataFrame(rows, columns=RESULT_COLS)
    results["grid"] = results["grid"].astype("Int64")
    results["known_at"] = pd.to_datetime(results["known_at"], utc=True)
    return results


def build_all(raw_dir: Path, out_dir: Path, seasons: Sequence[int]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tables: dict[str, list[pd.DataFrame]] = {"races": [], "prices": [], "fantasy_points": [], "results": []}
    for season in seasons:
        races = build_races(season, raw_dir)
        prices, points = build_prices_points(season, races, raw_dir)
        tables["races"].append(races)
        tables["prices"].append(prices)
        tables["fantasy_points"].append(points)
        tables["results"].append(build_results(season, raw_dir))
    for name, frames in tables.items():
        pd.concat(frames, ignore_index=True).to_parquet(out_dir / f"{name}.parquet", index=False)
    prices = pd.concat(tables["prices"], ignore_index=True)
    realized_price_changes(prices).to_parquet(out_dir / "price_changes.parquet", index=False)
