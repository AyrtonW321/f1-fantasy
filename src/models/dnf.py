"""Per-driver race DNF probability, shrunk toward the field rate of the history it is given."""
import pandas as pd

# Statuses the official game scores as not classified (2026: every one of them scores the -20 race line).
DNF_STATUSES = ("Retired", "Did not start")


def dnf_probability(history: pd.DataFrame, drivers: list[str], shrink: float = 5.0) -> pd.Series:
    """history: race result rows already cut to before the target lock. p = (dnfs + shrink * rate) / (starts + shrink)."""
    race = history[history["session"] == "race"]
    flag = race["status"].isin(DNF_STATUSES)
    rate = float(flag.mean()) if len(race) else 0.0
    per = flag.groupby(race["driver_code"]).agg(["sum", "count"]).reindex(drivers, fill_value=0)
    return (per["sum"] + shrink * rate) / (per["count"] + shrink)
