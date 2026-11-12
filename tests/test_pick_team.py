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


def test_exclude_pushes_asset_below_everyone_and_rejects_unknown():
    import pandas as pd
    import pytest
    from pipelines.pick_team import exclude
    mu = pd.DataFrame({"asset_id": ["A", "B"], "mu": [5.0, 6.0]})
    assert exclude(mu, ["A"])["mu"].tolist() == [-1000.0, 6.0]
    with pytest.raises(ValueError):
        exclude(mu, ["Z"])


def test_swaps_pair_sold_with_bought_by_kind():
    from types import SimpleNamespace
    from pipelines.pick_team import swaps
    d = SimpleNamespace(drivers=("A", "X", "C"), constructors=("M", "N"))
    assert swaps(["A", "B", "C"], ["M", "F"], d) == ["B -> X", "F -> N"]
    assert swaps(["A", "X", "C"], ["M", "N"], d) == []
