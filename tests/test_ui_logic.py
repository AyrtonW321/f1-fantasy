import shutil

import pandas as pd
import pytest
import yaml

from src.optimize.ilp import TeamState
from src.ui import logic

DRIVERS = [f"D{i}" for i in range(1, 9)]
CONS = ["C1", "C2", "C3"]
LOCK1, LOCK2 = pd.Timestamp("2026-03-01", tz="UTC"), pd.Timestamp("2026-03-08", tz="UTC")


def tables():
    races = pd.DataFrame({"season": [2026, 2026], "round": [1, 2], "slug": ["a", "b"],
                          "lock_utc": [LOCK1, LOCK2], "race_utc": [LOCK1 + pd.Timedelta(days=1)] * 2,
                          "completed": [True, False], "sprint": [False, False]})
    ids = [(d, "driver", 10.0) for d in DRIVERS] + [(c, "constructor", 20.0) for c in CONS]
    prices = pd.DataFrame([(2026, r, a, k, p) for r in (1, 2) for a, k, p in ids],
                          columns=["season", "round", "asset_id", "kind", "price"])
    totals = dict(zip(DRIVERS + CONS, [8, 7, 6, 5, 4, 3, 2, -6, 10, 5, 1]))
    points = pd.DataFrame([(2026, 1, a, k, float(totals[a]), LOCK1 + pd.Timedelta(days=2), 0.0, None, float(totals[a]))
                           for a, k, _ in ids],
                          columns=["season", "round", "asset_id", "kind", "total", "known_at", "qualifying", "sprint", "race"])
    return {"races": races, "prices": prices, "fantasy_points": points}


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    shutil.copy("config/model.yaml", tmp_path / "model.yaml")
    monkeypatch.setattr(logic, "CONFIG", tmp_path)
    team = {"exclude": [], "drivers": DRIVERS[3:8], "constructors": ["C2", "C3"], "bank": 10.0,
            "free_transfers": 2, "chips_left": ["limitless", "x3_boost"]}
    (tmp_path / "my_team_1.yaml").write_text(yaml.safe_dump(team), encoding="utf-8")
    return tmp_path


def test_validate():
    t = tables()
    good = {"drivers": DRIVERS[:5], "constructors": CONS[:2], "bank": 0.5, "free_transfers": 2, "chips_left": ["wildcard"]}
    assert logic.validate(good, 2026, t) == []
    bad = dict(good, drivers=["D1", "D1", "D2", "D3", "XX"], bank=-1, free_transfers=9, chips_left=["nope"])
    errors = " ".join(logic.validate(bad, 2026, t))
    for word in ("drivers: need 5", "unknown driver ids ['XX']", "bank", "free_transfers", "unknown chips"):
        assert word in errors


def test_top_teams_distinct_and_in_budget(cfg):
    t = tables()
    best = logic.top_teams(None, 90.0, 5, tables=t)
    assert len(best) == 5 and len({(d.drivers, d.constructors) for d in best}) == 5
    assert all(d.cost <= 90.0 for d in best)
    assert [d.expected_points for d in best] == sorted((d.expected_points for d in best), reverse=True)
    state = TeamState({a: 10.0 for a in DRIVERS[3:8]} | {"C2": 20.0, "C3": 20.0}, 10.0, 1)
    reach = logic.top_teams(state, n=3, tables=t)
    assert len(reach) == 3 and reach[0].penalty_transfers >= 0 and reach[0].budget == 100.0


