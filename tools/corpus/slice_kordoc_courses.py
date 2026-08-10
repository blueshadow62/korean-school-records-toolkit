"""Slice kordoc v2 whole-document MD into per-course corpus files, with verification.

Course sections in the NKIS reports are delimited by roman-numeral headings
(`# Ⅶ. 안무 성취수준`). Intro sections (Ⅰ 성취수준 개발의 이해, Ⅱ 성취수준 활용)
carry no course content and are skipped by name.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import unicodedata
from pathlib import Path

ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"
# The roman numeral must be a standalone token; otherwise "Ⅰ장에서는 ..." parses as a chapter.
HEADING_RE = re.compile(rf"^#+\s*([{ROMAN}]+)(?=[\s.．]|$)\s*[.．]?\s*(.*)$")
TRIM_RE = re.compile(r"예시\s*평가\s*도구")
CODE_RE = re.compile(r"\[\d{2}[^\]\s]{1,14}\d{2}-\d{2}\]")
DESCRIPTOR_RE = re.compile(r"성취기준별 성취수준|영역별 성취수준")
# Same contract the corpus test enforces: course files carry descriptors only.
EXCLUDED_RE = re.compile(r"성취수준 개발의 이해|성취수준 활용|예시.{0,20}평가|<img|!\[|image_[0-9]+", re.I)
IMAGE_RE = re.compile(r"!\[[^]]*\]\([^)]*\)")
# Intro chapters that describe the framework rather than a course.
SKIP_TITLES = ("성취수준 개발의 이해", "성취수준 활용", "연구", "부록")


def norm(s: str) -> str:
    """Fold to a comparison key: NFC, drop spaces/underscores/middots."""
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"[\s_·ㆍ・･]+", "", s)


def strip_ws(s: str) -> str:
    return re.sub(r"\s+", "", s)


def course_sections(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return (start, end, title) for every roman-numeral chapter occurrence.

    All occurrences are kept, not just the first per numeral: several reports
    restart numbering in an appendix where the real course content lives, so the
    caller picks the right candidate by matching achievement-standard codes.
    """
    marks: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if "···" in line or "…" in line:
            continue  # table-of-contents entry
        m = HEADING_RE.match(line)
        if not m:
            continue
        title = re.sub(r"성취수준\s*$", "", m.group(2).strip()).strip()
        # Cover page and running header repeat the same chapter within a few lines.
        if marks and i - marks[-1][0] <= 20:
            if not marks[-1][1] and title:
                marks[-1] = (marks[-1][0], title)
            continue
        marks.append((i, title))

    out = []
    for idx, (start, title) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        out.append((start, end, title))
    return out


def build_body(lines: list[str], start: int, end: int, want: set[str] | None = None) -> str:
    """Cut a course section down to descriptor tables only.

    Mirrors trim_achievement_examples.py: the 예시 평가 도구 boundary only counts once
    real descriptor content precedes it, because each course opens with a mini table of
    contents that names the same section. Stray mentions left over from that mini TOC are
    dropped afterwards so the corpus stays descriptor-only.
    """
    chunk = lines[start:end]
    for i, line in enumerate(chunk):
        if not TRIM_RE.search(line):
            continue
        before = "\n".join(chunk[:i])
        if len(strip_ws(before)) >= 200 and DESCRIPTOR_RE.search(before):
            chunk = chunk[:i]
            break
    chunk = [line for line in chunk if not EXCLUDED_RE.search(line)]
    text = "\n".join(chunk).rstrip() + "\n"
    return IMAGE_RE.sub("", text)


def cells_of(text: str) -> list[str]:
    raw = re.findall(r"<td[^>]*>(.*?)</td>", text, flags=re.S)
    out = []
    for c in raw:
        c = re.sub(r"<[^>]+>", " ", c)
        if len(strip_ws(c)) >= 8 and re.search(r"[가-힣]", c):
            out.append(c)
    return out


def git_show(git_root: Path, path: Path) -> str:
    """Committed content of a tracked file, used as the stable verification baseline."""
    rel = path.resolve().relative_to(git_root.resolve()).as_posix()
    out = subprocess.run(
        ["git", "-C", str(git_root), "show", f"HEAD:{rel}"],
        capture_output=True, check=True,
    )
    return out.stdout.decode("utf-8")


