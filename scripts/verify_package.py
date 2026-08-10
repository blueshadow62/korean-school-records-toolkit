#!/usr/bin/env python3
"""Verify plugin structure, provenance, and basic safety invariants."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


EXPECTED_SKILLS = {
    "write-school-records",
    "korean-character-count",
}
EXPECTED_RELEASE_VERSION = "2.0.0"
IGNORED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    "dist",
    ".git",
    ".superpowers",
    "superpowers",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}"),
)
LOCAL_ONLY_FILES = {"SOURCE_METADATA.local.json"}
WRITE_SCHOOL_RECORDS_LICENSE_MARKERS = ("CC BY-NC-SA 4.0", "류기현")


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


def verify_achievement_sources(root: Path, errors: list[str]) -> None:
    corpus = root / "skills" / "write-school-records" / "references" / "achievement-standards"
    attribution_path = corpus / "ATTRIBUTION.md"
    catalog_path = corpus / "sources.json"
    try:
        attribution = attribution_path.read_text(encoding="utf-8")
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Invalid achievement-standards source information: {error}")
        return
    if catalog.get("distribution") != "public":
        errors.append("Achievement-standards catalog must declare public distribution")
    for marker in (
        "NCIC 국가교육과정정보센터",
        "NKIS 연구정보",
        "공공누리 제1유형",
        "공공누리 제2유형",
    ):
        if marker not in attribution:
            errors.append(f"Achievement-standards attribution is missing: {marker}")


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
    metadata_path = root / "SOURCE_METADATA.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Invalid public source metadata: {error}")
    else:
        if metadata.get("plugin_version") != EXPECTED_RELEASE_VERSION:
            errors.append(f"Public source metadata version must be {EXPECTED_RELEASE_VERSION}")
        if {skill.get("name") for skill in metadata.get("skills", [])} != EXPECTED_SKILLS:
            errors.append("Public source metadata must list exactly the two bundled skills")
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


def verify_archives_absent(root: Path, errors: list[str]) -> None:
    archives = [path.relative_to(root) for path in root.rglob("*.zip") if path.is_file()]
    archive_checksums = [path.relative_to(root) for path in root.rglob("*.zip.sha256") if path.is_file()]
    if archives or archive_checksums:
        errors.append(f"ZIP artifacts must be absent: {archives + archive_checksums}")


def scan_text_files(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative_path.parts):
            continue
        if path.suffix.lower() in {".pyc", ".zip"}:
            errors.append(f"Excluded artifact present: {relative_path}")
            continue
        relative = relative_path.as_posix()
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
    verify_achievement_sources(root, errors)
    verify_release_contract(root, errors)
    verify_archives_absent(root, errors)
    scan_text_files(root, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(f"Package verification passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
