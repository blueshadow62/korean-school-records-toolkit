#!/usr/bin/env python3
"""학교급별 기재요령 요약(summary.md)을 검사 규칙과 원문에 대조한다.

- SummaryShapeTests: 요약만으로 확인할 수 있는 것. 원문이 없는 배포본에서도 언제나 돈다.
- *SummaryOriginalTests: 원문 변환본이 등록된 환경(개발본·사용자 등록)에서만 돈다.
  최대 글자수 표의 모든 값, 인용한 훈령 조문, 장 제목, 금지 항목 이름을 원문과 대조한다.
"""

from __future__ import annotations

import html
import json
import re
import unittest
from pathlib import Path

from update_guidelines import load_manifest, read_summary_metadata, root_paths


SKILL_ROOT = Path(__file__).resolve().parents[1]
LEVELS = {"high": "guidelines", "middle": "guidelines-middle"}
LIMIT_TITLE = "영역별 입력 가능 최대 글자수"
QUOTE_RE = re.compile(r"(?m)^> 훈령 (제\d+조(?:의\d+)?제\d+항)(?:\([^)]*\))?: (.+)$")
RULE_BULLET_RE = re.compile(r"(?m)^- \*\*(\d+-\d+)\*\* (.+)$")
CITATION_RE = re.compile(r"〔([^〕]+)〕")

# 검사 규칙의 금지 표현 이름마다 요약에 그 규칙이 있음을 보여 주는 낱말.
LABEL_KEYWORDS = {
    "공인어학시험": ["공인어학시험"],
    "대회·수상": ["대회", "수상 실적"],
    "인증시험": ["인증시험"],
    "모의고사·전국연합학력평가": ["모의고사·전국연합학력평가"],
    "논문 투고·등재·학회 발표": ["논문", "학회"],
    "도서 출간": ["도서 출간"],
    "지식재산권 출원·등록": ["지식재산권"],
    "해외 활동": ["해외 활동실적"],
    "부모·친인척의 사회경제적 지위": ["사회·경제적 지위"],
    "장학금": ["장학금"],
    "자격증": ["자격증"],
    "구체적인 대학·기관·학교명 후보": ["대학명", "기관명"],
    "서울대 등 대학 약칭·별칭 후보": ["대학명"],
    "학원 강사 등 사교육·외부활동 후보": ["강사명"],
    "재학 학교 식별 후보": ["고등학교를 알 수 있는 내용"],
    "K-MOOC·MOOC·KOCW": ["K-MOOC, MOOC, KOCW"],
    "방과후학교": ["방과후학교"],
    "연구보고서·소논문": ["연구보고서(소논문)"],
}

# 원문 「01 학교생활기록부 작성 시 유의사항」에 있어야 하는 금지 항목 이름. 요약 2절에도 있어야 한다.
COMMON_PROHIBITED_TERMS = [
    "공인어학시험", "TOEIC", "TOEFL", "TEPS", "HSK", "JPT", "JLPT", "DELF", "DALF", "ZD", "TESTDAF", "DSH", "DSD",
    "TORFL", "DELE", "상공회의소한자시험", "한자능력검정", "실용한자", "한자급수자격검정", "YBM 상무한검",
    "한자급수인증시험", "한자자격검정", "교내·외 대회", "교외상", "표창장", "감사장", "공로상", "인증시험",
    "학회지", "도서출간", "지식재산권", "특허", "실용신안", "상표", "디자인", "어학연수", "해외 활동실적",
    "사회·경제적 지위", "직종명", "직업명", "직장명", "직위명", "장학생", "장학금", "대학명", "기관명", "상호명",
    "강사명", "자격증 명칭", "대한민국학술원", "국사편찬위원회", "국립국제교육원", "국립특수교육원",
    "교원소청심사위원회", "중앙교육연수원",
]
HIGH_ONLY_PROHIBITED_TERMS = ["모의고사·전국연합학력평가", "학교명", "재단명", "학교 축제명", "학교 별칭"]

