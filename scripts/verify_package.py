#!/usr/bin/env python3
"""Verify plugin structure, provenance, and basic safety invariants."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


EXPECTED_SKILLS = {
    "write-school-records",
    "korean-character-count",
}
EXPECTED_RELEASE_VERSION = "3.1.0"
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
    for field in ("homepage", "repository"):
        if not str(manifest.get(field, "")).startswith("https://"):
            errors.append(f"Claude Code manifest {field} must be an https:// URL")
    # The directory shows this address as the listing's privacy policy. It must name the PRIVACY.md in this repository.
    expected_privacy_url = f"{manifest.get('repository')}/blob/master/PRIVACY.md"
    if manifest.get("privacyPolicyUrl") != expected_privacy_url:
        errors.append(f"Claude Code manifest privacyPolicyUrl must be {expected_privacy_url}")


def verify_publisher(root: Path, errors: list[str]) -> None:
    """The publisher is written the same way in both manifests and in the Codex interface."""
    try:
        claude = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        codex = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Cannot read plugin manifests: {error}")
        return
    author = claude.get("author", {})
    if codex.get("author") != author:
        errors.append("Codex and Claude Code manifests must name the same author")
    if codex.get("interface", {}).get("developerName") != author.get("name"):
        errors.append("Codex interface.developerName must match author.name")
    if not str(author.get("url", "")).startswith("https://"):
        errors.append("author.url must be an https:// URL")


MARKETPLACE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def verify_marketplace(root: Path, errors: list[str]) -> None:
    """The repository also works as its own marketplace: the full plugin from the repository root
    and the documents-only edition from editions/<name>/."""
    path = root / ".claude-plugin" / "marketplace.json"
    if not path.exists():
        return
    try:
        marketplace = json.loads(path.read_text(encoding="utf-8"))
        manifest = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        edition = json.loads((root / "editions" / "source" / "edition.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Invalid marketplace manifest: {error}")
        return
    name = str(marketplace.get("name", ""))
    if not MARKETPLACE_NAME.match(name) or ".." in name:
        errors.append(f"Marketplace name is not allowed: {name!r}")
    if marketplace.get("owner", {}).get("name") != manifest.get("author", {}).get("name"):
        errors.append("Marketplace owner.name must match plugin.json author.name")
    plugins = marketplace.get("plugins", [])
    expected = [(manifest.get("name"), "./"), (edition.get("name"), f"./editions/{edition.get('name')}")]
    if [(entry.get("name"), entry.get("source")) for entry in plugins] != expected:
        errors.append("Marketplace must list the full plugin (source ./) and then the documents-only edition "
                      "(source ./editions/<name>)")
    descriptions = [str(entry.get("description", "")).strip() for entry in plugins]
    if not all(descriptions) or len(set(descriptions)) != len(descriptions):
        errors.append("Each marketplace entry needs its own description, so that users can tell the editions apart")


def verify_directory_edition(root: Path, errors: list[str]) -> None:
    """The documents-only edition must equal a fresh build and follow the directory file rules."""
    builder_path = Path(__file__).resolve().with_name("build_directory_edition.py")
    spec = importlib.util.spec_from_file_location("build_directory_edition", builder_path)
    if spec is None or spec.loader is None:
        errors.append(f"Cannot load {builder_path.name}")
        return
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    errors.extend(f"Directory edition: {problem}" for problem in builder.check(root))


def verify_bundled_licenses(root: Path, errors: list[str]) -> None:
    """The MIT skill keeps the upstream notice and permission text; the package keeps a security policy and a privacy notice."""
    path = root / "skills" / "korean-character-count" / "LICENSE"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"Missing korean-character-count/LICENSE: {error}")
    else:
        for marker in ("https://github.com/NomaDamas/k-skill", "MIT License", "Copyright (c) 2026",
                       "The above copyright notice and this permission notice shall be included"):
            if marker not in text:
                errors.append(f"korean-character-count/LICENSE is missing: {marker}")
    if not (root / "SECURITY.md").is_file():
        errors.append("Missing SECURITY.md")
    if not (root / "PRIVACY.md").is_file():
        errors.append("Missing PRIVACY.md")


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


def verify_middle_achievement_sources(root: Path, errors: list[str]) -> None:
    corpus = root / "skills" / "write-school-records" / "references" / "achievement-standards-middle"
    try:
        attribution = (corpus / "ATTRIBUTION.md").read_text(encoding="utf-8")
        catalog = json.loads((corpus / "sources.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"Invalid middle-school achievement source information: {error}")
        return
    if catalog.get("distribution") != "public":
        errors.append("Middle-school achievement catalog must declare public distribution")
    for marker in ("NCIC 국가교육과정정보센터", "공공누리 제2유형"):
        if marker not in attribution:
            errors.append(f"Middle-school achievement attribution is missing: {marker}")


GUIDELINE_FOLDERS = {"guidelines": "high", "guidelines-middle": "middle"}
# 기재요령 원문(공공누리 제4유형)의 변환본과 그 색인·등록 기록. 배포본에는 넣지 않고 요약으로 동작한다.
GUIDELINE_ORIGINAL_FILES = ("current.md", "current.index.md", "manifest.json")


def verify_guideline_summaries(root: Path, errors: list[str]) -> None:
    references = root / "skills" / "write-school-records" / "references"
    for folder, level in GUIDELINE_FOLDERS.items():
        directory = references / folder
        for name in GUIDELINE_ORIGINAL_FILES:
            if (directory / name).exists():
                errors.append(f"Guideline original must not be shipped: {folder}/{name}")
        versions = directory / "versions"
        if versions.exists() and any(versions.iterdir()):
            errors.append(f"Guideline original archive must not be shipped: {folder}/versions/")
        try:
            summary = (directory / "summary.md").read_text(encoding="utf-8")
            attribution = (directory / "ATTRIBUTION.md").read_text(encoding="utf-8")
        except OSError as error:
            errors.append(f"Missing guideline summary or attribution in {folder}: {error}")
            continue
        head = summary.split("\n---", 1)[0]
        year = re.search(r"(?m)^school_year: (20\d{2})$", head)
        for marker in ("---\ndocument: guideline-summary", f"school_level: {level}", "revision_date: ", "source_url: https://www.moe.go.kr/"):
            if marker not in head:
                errors.append(f"Guideline summary front matter is missing '{marker.strip()}': {folder}/summary.md")
        if year is None:
            errors.append(f"Guideline summary front matter has no school_year: {folder}/summary.md")
        elif not (directory / "analyzer-rules" / f"{year.group(1)}.json").is_file():
            errors.append(f"Analyzer rules for the summary year are missing: {folder}/analyzer-rules/{year.group(1)}.json")
        for marker in ("공공누리 **제4유형**", "summary.md", "포함하지 않음"):
            if marker not in attribution:
                errors.append(f"Guideline attribution is missing '{marker}': {folder}/ATTRIBUTION.md")
    if not (references / "guidelines-middle" / "differences.md").is_file():
        errors.append("Missing guidelines-middle/differences.md")


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
    # 문서 전용판 검사의 오류 문장은 한국어다. Windows 기본 로캘(cp1252 등)에서도 출력하다 멈추지 않게 한다.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_root", type=Path, nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.plugin_root.resolve()
    errors: list[str] = []
    verify_manifest(root, errors)
    verify_claude_manifest(root, errors)
    verify_publisher(root, errors)
    verify_marketplace(root, errors)
    verify_directory_edition(root, errors)
    verify_bundled_licenses(root, errors)
    verify_skills(root, errors)
    verify_achievement_sources(root, errors)
    verify_middle_achievement_sources(root, errors)
    verify_guideline_summaries(root, errors)
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
