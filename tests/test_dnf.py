import pandas as pd
import pytest

from src.models.dnf import dnf_probability


def test_dnf_probability_shrinks_to_field_rate():
    history = pd.DataFrame({
        "session": ["race"] * 4 + ["qualifying"],
        "driver_code": ["AAA", "AAA", "BBB", "BBB", "AAA"],
        "status": ["Retired", "Finished", "Finished", "Did not start", None],
    })
    p = dnf_probability(history, ["AAA", "BBB", "NEW"], shrink=2.0)
    # Field rate 2/4 = 0.5 (qualifying ignored); AAA (1 + 2*0.5) / (2 + 2) = 0.5; unseen driver gets the rate.
    assert p.tolist() == pytest.approx([0.5, 0.5, 0.5])
    p = dnf_probability(history.iloc[[0, 2, 3]].assign(status=["Retired", "Finished", "Finished"]), ["AAA", "BBB"], 1.0)
    assert p.tolist() == pytest.approx([(1 + 1 / 3) / 2, (0 + 1 / 3) / 3])


def test_no_history_gives_zero():
    empty = pd.DataFrame(columns=["session", "driver_code", "status"])
    assert dnf_probability(empty, ["AAA"]).tolist() == [0.0]
