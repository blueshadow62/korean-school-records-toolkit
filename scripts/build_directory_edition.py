#!/usr/bin/env python3
"""Build the documents-only directory edition from the full plugin, or check it.

The full plugin at the repository root is the source. This script copies the allowed
documents of the write-school-records skill, applies the replacements in
editions/source/changes.md, adds the files that only the edition has, copies the plugin icon
(.claude-plugin/icon.png) unchanged, and writes editions/<name>/. The edition has no scripts,
so it can go to the Claude plugin directory.

Usage:
  python scripts/build_directory_edition.py            # write editions/<name>/
  python scripts/build_directory_edition.py --check    # compare and audit only; write nothing
  python scripts/build_directory_edition.py --output <folder>
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import unicodedata
import zlib
from pathlib import Path, PurePosixPath
from typing import NamedTuple
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
EDITIONS = "editions"
SOURCE = "editions/source"
SKILL = "skills/write-school-records"
# 문서 전용판에만 있는 파일. editions/source/에서 그대로 옮긴다.
EDITION_ONLY_FILES = ("README.md", "SECURITY.md")
# editions/source/에 있어도 되는 파일. 모르는 파일이 생기면 넣을지 정하도록 빌드를 멈춘다.
SOURCE_FILES = {"edition.json", "changes.md", *EDITION_ONLY_FILES}
# 전체판 루트에서 옮기는 파일(changes.md의 문구를 바꿔 넣는다).
ROOT_FILES = ("LICENSE",)
# 두 판이 같은 아이콘을 쓴다. 전체판 루트의 이 파일이 원본이고, 문서 전용판에는 바이트 그대로 옮긴다.
# editions/source/에는 두지 않는다. 사본이 둘이면 서로 달라질 수 있기 때문이다.
ICON = ".claude-plugin/icon.png"
# .claude-plugin/ 폴더에 둘 수 있는 파일. plugin.json이 아닌 파일은 아이콘만 받는다.
PLUGIN_FOLDER_FILES = {".claude-plugin/plugin.json", ICON}
# 디렉터리의 아이콘 규칙(claude plugin validate의 ICON_MISSING 안내문과 같다): 정사각 PNG, 한 변 512~2048픽셀,
# 2MB 미만(2MiB로 센다). validate(2.1.328)는 파일이 있는지만 보고 크기·모양은 보지 않으므로 여기서 직접 본다.
ICON_MIN_SIDE = 512
ICON_MAX_SIDE = 2048
ICON_MAX_BYTES = 2 * 1024 * 1024
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc"}

# 스킬 폴더 안의 파일을 문서 전용판에 넣을지 정하는 규칙. 위에서부터 처음 맞는 규칙을 쓴다.
# 어느 규칙에도 맞지 않는 파일이 생기면 빌드가 멈춘다. 새 파일을 넣을지 뺄지 사람이 정하게 하려는 것이다.
SKILL_RULES = (
    (r"SKILL\.md", True, "스킬 지시문(스크립트 부분은 changes.md로 바꿈)"),
    (r"LICENSE", True, "스킬 라이선스 고지"),
    (r"agents/.*", False, "Codex 전용 설정"),
    (r"scripts/.*", False, "스크립트"),
    (r"tests/.*", False, "시험 자료와 평가 사례"),
    (r"references/guidelines(?:-middle)?/analyzer-rules/.*", False, "점검 스크립트의 검사 규칙"),
    (r"references/guidelines(?:-middle)?/index-terms\.json", False, "원문 등록 도구의 색인 검색어"),
    (r"references/guidelines(?:-middle)?/(?:current\.md|current\.index\.md|manifest\.json|versions/.*)", False,
     "기재요령 원문 변환본과 등록 기록(배포하지 않음)"),
    (r"references/.*\.(?:md|json)", True, "참조 문서"),
)

# 디렉터리 개발자 포털의 검사(2026-11-19 사용자 계정 기준 메시지)가 받는 파일. 인증된 조직이 아니면
# 이 밖의 파일(이름과 무관), '#!'로 시작하는 파일, 패키지 관리자 설정 파일을 받지 않는다.
ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
ALLOWED_NAMES = {"LICENSE", "README", ".gitignore"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_SIGNATURES = {
    ".png": (PNG_SIGNATURE,),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".webp": (b"RIFF",),
    ".ico": (b"\x00\x00\x01\x00",),
}
PACKAGE_MANAGER_FILES = {
    "package.json", "package-lock.json", "npm-shrinkwrap.json", ".npmrc", ".yarnrc", ".yarnrc.yml",
    "yarn.lock", "pnpm-workspace.yaml", "pnpm-lock.yaml", ".pnpmfile.cjs", "bunfig.toml", "bun.lock",
    "bun.lockb", "deno.json", "deno.jsonc", "uv.toml", "uv.lock", "pyproject.toml", "requirements.txt",
    "Pipfile", "Pipfile.lock", "poetry.lock", "setup.py", "setup.cfg", "pip.conf", "pip.ini", ".pypirc",
    "environment.yml", "Gemfile", "Cargo.toml", "go.mod", "composer.json",
}
# 문서 전용판은 아무것도 실행하지 않는다. 실행 구성 요소를 담는 이름도 두지 않는다.
FORBIDDEN_NAMES = {".mcp.json", ".lsp.json", "hooks", "bin", "scripts", ".codex-plugin", "egress"}
MAX_FILES = 512
MAX_FILE_BYTES = 256 * 1024
WINDOWS_DEVICE = re.compile(r"(?i)^(?:con|prn|aux|nul|com[0-9¹²³]|lpt[0-9¹²³])(?:\..*)?$")
WINDOWS_BAD_CHARS = re.compile(r'[<>:"\\|?*\x00-\x1f]')
FOLDER_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
PLUGIN_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
RESERVED_NAMES = {"claude", "anthropic", "official", "plugin", "mcp", "test"}
MIN_README_WORDS = 40
# 패키지를 내려받아 설치·실행하는 명령과 패키지 출처를 바꾸는 설정. 문서에도 넣지 않는다.
INSTALL_COMMAND = re.compile(
    r"\b(?:npx|bunx|uvx|pnpm\s+dlx|yarn\s+dlx|pipx\s+run|uv\s+(?:run|pip|tool|add)|pip3?\s+install|"
    r"python3?\s+-m\s+pip|npm\s+(?:install|i|ci|exec|run|x)|pnpm\s+(?:install|add|i)|yarn\s+(?:add|install)|"
    r"bun\s+(?:add|install|x)|brew\s+install|apt(?:-get)?\s+install|winget\s+install|choco\s+install|"
    r"scoop\s+install|conda\s+install|gem\s+install|cargo\s+install|go\s+install)\b"
    r"|--registry\b|--index-url\b|--extra-index-url\b|^\s*registry\s*="
)
# 이 판에 없는 스크립트를 가리키는 말. 문서가 없는 파일을 실행하게 만들지 않도록 남기지 않는다.
SCRIPT_REFERENCE = re.compile(r"scripts/|\b(?!Node\.js\b)[\w-]+\.(?:py|js|mjs|cjs|sh|ps1|bat|cmd)\b")
# 사용자 환경의 자격 증명이나 설정 폴더를 읽는 것으로 보일 만한 표현.
ENVIRONMENT_REFERENCE = re.compile(
    r"\$\{?[A-Z][A-Z0-9_]{2,}\}?|%[A-Z][A-Z0-9_]{2,}%|\$env:[A-Za-z_]|"
    r"~[/\\]\.(?:claude|codex|ssh|aws|npmrc|netrc|config|gitconfig)\b|\.claude[/\\]skills"
)
CREDENTIAL_WORD = re.compile(
    r"(?i)\b(?:api[_ -]?keys?|access[_ -]?tokens?|auth[_ -]?tokens?|bearer|secret[_ -]?keys?|passwords?|passwd|credentials?)\b"
)
MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
FENCE = re.compile(r"^\s*(```|~~~)")


class BuildError(RuntimeError):
    pass


# dataclass 대신 NamedTuple을 쓴다. 테스트와 verify_package.py가 이 파일을 importlib로 불러오는데,
# dataclass는 sys.modules에 등록되지 않은 모듈에서 만들 수 없기 때문이다.
class Change(NamedTuple):
    path: str
    find: str
    replace: str
    line: int


def read_text(path: Path) -> str:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise BuildError(f"UTF-8이 아닌 파일: {path}") from error
    if text.startswith("\ufeff"):
        raise BuildError(f"BOM으로 시작하는 파일: {path}")
    # 작업 폴더가 CRLF로 받은 파일도 같은 결과가 나오도록 LF로 맞춘다. 저장소는 LF로 저장한다.
    return text.replace("\r\n", "\n")


def edition_config(root: Path = ROOT) -> dict:
    return json.loads(read_text(root / SOURCE / "edition.json"))


def edition_folder(root: Path = ROOT) -> Path:
    return root / EDITIONS / edition_config(root)["name"]


def parse_changes(text: str) -> list[Change]:
    """Read the ````find <path> / ````replace block pairs in changes.md."""
    lines = text.split("\n")
    changes: list[Change] = []
    pending: tuple[str, str, int] | None = None
    index = 0

    def block(start: int) -> tuple[str, int]:
        end = start
        while end < len(lines) and lines[end] != "````":
            if lines[end].startswith("````"):
                raise BuildError(f"changes.md {end + 1}행: 블록이 닫히기 전에 새 블록이 열림")
            end += 1
        if end == len(lines):
            raise BuildError(f"changes.md {start}행: 닫히지 않은 블록")
        return "\n".join(lines[start:end]), end + 1

    while index < len(lines):
        line = lines[index]
        find = re.fullmatch(r"````find (\S+)", line)
        if find:
            if pending:
                raise BuildError(f"changes.md {pending[2]}행: replace 블록이 없음")
            body, next_index = block(index + 1)
            if not body.strip():
                raise BuildError(f"changes.md {index + 1}행: 빈 find 블록")
            pending = (find.group(1), body, index + 1)
            index = next_index
        elif line == "````replace":
            if not pending:
                raise BuildError(f"changes.md {index + 1}행: find 블록 없이 replace 블록이 있음")
            body, next_index = block(index + 1)
            changes.append(Change(pending[0], pending[1], body, pending[2]))
            pending = None
            index = next_index
        elif line.startswith("````"):
            raise BuildError(f"changes.md {index + 1}행: 알 수 없는 블록 머리 {line!r}")
        else:
            index += 1
    if pending:
        raise BuildError(f"changes.md {pending[2]}행: replace 블록이 없음")
    return changes


def load_changes(root: Path = ROOT) -> list[Change]:
    return parse_changes(read_text(root / SOURCE / "changes.md"))


def apply_changes(relative: str, text: str, changes: list[Change]) -> str:
    mine = [change for change in changes if change.path == relative]
    # 횟수는 바꾸기 전의 전체판 문서에서 센다. 앞 교체가 넣은 문구를 뒤 교체가 다시 찾지 않게 하려는 것이다.
    for change in mine:
        count = text.count(change.find)
        if count != 1:
            raise BuildError(
                f"changes.md {change.line}행의 find 문구가 {relative}에 {count}번 나온다(정확히 1번이어야 함). "
                "전체판 문구가 바뀌었으면 changes.md를 함께 고친다."
            )
    spans = sorted(((text.index(change.find), change) for change in mine), key=lambda item: item[0])
    for (start, change), following in zip(spans, spans[1:]):
        if start + len(change.find) > following[0]:
            raise BuildError(f"changes.md {change.line}행과 {following[1].line}행의 find 문구가 겹친다: {relative}")
    for start, change in reversed(spans):
        text = text[:start] + change.replace + text[start + len(change.find):]
    return text


def classify_skill_file(relative: str) -> tuple[bool, str]:
    for pattern, include, reason in SKILL_RULES:
        if re.fullmatch(pattern, relative):
            return include, reason
    raise BuildError(
        f"{SKILL}/{relative}: 문서 전용판에 넣을지 정하지 않은 파일이다. "
        "scripts/build_directory_edition.py의 SKILL_RULES에 규칙을 더한다."
    )


def skill_files(root: Path) -> list[str]:
    base = root / SKILL
    found = []
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(base)
        if not path.is_file() or IGNORED_PARTS & set(relative.parts) or path.suffix in IGNORED_SUFFIXES:
            continue
        found.append(relative.as_posix())
    return found


def manifest(root: Path) -> dict:
    full = json.loads(read_text(root / ".claude-plugin" / "plugin.json"))
    config = edition_config(root)
    return {
        "$schema": full["$schema"],
        "name": config["name"],
        "displayName": config["displayName"],
        "version": read_text(root / "VERSION").strip(),
        "description": config["description"],
        "author": full["author"],
        "homepage": full["homepage"],
        "repository": full["repository"],
        "license": full["license"],
        "keywords": config["keywords"],
        "skills": "./skills/",
    }


def png_size(data: bytes) -> tuple[int, int]:
    """Read (width, height) from the IHDR chunk, which must follow the PNG signature directly."""
    if not data.startswith(PNG_SIGNATURE):
        raise BuildError("PNG가 아니다(파일 머리가 PNG 서명과 다르다)")
    # 서명 뒤: 길이 4바이트(13) + 'IHDR' + 내용 13바이트(너비·높이가 각 4바이트) + CRC 4바이트.
    chunk = data[len(PNG_SIGNATURE):len(PNG_SIGNATURE) + 25]
    if len(chunk) < 25 or chunk[:8] != b"\x00\x00\x00\x0dIHDR":
        raise BuildError("PNG의 첫 덩어리가 IHDR이 아니다")
    if zlib.crc32(chunk[4:21]) != struct.unpack(">I", chunk[21:25])[0]:
        raise BuildError("PNG 머리(IHDR)의 CRC가 맞지 않는다(파일이 깨졌다)")
    width, height = struct.unpack(">II", chunk[8:16])
    return width, height


def icon_problems(data: bytes) -> list[str]:
    """List what keeps an icon from meeting the directory rule: a square PNG, 512-2048 px on a side, under 2 MiB."""
    try:
        width, height = png_size(data)
    except BuildError as error:
        return [str(error)]
    problems = []
    if width != height:
        problems.append(f"정사각이 아니다({width}×{height}픽셀)")
    if not all(ICON_MIN_SIDE <= side <= ICON_MAX_SIDE for side in (width, height)):
        problems.append(f"한 변은 {ICON_MIN_SIDE}~{ICON_MAX_SIDE}픽셀이어야 한다({width}×{height}픽셀)")
    if len(data) >= ICON_MAX_BYTES:
        problems.append(f"2MiB 이상이다({len(data):,}바이트)")
    return problems


def read_icon(root: Path = ROOT) -> bytes:
    """Read the full edition's icon. Stop the build if it is missing or breaks the directory rule."""
    path = root / ICON
    if not path.is_file():
        raise BuildError(f"전체판에 {ICON}가 없다. 두 판이 같은 아이콘을 쓰므로 전체판 루트에 먼저 둔다.")
    data = path.read_bytes()
    problems = icon_problems(data)
    if problems:
        raise BuildError(f"전체판 {ICON}: " + "; ".join(problems))
    return data


