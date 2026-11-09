"""Encrypted archive of data/raw: seal to data/raw.tar.gz.enc, unseal back.

Uses the OpenSSL CLI (AES-256-CBC, PBKDF2). The key comes only from the
F1_DATA_KEY env var and reaches openssl only through the child's environment.
Plaintext lives only in system temp dirs, never inside the repo.
"""

import argparse
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

KEY_VAR = "F1_DATA_KEY"
MAX_ARCHIVE_BYTES = 95_000_000
_CIPHER = ["-aes-256-cbc", "-pbkdf2", "-iter", "600000"]


class MissingKeyError(Exception):
    """F1_DATA_KEY is unset or empty."""


def _key() -> str:
    key = os.environ.get(KEY_VAR, "")
    if not key:
        raise MissingKeyError(f"{KEY_VAR} is not set or empty")
    return key


def _openssl() -> str:
    path = shutil.which("openssl")
    if path is None:
        raise RuntimeError("openssl not found on PATH; install the OpenSSL CLI")
    return path


def _openssl_enc(openssl: str, key: str, *args: str) -> None:
    cmd = [openssl, "enc", *args, "-pass", f"env:{KEY_VAR}"]
    proc = subprocess.run(cmd, env={**os.environ, KEY_VAR: key}, capture_output=True, check=False)
    if proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"openssl enc failed (exit {proc.returncode}): {detail}")


def _swap_in(staged: Path, raw_dir: Path, previous: Path) -> None:
    """Replace raw_dir with staged; put the old raw_dir back if the move fails."""
    raw_dir.parent.mkdir(parents=True, exist_ok=True)
    if raw_dir.exists():
        os.replace(raw_dir, previous)
    try:
        shutil.move(str(staged), str(raw_dir))
    except BaseException:
        if previous.exists():
            shutil.rmtree(raw_dir, ignore_errors=True)
            shutil.move(str(previous), str(raw_dir))
        raise


def seal(raw_dir: Path, archive: Path) -> None:
    key = _key()
    openssl = _openssl()
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        plain = tmp / "raw.tar.gz"
        enc = tmp / "raw.tar.gz.enc"
        with tarfile.open(plain, "w:gz") as tar:
            for child in sorted(Path(raw_dir).iterdir()):
                tar.add(str(child), arcname=child.name)
        _openssl_enc(openssl, key, "-salt", *_CIPHER, "-in", str(plain), "-out", str(enc))
        size = enc.stat().st_size
        if size > MAX_ARCHIVE_BYTES:
            raise RuntimeError(
                f"encrypted archive is {size} bytes, over the {MAX_ARCHIVE_BYTES}-byte limit; "
                "existing archive left unchanged"
            )
        os.replace(enc, archive)


def unseal(archive: Path, raw_dir: Path) -> None:
    key = _key()
    openssl = _openssl()
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        plain = tmp / "raw.tar.gz"
        staged = tmp / "staged"
        staged.mkdir()
        _openssl_enc(openssl, key, "-d", *_CIPHER, "-in", str(archive), "-out", str(plain))
        try:
            with tarfile.open(plain, "r:gz") as tar:
                tar.extractall(staged, filter="data")
        except Exception as exc:
            raise RuntimeError("archive could not be extracted (wrong key or corrupt data)") from exc
        _swap_in(staged, Path(raw_dir), tmp / "previous")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m src.ingest.vault")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("seal", "unseal"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
        cmd.add_argument("--archive", type=Path, default=Path("data/raw.tar.gz.enc"))
    args = parser.parse_args(argv)
    if args.command == "seal":
        seal(args.raw_dir, args.archive)
    else:
        unseal(args.archive, args.raw_dir)
    print(f"{args.command} ok: {args.raw_dir} <-> {args.archive}")


if __name__ == "__main__":
    main()
