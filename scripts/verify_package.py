#!/usr/bin/env python3
"""Verify plugin structure, file checksums, and basic safety invariants."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


EXPECTED_SKILLS = {
    "write-school-records",
    "korean-character-count",
    "korean-spell-check",
}
EXPECTED_RELEASE_VERSION = "1.1.0"
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}"),
)
LOCAL_ONLY_FILES = {"SOURCE_METADATA.local.json"}
EXPECTED_SPELL_FIXTURES = {
    "blocked_response.html",
    "current_response.html",
    "multiple_corrections.html",
    "service_error_response.html",
    "success_with_corrections.html",
    "success_without_corrections.html",
    "unexpected_response.html",
}
WRITE_SCHOOL_RECORDS_LICENSE_MARKERS = ("MIT License", "Copyright © 2026 blueshadow62")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def parse_checksum_file(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9A-Fa-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"Malformed checksum line {line_number}")
        digest, relative = match.groups()
        if relative in entries:
            raise ValueError(f"Duplicate checksum entry: {relative}")
        entries[relative] = digest.upper()
    return entries


def frontmatter_name(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    match = re.search(r"(?m)^name:\s*([^\r\n]+)$", text)
    if not match:
        raise ValueError(f"Missing frontmatter name: {skill_md}")
    return match.group(1).strip().strip("'\"")


def verify_manifest(root: Path, errors: list[str]) -> None:
    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Invalid plugin manifest: {error}")
        return
    if manifest.get("name") != "korean-school-records-toolkit":
        errors.append("Unexpected plugin name")
    if manifest.get("version") != (root / "VERSION").read_text(encoding="utf-8").strip():
        errors.append("Manifest version and VERSION differ")
    if manifest.get("skills") != "./skills/":
        errors.append("Manifest skills path must be ./skills/")


def verify_claude_manifest(root: Path, errors: list[str]) -> None:
    manifest_path = root / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Invalid Claude Code plugin manifest: {error}")
        return
    if manifest.get("name") != "korean-school-records-toolkit":
        errors.append("Unexpected Claude Code plugin name")
    if manifest.get("version") != (root / "VERSION").read_text(encoding="utf-8").strip():
        errors.append("Claude Code manifest version and VERSION differ")
    if manifest.get("skills") != "./skills/":
        errors.append("Claude Code manifest skills path must be ./skills/")


def verify_skills(root: Path, errors: list[str]) -> None:
    skills_root = root / "skills"
    actual = {path.name for path in skills_root.iterdir() if path.is_dir()}
    if actual != EXPECTED_SKILLS:
        errors.append(f"Skill set mismatch: {sorted(actual)}")
    names = []
    for directory_name in sorted(EXPECTED_SKILLS & actual):
        skill_md = skills_root / directory_name / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"Missing SKILL.md: {directory_name}")
            continue
        try:
            name = frontmatter_name(skill_md)
        except ValueError as error:
            errors.append(str(error))
            continue
        names.append(name)
        if name != directory_name:
            errors.append(f"Skill folder/name mismatch: {directory_name} != {name}")
    if len(names) != len(set(names)):
        errors.append("Duplicate skill names")


def verify_release_contract(root: Path, errors: list[str]) -> None:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if version != EXPECTED_RELEASE_VERSION:
        errors.append(f"Expected release version {EXPECTED_RELEASE_VERSION}, got {version}")
    license_path = root / "skills" / "write-school-records" / "LICENSE"
    if not license_path.is_file():
        errors.append("Missing write-school-records/LICENSE")
    else:
        license_text = license_path.read_text(encoding="utf-8")
        if not all(marker in license_text for marker in WRITE_SCHOOL_RECORDS_LICENSE_MARKERS):
            errors.append("write-school-records/LICENSE does not match the approved notice")
    fixture_root = root / "skills" / "korean-spell-check" / "tests" / "fixtures"
    fixtures = {path.name for path in fixture_root.iterdir() if path.is_file()} if fixture_root.is_dir() else set()
    if fixtures != EXPECTED_SPELL_FIXTURES:
        errors.append(f"Spell-check fixture set mismatch: {sorted(fixtures)}")
    metadata_path = root / "SOURCE_METADATA.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Invalid public source metadata: {error}")
    else:
        if metadata.get("plugin_version") != EXPECTED_RELEASE_VERSION:
            errors.append(f"Public source metadata version must be {EXPECTED_RELEASE_VERSION}")
        if "source_path" in metadata_path.read_text(encoding="utf-8"):
            errors.append("Public source metadata contains a local source_path")
    claude_readme = root / "README_CLAUDE_CODE.md"
    try:
        claude_text = claude_readme.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"Missing Claude Code installation README: {error}")
    else:
        for command in ("claude plugin validate . --strict", "claude --plugin-dir ."):
            if command not in claude_text:
                errors.append(f"Claude Code installation README is missing: {command}")


def verify_checksums(root: Path, errors: list[str]) -> None:
    checksum_path = root / "checksums.sha256"
    try:
        entries = parse_checksum_file(checksum_path)
    except (OSError, ValueError) as error:
        errors.append(f"Unable to read checksums: {error}")
        return
    for relative, expected in entries.items():
        path = root / Path(relative)
        try:
            resolved = path.resolve()
            resolved.relative_to(root.resolve())
        except ValueError:
            errors.append(f"Checksum path escapes package: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Checksum target missing: {relative}")
        elif sha256(path) != expected:
            errors.append(f"Checksum mismatch: {relative}")
    expected_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.name != "checksums.sha256"
        and path.relative_to(root).as_posix() not in LOCAL_ONLY_FILES
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and path.suffix.lower() not in {".pyc", ".log", ".zip"}
    }
    if set(entries) != expected_files:
        missing = sorted(expected_files - set(entries))
        extra = sorted(set(entries) - expected_files)
        errors.append(f"Checksum inventory mismatch: missing={missing}, extra={extra}")


def scan_text_files(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.name == "checksums.sha256":
            continue
        if "__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".zip"}:
            errors.append(f"Excluded artifact present: {path.relative_to(root)}")
            continue
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() not in {".md", ".py", ".js", ".json", ".yaml", ".yml", ""}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"Possible secret in {path.relative_to(root)}")
        if path.suffix.lower() in {".py", ".js"} and re.search(r"C:\\\\Users\\\\[^\\\s'\"]+", text):
            errors.append(f"Executable contains a user-specific absolute path: {path.relative_to(root)}")
        if relative not in LOCAL_ONLY_FILES and re.search(r"(?i)C:[\\/]Users[\\/][^\\/ \r\n]+", text):
            errors.append(f"Public package text contains a user-specific absolute path: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path, nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.plugin_root.resolve()
    errors: list[str] = []
    verify_manifest(root, errors)
    verify_claude_manifest(root, errors)
    verify_skills(root, errors)
    verify_release_contract(root, errors)
    verify_checksums(root, errors)
    scan_text_files(root, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(f"Package verification passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
