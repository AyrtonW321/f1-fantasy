from pathlib import Path

import pandas as pd
import pytest

from src.ingest.tracks import blank_ratings, load_tracks, write_template

HEADER = "slug,circuit_type,overtaking_difficulty,notes\n"


def _races(*slugs: str) -> pd.DataFrame:
    rows = []
    for i, slug in enumerate(slugs):
        rows.append({"season": 2023 + i % 2, "round": i + 1, "slug": slug})
    return pd.DataFrame(rows)


def _csv(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "tracks.csv"
    path.write_text(HEADER + body)
    return path


def test_every_race_slug_has_a_row(tmp_path):
    races = _races("monaco", "silverstone")
    path = _csv(tmp_path, "monaco,street,1,\n")
    with pytest.raises(ValueError, match="silverstone"):
        load_tracks(path, races)


def test_unknown_slug_in_csv_raises(tmp_path):
    races = _races("monaco")
    path = _csv(tmp_path, "monaco,street,1,\natlantis,permanent,3,\n")
    with pytest.raises(ValueError, match="atlantis"):
        load_tracks(path, races)


def test_duplicate_slug_raises(tmp_path):
    races = _races("monaco")
    path = _csv(tmp_path, "monaco,street,1,\nmonaco,street,2,\n")
    with pytest.raises(ValueError, match="monaco"):
        load_tracks(path, races)


def test_distinct_slugs_across_seasons_load_once_each(tmp_path):
    races = _races("monaco", "monaco", "spa")
    path = _csv(tmp_path, "monaco,street,1,\nspa,permanent,4,\n")
    df = load_tracks(path, races)
    assert sorted(df["slug"]) == ["monaco", "spa"]


def test_valid_csv_loads_typed_columns(tmp_path):
    races = _races("monaco", "spa")
    path = _csv(tmp_path, "monaco,street,1,tight\nspa,permanent,4,\n")
    df = load_tracks(path, races)
    assert list(df.columns) == ["slug", "circuit_type", "overtaking_difficulty", "notes"]
    assert df.loc[df["slug"] == "spa", "overtaking_difficulty"].iloc[0] == 4
    assert df.loc[df["slug"] == "monaco", "notes"].iloc[0] == "tight"


def test_blank_rating_is_nan_and_reported(tmp_path):
    races = _races("monaco", "spa", "suzuka")
    path = _csv(tmp_path, "monaco,,1,\nspa,permanent,,\nsuzuka,permanent,3,\n")
    df = load_tracks(path, races)
    assert pd.isna(df.loc[df["slug"] == "monaco", "circuit_type"].iloc[0])
    assert pd.isna(df.loc[df["slug"] == "spa", "overtaking_difficulty"].iloc[0])
    assert blank_ratings(df) == ["monaco", "spa"]


def test_fully_rated_csv_has_no_blank_ratings(tmp_path):
    races = _races("monaco")
    path = _csv(tmp_path, "monaco,street,1,\n")
    assert blank_ratings(load_tracks(path, races)) == []


@pytest.mark.parametrize("value", ["0", "6", "2.5", "abc"])
def test_overtaking_out_of_range_or_non_integer_raises(tmp_path, value):
    races = _races("monaco")
    path = _csv(tmp_path, f"monaco,street,{value},\n")
    with pytest.raises(ValueError, match="monaco"):
        load_tracks(path, races)


def test_bad_circuit_type_raises(tmp_path):
    races = _races("monaco")
    path = _csv(tmp_path, "monaco,city,1,\n")
    with pytest.raises(ValueError, match="city"):
        load_tracks(path, races)


def test_template_contains_each_slug_once_sorted_and_blank(tmp_path):
    races = _races("spa", "monaco", "spa", "suzuka")
    out = tmp_path / "static" / "tracks.csv"
    write_template(races, out)
    raw = pd.read_csv(out, dtype=str, keep_default_na=False)
    assert list(raw.columns) == ["slug", "circuit_type", "overtaking_difficulty", "notes"]
    assert list(raw["slug"]) == ["monaco", "spa", "suzuka"]
    assert (raw["circuit_type"] == "").all()
    assert (raw["overtaking_difficulty"] == "").all()
    assert (raw["notes"] == "").all()


def test_template_is_loadable_and_lists_all_blank(tmp_path):
    races = _races("spa", "monaco")
    out = tmp_path / "tracks.csv"
    write_template(races, out)
    df = load_tracks(out, races)
    assert blank_ratings(df) == ["monaco", "spa"]


def test_template_refuses_to_overwrite(tmp_path):
    out = tmp_path / "tracks.csv"
    out.write_text(HEADER + "monaco,street,1,hand made\n")
    before = out.read_text()
    with pytest.raises(FileExistsError):
        write_template(_races("monaco"), out)
    assert out.read_text() == before
