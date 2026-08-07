#!/usr/bin/env python3
"""Register, activate, verify, and roll back year-specific school-record guidelines."""

from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any


YEAR_RE = re.compile(r"^20\d{2}$")
DATE_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
INDEX_META_RE = re.compile(r"^<!-- active_version=(\S+) sha256=([0-9a-f]{64}) -->$")
SPACE_RE = re.compile(r"\s+")
MAX_ANCHOR_TEXT_LENGTH = 80
MAX_TABLE_HEADER_ANCHOR_TEXT_LENGTH = 500
ANCHOR_LOOKBACK = 4
ANCHOR_LOOKAHEAD = 45


class GuidelineError(Exception):
    """An expected input or validation failure."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def root_paths(root: Path) -> dict[str, Path]:
    root = root.resolve()
    guidelines = root / "references" / "guidelines"
    return {
        "root": root,
        "guidelines": guidelines,
        "versions": guidelines / "versions",
        "manifest": guidelines / "manifest.json",
        "current": guidelines / "current.md",
        "index": guidelines / "current.index.md",
        "index_terms": guidelines / "index-terms.json",
    }


def safe_relative(root: Path, value: str) -> Path:
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise GuidelineError(f"manifest 경로가 스킬 디렉터리 밖을 가리킵니다: {value}") from error
    return candidate


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GuidelineError(f"manifest를 읽을 수 없습니다: {path} ({error})") from error
    if not isinstance(value, dict) or not isinstance(value.get("versions"), dict):
        raise GuidelineError("manifest 형식이 올바르지 않습니다: versions 객체가 필요합니다.")
    return value


def empty_manifest() -> dict[str, Any]:
    return {"schema_version": 1, "active_version": None, "versions": {}}


def load_manifest(paths: dict[str, Path]) -> dict[str, Any]:
    return read_json(paths["manifest"]) if paths["manifest"].exists() else empty_manifest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def heading_index(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    headings: list[tuple[int, int, str]] = []
    for number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append((number, len(match.group(1)), match.group(2)))
    return [
        {
            "title": title,
            "level": level,
            "start_line": start,
            "end_line": (headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)),
        }
        for index, (start, level, title) in enumerate(headings)
    ]


def normalize_search_text(value: str) -> str:
    value = value.replace("ㆍ", "·").replace("･", "·").replace("&middot;", "·")
    return SPACE_RE.sub(" ", value).strip()


def compact_search_text(value: str) -> str:
    """Compare configured Korean labels despite conversion-introduced spacing."""
    return normalize_search_text(value).replace(" ", "")


class InlineHtmlCollector(HTMLParser):
    """Collect short visible text from table cells and strong elements on one line."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._active: list[tuple[str, list[str]]] = []
        self.values: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"td", "th"}:
            self._active.append(("html-table-cell", []))
        elif tag in {"strong", "b"}:
            self._active.append(("html-strong", []))

    def handle_data(self, data: str) -> None:
        for _, parts in self._active:
            parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        expected = {"td", "th"} if tag in {"td", "th"} else {"strong", "b"}
        for index in range(len(self._active) - 1, -1, -1):
            kind, parts = self._active[index]
            if (kind == "html-table-cell" and tag in {"td", "th"}) or (
                kind == "html-strong" and tag in {"strong", "b"}
            ):
                self.values.append((kind, normalize_search_text("".join(parts))))
                del self._active[index]
                return


def load_index_terms(path: Path) -> list[tuple[str, str]]:
    """Read optional category-to-term mappings; invalid files disable anchors only."""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    if not isinstance(raw, dict):
        return []
    terms: list[tuple[str, str]] = []
    for category, values in raw.items():
        if not isinstance(category, str) or not isinstance(values, list):
            continue
        for value in values:
            normalized = normalize_search_text(value) if isinstance(value, str) else ""
            if normalized and len(normalized) <= MAX_ANCHOR_TEXT_LENGTH:
                terms.append((category, normalized))
    return terms


def html_values(line: str) -> list[tuple[str, str]]:
    parser = InlineHtmlCollector()
    try:
        parser.feed(line)
        parser.close()
    except Exception:
        return []
    return [(kind, value) for kind, value in parser.values if value]


