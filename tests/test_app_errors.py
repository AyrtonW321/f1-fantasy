from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import src.ui.logic as logic

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.mark.skipif(not Path("data/processed/races.parquet").exists(), reason="real data not unpacked")
def test_failed_team_shows_message_and_retry(monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("disk gone")
    monkeypatch.setattr(logic, "team_state", boom)
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    page = " ".join(h.proto.body for h in at.get("html"))
    assert "Couldn't load Team 1." in page and "disk gone" not in page
    assert any(b.label == "Retry" for b in at.button)
    assert not at.exception
