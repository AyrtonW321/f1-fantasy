import pytest

from src.sim.scoring import (
    DriverLine,
    PitResult,
    UnknownRuleError,
    load_rules,
    score_constructor,
    score_driver,
)


def test_race_win_all_bonuses_2026():
    line = DriverLine("VER", "race", position=1, gained=3, overtakes=2, fastest_lap=True, dotd=True)
    assert score_driver(load_rules(2026), line) == 50

def test_positions_lost_are_negative():
    assert score_driver(load_rules(2026), DriverLine("X", "race", position=12, gained=-4)) == -4

def test_sprint_nc_changes_by_season():
    line = DriverLine("X", "sprint", not_classified=True)
    assert score_driver(load_rules(2025), line) == -20
    assert score_driver(load_rules(2026), line) == -10

def test_null_rule_raises():
    with pytest.raises(UnknownRuleError):
        score_driver(load_rules(2026), DriverLine("X", "race", disqualified=True))

def test_constructor_excludes_dotd():
    lines = [DriverLine("A", "race", position=1, dotd=True), DriverLine("B", "race", position=2)]
    assert score_constructor(load_rules(2026), lines) == 43

def test_constructor_uses_own_dsq_value():
    lines = [DriverLine("A", "sprint", disqualified=True), DriverLine("B", "sprint", not_classified=True)]
    assert score_constructor(load_rules(2026), lines) == -30

def test_constructor_qualifying_mexico_2026_shape():
    lines = [DriverLine("LAW", "qualifying", disqualified=True), DriverLine("LIN", "qualifying", position=8)]
    assert score_constructor(load_rules(2026), lines, teamwork="one_q3") == -2

def test_rank_pit_sums():
    lines = [DriverLine("A", "race"), DriverLine("B", "race")]
    assert score_constructor(load_rules(2024), lines, pit=PitResult(ranks=(1, 3))) == 13

@pytest.mark.parametrize("seconds,points", [(1.99, 20), (2.00, 10), (2.19, 10), (2.20, 5), (2.50, 2), (3.00, 2), (3.01, 0)])
def test_time_band_boundaries(seconds, points):
    lines = [DriverLine("A", "race"), DriverLine("B", "race")]
    assert score_constructor(load_rules(2026), lines, pit=PitResult(seconds=seconds)) == points

def test_overall_fastest_stop_null_raises_in_2024():
    with pytest.raises(UnknownRuleError):
        score_constructor(load_rules(2024), [DriverLine("A", "race")], pit=PitResult(overall_fastest=True))


def _structure(rules: dict) -> dict:
    # Key names only. pit_ranks and pit_bands are null in some seasons, so their values are not compared.
    return {
        "top": sorted(rules),
        "driver": {s: sorted(rules["driver"][s]) for s in ("qualifying", "sprint", "race")},
        "constructor": sorted(rules["constructor"]),
        "constructor.disqualified": sorted(rules["constructor"]["disqualified"]),
        "constructor.teamwork": sorted(rules["constructor"]["teamwork"]),
        "team": sorted(rules["team"]),
        "transfers": sorted(rules["transfers"]),
    }

def test_all_seasons_load_with_same_keys():
    loaded = {season: load_rules(season) for season in (2023, 2024, 2025, 2026)}
    for season, rules in loaded.items():
        assert rules["season"] == season
    shapes = {season: _structure(rules) for season, rules in loaded.items()}
    assert shapes[2023] == shapes[2024] == shapes[2025] == shapes[2026]
    assert loaded[2023]["assumed"] == ["transfers.carry_max"]


def test_pit_points_only_count_in_race_sessions():
    from src.sim.scoring import DriverLine, PitResult, load_rules, score_constructor

    lines = [DriverLine("A", "qualifying"), DriverLine("B", "qualifying")]
    assert score_constructor(load_rules(2024), lines, pit=PitResult(ranks=(1,))) == 0
    sprint = [DriverLine("A", "sprint"), DriverLine("B", "sprint")]
    assert score_constructor(load_rules(2026), sprint, pit=PitResult(seconds=1.9)) == 0


def test_null_pit_table_raises_unknown_rule_error():
    import pytest

    from src.sim.scoring import DriverLine, PitResult, UnknownRuleError, load_rules, score_constructor

    race = [DriverLine("A", "race")]
    rules = load_rules(2026)
    rules["constructor"]["pit_bands"] = None
    with pytest.raises(UnknownRuleError):
        score_constructor(rules, race, pit=PitResult(seconds=2.1))
    rules = load_rules(2024)
    rules["constructor"]["pit_ranks"] = None
    with pytest.raises(UnknownRuleError):
        score_constructor(rules, race, pit=PitResult(ranks=(1,)))


# season-to-season differences from the spec table: values the YAML files must hold exactly
_SPEC = {
    2023: dict(q_dsq=-15, s_nc=-20, s_dsq=None, r_dsq=-25, c_q=-15, c_s=None, c_r=-25, pit="rank", overall=None, penalty=4, net=False),
    2024: dict(q_dsq=-15, s_nc=-20, s_dsq=None, r_dsq=-25, c_q=-15, c_s=None, c_r=-25, pit="rank", overall=None, penalty=10, net=False),
    2025: dict(q_dsq=-5, s_nc=-20, s_dsq=None, r_dsq=-20, c_q=-10, c_s=None, c_r=-30, pit="time_bands", overall=5, penalty=10, net=False),
    2026: dict(q_dsq=-5, s_nc=-10, s_dsq=-10, r_dsq=None, c_q=-10, c_s=-20, c_r=None, pit="time_bands", overall=5, penalty=10, net=True),
}


def test_season_values_match_spec():
    from src.sim.scoring import load_rules

    for season, e in _SPEC.items():
        r = load_rules(season)
        d, c, t = r["driver"], r["constructor"], r["transfers"]
        got = dict(
            q_dsq=d["qualifying"]["disqualified"], s_nc=d["sprint"]["not_classified"], s_dsq=d["sprint"]["disqualified"],
            r_dsq=d["race"]["disqualified"], c_q=c["disqualified"]["qualifying"], c_s=c["disqualified"]["sprint"],
            c_r=c["disqualified"]["race"], pit=c["pit_scoring"], overall=c["overall_fastest_stop"],
            penalty=t["penalty"], net=t["net"],
        )
        assert got == e, season
        assert c["world_record_stop"] is None
        assert (t["free"], t["carry_max"], t["max_free"]) == (2, 1, 3)
        assert r["team"] == {"budget": 100.0, "drivers": 5, "constructors": 2, "boost_multiplier": 2}