# 검사 규칙 field_limits_v2의 값과 요약 표의 행(영역에 든 낱말, 세부항목 앞부분, 한도 칸)을 잇는다.
RULE_ROWS = {
    "high": [
        (("subject", "default"), "교과학습발달상황", "과목별 세부능력 및 특기사항", "과목별 500자"),
        (("creative", "autonomy"), "창의적 체험활동상황", "자율·자치활동 특기사항", "500자"),
        (("creative", "club"), "창의적 체험활동상황", "동아리활동 특기사항", "500자"),
        (("creative", "career"), "창의적 체험활동상황", "진로활동 특기사항", "500자"),
        (("creative", "service_record_item"), "창의적 체험활동상황", "봉사활동실적 활동내용", "실적별 50자"),
        (("behavior",), "행동특성 및 종합의견", "행동특성 및 종합의견", "300자"),
        (("individual_subject",), "교과학습발달상황", "개인별 세부능력 및 특기사항", "500자"),
    ],
    "middle": [
        (("subject", "default"), "교과학습발달상황", "과목별 세부능력 및 특기사항", "과목별 500자"),
        (("creative", "autonomy"), "창의적 체험활동상황", "자율·자치활동 특기사항", "500자"),
        (("creative", "club"), "창의적 체험활동상황", "동아리활동 특기사항", "500자"),
        (("creative", "career"), "창의적 체험활동상황", "진로활동 특기사항", "500자"),
        (("creative", "service_record_item"), "창의적 체험활동상황", "봉사활동실적 활동내용", "실적별 50자"),
        (("behavior",), "행동특성 및 종합의견", "행동특성 및 종합의견", "300자"),
        (("individual_subject",), "교과학습발달상황", "개인별 세부능력 및 특기사항", "500자"),
        (("free_semester",), "자유학기활동상황", "진로탐색활동 특기사항", "1,000자"),
        (("free_semester",), "자유학기활동상황", "주제선택활동 특기사항", "1,000자"),
        (("free_semester",), "자유학기활동상황", "예술·체육활동 특기사항", "1,000자"),
        (("free_semester",), "자유학기활동상황", "동아리활동 특기사항", "1,000자"),
    ],
}


def dots(value: str) -> str:
    for mark in ("ㆍ", "･", "‧", "・", "∙"):
        value = value.replace(mark, "·")
    return value


def squash(value: str) -> str:
    """비교용: 가운뎃점을 하나로 맞추고 공백·쉼표·별표를 지운다."""
    return re.sub(r"[\s,*]+", "", dots(value))


def normalize_original(text: str) -> str:
    """원문 변환본을 조문 대조용 한 줄 글로 바꾼다. 표 태그와 줄바꿈, 목록 기호, 이스케이프만 지운다."""
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text).replace("\\", "")
    text = re.sub(r"(?m)^\s*(?:[-*]\s+|#+\s+)", " ", text)
    return re.sub(r"\s+", " ", text)


def chapter_key(title: str) -> str:
    return squash(re.sub(r"^\d+(?:-\d+)?\s*", "", title.strip()))


def summary_path(level: str) -> Path:
    return SKILL_ROOT / "references" / LEVELS[level] / "summary.md"


def summary_text(level: str) -> str:
    return summary_path(level).read_text(encoding="utf-8")


def section(text: str, title_word: str) -> str:
    parts = re.split(r"(?m)^## \d+\. [^\n]*" + re.escape(title_word) + r"[^\n]*$", text, maxsplit=1)
    if len(parts) != 2:
        raise AssertionError(f"요약에 '{title_word}' 절이 없다")
    return parts[1].split("\n## ", 1)[0]


def summary_limit_rows(text: str) -> list[tuple[str, str, str, str]]:
    rows = []
    for line in section(text, LIMIT_TITLE).splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| 영역 |"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append((cells[0], cells[1], cells[2], cells[3]))
    return rows


def legend_keys(text: str) -> dict[str, str]:
    keys = {}
    for line in text.split("## 1.", 1)[0].splitlines():
        match = re.match(r"^\| (\S+) \| 「(.+)」 \| .+ \|$", line)
        if match:
            keys[match.group(1)] = match.group(2)
    return keys


def original_registered(level: str) -> bool:
    folder = SKILL_ROOT / "references" / LEVELS[level]
    return (folder / "manifest.json").is_file() and (folder / "current.md").is_file()


