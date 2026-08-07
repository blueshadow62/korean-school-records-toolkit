#!/usr/bin/env python3
"""Build integrity metadata and the repo-marketplace distribution archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import date
from pathlib import Path


IGNORED_PARTS = {"__pycache__", ".pytest_cache", "dist", ".git"}
IGNORED_SUFFIXES = {".pyc", ".log"}
LOCAL_ONLY_FILES = {"SOURCE_METADATA.local.json"}
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
CLAUDE_ROOT_FILES = {
    "CHANGELOG.md",
    "LICENSE",
    "README_CLAUDE_CODE.md",
    "VERSION",
}

SOURCE_DETAILS = {
    "write-school-records": {
        "source_type": "development baseline",
        "source_identifier": "development-baseline:write-school-records",
        "test_status": "See TEST_REPORT.md",
        "selection_reason": "Required development baseline with the verified component license notice.",
    },
    "korean-character-count": {
        "source_type": "existing 1.0.0 source selection",
        "source_identifier": "existing-1.0.0-source:korean-character-count",
        "test_status": "See TEST_REPORT.md",
        "selection_reason": "Preserves the source selected for 1.0.0 without payload changes.",
    },
    "korean-spell-check": {
        "source_type": "validated development baseline",
        "source_identifier": "validated-development-baseline:korean-spell-check",
        "test_status": "See TEST_REPORT.md",
        "selection_reason": "Matches the recovered baseline and its P1-P10 fixture contract.",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def files(root: Path, *, skip_generated: bool = False):
    generated = {"checksums.sha256", "PACKAGE_CONTENTS.txt"} if skip_generated else set()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in generated:
            continue
        relative = path.relative_to(root)
        if relative.as_posix() in LOCAL_ONLY_FILES:
            continue
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        yield relative, path


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for relative, path in files(root):
        digest.update(f"{sha256(path)}  {relative.as_posix()}\n".encode("utf-8"))
    return digest.hexdigest().upper()


def normalized_tree_hash(root: Path) -> str:
    """Match the lowercase per-file hash contract used by the spell-check recovery report."""
    digest = hashlib.sha256()
    for relative, path in files(root):
        digest.update(f"{sha256(path).lower()}  {relative.as_posix()}\n".encode("utf-8"))
    return digest.hexdigest().lower()


def parse_sources(values: list[str]) -> dict[str, Path]:
    sources = {}
    for value in values:
        name, separator, raw_path = value.partition("=")
        if not separator or not name or not raw_path:
            raise ValueError(f"Expected NAME=PATH, got: {value}")
        sources[name] = Path(raw_path).resolve()
    return sources


def compare_source(plugin_root: Path, name: str, source: Path) -> dict:
    packaged = plugin_root / "skills" / name
    source_files = {rel.as_posix(): sha256(path) for rel, path in files(source)}
    package_files = {rel.as_posix(): sha256(path) for rel, path in files(packaged)}
    if source_files != package_files:
        missing = sorted(set(source_files) - set(package_files))
        extra = sorted(set(package_files) - set(source_files))
        changed = sorted(key for key in set(source_files) & set(package_files) if source_files[key] != package_files[key])
        raise ValueError(f"Source mismatch for {name}: missing={missing}, extra={extra}, changed={changed}")
    result = {
        "name": name,
        "declared_version": "not declared",
        "file_count": len(source_files),
        "tree_sha256": tree_hash(source),
        "package_tree_sha256": tree_hash(packaged),
        "normalized_tree_sha256": normalized_tree_hash(source),
        "package_normalized_tree_sha256": normalized_tree_hash(packaged),
    }
    result.update(SOURCE_DETAILS[name])
    return result


def write_metadata(
    plugin_root: Path,
    sources: dict[str, Path],
    build_date: str,
    spell_validation_report: Path,
) -> None:
    metadata = {
        "plugin_name": "korean-school-records-toolkit",
        "plugin_version": (plugin_root / "VERSION").read_text(encoding="utf-8").strip(),
        "build_date": build_date,
        "compatible_environment": (
            "Codex plugin schema and Claude Code plugin layout; "
            "see INSTALL.md and README_CLAUDE_CODE.md"
        ),
        "spell_validation_report": spell_validation_report.name,
        "final_validation_status": "See TEST_REPORT.md",
        "external_service_dependency": (
            "korean-spell-check uses the Nara/PNU public web surface at low request volume."
        ),
        "approval_behavior": (
            "Denied approval or service failure is reported as incomplete inspection, "
            "not as success or no spelling errors."
        ),
        "dependencies": {
            "write-school-records": "Python 3 standard library; local reference files",
            "korean-character-count": "Node.js 18+; no network",
            "korean-spell-check": "Python 3.10+ standard library; network access to nara-speller.co.kr",
        },
        "skills": [compare_source(plugin_root, name, source) for name, source in sorted(sources.items())],
    }
    (plugin_root / "SOURCE_METADATA.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    local_metadata = {
        "plugin_version": metadata["plugin_version"],
        "build_date": build_date,
        "source_paths": {name: str(path) for name, path in sorted(sources.items())},
        "spell_validation_report": str(spell_validation_report.resolve()),
        "note": "Local reproduction metadata; intentionally excluded from the public ZIP.",
    }
    (plugin_root / "SOURCE_METADATA.local.json").write_text(
        json.dumps(local_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_inventory(plugin_root: Path) -> None:
    inventory = [relative.as_posix() for relative, _ in files(plugin_root, skip_generated=True)]
    inventory.append("PACKAGE_CONTENTS.txt")
    inventory.append("checksums.sha256")
    (plugin_root / "PACKAGE_CONTENTS.txt").write_text("\n".join(sorted(inventory)) + "\n", encoding="utf-8")
    checksum_lines = [
        f"{sha256(path)}  {relative.as_posix()}"
        for relative, path in files(plugin_root)
        if relative.as_posix() != "checksums.sha256"
    ]
    (plugin_root / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def build_archive(plugin_root: Path, repo_root: Path, dist_root: Path) -> Path:
    version = (plugin_root / "VERSION").read_text(encoding="utf-8").strip()
    archive = dist_root / f"korean-school-records-toolkit-{version}.zip"
    dist_root.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    marketplace = repo_root / ".agents" / "plugins" / "marketplace.json"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        write_zip_entry(bundle, marketplace.relative_to(repo_root).as_posix(), marketplace.read_bytes())
        for relative, path in files(plugin_root):
            archive_path = Path("plugins") / "korean-school-records-toolkit" / relative
            write_zip_entry(bundle, archive_path.as_posix(), path.read_bytes())
    return archive


def build_claude_archive(plugin_root: Path, dist_root: Path) -> Path:
    version = (plugin_root / "VERSION").read_text(encoding="utf-8").strip()
    archive = dist_root / f"korean-school-records-toolkit-claude-code-{version}.zip"
    dist_root.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for relative, path in files(plugin_root):
            if (
                relative.as_posix() in CLAUDE_ROOT_FILES
                or relative.parts[0] in {".claude-plugin", "skills"}
            ):
                write_zip_entry(bundle, relative.as_posix(), path.read_bytes())
    return archive


def write_archive_checksum(archive: Path) -> None:
    archive.with_suffix(".zip.sha256").write_text(
        f"{sha256(archive)}  {archive.name}\n",
        encoding="utf-8",
    )


def write_zip_entry(bundle: zipfile.ZipFile, archive_path: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(archive_path, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    bundle.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--dist-root", type=Path, required=True)
    parser.add_argument("--source", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--build-date", default=date.today().isoformat())
    parser.add_argument("--spell-validation-report", type=Path, required=True)
    args = parser.parse_args()
    plugin_root = args.plugin_root.resolve()
    sources = parse_sources(args.source)
    if set(sources) != {"write-school-records", "korean-character-count", "korean-spell-check"}:
        raise SystemExit("All three --source NAME=PATH arguments are required")
    try:
        date.fromisoformat(args.build_date)
    except ValueError as error:
        raise SystemExit(f"--build-date must use YYYY-MM-DD: {error}") from error
    write_metadata(
        plugin_root,
        sources,
        args.build_date,
        args.spell_validation_report,
    )
    write_inventory(plugin_root)
    dist_root = args.dist_root.resolve()
    archives = [
        build_archive(plugin_root, args.repo_root.resolve(), dist_root),
        build_claude_archive(plugin_root, dist_root),
    ]
    for archive in archives:
        write_archive_checksum(archive)
        print(f"Built: {archive}")
        print(f"SHA-256: {sha256(archive)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
