import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
from pick_team import load_team


def test_load_team_reads_state_and_rejects_unknown_assets(tmp_path):
    f = tmp_path / "my_team.yaml"
    f.write_text("drivers: [VER]\nconstructors: [RED]\nbank: 1.5\nfree_transfers: 2\n")
    state = load_team(f, {"VER": 29.1, "RED": 33.6})
    assert state.owned == {"VER": 29.1, "RED": 33.6} and state.bank == 1.5 and state.free_transfers == 2
    with pytest.raises(ValueError, match="XXX"):
        f.write_text("drivers: [XXX]\nconstructors: [RED]\nbank: 0\nfree_transfers: 2\n")
        load_team(f, {"RED": 33.6})
