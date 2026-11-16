import json

import pandas as pd
import pytest

from src.ui import logic
from src.ui.timeline import timeline_frame, timeline_spec


PRICES = logic.DATA / "prices.parquet"


def test_spec_dashes_expected_and_has_tooltip():
    frame = pd.DataFrame({"team": ["Team 1"] * 2, "season": [2026] * 2, "round": [20, 21],
                          "points": [50.0, 60.0], "cumulative": [50.0, 110.0],
                          "kind": ["actual", "expected"], "transfers": ["", "OUT GAS → IN ALO"],
                          "chip": ["", ""], "boost": ["RUS", "RUS"]})
    spec = timeline_spec(frame)
    text = json.dumps(spec)
    assert "strokeDash" in text and "transfers" in text and "cumulative" in text
    assert spec["data"]["values"][1]["kind"] == "expected"
    assert spec["background"] is None
    assert "#E10600" not in text and "#2EB86A" not in text


def _fixture_tables():
    races = pd.DataFrame({"season": [2026] * 4, "round": [20, 21, 22, 23],
                          "completed": [True, False, False, False]})
    prices = pd.DataFrame([(2026, r, a, k, 10.0 if k == "driver" else 20.0)
                           for r in range(20, 24)
                           for k, ids in (("driver", [f"D{i}" for i in range(1, 9)]),
                                          ("constructor", [f"C{i}" for i in range(1, 4)]))
                           for a in ids], columns=["season", "round", "asset_id", "kind", "price"])
    pts = pd.DataFrame([(2026, 20, a, k, float(i + 1))
                        for i, (k, ids) in enumerate((("driver", [f"D{i}" for i in range(1, 9)]),
                                                      ("constructor", [f"C{i}" for i in range(1, 4)])))
                        for a in ids], columns=["season", "round", "asset_id", "kind", "total"])
    return {"races": races, "prices": prices, "fantasy_points": pts}


@pytest.fixture
def timeline_config(tmp_path, monkeypatch):
    import shutil
    import yaml
    shutil.copy(logic.CONFIG / "model.yaml", tmp_path / "model.yaml")
    monkeypatch.setattr(logic, "CONFIG", tmp_path)
    team = {"drivers": [f"D{i}" for i in range(1, 6)], "constructors": ["C1", "C2"],
            "bank": 0.0, "free_transfers": 2, "chips_left": []}
    (tmp_path / "my_team_1.yaml").write_text(yaml.safe_dump(team), encoding="utf-8")
    return tmp_path


def _patch_model(monkeypatch, timeline_config, tables):
    from src.optimize.ilp import Asset, Decision, TeamState
    monkeypatch.setattr(logic, "next_round", lambda t: (2026, 21))
    monkeypatch.setattr(logic, "load", lambda n: {"drivers": [f"D{i}" for i in range(1, 6)],
                                                       "constructors": ["C1", "C2"]} if n == 1 else (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr(logic, "asset_mu", lambda s, r, t: {f"D{i}": float(i) for i in range(1, 9)})
    monkeypatch.setattr(logic, "history_points", lambda n, t: pd.DataFrame(columns=["season", "round", "points", "chip"]))
    monkeypatch.setattr(logic, "swaps_log", lambda n: [])
    monkeypatch.setattr(logic, "team_state", lambda n, t: TeamState({}, 0.0, 1))
    monkeypatch.setattr(logic, "top_teams", lambda state, n=1, tables=None: [Decision(
        ("D1", "D2", "D3", "D4", "D6"), ("C1", "C2"), "D6", ("D6",), 0, 70.0, 80.0, 80.0)])
    monkeypatch.setattr(logic, "history_path", lambda n: timeline_config / f"team_{n}.csv")


def test_frame_round20_then_expected(timeline_config, monkeypatch):
    t = _fixture_tables()
    _patch_model(monkeypatch, timeline_config, t)
    f = timeline_frame([1], t)
    assert f["round"].tolist() == [20, 21, 22, 23]
    assert f["kind"].tolist() == ["actual", "expected", "expected", "expected"]
    assert f["cumulative"].tolist() == pytest.approx(f["points"].cumsum().tolist())
    assert f.loc[1, "transfers"] == "OUT D5 → IN D6"


def test_logged_round_replaces_expected(timeline_config, monkeypatch):
    t = _fixture_tables()
    _patch_model(monkeypatch, timeline_config, t)
    monkeypatch.setattr(logic, "history_points", lambda n, tables: pd.DataFrame([
        {"season": 2026, "round": 21, "points": 91.0, "chip": "wildcard"}]))
    monkeypatch.setattr(logic, "swaps_log", lambda n: [{"season": 2026, "round": 21,
                                                          "out": ["D4"], "in": ["D5"], "chip": "wildcard"}])
    f = timeline_frame([1], t)
    row = f[f["round"] == 21].iloc[0]
    assert row["kind"] == "actual" and row["points"] == 91.0
    assert row["transfers"] == "OUT D4 → IN D5" and row["chip"] == "wildcard"


def test_missing_team_is_skipped(timeline_config, monkeypatch):
    t = _fixture_tables()
    _patch_model(monkeypatch, timeline_config, t)
    assert set(timeline_frame([1, 9], t)["team"]) == {"Team 1"}


@pytest.mark.skipif(not PRICES.exists(), reason="real data not unpacked")
def test_real_team_frame_uses_round20(monkeypatch, tmp_path):
    from src.optimize.ilp import Decision, TeamState
    t = logic._tables()
    assets = t["prices"].query("season == 2026 and round == 20")
    drivers = assets.loc[assets["kind"] == "driver", "asset_id"].head(5).tolist()
    constructors = assets.loc[assets["kind"] == "constructor", "asset_id"].head(2).tolist()
    monkeypatch.setattr(logic, "load", lambda n: {"drivers": drivers, "constructors": constructors})
    monkeypatch.setattr(logic, "team_state", lambda n, tables: TeamState({}, 0.0, 1))
    monkeypatch.setattr(logic, "top_teams", lambda state, n=1, tables=None: [Decision(
        tuple(drivers), tuple(constructors), drivers[0], (), 0, 70.0, 80.0, 80.0)])
    monkeypatch.setattr(logic, "history_path", lambda n: tmp_path / f"team_{n}.csv")
    frame = timeline_frame([1], t)
    assert frame["round"].tolist() == [20, 21, 22, 23]
    assert frame["kind"].tolist() == ["actual", "expected", "expected", "expected"]
