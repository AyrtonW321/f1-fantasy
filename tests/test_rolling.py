import pandas as pd
import pytest

from src.features.rolling import baseline_mu

SEASON = 2026
FIRST_LOCK = pd.Timestamp("2026-03-06T12:00:00Z")
KNOWN_AFTER_LOCK = pd.Timedelta(days=2, hours=6)  # race (lock + 2 days) + 6 hours
POINTS_COLS = [
    "season", "round", "asset_id", "kind", "qualifying", "sprint", "race",
    "total", "known_at", "source",
]


def lock(round_):
    return FIRST_LOCK + pd.Timedelta(weeks=int(round_) - 1)


def races(n=9):
    return pd.DataFrame({
        "season": SEASON,
        "round": range(1, n + 1),
        "lock_utc": [lock(r) for r in range(1, n + 1)],
    })


def prices(rows, season=SEASON):
    """rows: (round, asset_id, price)."""
    df = pd.DataFrame(rows, columns=["round", "asset_id", "price"])
    df.insert(0, "season", season)
    df["kind"] = "driver"
    df["known_at"] = [lock(r) for r in df["round"]]
    df["source"] = "test"
    return df


def points(rows, season=SEASON):
    """rows: (round, asset_id, total) or (round, asset_id, total, known_at)."""
    recs = []
    for r, asset, total, *known in rows:
        recs.append({
            "season": season, "round": r, "asset_id": asset, "kind": "driver",
            "qualifying": 0, "sprint": 0, "race": total, "total": total,
            "known_at": known[0] if known else lock(r) + KNOWN_AFTER_LOCK,
            "source": "test",
        })
    df = pd.DataFrame(recs, columns=POINTS_COLS).astype({"season": "int64", "round": "int64"})
    df["known_at"] = pd.to_datetime(df["known_at"], utc=True)
    return df


def mu_of(out, asset_id):
    return out.loc[out["asset_id"] == asset_id, "mu"].item()


def test_round_one_mu_equals_price():
    out = baseline_mu(prices([(1, "VER", 20.0), (1, "HAM", 15.0)]), points([]), races(), SEASON, 1)
    assert list(out.columns) == ["season", "round", "asset_id", "kind", "price", "mu", "known_at"]
    assert dict(zip(out["asset_id"], out["mu"])) == {"VER": 20.0, "HAM": 15.0}
    assert (out["known_at"] == lock(1)).all()


def test_partial_history_blends_with_prior():
    # Two assets priced 20 in rounds 1-3. VER scored 10 then 20, HAM 10 then 10.
    # Ratios 0.5, 1.0, 0.5, 0.5 -> median 0.5 -> prior at round 3 = 20 * 0.5 = 10.
    # VER mu = (30 + 3 * 10) / 5 = 12.0
    p = prices([(r, a, 20.0) for r in (1, 2, 3) for a in ("VER", "HAM")])
    pts = points([(1, "VER", 10.0), (2, "VER", 20.0), (1, "HAM", 10.0), (2, "HAM", 10.0)])
    out = baseline_mu(p, pts, races(), SEASON, 3)
    assert mu_of(out, "VER") == pytest.approx(12.0)
    assert mu_of(out, "HAM") == pytest.approx(10.0)


def test_only_latest_window_counts():
    # Round 1 scored 100 (oldest, excluded). Rounds 2-6 scored 10 each.
    # k == 5, so the prior has weight 0: mu = 50 / 5 = 10.0
    p = prices([(r, "VER", 20.0) for r in range(1, 8)])
    pts = points([(1, "VER", 100.0)] + [(r, "VER", 10.0) for r in range(2, 7)])
    out = baseline_mu(p, pts, races(), SEASON, 7)
    assert mu_of(out, "VER") == pytest.approx(10.0)


def test_prior_uses_current_round_price():
    # Price 10, 10, then 30 at round 3. Ratios 1.0, 1.0 -> median 1.0.
    # Prior uses the round 3 price: 30. mu = (20 + 3 * 30) / 5 = 22.0
    p = prices([(1, "VER", 10.0), (2, "VER", 10.0), (3, "VER", 30.0)])
    pts = points([(1, "VER", 10.0), (2, "VER", 10.0)])
    out = baseline_mu(p, pts, races(), SEASON, 3)
    assert mu_of(out, "VER") == pytest.approx(22.0)


def test_future_rows_ignored():
    # Same league as the blend test, plus a 1000-point row at round 9.
    p = prices([(r, a, 20.0) for r in (1, 2, 3) for a in ("VER", "HAM")])
    pts = points([
        (1, "VER", 10.0), (2, "VER", 20.0), (1, "HAM", 10.0), (2, "HAM", 10.0),
        (9, "VER", 1000.0),
    ])
    out = baseline_mu(p, pts, races(), SEASON, 3)
    assert mu_of(out, "VER") == pytest.approx(12.0)


def test_other_season_ignored():
    # Same 2026 league as the blend test. 2025 has VER at ratio 100 in rounds 1-2.
    # If 2025 leaked, the median and the form window would both change.
    p = pd.concat([
        prices([(r, a, 20.0) for r in (1, 2, 3) for a in ("VER", "HAM")]),
        prices([(1, "VER", 10.0), (2, "VER", 10.0)], season=2025),
    ])
    pts = pd.concat([
        points([(1, "VER", 10.0), (2, "VER", 20.0), (1, "HAM", 10.0), (2, "HAM", 10.0)]),
        points([(1, "VER", 1000.0), (2, "VER", 1000.0)], season=2025),
    ])
    out = baseline_mu(p, pts, races(), SEASON, 3)
    assert mu_of(out, "VER") == pytest.approx(12.0)


def test_unplayed_round_is_not_zero_form():
    # VER priced 20 in rounds 1-3, no points row for round 2.
    # History is round 1 only: k == 1, ratio 0.5, prior 10.
    # mu = (10 + 4 * 10) / 5 = 10.0 (counting round 2 as a zero would give 8.0)
    p = prices([(r, "VER", 20.0) for r in (1, 2, 3)])
    pts = points([(1, "VER", 10.0)])
    out = baseline_mu(p, pts, races(), SEASON, 3)
    assert mu_of(out, "VER") == pytest.approx(10.0)


def test_known_at_after_lock_row_ignored():
    # VER's round 2 row was known one hour after round 3 locked, so it does not count
    # even though its round is smaller. History is round 1 only: mu = 10.0
    p = prices([(r, "VER", 20.0) for r in (1, 2, 3)])
    pts = points([(1, "VER", 10.0), (2, "VER", 20.0, lock(3) + pd.Timedelta(hours=1))])
    out = baseline_mu(p, pts, races(), SEASON, 3)
    assert mu_of(out, "VER") == pytest.approx(10.0)
