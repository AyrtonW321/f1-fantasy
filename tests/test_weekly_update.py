import os
from pathlib import Path

import pandas as pd

from pipelines import weekly_update as wu

LOCK = pd.Timestamp("2026-11-21 04:00", tz="UTC")


def races():
    return pd.DataFrame({
        "season": [2026, 2026], "round": [20, 21], "slug": ["qatar", "las-vegas"],
        "lock_utc": [LOCK - pd.Timedelta(days=7), LOCK],
        "race_utc": [LOCK - pd.Timedelta(days=6), LOCK + pd.Timedelta(days=1)],
        "completed": [True, False],
    })


def test_due_gate(tmp_path):
    r = races()
    assert wu.due(r, LOCK - pd.Timedelta(hours=60), False, tmp_path) is None  # too early
    assert wu.due(r, LOCK - pd.Timedelta(hours=30), False, tmp_path)["round"] == 21
    assert wu.due(r, LOCK + pd.Timedelta(hours=1), False, tmp_path) is None  # already locked
    path = wu.report_path(2026, 21, tmp_path)
    path.write_text("# 2026 round 21\n", encoding="utf-8")
    assert wu.due(r, LOCK - pd.Timedelta(hours=30), False, tmp_path) is None  # report written
    path.write_text("# FAILED at jolpica\n", encoding="utf-8")
    assert wu.due(r, LOCK - pd.Timedelta(hours=30), False, tmp_path)["round"] == 21  # retry
    assert wu.due(r, LOCK - pd.Timedelta(days=5), True, tmp_path)["round"] == 21  # --force


def test_failing_step_writes_failed_report(tmp_path):
    path = tmp_path / "round.md"

    def boom():
        raise RuntimeError("feed down\nHTTP 503")

    ok = wu.execute("# 2026 round 21 (las-vegas)\n\nLock: x.", [("pick", lambda: "VER"), ("jolpica", boom)], path)
    text = path.read_text(encoding="utf-8")
    assert not ok and text.startswith("# FAILED at jolpica") and "HTTP 503" in text and "VER" not in text

    assert wu.execute("# 2026 round 21\n", [("team 1 pick", lambda: "VER"), ("pull", lambda: None)], path)
    text = path.read_text(encoding="utf-8")
    assert "### team 1 pick" in text and "VER" in text and "### pull" not in text


def test_stale_team_warning(tmp_path):
    team = tmp_path / "my_team_1.yaml"
    team.write_text("drivers: []\n", encoding="utf-8")
    before = (LOCK - pd.Timedelta(days=6, hours=1)).timestamp()  # before the round 20 race
    os.utime(team, (before, before))
    assert "before the round 20 race" in wu.stale_warning(team, races(), 2026, 21)
    after = (LOCK - pd.Timedelta(days=5)).timestamp()
    os.utime(team, (after, after))
    assert wu.stale_warning(team, races(), 2026, 21) is None


def test_never_reads_data_key():
    source = Path(wu.__file__).read_text(encoding="utf-8")
    assert "F1_DATA_KEY" not in source and "from src.ingest.vault" not in source and "import vault" not in source


def test_failure_keeps_last_good_report(tmp_path):
    path = tmp_path / "round.md"
    assert wu.execute("# 2026 round 22\n", [("team 1 pick", lambda: "VER")], path)

    def boom():
        raise RuntimeError("feed down")

    for _ in range(2):  # a second failure must not lose the kept report
        assert not wu.execute("# 2026 round 22\n", [("pull", boom)], path)
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# FAILED at pull") and text.count(wu.KEPT) == 1 and "VER" in text


def test_lagging_sources(tmp_path):
    races = pd.DataFrame({"season": [2026] * 3, "round": [1, 2, 3], "slug": ["a", "b", "c"],
                          "completed": [True, True, False]})
    points = pd.DataFrame({"season": [2026], "round": [1]})
    (tmp_path / "tracinginsights" / "2026" / "a").mkdir(parents=True)
    (tmp_path / "tracinginsights" / "2026" / "a" / "race_all.json").write_text("[]")
    out = wu.lagging_sources(races, points, 2026, tmp_path)
    assert len(out) == 2 and all(x.startswith("round 2 (b)") for x in out)
