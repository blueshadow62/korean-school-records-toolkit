#!/usr/bin/env python3
"""Transactionally install, verify, uninstall, or roll back bundled skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


SKILL_NAMES = (
    "write-school-records",
    "korean-character-count",
)
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".log"}


class BundleError(RuntimeError):
    pass


def iter_payload_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        yield relative, path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def tree_manifest(root: Path) -> dict[str, str]:
    return {relative.as_posix(): sha256(path) for relative, path in iter_payload_files(root)}


def payload_root() -> Path:
    return Path(__file__).resolve().parents[1] / "skills"


def validate_payload() -> None:
    root = payload_root()
    missing = [name for name in SKILL_NAMES if not (root / name / "SKILL.md").is_file()]
    if missing:
        raise BundleError(f"Bundled skill payload is incomplete: {', '.join(missing)}")


def default_install_root() -> Path:
    return Path.home() / ".codex" / "skills"


def default_backup_root() -> Path:
    return Path.home() / "CodexSkillBackups" / "korean-school-records-toolkit"


def validate_install_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise BundleError(f"Refusing broad install root: {resolved}")
    return resolved


def compare_skill(source: Path, installed: Path) -> list[str]:
    if not installed.is_dir():
        return ["missing directory"]
    source_files = tree_manifest(source)
    installed_files = tree_manifest(installed)
    issues = []
    for relative in sorted(set(source_files) | set(installed_files)):
        if relative not in installed_files:
            issues.append(f"missing: {relative}")
        elif relative not in source_files:
            issues.append(f"unexpected: {relative}")
        elif source_files[relative] != installed_files[relative]:
            issues.append(f"hash mismatch: {relative}")
    return issues


def verify_install(install_root: Path) -> None:
    validate_payload()
    failures = []
    for name in SKILL_NAMES:
        issues = compare_skill(payload_root() / name, install_root / name)
        failures.extend(f"{name}: {issue}" for issue in issues)
    if failures:
        raise BundleError("Installed bundle verification failed:\n" + "\n".join(failures))
    print(f"Verification passed: {install_root}")


def timestamped_backup(backup_root: Path, operation: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = backup_root / f"{stamp}-{operation}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_backup_metadata(path: Path, operation: str, install_root: Path, present: dict[str, bool]) -> None:
    metadata = {
        "operation": operation,
        "install_root": str(install_root),
        "skills": {name: {"previously_present": present[name]} for name in SKILL_NAMES},
    }
    (path / "backup.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def all_skills_match(install_root: Path) -> bool:
    return all(not compare_skill(payload_root() / name, install_root / name) for name in SKILL_NAMES)


def install_bundle(install_root: Path, backup_root: Path) -> None:
    validate_payload()
    install_root.mkdir(parents=True, exist_ok=True)
    if all_skills_match(install_root):
        print(f"Already installed and verified: {install_root}")
        return

    stage = Path(tempfile.mkdtemp(prefix=".korean-school-records-stage-", dir=install_root.parent))
    backup = timestamped_backup(backup_root, "install")
    present = {name: (install_root / name).exists() for name in SKILL_NAMES}
    write_backup_metadata(backup, "install", install_root, present)
    committed: list[str] = []
    moved_existing: list[str] = []
    try:
        for name in SKILL_NAMES:
            shutil.copytree(payload_root() / name, stage / name)
            if compare_skill(payload_root() / name, stage / name):
                raise BundleError(f"Staging verification failed for {name}")
        for name in SKILL_NAMES:
            target = install_root / name
            if target.exists():
                shutil.move(str(target), str(backup / name))
                moved_existing.append(name)
        for name in SKILL_NAMES:
            shutil.move(str(stage / name), str(install_root / name))
            committed.append(name)
        verify_install(install_root)
    except Exception:
        for name in reversed(committed):
            target = install_root / name
            if target.exists():
                shutil.rmtree(target)
        for name in reversed(moved_existing):
            saved = backup / name
            if saved.exists():
                shutil.move(str(saved), str(install_root / name))
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f"Installation complete. Backup: {backup}")


def uninstall_bundle(install_root: Path, backup_root: Path) -> None:
    present = {name: (install_root / name).exists() for name in SKILL_NAMES}
    if not any(present.values()):
        print(f"Bundle is already absent: {install_root}")
        return
    backup = timestamped_backup(backup_root, "uninstall")
    write_backup_metadata(backup, "uninstall", install_root, present)
    moved: list[str] = []
    try:
        for name in SKILL_NAMES:
            target = install_root / name
            if target.exists():
                shutil.move(str(target), str(backup / name))
                moved.append(name)
    except Exception:
        for name in reversed(moved):
            saved = backup / name
            if saved.exists():
                shutil.move(str(saved), str(install_root / name))
        raise
    print(f"Uninstall complete. Recoverable backup: {backup}")


def latest_backup(backup_root: Path) -> Path:
    candidates = sorted(
        (path for path in backup_root.iterdir() if path.is_dir() and (path / "backup.json").is_file()),
        reverse=True,
    ) if backup_root.is_dir() else []
    if not candidates:
        raise BundleError(f"No rollback backup found under {backup_root}")
    return candidates[0]


def rollback_bundle(install_root: Path, backup_root: Path, selected_backup: Path | None) -> None:
    backup = selected_backup.resolve() if selected_backup else latest_backup(backup_root)
    metadata_path = backup / "backup.json"
    if not metadata_path.is_file():
        raise BundleError(f"Rollback metadata missing: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    recorded_root = Path(metadata["install_root"]).resolve()
    if recorded_root != install_root:
        raise BundleError(f"Backup belongs to a different install root: {recorded_root}")

    stage = Path(tempfile.mkdtemp(prefix=".korean-school-records-rollback-", dir=install_root.parent))
    moved_current: list[str] = []
    restored: list[str] = []
    try:
        for name in SKILL_NAMES:
            target = install_root / name
            if target.exists():
                shutil.move(str(target), str(stage / name))
                moved_current.append(name)
        for name in SKILL_NAMES:
            if metadata["skills"][name]["previously_present"]:
                saved = backup / name
                if not saved.is_dir():
                    raise BundleError(f"Backup payload missing: {saved}")
                shutil.copytree(saved, install_root / name)
                restored.append(name)
    except Exception:
        for name in reversed(restored):
            target = install_root / name
            if target.exists():
                shutil.rmtree(target)
        for name in reversed(moved_current):
            shutil.move(str(stage / name), str(install_root / name))
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    print(f"Rollback complete from: {backup}")


def dry_run(install_root: Path, backup_root: Path) -> None:
    validate_payload()
    print(f"Package: {payload_root().parent}")
    print(f"Install root: {install_root}")
    print(f"Backup root: {backup_root}")
    for name in SKILL_NAMES:
        target = install_root / name
        state = "replace" if target.exists() else "add"
        print(f"{state}: {target}")
    print("No files changed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--dry-run", action="store_true")
    actions.add_argument("--install", action="store_true")
    actions.add_argument("--verify", action="store_true")
    actions.add_argument("--uninstall", action="store_true")
    actions.add_argument("--rollback", action="store_true")
    parser.add_argument("--install-root", type=Path, default=default_install_root())
    parser.add_argument("--backup-root", type=Path, default=default_backup_root())
    parser.add_argument("--backup", type=Path, help="Specific backup directory for rollback.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        install_root = validate_install_root(args.install_root)
        backup_root = args.backup_root.expanduser().resolve()
        if args.dry_run:
            dry_run(install_root, backup_root)
        elif args.install:
            install_bundle(install_root, backup_root)
        elif args.verify:
            verify_install(install_root)
        elif args.uninstall:
            uninstall_bundle(install_root, backup_root)
        else:
            rollback_bundle(install_root, backup_root, args.backup)
        return 0
    except (BundleError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