def build(root: Path = ROOT) -> dict[str, bytes]:
    """Return the edition as {relative POSIX path: file bytes}. Nothing is written."""
    root = root.resolve()
    unknown = sorted(p.name for p in (root / SOURCE).iterdir() if p.name not in SOURCE_FILES)
    if unknown:
        raise BuildError(f"{SOURCE}/에 쓰임이 정해지지 않은 파일이 있다: {unknown}")
    changes = load_changes(root)
    texts: dict[str, str] = {}
    for name in ROOT_FILES:
        texts[name] = read_text(root / name)
    for relative in skill_files(root):
        include, _reason = classify_skill_file(relative)
        if include:
            texts[f"{SKILL}/{relative}"] = read_text(root / SKILL / relative)
    targets = {change.path for change in changes}
    missing = sorted(targets - set(texts))
    if missing:
        raise BuildError(f"changes.md가 문서 전용판에 없는 파일을 가리킨다: {missing}")
    for relative in targets:
        texts[relative] = apply_changes(relative, texts[relative], changes)
    for name in EDITION_ONLY_FILES:
        texts[name] = read_text(root / SOURCE / name)
    texts[".claude-plugin/plugin.json"] = json.dumps(manifest(root), ensure_ascii=False, indent=2) + "\n"
    files = {relative: text.encode("utf-8") for relative, text in texts.items()}
    files[ICON] = read_icon(root)
    return dict(sorted(files.items()))