def test_apply_transfers_writes_backup_team_and_history(cfg):
    t = tables()
    d = logic.top_teams(TeamState({a: 10.0 for a in DRIVERS[3:8]} | {"C2": 20.0, "C3": 20.0}, 10.0, 2), tables=t)[0]
    new = logic.apply_transfers(1, d, tables=t)
    saved = yaml.safe_load((cfg / "my_team_1.yaml").read_text(encoding="utf-8"))
    assert saved["drivers"] == list(d.drivers) and saved["bank"] == round(d.budget - d.cost, 1) == new["bank"]
    assert len(d.transfers_in) == 2 and saved["free_transfers"] == 2  # 2 free, both used: no carry
    assert len(list((cfg / "backup").iterdir())) == 1
    hist = pd.read_csv(cfg / "history" / "team_1.csv")
    assert hist[["season", "round"]].values.tolist() == [[2026, 2]]

    # limitless: team and bank revert, chip used, history row for round 2 replaced not duplicated
    logic.apply_transfers(1, d, chip="limitless", tables=t)
    saved2 = yaml.safe_load((cfg / "my_team_1.yaml").read_text(encoding="utf-8"))
    assert saved2["drivers"] == saved["drivers"] and saved2["chips_left"] == ["x3_boost"]
    assert saved2["free_transfers"] == 3  # unlimited round uses none: 2 + carry 1
    assert len(pd.read_csv(cfg / "history" / "team_1.csv")) == 1
    with pytest.raises(ValueError, match="not in chips_left"):
        logic.apply_transfers(1, d, chip="wildcard", tables=t)


def test_history_points_applies_boost_chip_and_penalty(cfg):
    t = tables()
    logic._log(1, {"season": 2026, "round": 1, "drivers": "D1|D2|D3|D4|D8", "constructors": "C1|C2",
                   "boost": "D1", "boost3": "D2", "chip": "x3_boost", "transfers_in": "D8",
                   "penalty_transfers": 1, "bank": 0.0, "team_value": 90.0})
    logic._log(1, {"season": 2026, "round": 2, "drivers": "D1|D2|D3|D4|D8", "constructors": "C1|C2",
                   "boost": "D1", "chip": "", "transfers_in": "", "penalty_transfers": 0,
                   "bank": 0.0, "team_value": 90.0})
    h = logic.history_points(1, tables=t)
    # 8+7+6+5-6 + 10+5 = 35; boost D1 +8; x3 on D2 +14; penalty 10 (2026 rules)
    assert h.loc[0, "points"] == 35 + 8 + 14 - 10 and h.loc[0, "chip"] == "x3_boost"
    assert pd.isna(h.loc[1, "points"]) and h.loc[0, "lineup"].startswith("D1, D2")
    assert logic.history_points(2, tables=t).empty


def test_top_teams_chip_and_no_round_left(cfg):
    t = tables()
    state = TeamState({a: 10.0 for a in DRIVERS[3:8]} | {"C2": 20.0, "C3": 20.0}, 10.0, 0)
    x3 = logic.top_teams(state, chip="x3_boost", tables=t)
    assert len(x3) == 1 and x3[0].boost3 in x3[0].drivers and x3[0].boost3 != x3[0].boost
    wild = logic.top_teams(state, chip="wildcard", tables=t)[0]
    normal = logic.top_teams(state, n=1, tables=t)[0]
    assert wild.expected_points >= normal.expected_points and wild.transfers_in  # no penalty: changes freely
    assert len(logic.top_teams(state, chip="autopilot", tables=t)) == 5  # team unchanged by chip
    done = dict(t, races=t["races"].assign(completed=True))
    with pytest.raises(ValueError, match="no upcoming round"):
        logic.next_round(done)


def test_saved_xpts_boost_and_x3():
    rules = {"team": {"boost_multiplier": 2}, "chips": {"x3_boost": {"extra_multiplier": 3}}}
    team = {"drivers": ["A", "B", "C", "D", "E"], "constructors": ["X", "Y"]}
    mu = {"A": 10, "B": 8, "C": 1, "D": 1, "E": 1, "X": 5, "Y": 5}
    assert logic.saved_xpts(team, mu, rules, None) == (41.0, "A")  # 31 + 10
    assert logic.saved_xpts(team, mu, rules, "x3_boost") == (59.0, "B")  # 31 + 2*10 + 8; A tripled, B x2
    assert logic.saved_xpts({"drivers": [], "constructors": ["X", "Y"]}, mu, rules, None) == (None, None)
    assert logic.saved_xpts(team, {k: v for k, v in mu.items() if k != "C"}, rules, None) == (None, "A")


def _two_rounds(cfg):
    rows = [{"season": 2026, "round": 21, "drivers": "A|B|C|D|E", "constructors": "X|Y", "transfers_in": "A"},
            {"season": 2026, "round": 22, "drivers": "A|B|C|D|F", "constructors": "X|Z", "chip": "wildcard"}]
    for r in rows:
        logic._log(1, r)


