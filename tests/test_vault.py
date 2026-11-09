from pathlib import Path

import pytest

from src.ingest.vault import seal, unseal, MissingKeyError, MAX_ARCHIVE_BYTES

FAKE_KEY = "fake-key-for-tests-only"
OTHER_KEY = "another-fake-key-for-tests"


@pytest.fixture
def raw_tree(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    (raw / "official" / "2026" / "drivers").mkdir(parents=True)
    (raw / "official" / "2026" / "drivers" / "1.json").write_text('{"good": 1}')
    (raw / "top.txt").write_text("top level")
    return raw


def _tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_seal_unseal_round_trip(tmp_path, raw_tree, monkeypatch):
    monkeypatch.setenv("F1_DATA_KEY", FAKE_KEY)
    archive = tmp_path / "raw.tar.gz.enc"
    restored = tmp_path / "restored"

    seal(raw_tree, archive)
    unseal(archive, restored)

    assert _tree(restored) == _tree(raw_tree)


def test_archive_contains_no_plaintext(tmp_path, raw_tree, monkeypatch):
    monkeypatch.setenv("F1_DATA_KEY", FAKE_KEY)
    marker = "PLAINTEXT-MARKER-7f3a9c"
    (raw_tree / "official" / "2026" / "drivers" / "1.json").write_text(f'{{"marker": "{marker}"}}')
    archive = tmp_path / "raw.tar.gz.enc"

    seal(raw_tree, archive)

    data = archive.read_bytes()
    assert data.startswith(b"Salted__")  # openssl enc header; a plain tar.gz would not
    assert marker.encode() not in data


def test_wrong_key_keeps_existing_raw(tmp_path, raw_tree, monkeypatch):
    monkeypatch.setenv("F1_DATA_KEY", FAKE_KEY)
    archive = tmp_path / "raw.tar.gz.enc"
    seal(raw_tree, archive)

    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "keep.txt").write_text("original")

    monkeypatch.setenv("F1_DATA_KEY", OTHER_KEY)
    with pytest.raises(RuntimeError):
        unseal(archive, existing)

    assert _tree(existing) == {"keep.txt": b"original"}


def test_missing_key_raises(tmp_path, raw_tree, monkeypatch):
    archive = tmp_path / "raw.tar.gz.enc"

    monkeypatch.delenv("F1_DATA_KEY", raising=False)
    with pytest.raises(MissingKeyError, match="F1_DATA_KEY"):
        seal(raw_tree, archive)
    with pytest.raises(MissingKeyError, match="F1_DATA_KEY"):
        unseal(archive, tmp_path / "out")

    monkeypatch.setenv("F1_DATA_KEY", "")
    with pytest.raises(MissingKeyError, match="F1_DATA_KEY"):
        seal(raw_tree, archive)
    assert not archive.exists()


def test_oversize_keeps_old_archive(tmp_path, raw_tree, monkeypatch):
    monkeypatch.setenv("F1_DATA_KEY", FAKE_KEY)
    archive = tmp_path / "raw.tar.gz.enc"
    archive.write_bytes(b"old archive")
    monkeypatch.setattr("src.ingest.vault.MAX_ARCHIVE_BYTES", 10)

    with pytest.raises(RuntimeError):
        seal(raw_tree, archive)

    assert archive.read_bytes() == b"old archive"
