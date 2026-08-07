#!/usr/bin/env python3
"""Synchronize this development skill with the user Codex installation."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


EXCLUDED_DIRS = {"__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".log"}


class SyncError(Exception):
    """An expected path or synchronization error."""


def default_install_dir() -> Path:
    return Path.home() / ".codex" / "skills" / "write-school-records"


def default_backup_dir() -> Path:
    return Path.home() / "CodexSkillBackups" / "write-school-records"


def is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDED_DIRS) or path.suffix.lower() in EXCLUDED_SUFFIXES


def files_under(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        raise SyncError(f"기준본 또는 설치본 폴더가 없습니다: {root}")
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise SyncError(f"심볼릭 링크는 동기화하지 않습니다: {path}")
        if path.is_file() and not is_excluded(path.relative_to(root)):
            result[path.relative_to(root).as_posix()] = path
    return dict(sorted(result.items()))


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def compare(source: Path, install: Path) -> tuple[list[str], list[str], list[str]]:
    source_files = files_under(source)
    install_files = files_under(install) if install.exists() else {}
    added = sorted(set(source_files) - set(install_files))
    removed = sorted(set(install_files) - set(source_files))
    changed = sorted(
        name for name in set(source_files) & set(install_files)
        if digest(source_files[name]) != digest(install_files[name])
    )
    return added, changed, removed


def validate_paths(source: Path, install: Path) -> tuple[Path, Path]:
    source = source.resolve()
    install = install.resolve()
    home = Path.home().resolve()
    try:
        install.relative_to(home)
    except ValueError as error:
        raise SyncError(f"설치 경로는 사용자 홈 안이어야 합니다: {install}") from error
    if source == install:
        raise SyncError("기준본 자체를 설치 대상으로 지정할 수 없습니다.")
    if not (source / "SKILL.md").is_file():
        raise SyncError(f"기준본 SKILL.md가 없습니다: {source}")
    return source, install


def print_plan(source: Path, install: Path) -> tuple[list[str], list[str], list[str]]:
    added, changed, removed = compare(source, install)
    print(f"기준본: {source}")
    print(f"설치본: {install}")
    for label, names in (("추가", added), ("변경", changed), ("삭제", removed)):
        for name in names:
            print(f"{label}: {name}")
    if not any((added, changed, removed)):
        print("차이 없음")
    return added, changed, removed


def copy_file_atomic(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream, source.open("rb") as source_stream:
            shutil.copyfileobj(source_stream, stream)
            stream.flush()
            os.fsync(stream.fileno())
        shutil.copystat(source, temp_name)
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def backup_install(install: Path, backup_root: Path) -> Path | None:
    if not install.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_root / stamp / "installed"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(install, backup, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", "*.log"))
    return backup


def restore_backup(install: Path, backup: Path | None) -> None:
    if install.exists():
        shutil.rmtree(install)
    if backup is not None:
        shutil.copytree(backup, install)


def install(source: Path, install_dir: Path, backup_root: Path) -> Path | None:
    added, changed, removed = print_plan(source, install_dir)
    if not any((added, changed, removed)):
        return None
    if removed:
        print("설치 전에 삭제될 파일을 위에 표시했습니다.")
    backup = backup_install(install_dir, backup_root)
    try:
        source_files = files_under(source)
        install_dir.mkdir(parents=True, exist_ok=True)
        for name, source_file in source_files.items():
            copy_file_atomic(source_file, install_dir / Path(name))
        for name in removed:
            (install_dir / Path(name)).unlink()
    except Exception as error:
        try:
            restore_backup(install_dir, backup)
        except Exception as restore_error:
            raise SyncError(f"동기화 실패 후 복구도 실패했습니다: {restore_error}") from error
        raise SyncError(f"동기화 실패. 기존 설치본을 복구했습니다: {error}") from error
    return backup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="개발 기준본(기본: 이 스크립트가 속한 스킬 폴더)")
    parser.add_argument("--install-dir", type=Path, default=default_install_dir())
    parser.add_argument("--backup-dir", type=Path, default=default_backup_dir())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--verify", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_arg = args.source or Path(__file__).resolve().parents[1]
    try:
        source, install_dir = validate_paths(source_arg, args.install_dir)
        if args.dry_run:
            print_plan(source, install_dir)
            return 0
        if args.verify:
            added, changed, removed = compare(source, install_dir)
            if any((added, changed, removed)):
                print_plan(source, install_dir)
                return 2
            print("검증 통과: 기준본과 설치본이 일치합니다.")
            return 0
        backup = install(source, install_dir, args.backup_dir)
        if backup:
            print(f"백업: {backup}")
        print("동기화 완료")
        return 0
    except SyncError as error:
        print(f"오류: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"오류: 파일 작업에 실패했습니다: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