def test_swaps_log_diffs_rows(cfg):
    _two_rounds(cfg)
    log = logic.swaps_log(1)
    assert log[0]["out"] == [] and log[0]["in"] == ["A"]
    assert sorted(log[1]["out"]) == ["E", "Y"] and sorted(log[1]["in"]) == ["F", "Z"]
    assert log[1]["chip"] == "wildcard" and logic.swaps_log(9) == []


def test_round_chip(cfg):
    _two_rounds(cfg)
    assert logic.round_chip(1, 2026, 22) == "wildcard"
    assert logic.round_chip(1, 2026, 21) is None
    assert logic.round_chip(1, 2026, 23) is None
    assert logic.round_chip(9, 2026, 22) is None  # no history file


def test_advised_chip():
    text = "Round 21: no_negative; expected gain 11.8; swaps\nRound 22: none; expected gain 0.0"
    assert logic.advised_chip(text, 21) == "no_negative"
    assert logic.advised_chip(text, 22) is None
    assert logic.advised_chip(text, 23) is None
    assert logic.advised_chip(None, 21) is None


def test_swaps_log_skips_reverting_chip(cfg):
    for r in [{"season": 2026, "round": 20, "drivers": "A|B|C|D|E", "constructors": "X|Y"},
              {"season": 2026, "round": 21, "drivers": "F|G|H|I|J", "constructors": "Z|W", "chip": "limitless"},
              {"season": 2026, "round": 22, "drivers": "A|B|C|D|K", "constructors": "X|Y"}]:
        logic._log(1, r)
    log = logic.swaps_log(1)
    assert log[2]["out"] == ["E"] and log[2]["in"] == ["K"]  # diffed against R20, not the limitless team


def test_snapshot_and_record_round(cfg):
    t = tables()
    # snapshot logs the team file for the next round (2), boost on best expected driver; once only
    assert logic.snapshot_next(1, tables=t) is True and logic.snapshot_next(1, tables=t) is False
    row = pd.read_csv(cfg / "history" / "team_1.csv", dtype=str, keep_default_na=False).iloc[0]
    assert (row["round"], row["drivers"], row["source"]) == ("2", "|".join(DRIVERS[3:8]), "snapshot")
    assert row["boost"] == "D4" and float(row["team_value"]) == 90.0
    # recording a past round (1) with chip and boost: own row, scored, transfers vs nothing before
    logic.record_round(1, 2026, 1, DRIVERS[:5], ["C1", "C2"], "D1", chip="x3_boost", boost3="D2", tables=t)
    h = logic.history_points(1, tables=t)
    assert h["round"].tolist() == [1, 2]
    assert h["points"].iloc[0] == 8 + 7 + 6 + 5 + 4 + 10 + 5 + 8 + 2 * 7  # x2 D1 extra, x3 D2 extra
    # record_round replaces the snapshot for the same round
    logic.record_round(1, 2026, 2, DRIVERS[:5], ["C1", "C2"], "D1", tables=t)
    hist = pd.read_csv(cfg / "history" / "team_1.csv", dtype=str, keep_default_na=False)
    assert len(hist) == 2 and hist.iloc[-1]["source"] == "edit" and hist.iloc[-1]["transfers_in"] == ""


def test_round_source_confirm_and_review(cfg):
    t = tables()
    assert logic.round_source(1, 2026, 1) is None
    with pytest.raises(ValueError):
        logic.confirm_round(1, 2026, 1)
    logic.record_round(1, 2026, 1, DRIVERS[:5], ["C1", "C2"], "D1", source="snapshot", tables=t)
    assert logic.round_source(1, 2026, 1) == "snapshot"
    logic.confirm_round(1, 2026, 1)
    assert logic.round_source(1, 2026, 1) == "edit"
    r = logic.race_review(1, 2026, 1, tables=t)
    assert r["points"] == 8 + 7 + 6 + 5 + 4 + 10 + 5 + 8  # x2 D1
    # best under budget 90 (team value) + 10 (bank): every driver costs 10, constructors 20
    assert r["best_points"] >= r["points"] and r["misses"][0][0] in DRIVERS + CONS
    assert logic.race_review(1, 2026, 2, tables=t) is None  # no lineup/points