def is_anchor_cell(value: str, term: str, table_header: bool) -> bool:
    """Accept labels, not prose or table values, even when a configured term occurs."""
    if compact_search_text(term) not in compact_search_text(value):
        return False
    limit = MAX_TABLE_HEADER_ANCHOR_TEXT_LENGTH if table_header else MAX_ANCHOR_TEXT_LENGTH
    if len(value) > limit:
        return False
    if re.search(r"\d+\s*(자|Byte|시간)", value):
        return False
    return not value.endswith(("한다.", "한다", "있다.", "있음"))


def enclosing_table_end(lines: list[str], line_number: int) -> int | None:
    """Return the closing line for a table containing the anchor, if any."""
    depth = 0
    for line in lines[:line_number]:
        depth += line.count("<table") - line.count("</table>")
    if depth <= 0:
        return None
    for number in range(line_number, len(lines)):
        depth += lines[number].count("<table") - lines[number].count("</table>")
        if depth <= 0:
            return number + 1
    return None


def anchor_index(text: str, terms: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Find configured terms only; never promote arbitrary table data to anchors."""
    if not terms:
        return []
    candidates: list[dict[str, Any]] = []
    for number, raw_line in enumerate(text.splitlines(), start=1):
        values = html_values(raw_line)
        normalized_line = normalize_search_text(re.sub(r"<[^>]+>", " ", raw_line))
        for category, term in terms:
            matches = [
                (kind, value)
                for kind, value in values
                if is_anchor_cell(value, term, "<th" in raw_line.lower())
            ]
            if matches:
                kind, _ = matches[0]
            elif raw_line.lstrip().startswith("#") and term in normalize_search_text(raw_line.lstrip("# ")):
                kind = "plain-label"
            elif (
                term == normalized_line.lstrip("-•▪ ")
                or (normalized_line.startswith(term + ":") and len(normalized_line) <= MAX_ANCHOR_TEXT_LENGTH)
            ):
                kind = "plain-label"
            else:
                continue
            candidates.append({"text": term, "normalized": term, "line": number, "kind": kind, "category": category})
    deduplicated: dict[tuple[str, int], dict[str, Any]] = {}
    for candidate in candidates:
        key = (candidate["text"], candidate["line"])
        deduplicated.setdefault(key, candidate)
    anchors = list(deduplicated.values())
    counts: dict[str, int] = {}
    for anchor in anchors:
        counts[anchor["text"]] = counts.get(anchor["text"], 0) + 1
    lines = text.splitlines()
    headings = heading_index(text)
    total_lines = len(lines)
    for anchor in anchors:
        next_related = next(
            (other["line"] for other in anchors if other["category"] == anchor["category"] and other["line"] > anchor["line"]),
            total_lines + 1,
        )
        next_heading = next((heading["start_line"] for heading in headings if heading["start_line"] > anchor["line"]), total_lines + 1)
        start = max(1, anchor["line"] - ANCHOR_LOOKBACK)
        table_end = enclosing_table_end(lines, anchor["line"])
        related_limit = total_lines if table_end else next_related - 1
        table_limit = table_end if table_end else total_lines
        end = min(anchor["line"] + ANCHOR_LOOKAHEAD, related_limit, table_limit, next_heading - 1, total_lines)
        anchor["range"] = f"{start}–{max(start, end)}"
        anchor["occurrences"] = counts[anchor["text"]]
        nearby = " ".join(lines[max(0, anchor["line"] - 16):anchor["line"]]).lower()
        if "목차" in nearby or "contents" in nearby:
            anchor["context"] = "table-of-contents"
        elif any("참고자료" in heading["title"] for heading in headings if heading["start_line"] <= anchor["line"] <= heading["end_line"]):
            anchor["context"] = "reference"
        else:
            anchor["context"] = "body"
        parent = next(
            (heading["title"] for heading in reversed(headings) if heading["level"] == 1 and heading["start_line"] <= anchor["line"]),
            "",
        )
        anchor["section"] = parent
    return anchors


def index_bytes(version: str, digest: str, text: str, terms: list[tuple[str, str]] | None = None) -> bytes:
    lines = [f"<!-- active_version={version} sha256={digest} -->", "# 기재요령 제목 색인", ""]
    lines.append("| 수준 | 제목 | 시작 줄 | 종료 줄 |")
    lines.append("| ---: | --- | ---: | ---: |")
    for heading in heading_index(text):
        title = heading["title"].replace("|", "\\|")
        lines.append(f"| {heading['level']} | {title} | {heading['start_line']} | {heading['end_line']} |")
    anchors = anchor_index(text, terms or [])
    if anchors:
        lines.extend(["", "## 검색 앵커", "", "| 항목 | 정규화 검색어 | 원문 줄 | 형식 | 위치 | 상위 제목 | 초기 읽기 범위 | 출현 횟수 |", "| --- | --- | ---: | --- | --- | --- | --- | ---: |"])
        for anchor in anchors:
            lines.append(
                f"| {anchor['text']} | {anchor['normalized']} | {anchor['line']} | {anchor['kind']} | {anchor['context']} | {anchor['section']} | {anchor['range']} | {anchor['occurrences']} |"
            )
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_date(value: str, label: str) -> None:
    if not DATE_RE.fullmatch(value):
        raise GuidelineError(f"{label}는 YYYY-MM-DD 형식이어야 합니다: {value}")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise GuidelineError(f"{label}가 유효한 날짜가 아닙니다: {value}") from error


def validate_year(value: str) -> None:
    if not YEAR_RE.fullmatch(value):
        raise GuidelineError(f"학년도는 20XX 형식이어야 합니다: {value}")


def version_id(school_year: str, revision_date: str) -> str:
    validate_year(school_year)
    validate_date(revision_date, "개정일")
    return f"{school_year}_{revision_date}"


def read_input(path: Path) -> tuple[str, bytes]:
    if not path.exists():
        raise GuidelineError(f"입력 파일이 없습니다: {path}")
    if path.suffix.lower() != ".md":
        raise GuidelineError("입력 파일은 .md 확장자여야 합니다.")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise GuidelineError(f"UTF-8 Markdown으로 읽을 수 없습니다: {path} ({error})") from error
    if not text.strip():
        raise GuidelineError("빈 Markdown은 등록할 수 없습니다.")
    if not heading_index(text):
        raise GuidelineError("Markdown 제목(#)이 하나 이상 필요합니다.")
    data = text.encode("utf-8")
    return text, data


def entry_path(paths: dict[str, Path], entry: dict[str, Any]) -> Path:
    value = entry.get("archive_path")
    if not isinstance(value, str) or not value:
        raise GuidelineError("manifest 항목에 archive_path가 없습니다.")
    return safe_relative(paths["root"], value)


def verify_manifest(paths: dict[str, Path], manifest: dict[str, Any], require_current: bool = True) -> None:
    active = manifest.get("active_version")
    versions = manifest.get("versions")
    if not isinstance(versions, dict):
        raise GuidelineError("manifest의 versions가 객체가 아닙니다.")
    if require_current and not isinstance(active, str):
        raise GuidelineError("활성 버전이 없습니다. 먼저 activate를 실행하세요.")
    for identifier, entry in sorted(versions.items()):
        if not isinstance(entry, dict):
            raise GuidelineError(f"manifest 항목이 객체가 아닙니다: {identifier}")
        archive = entry_path(paths, entry)
        if not archive.exists():
            raise GuidelineError(f"보관 파일이 없습니다: {archive}")
        actual = sha256_bytes(archive.read_bytes())
        if actual != entry.get("sha256"):
            raise GuidelineError(f"보관 파일 해시가 다릅니다: {identifier}")
    if not require_current:
        return
    if active not in versions:
        raise GuidelineError(f"활성 버전이 manifest에 없습니다: {active}")
    active_entry = versions[active]
    archive = entry_path(paths, active_entry)
    digest = active_entry["sha256"]
    if not paths["current"].exists() or sha256_bytes(paths["current"].read_bytes()) != digest:
        raise GuidelineError("current.md가 활성 보관 파일과 일치하지 않습니다.")
    if not paths["index"].exists():
        raise GuidelineError("current.index.md가 없습니다.")
    try:
        first_line = paths["index"].read_text(encoding="utf-8").splitlines()[0]
    except (OSError, UnicodeError, IndexError) as error:
        raise GuidelineError(f"current.index.md를 읽을 수 없습니다: {error}") from error
    match = INDEX_META_RE.match(first_line)
    if not match or match.group(1) != active or match.group(2) != digest:
        raise GuidelineError("current.index.md의 버전 또는 해시가 활성 버전과 다릅니다.")


def activate_version(paths: dict[str, Path], manifest: dict[str, Any], identifier: str, allow_unconfirmed: bool) -> None:
    versions = manifest["versions"]
    if identifier not in versions:
        raise GuidelineError(f"등록된 버전이 없습니다: {identifier}")
    entry = versions[identifier]
    archive = entry_path(paths, entry)
    if not archive.exists() or sha256_bytes(archive.read_bytes()) != entry.get("sha256"):
        raise GuidelineError(f"활성화 전 해시 검증에 실패했습니다: {identifier}")
    if not entry.get("confirmed_official", False) and not allow_unconfirmed:
        raise GuidelineError("공식 확인되지 않은 문서는 --allow-unconfirmed 없이는 활성화할 수 없습니다.")
    current_bytes = archive.read_bytes()
    index = index_bytes(
        identifier,
        entry["sha256"],
        current_bytes.decode("utf-8"),
        load_index_terms(paths["index_terms"]),
    )
    new_manifest = dict(manifest)
    new_manifest["active_version"] = identifier
    old: dict[Path, bytes | None] = {}
    for path in (paths["current"], paths["index"], paths["manifest"]):
        old[path] = path.read_bytes() if path.exists() else None
    try:
        atomic_write(paths["current"], current_bytes)
        atomic_write(paths["index"], index)
        atomic_write(paths["manifest"], json_bytes(new_manifest))
        verify_manifest(paths, new_manifest)
    except Exception as error:
        for path, data in old.items():
            if data is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                atomic_write(path, data)
        raise GuidelineError(f"활성화에 실패해 기존 상태를 복구했습니다: {error}") from error


def command_import(args: argparse.Namespace, paths: dict[str, Path]) -> None:
    identifier = version_id(args.school_year, args.revision_date)
    if not args.source_title.strip():
        raise GuidelineError("source-title은 비워 둘 수 없습니다.")
    text, data = read_input(args.input)
    manifest = load_manifest(paths)
    if identifier in manifest["versions"]:
        raise GuidelineError(f"동일 버전이 이미 존재합니다: {identifier}")
    if args.activate and not args.confirmed_official and not args.allow_unconfirmed:
        raise GuidelineError("미확인 문서는 --allow-unconfirmed 없이 --activate할 수 없습니다.")
    paths["versions"].mkdir(parents=True, exist_ok=True)
    archive = paths["versions"] / f"{identifier}.md"
    atomic_write(archive, data)
    stored = archive.read_bytes()
    entry = {
        "version": identifier,
        "school_year": args.school_year,
        "revision_date": args.revision_date,
        "registered_at": date.today().isoformat(),
        "original_filename": args.input.name,
        "archive_path": str(archive.relative_to(paths["root"])).replace(os.sep, "/"),
        "source_title": args.source_title,
        "source_url": args.source_url or "",
        "confirmed_official": bool(args.confirmed_official),
        "sha256": sha256_bytes(stored),
        "file_size": len(stored),
        "encoding": "UTF-8",
    }
    manifest["versions"][identifier] = entry
    if args.activate:
        activate_version(paths, manifest, identifier, args.allow_unconfirmed)
    else:
        try:
            atomic_write(paths["manifest"], json_bytes(manifest))
        except Exception:
            try:
                archive.unlink()
            except FileNotFoundError:
                pass
            raise
    if not args.source_url:
        print("경고: source-url이 없어 출처 URL을 빈 값으로 기록했습니다.", file=sys.stderr)
    print(f"등록 완료: {identifier}")


def command_list(paths: dict[str, Path]) -> None:
    manifest = load_manifest(paths)
    active = manifest.get("active_version")
    print("버전\t학년도\t개정일\t확인\t활성")
    for identifier, entry in sorted(manifest["versions"].items()):
        status = "확인" if entry.get("confirmed_official") else "미확인"
        marker = "*" if identifier == active else ""
        print(f"{identifier}\t{entry.get('school_year','')}\t{entry.get('revision_date','')}\t{status}\t{marker}")


def command_activate(args: argparse.Namespace, paths: dict[str, Path]) -> None:
    manifest = load_manifest(paths)
    activate_version(paths, manifest, args.version, args.allow_unconfirmed)
    print(f"활성화 완료: {args.version}")


def command_verify(paths: dict[str, Path]) -> None:
    manifest = load_manifest(paths)
    verify_manifest(paths, manifest)
    active = manifest["active_version"]
    entry = manifest["versions"][active]
    confirmation = "사용자 확인" if entry.get("confirmed_official") else "확인 필요"
    print(f"검증 통과: {active} ({confirmation})")


def command_rebuild_index(paths: dict[str, Path]) -> None:
    """Regenerate the derived index without changing an active record or manifest."""
    manifest = load_manifest(paths)
    verify_manifest(paths, manifest)
    active = manifest["active_version"]
    entry = manifest["versions"][active]
    current = paths["current"].read_bytes()
    if sha256_bytes(current) != entry["sha256"]:
        raise GuidelineError("색인 재생성 전 current.md 해시 검증에 실패했습니다.")
    index = index_bytes(active, entry["sha256"], current.decode("utf-8"), load_index_terms(paths["index_terms"]))
    atomic_write(paths["index"], index)
    verify_manifest(paths, manifest)
    print(f"색인 재생성 완료: {active}")


def command_update_metadata(args: argparse.Namespace, paths: dict[str, Path]) -> None:
    if not args.source_url.startswith("https://"):
        raise GuidelineError("source-url은 https:// 형식이어야 합니다.")
    manifest = load_manifest(paths)
    entry = manifest["versions"].get(args.version)
    if not isinstance(entry, dict):
        raise GuidelineError(f"등록된 버전이 없습니다: {args.version}")
    archive = entry_path(paths, entry)
    if not archive.exists():
        raise GuidelineError(f"보관 파일이 없습니다: {archive}")
    if sha256_bytes(archive.read_bytes()) != entry.get("sha256"):
        raise GuidelineError(f"원문 해시 검증에 실패했습니다: {args.version}")
    updated = json.loads(json.dumps(manifest))
    old_url = updated["versions"][args.version].get("source_url", "")
    updated["versions"][args.version]["source_url"] = args.source_url
    atomic_write(paths["manifest"], json_bytes(updated))
    try:
        verify_manifest(paths, updated)
    except Exception as error:
        atomic_write(paths["manifest"], json_bytes(manifest))
        raise GuidelineError(f"메타데이터 수정에 실패해 기존 상태를 복구했습니다: {error}") from error
    print(f"출처 URL 수정 완료: {args.version}")
    print(f"이전 URL: {old_url or '(없음)'}")
    print(f"현재 URL: {args.source_url}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="스킬 디렉터리(기본: 이 스크립트의 상위 디렉터리)")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="새 Markdown 원문 등록")
    imp.add_argument("--input", type=Path, required=True)
    imp.add_argument("--school-year", required=True)
    imp.add_argument("--revision-date", required=True)
    imp.add_argument("--source-title", required=True)
    imp.add_argument("--source-url", default="")
    imp.add_argument("--confirmed-official", action="store_true")
    imp.add_argument("--activate", action="store_true")
    imp.add_argument("--allow-unconfirmed", action="store_true")
    listing = sub.add_parser("list", help="등록 버전 목록")
    listing.set_defaults()
    activate = sub.add_parser("activate", help="등록 버전 활성화")
    activate.add_argument("--version", required=True)
    activate.add_argument("--allow-unconfirmed", action="store_true")
    sub.add_parser("verify", help="활성 버전과 해시 검증")
    sub.add_parser("rebuild-index", help="활성 원문을 유지한 채 검색 색인 재생성")
    metadata = sub.add_parser("update-metadata", help="등록 버전의 출처 메타데이터 수정")
    metadata.add_argument("--version", required=True)
    metadata.add_argument("--source-url", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve() if args.root else Path(__file__).resolve().parents[1]
    paths = root_paths(root)
    try:
        if args.command == "import":
            command_import(args, paths)
        elif args.command == "list":
            command_list(paths)
        elif args.command == "activate":
            command_activate(args, paths)
        elif args.command == "update-metadata":
            command_update_metadata(args, paths)
        elif args.command == "rebuild-index":
            command_rebuild_index(paths)
        else:
            command_verify(paths)
        return 0
    except GuidelineError as error:
        print(f"오류: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