def original_text(level: str) -> str:
    return (SKILL_ROOT / "references" / LEVELS[level] / "current.md").read_text(encoding="utf-8")


def original_limit_rows(text: str) -> list[tuple[str, str, str, str]]:
    """원문 최대 글자수 표를 (영역, 세부항목, 한도, 비고)로 바꾼다. rowspan으로 생략된 영역과 비고는 앞 행에서 잇는다."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(r"^#\s+\d+\s+학교생활기록부 영역별 입력 가능 최대 글자수\s*$", line))
    table = re.search(r"<table>(.*?)</table>", "\n".join(lines[start + 1:]), re.S).group(1)
    rows, area, area_left, note, note_left = [], "", 0, "", 0
    for row in re.findall(r"<tr>(.*?)</tr>", table, re.S):
        if "<th" in row:
            continue
        cells = re.findall(r"<td([^>]*)>(.*?)</td>", row, re.S)
        values = [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<br\s*/?>", " ", raw))).split()) for _, raw in cells]
        spans = [int(re.search(r'rowspan="(\d+)"', attrs).group(1)) if "rowspan" in attrs else 1 for attrs, _ in cells]
        if area_left == 0:
            area, area_left = values.pop(0), spans.pop(0)
        item, limit = values.pop(0), values.pop(0)
        spans = spans[2:]
        if note_left == 0:
            note, note_left = (values.pop(0), spans.pop(0)) if values else ("", 1)
        rows.append((re.sub(r"^\d+\.\s*", "", area), item, limit, note))
        area_left -= 1
        note_left -= 1
    return rows


class SummaryShapeTests(unittest.TestCase):
    """요약만으로 확인한다. 원문이 없는 배포본에서도 돈다."""

    def test_front_matter_matches_the_folder_and_the_analyzer_rules(self) -> None:
        for level, folder in LEVELS.items():
            with self.subTest(level=level):
                meta = read_summary_metadata(summary_path(level))
                self.assertEqual(level, meta["school_level"])
                self.assertEqual("guideline-summary", meta["document"])
                self.assertIn("(고등학교)" if level == "high" else "(중학교)", meta["source_title"])
                self.assertTrue(meta["source_url"].startswith("https://www.moe.go.kr/"))
                self.assertRegex(meta["summary_written"], r"^20\d{2}-\d{2}-\d{2}$")
                rules_path = SKILL_ROOT / "references" / folder / "analyzer-rules" / f"{meta['school_year']}.json"
                rules = json.loads(rules_path.read_text(encoding="utf-8"))
                self.assertEqual(meta["school_year"], str(rules["school_year"]))
                self.assertTrue(rules["reviewed"], "요약 학년도의 검사 규칙이 검토되지 않았다")

    def test_states_what_it_is_and_where_authority_lies(self) -> None:
        for level in LEVELS:
            with self.subTest(level=level):
                text = summary_text(level)
                meta = read_summary_metadata(summary_path(level))
                head = text.split("## 1.", 1)[0]
                self.assertIn("이 스킬이 직접 정리한 요약이다", head)
                self.assertIn("공식 효력은 교육부 원문에 있다", head)
                self.assertIn("[ATTRIBUTION.md](ATTRIBUTION.md)", head)
                self.assertIn(f"요약 작성일은 {meta['summary_written']}이다", head)
                self.assertIn(meta["source_url"], head)
                self.assertIn("이 요약에 없는 규정을 추측해 채우지 않는다", head)

    def test_does_not_depend_on_the_original_file_or_line_numbers(self) -> None:
        for level in LEVELS:
            with self.subTest(level=level):
                text = summary_text(level)
                self.assertNotIn("current.md", text)
                self.assertEqual(re.findall(r"\d{2,4}(?:[~–-]\d{2,4})?행", text), [], "행 번호 인용")

    def test_every_rule_cites_a_known_chapter(self) -> None:
        for level in LEVELS:
            text = summary_text(level)
            keys = legend_keys(text)
            self.assertGreaterEqual(len(keys), 9)
            bullets = RULE_BULLET_RE.findall(text)
            self.assertGreaterEqual(len(bullets), 60)
            for number, body in bullets:
                with self.subTest(level=level, rule=number):
                    citations = CITATION_RE.findall(body)
                    self.assertTrue(citations, "규칙 끝에 원문 장 표기가 없다")
                    for part in ", ".join(citations).split(", "):
                        self.assertIn(part.split(" ")[0], keys, f"약칭 표에 없는 장: {part}")

    def test_directive_quotes_are_marked_and_few(self) -> None:
        expected = {"high": 6, "middle": 10}
        for level in LEVELS:
            with self.subTest(level=level):
                text = summary_text(level)
                quotes = QUOTE_RE.findall(text)
                self.assertEqual(expected[level], len(quotes))
                self.assertEqual(len(quotes), len(re.findall(r"(?m)^> 훈령 ", text)), "형식이 다른 조문 인용")
                for article, body in quotes:
                    self.assertTrue(body.startswith(("①", "②", "③", "④", "⑥", "⑦", "⑪", "⑬")), f"{article} 인용은 항 번호부터 옮긴다")

    def test_limit_table_matches_the_analyzer_rules(self) -> None:
        for level, folder in LEVELS.items():
            text = summary_text(level)
            rows = summary_limit_rows(text)
            rules = json.loads((SKILL_ROOT / "references" / folder / "analyzer-rules" / "2026.json").read_text(encoding="utf-8"))
            limits = rules["field_limits_v2"]
            for keys, area_word, item_prefix, cell in RULE_ROWS[level]:
                with self.subTest(level=level, item=item_prefix):
                    matches = [row for row in rows if area_word in row[0] and row[1].startswith(item_prefix)]
                    self.assertEqual(1, len(matches), f"요약 표에서 찾은 행: {matches}")
                    self.assertEqual(cell, matches[0][2])
                    rule = limits
                    for key in keys:
                        rule = rule[key]
                    number = int(re.sub(r"[^\d]", "", cell))
                    self.assertEqual(number, rule["korean_characters"])
                    self.assertEqual(number * 3, rule["bytes"])
            if level == "high":
                subject_note = next(row[3] for row in rows if row[1] == "과목별 세부능력 및 특기사항")
                self.assertIn("공통과목 1·2 합산 500자", subject_note)
                self.assertIn("전공실무과목 학기별 500자", subject_note)
                self.assertEqual(500, limits["subject"]["common_combined"]["korean_characters"])
                self.assertEqual(500, limits["subject"]["vocational_per_semester"]["korean_characters"])
            else:
                self.assertEqual({"default"}, set(limits["subject"]))
                self.assertFalse([row for row in rows if "공통과목" in row[3] or "전공·과정" in row[0]])
            self.assertFalse([row for row in rows if "봉사활동 특기사항" in row[1]], "원문에 없는 봉사활동 특기사항 칸")

    def test_every_analyzer_prohibition_has_a_rule_in_the_summary(self) -> None:
        for level, folder in LEVELS.items():
            text = summary_text(level)
            rules = json.loads((SKILL_ROOT / "references" / folder / "analyzer-rules" / "2026.json").read_text(encoding="utf-8"))
            for label in rules["prohibited_patterns"]:
                with self.subTest(level=level, label=label):
                    self.assertIn(label, LABEL_KEYWORDS, "새 금지 표현 이름은 LABEL_KEYWORDS에 근거 낱말을 함께 적는다")
                    for keyword in LABEL_KEYWORDS[label]:
                        self.assertIn(keyword, text)
        middle = summary_text("middle")
        self.assertIn("'고등학교 관련 내용으로 생략'", middle)
        self.assertNotIn("고등학교를 알 수 있는 내용", middle)

    def test_unsupported_areas_get_limits_and_chapters_only(self) -> None:
        for level in LEVELS:
            with self.subTest(level=level):
                body = section(summary_text(level), "지원하지 않는 영역")
                self.assertIn("이 요약에 없는 세부 규정을 추측해 답하지 않는다", body)
                for area in ("개인별 세부능력 및 특기사항", "독서활동상황", "봉사활동 실적", "출결상황 특기사항", "인적·학적사항 특기사항", "학생부 자료의 정정"):
                    row = next((line for line in body.splitlines() if line.startswith(f"| {area}")), None)
                    self.assertIsNotNone(row, area)
                    self.assertIn("「", row)


class SummaryOriginalMixin:
    """원문이 등록된 환경에서 요약을 원문과 대조한다."""

    level = ""

    def setUp(self) -> None:
        self.summary = summary_text(self.level)
        self.original = original_text(self.level)
        self.normalized = normalize_original(self.original)

    def test_front_matter_matches_the_registered_original(self) -> None:
        paths = root_paths(SKILL_ROOT, self.level)
        manifest = load_manifest(paths)
        entry = manifest["versions"][manifest["active_version"]]
        meta = read_summary_metadata(summary_path(self.level))
        for key in ("school_year", "revision_date", "source_title", "source_url"):
            with self.subTest(key=key):
                self.assertEqual(str(entry[key]), meta[key], "요약을 등록된 원문의 학년도·개정판에 맞춰 갱신해야 한다")
        self.assertIn(meta["directive"].split("(")[0], self.original)

    def test_quoted_directive_text_is_verbatim(self) -> None:
        for article, body in QUOTE_RE.findall(self.summary):
            with self.subTest(article=article):
                self.assertIn(body, self.normalized)

    def test_cited_chapter_titles_exist_in_the_original(self) -> None:
        headings = {
            chapter_key(match.group(1))
            for line in self.original.splitlines()
            for match in [re.match(r"^#{1,6}\s+(.+?)\s*$", line)]
            if match
        }
        titles = set(re.findall(r"「((?:[^「」]|「[^「」]*」)+)」", self.summary))
        # 장 제목은 '01 ', '13-1 '처럼 장 번호와 공백으로 시작한다. 문서 제목(2026학년도 …)은 제외한다.
        chapters = {title for title in titles if re.match(r"^\d{1,2}(?:-\d+)?\s", title)}
        self.assertGreaterEqual(len(chapters), 10)
        for title in sorted(chapters):
            with self.subTest(title=title):
                self.assertIn(chapter_key(title), headings)
        for key, title in legend_keys(self.summary).items():
            with self.subTest(legend=key):
                self.assertIn(chapter_key(title), headings)

    def test_limit_table_matches_the_original_table_row_by_row(self) -> None:
        original = original_limit_rows(self.original)
        summary = summary_limit_rows(self.summary)
        self.assertEqual(len(original), len(summary))
        for left, right in zip(original, summary):
            with self.subTest(row=right[1]):
                self.assertEqual([squash(value) for value in left], [squash(value) for value in right])

    def test_limit_footnotes_match(self) -> None:
        body = section(self.summary, LIMIT_TITLE)
        self.assertIn("최대 글자수 기준은 학년 단위임", self.original)
        self.assertIn("한글 1자는 3Byte, 영문･숫자 1자는 1Byte, 엔터(Enter)는 1Byte", self.original)
        self.assertIn("한글 1자 3Byte, 영문·숫자 1자 1Byte, 엔터 1Byte", body)
        self.assertIn("학년 단위", body)

    def test_prohibited_item_names_appear_in_the_original(self) -> None:
        start = self.original.index("# 01 학교생활기록부 작성 시 유의사항")
        end = self.original.index("# 02 학교생활기록부 관련 문의 방법")
        chapter = squash(normalize_original(self.original[start:end]))
        rules_section = section(self.summary, "모든 항목에서 쓸 수 없는 것")
        terms = COMMON_PROHIBITED_TERMS + (HIGH_ONLY_PROHIBITED_TERMS if self.level == "high" else [])
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(squash(term), squash(rules_section), "요약 2절에 없는 항목")
                self.assertIn(squash(term), chapter, "원문 유의사항 장에 없는 항목")


@unittest.skipUnless(original_registered("high"), "고등학교 기재요령 원문이 등록되지 않은 환경(배포본)")
class HighSummaryOriginalTests(SummaryOriginalMixin, unittest.TestCase):
    level = "high"


@unittest.skipUnless(original_registered("middle"), "중학교 기재요령 원문이 등록되지 않은 환경(배포본)")
class MiddleSummaryOriginalTests(SummaryOriginalMixin, unittest.TestCase):
    level = "middle"


if __name__ == "__main__":
    unittest.main()
