import pandas as pd
import pytest

from src.features.guard import LeakageError, assert_known_before_lock

LOCK_3 = pd.Timestamp("2026-03-20T12:00:00Z")
RACES = pd.DataFrame({
    "season": [2026, 2026],
    "round": [2, 3],
    "lock_utc": [LOCK_3 - pd.Timedelta(weeks=1), LOCK_3],
})


def frame(known_at):
    return pd.DataFrame({"season": [2026], "round": [3], "known_at": [known_at]})


def test_guard_passes_at_lock():
    assert assert_known_before_lock(frame(LOCK_3), RACES) is None


def test_guard_raises_after_lock():
    with pytest.raises(LeakageError, match="round 3"):
        assert_known_before_lock(frame(LOCK_3 + pd.Timedelta(seconds=1)), RACES)
