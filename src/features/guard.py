import pandas as pd


class LeakageError(Exception):
    """A row became known after the lock of the round it feeds."""


def assert_known_before_lock(frame: pd.DataFrame, races: pd.DataFrame) -> None:
    locks = races[["season", "round", "lock_utc"]]
    checked = frame[["season", "round", "known_at"]].merge(locks, on=["season", "round"], how="left")
    # Fail closed: a missing lock or known_at makes the comparison False.
    bad = checked[~(checked["known_at"] <= checked["lock_utc"])]
    if not bad.empty:
        row = bad.iloc[0]
        raise LeakageError(
            f"season {row['season']} round {row['round']}: known_at {row['known_at']} "
            f"is not at or before lock_utc {row['lock_utc']}"
        )