def folder_files(folder: Path) -> dict[str, Path]:
    return {
        path.relative_to(folder).as_posix(): path
        for path in sorted(folder.rglob("*"))
        if path.is_file() and not (IGNORED_PARTS & set(path.relative_to(folder).parts))
    }


def comparable(relative: str, data: bytes) -> bytes:
    if PurePosixPath(relative).suffix in TEXT_SUFFIXES or PurePosixPath(relative).name in ALLOWED_NAMES:
        return data.replace(b"\r\n", b"\n")
    return data


def compare(expected: dict[str, bytes], folder: Path) -> list[str]:
    """List the differences between a fresh build and a folder (line endings are ignored)."""
    if not folder.is_dir():
        return [f"문서 전용판 폴더가 없다: {folder}"]
    actual = folder_files(folder)
    problems = [f"빠진 파일: {name}" for name in sorted(set(expected) - set(actual))]
    problems += [f"빌드에 없는 파일: {name}" for name in sorted(set(actual) - set(expected))]
    for name in sorted(set(expected) & set(actual)):
        if comparable(name, expected[name]) != comparable(name, actual[name].read_bytes()):
            problems.append(f"빌드 결과와 다른 파일: {name}")
    return problems


def write(expected: dict[str, bytes], folder: Path) -> list[str]:
    """Write the build into folder and delete files that the build does not have."""
    folder.mkdir(parents=True, exist_ok=True)
    changed = []
    for relative, data in expected.items():
        target = folder / relative
        if target.is_file() and comparable(relative, target.read_bytes()) == comparable(relative, data):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        changed.append(relative)
    for relative, path in folder_files(folder).items():
        if relative not in expected:
            path.unlink()
            changed.append(f"(삭제) {relative}")
    for directory in sorted((p for p in folder.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()
    return changed


# ---- 디렉터리 제출 규칙 점검 ----

def _files(folder: Path) -> dict[str, Path]:
    return {
        path.relative_to(folder).as_posix(): path
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def _is_text(relative: str) -> bool:
    path = PurePosixPath(relative)
    return path.suffix in TEXT_SUFFIXES or path.name in ALLOWED_NAMES


def _texts(folder: Path) -> dict[str, str]:
    texts = {}
    for relative, path in _files(folder).items():
        if _is_text(relative):
            try:
                texts[relative] = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
            except UnicodeDecodeError:
                continue
    return texts


def check_file_types(folder: Path) -> list[str]:
    problems = []
    for relative in _files(folder):
        path = PurePosixPath(relative)
        if path.name not in ALLOWED_NAMES and path.suffix.lower() not in ALLOWED_SUFFIXES:
            problems.append(f"허용 목록 밖의 파일: {relative}")
        elif path.suffix != path.suffix.lower():
            problems.append(f"확장자를 소문자로 쓴다: {relative}")
    return problems


def check_no_shebang(folder: Path) -> list[str]:
    return [f"'#!'로 시작하는 파일: {relative}" for relative, path in _files(folder).items()
            if path.read_bytes()[:2] == b"#!"]


def check_encoding(folder: Path) -> list[str]:
    problems = []
    for relative, path in _files(folder).items():
        data = path.read_bytes()
        suffix = PurePosixPath(relative).suffix.lower()
        if _is_text(relative):
            if b"\x00" in data:
                problems.append(f"NUL 바이트가 있는 텍스트 파일: {relative}")
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                problems.append(f"UTF-8이 아닌 텍스트 파일: {relative}")
        elif suffix in IMAGE_SIGNATURES and not data.startswith(IMAGE_SIGNATURES[suffix]):
            problems.append(f"확장자와 내용이 맞지 않는 그림 파일: {relative}")
    return problems


def check_limits(folder: Path) -> list[str]:
    files = _files(folder)
    problems = [] if len(files) <= MAX_FILES else [f"파일이 {len(files)}개다(한도 {MAX_FILES}개)"]
    problems += [f"256KiB 이상인 파일({path.stat().st_size}바이트): {relative}"
                 for relative, path in files.items() if path.stat().st_size >= MAX_FILE_BYTES]
    return problems


def check_forbidden_files(folder: Path) -> list[str]:
    problems = []
    for path in sorted(folder.rglob("*")):
        relative = path.relative_to(folder)
        parts = relative.parts
        if path.name in PACKAGE_MANAGER_FILES:
            problems.append(f"패키지 관리자 설정 파일: {relative.as_posix()}")
        if path.name in FORBIDDEN_NAMES:
            problems.append(f"문서 전용판에 두지 않는 이름: {relative.as_posix()}")
        if path.is_dir() and path.name == ".claude-plugin" and len(parts) > 1:
            problems.append(f"플러그인 자신의 것이 아닌 .claude-plugin 폴더: {relative.as_posix()}")
        if path.is_dir() and path.name == "skills" and len(parts) >= 2 and parts[-2] == ".claude":
            problems.append(f".claude/skills 폴더: {relative.as_posix()}")
        if (path.is_file() and len(parts) == 2 and parts[0] == ".claude-plugin"
                and relative.as_posix() not in PLUGIN_FOLDER_FILES):
            problems.append(f".claude-plugin 안의 plugin.json·icon.png가 아닌 파일: {relative.as_posix()}")
    return problems


def check_icon(folder: Path, root: Path = ROOT) -> list[str]:
    """The folder has .claude-plugin/icon.png: it meets the directory rule and is the full edition's file."""
    path = folder / ICON
    if not path.is_file():
        return [f"{ICON}가 없다: {folder.name}"]
    data = path.read_bytes()
    problems = [f"{folder.name}/{ICON}: {problem}" for problem in icon_problems(data)]
    original = root / ICON
    if original.is_file() and data != original.read_bytes():
        problems.append(f"{folder.name}/{ICON}가 전체판의 {ICON}와 다르다")
    return problems


def portable_name_problems(relative: str) -> list[str]:
    """Problems that keep a path from staying the same on Windows and macOS."""
    problems = []
    for part in PurePosixPath(relative).parts:
        if WINDOWS_BAD_CHARS.search(part):
            problems.append(f"Windows에서 쓸 수 없는 글자: {relative}")
        if part.endswith((".", " ")):
            problems.append(f"점이나 공백으로 끝나는 이름: {relative}")
        if WINDOWS_DEVICE.match(part):
            problems.append(f"Windows 장치 이름: {relative}")
        # macOS는 한글 이름을 풀어쓴 꼴(NFD)로 바꿔 저장할 수 있어, 모아쓴 꼴(NFC)이 아니면 이름이 달라진다.
        if unicodedata.normalize("NFC", part) != part:
            problems.append(f"NFC 정규형이 아닌 이름: {relative}")
    return problems


def case_collisions(relatives: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    problems = []
    for relative in relatives:
        folded = relative.casefold()
        if folded in seen and seen[folded] != relative:
            problems.append(f"대소문자만 다른 두 이름: {seen[folded]}, {relative}")
        seen.setdefault(folded, relative)
    return problems


def check_portable_paths(folder: Path, root: Path = ROOT) -> list[str]:
    try:
        location = folder.resolve().relative_to(root.resolve()).parts
    except ValueError:
        location = ()
    problems = [f"폴더 이름에 영문자·숫자·점·하이픈·밑줄이 아닌 글자: {part}"
                for part in location if not FOLDER_NAME.match(part)]
    relatives = [path.relative_to(folder).as_posix() for path in sorted(folder.rglob("*"))]
    for relative in relatives:
        problems += portable_name_problems(relative)
    return problems + case_collisions(relatives)


def readme_words(text: str) -> int:
    kept, fenced = [], False
    for line in text.split("\n"):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            kept.append(line)
    return sum(1 for word in re.split(r"\s+", "\n".join(kept)) if re.search(r"\w", word))


def check_readme(folder: Path) -> list[str]:
    path = folder / "README.md"
    if not path.is_file():
        return ["README.md가 없다"]
    words = readme_words(path.read_bytes().decode("utf-8"))
    return [] if words >= MIN_README_WORDS else [f"README.md가 {words}낱말이다(코드 블록 제외 {MIN_README_WORDS}낱말 이상)"]


def check_no_install_or_script_commands(folder: Path) -> list[str]:
    problems = []
    for relative, text in _texts(folder).items():
        for number, line in enumerate(text.split("\n"), 1):
            if INSTALL_COMMAND.search(line):
                problems.append(f"패키지 설치·실행 명령: {relative}:{number}")
            if SCRIPT_REFERENCE.search(line):
                problems.append(f"이 판에 없는 스크립트를 가리킴: {relative}:{number}")
    return problems


def check_no_environment_credentials(folder: Path) -> list[str]:
    problems = []
    for relative, text in _texts(folder).items():
        for number, line in enumerate(text.split("\n"), 1):
            if ENVIRONMENT_REFERENCE.search(line):
                problems.append(f"환경 변수나 사용자 설정 폴더를 가리킴: {relative}:{number}")
            if CREDENTIAL_WORD.search(line):
                problems.append(f"자격 증명으로 읽힐 수 있는 낱말: {relative}:{number}")
    return problems


def check_links(folder: Path) -> list[str]:
    problems = []
    base = folder.resolve()
    for relative, text in _texts(folder).items():
        if not relative.endswith(".md"):
            continue
        source = (folder / relative).parent
        for target in MARKDOWN_LINK.findall(text):
            if re.match(r"(?i)^(?:[a-z][a-z0-9+.-]*:|#)", target):
                continue
            resolved = (source / unquote(target.split("#", 1)[0])).resolve()
            try:
                resolved.relative_to(base)
            except ValueError:
                problems.append(f"플러그인 폴더 밖을 가리키는 링크: {relative} → {target}")
                continue
            if not resolved.exists():
                problems.append(f"없는 파일을 가리키는 링크: {relative} → {target}")
    return problems


def writing_systems(text: str) -> set[str]:
    systems = set()
    for char in text:
        if unicodedata.category(char) == "Cf":
            systems.add("INVISIBLE")
        elif unicodedata.category(char).startswith("L"):
            systems.add(unicodedata.name(char, "UNKNOWN").split(" ")[0])
    return systems


def check_manifest(folder: Path, root: Path = ROOT) -> list[str]:
    try:
        data = json.loads((folder / ".claude-plugin" / "plugin.json").read_bytes().decode("utf-8"))
    except (OSError, ValueError) as error:
        return [f"plugin.json을 읽을 수 없다: {error}"]
    problems = []
    name = str(data.get("name", ""))
    if not PLUGIN_NAME.match(name) or name in RESERVED_NAMES:
        problems.append(f"플러그인 이름 형식이 맞지 않다: {name!r}")
    if name != folder.name:
        problems.append(f"폴더 이름과 플러그인 이름이 다르다: {folder.name} != {name}")
    full = json.loads(read_text(root / ".claude-plugin" / "plugin.json"))
    if name == full.get("name"):
        problems.append("문서 전용판의 이름이 전체판과 같다")
    for field in ("displayName",):
        if len(writing_systems(str(data.get(field, "")))) != 1:
            problems.append(f"{field}는 한 가지 문자 체계로만 쓴다: {data.get(field)!r}")
    if len(writing_systems(str(data.get("author", {}).get("name", "")))) != 1:
        problems.append("author.name은 한 가지 문자 체계로만 쓴다")
    if data.get("version") != read_text(root / "VERSION").strip():
        problems.append("문서 전용판 version이 VERSION과 다르다")
    for field in ("author", "homepage", "repository", "license"):
        if data.get(field) != full.get(field):
            problems.append(f"문서 전용판 {field}가 전체판과 다르다")
    if data.get("skills") != "./skills/":
        problems.append("문서 전용판 skills 경로는 ./skills/이어야 한다")
    if not str(data.get("description", "")).strip():
        problems.append("문서 전용판 description이 비어 있다")
    return problems


AUDITS = (
    check_file_types,
    check_no_shebang,
    check_encoding,
    check_limits,
    check_forbidden_files,
    check_icon,
    check_portable_paths,
    check_readme,
    check_no_install_or_script_commands,
    check_no_environment_credentials,
    check_links,
    check_manifest,
)


def audit(folder: Path) -> list[str]:
    problems = []
    for check in AUDITS:
        problems += check(folder)
    return problems


def check(root: Path = ROOT) -> list[str]:
    """Compare the committed edition with a fresh build, then audit it. Return the problems."""
    root = root.resolve()
    try:
        expected = build(root)
        folder = edition_folder(root)
    except (BuildError, OSError, ValueError, KeyError) as error:
        return [f"문서 전용판을 만들 수 없다: {error}"]
    problems = compare(expected, folder)
    others = sorted(p.name for p in (root / EDITIONS).iterdir()
                    if p.is_dir() and p.name not in {"source", folder.name})
    problems += [f"editions/에 쓰지 않는 판 폴더가 있다(이름을 바꿨으면 옛 폴더를 지운다): {name}" for name in others]
    if folder.is_dir():
        problems += audit(folder)
    return problems


def statistics(folder: Path) -> list[str]:
    files = _files(folder)
    suffixes: dict[str, int] = {}
    for relative in files:
        key = PurePosixPath(relative).suffix or PurePosixPath(relative).name
        suffixes[key] = suffixes.get(key, 0) + 1
    largest = sorted(((path.stat().st_size, relative) for relative, path in files.items()), reverse=True)[:5]
    total = sum(path.stat().st_size for path in files.values())
    lines = [f"파일 {len(files)}개, 전체 {total:,}바이트",
             "확장자별: " + ", ".join(f"{key} {count}" for key, count in sorted(suffixes.items()))]
    lines += [f"  {size:,}바이트  {relative}" for size, relative in largest]
    return lines


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="compare the committed edition with a fresh build and audit it")
    group.add_argument("--output", type=Path, help="write the edition into this folder instead of editions/<name>/")
    args = parser.parse_args()
    if args.check:
        problems = check(ROOT)
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        if problems:
            print("문서 전용판이 빌드 결과와 다르거나 디렉터리 규칙에 맞지 않는다. "
                  "python scripts/build_directory_edition.py로 다시 만든 뒤 확인한다.", file=sys.stderr)
            return 1
        print(f"문서 전용판 확인 통과: {edition_folder(ROOT)}")
        print("\n".join(statistics(edition_folder(ROOT))))
        return 0
    try:
        expected = build(ROOT)
    except BuildError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    folder = args.output.resolve() if args.output else edition_folder(ROOT)
    if args.output and folder.exists() and any(folder.iterdir()):
        marker = folder / ".claude-plugin" / "plugin.json"
        if not marker.is_file() or json.loads(marker.read_text(encoding="utf-8")).get("name") != edition_config()["name"]:
            print(f"ERROR: 비어 있지 않은 다른 폴더에는 쓰지 않는다: {folder}", file=sys.stderr)
            return 1
    changed = write(expected, folder)
    print(f"문서 전용판을 만들었다: {folder} (바뀐 파일 {len(changed)}개)")
    for name in changed:
        print(f"  {name}")
    problems = audit(folder)
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    print("\n".join(statistics(folder)))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