def is_subseq(needle: str, hay: str) -> bool:
    it = iter(hay)
    return all(ch in it for ch in needle)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md-root", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--skip-list", type=Path, required=True, help="TSV report; 'skipped' rows are protected")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", default=None, help="limit to one subject folder")
    ap.add_argument("--git-root", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    protected = set()
    for row in args.skip_list.read_text(encoding="utf-8").splitlines():
        parts = row.split("\t")
        if len(parts) >= 2 and parts[0] == "skipped":
            protected.add(norm(parts[1].replace("\\", "/")))

    # corpus course files, keyed by normalised stem within their subject folder
    targets: dict[str, list[Path]] = collections.defaultdict(list)
    for path in sorted(args.corpus.rglob("*.md")):
        if path.name in ("index.md", "common.md", "ATTRIBUTION.md"):
            continue
        rel = path.relative_to(args.corpus).as_posix()
        if norm(rel) in protected:
            continue
        targets[norm(path.stem)].append(path)

    # Index every candidate section of every document once, then let each corpus
    # file claim the section that actually carries its achievement-standard codes.
    docs = []
    for md in sorted(args.md_root.glob("*.md")):
        lines = md.read_text(encoding="utf-8").splitlines()
        docs.append((md, lines, course_sections(lines)))

    lines_out = []
    stats = collections.Counter()
    for dests in targets.values():
        for dest in dests:
            if args.only and args.only not in dest.as_posix():
                continue
            rel = dest.relative_to(args.corpus).as_posix()
            # Baseline must be the committed original, not the working tree: re-running
            # this tool would otherwise compare against its own previous output.
            old = git_show(args.git_root, dest)
            want = set(CODE_RE.findall(re.sub(r"<[^>]+>", "", old)))
            if not want:
                stats["no-codes-in-corpus"] += 1
                lines_out.append(f"failed\t{rel}\t기존 파일에서 성취기준 코드를 찾지 못함")
                continue

            best = None
            for md, lines, sections in docs:
                for start, end, title in sections:
                    chunk = "\n".join(lines[start:end])
                    # Narrative chapters ("교육과정 및 성취기준 분석") also hold tables and cite
                    # course codes, so a candidate must carry an actual descriptor section.
                    if "<table" not in chunk or not DESCRIPTOR_RE.search(chunk):
                        continue
                    hit = len(want & set(CODE_RE.findall(chunk)))
                    if hit and (best is None or hit > best[0]):
                        best = (hit, md, lines, start, end, title)
            if best is None:
                stats["no-corpus-match"] += 1
                lines_out.append(f"failed\t{rel}\t새 MD에서 해당 코드를 가진 구간을 찾지 못함")
                continue

            _hit, md, lines, start, end, _title = best
            body = build_body(lines, start, end, want)
            cells = cells_of(body)

            if not cells:
                stats["no-cells"] += 1
                lines_out.append(f"failed\t{rel}\t표 셀 0개 (분할 경계 오류)")
                continue
            # Same contract the corpus test asserts, checked before anything is written.
            if not DESCRIPTOR_RE.search(body):
                stats["no-descriptor"] += 1
                lines_out.append(f"failed\t{rel}\t성취수준 표 머리글이 없음 (서술 장을 잘못 선택)")
                continue
            # fidelity: every cell must exist in the whole-document text
            doc = strip_ws("\n".join(lines))
            bad = [c for c in cells if not is_subseq(strip_ws(c), doc)]
            if bad:
                stats["fidelity"] += 1
                lines_out.append(f"failed\t{rel}\t충실성 실패 {len(bad)}셀: {bad[0][:60]}")
                continue
            # Completeness is measured by achievement-standard codes, not raw words:
            # the old file may still carry 예시 평가 도구 text that this slice correctly drops,
            # so word-level diffing would punish the better output.
            # kordoc wraps long cells with <br>, which can split a code in half.
            lost = want - set(CODE_RE.findall(re.sub(r"<[^>]+>", "", body)))
            if lost:
                stats["completeness"] += 1
                lines_out.append(f"failed\t{rel}\t성취기준 코드 누락 {len(lost)}/{len(want)}: {sorted(lost)[:5]}")
                continue
            if args.apply:
                dest.write_text(body, encoding="utf-8", newline="\n")
            stats["ok"] += 1
            lines_out.append(f"ok\t{rel}\t{md.stem[:28]}\t셀{len(cells)}\t코드{len(want)}")

    args.report.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    for k, v in sorted(stats.items()):
        print(f"{k}\t{v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
