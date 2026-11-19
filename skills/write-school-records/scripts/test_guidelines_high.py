#!/usr/bin/env python3
"""SKILL.md '지원 영역'의 한도가 고등학교 기재요령 최대 글자수 표와 맞는지 확인한다.

SKILL.md는 행 번호 대신 표 제목으로 요약의 표를 가리킨다. 요약의 표는 언제나 검사하고,
원문 변환본이 등록된 환경(개발본·사용자 등록)에서는 원문 표도 함께 검사한다.
새 학년도 기재요령을 활성화해 제목이 바뀌거나 표에서 영역이 빠지거나 한도가 달라지면 여기서 잡는다.
"""

import html
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL = SKILL_ROOT / "SKILL.md"
HIGH = SKILL_ROOT / "references" / "guidelines"
HIGH_CURRENT = HIGH / "current.md"
HIGH_SUMMARY = HIGH / "summary.md"
ORIGINAL_REGISTERED = (HIGH / "manifest.json").is_file() and HIGH_CURRENT.is_file()
TABLE_TITLE = "학교생활기록부 영역별 입력 가능 최대 글자수"
SUMMARY_TABLE_TITLE = "영역별 입력 가능 최대 글자수"
HEADING_RE = re.compile(r"^#\s+(?:\d+\s+)?" + re.escape(TABLE_TITLE) + r"\s*$")

# (영역 열에 들어 있는 낱말, 세부항목 열의 앞부분) -> 표의 한도 값.
# SKILL.md '지원 영역' 절이 근거로 드는 영역 전부이다.
EXPECTED_LIMITS = {
    ("인적", "특기사항"): "500자",
    ("출결", "특기사항"): "500자",
    ("창의적 체험활동", "자율"): "500자",
    ("창의적 체험활동", "동아리활동 특기사항"): "500자",
    ("창의적 체험활동", "진로활동 특기사항"): "500자",
    ("창의적 체험활동", "봉사활동실적"): "실적별 50자",
    ("교과학습발달", "과목별 세부능력 및 특기사항"): "과목별 500자",
    ("교과학습발달", "개인별 세부능력 및 특기사항"): "500자",
    ("독서활동", "공통"): "500자",
    ("독서활동", "과목별"): "250자",
    ("행동특성", "행동특성 및 종합의견"): "300자",
}


def cell_text(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", raw)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(html.unescape(text).split())


def limit_rows(markdown: str) -> list[tuple[str, str, str]]:
    """원문 제목 아래 첫 표를 (영역, 세부항목, 한도) 행으로 바꾼다. rowspan으로 생략된 영역은 앞 행에서 잇는다."""
    lines = markdown.splitlines()
    starts = [index for index, line in enumerate(lines) if HEADING_RE.match(line)]
    if len(starts) != 1:
        raise AssertionError(f"'{TABLE_TITLE}' 제목 줄이 {len(starts)}개 있다(1개여야 함)")
    rest = "\n".join(lines[starts[0] + 1:])
    table = re.search(r"<table>(.*?)</table>", rest, re.S)
    if table is None:
        raise AssertionError(f"'{TABLE_TITLE}' 제목 아래에 표가 없다")
    rows = []
    area = ""
    for row in re.findall(r"<tr>(.*?)</tr>", table.group(1), re.S):
        cells = [cell_text(cell) for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if "<th" in row:
            continue
        if len(cells) == 4:
            area, item, limit = cells[0], cells[1], cells[2]
        elif len(cells) == 3:
            item, limit = cells[0], cells[1]
        else:
            continue
        rows.append((area, item, limit))
    return rows


def summary_limit_rows(markdown: str) -> list[tuple[str, str, str]]:
    """요약의 최대 글자수 절에 있는 Markdown 표를 (영역, 세부항목, 한도) 행으로 바꾼다."""
    section = re.split(r"(?m)^## \d+\. " + re.escape(SUMMARY_TABLE_TITLE) + r"\s*$", markdown)
    if len(section) != 2:
        raise AssertionError(f"요약에 '{SUMMARY_TABLE_TITLE}' 절이 {len(section) - 1}개 있다(1개여야 함)")
    body = section[1].split("\n## ", 1)[0]
    rows = []
    for line in body.splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| 영역 |"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def find_limit(rows: list[tuple[str, str, str]], area_word: str, item_prefix: str) -> list[str]:
    return [limit for area, item, limit in rows if area_word in area and item.startswith(item_prefix)]


def supported_section(skill: str) -> str:
    return skill.split("### 지원 영역", 1)[1].split("\n#", 1)[0]


class HighGuidelineLimitTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = SKILL.read_text(encoding="utf-8")
        self.summary_rows = summary_limit_rows(HIGH_SUMMARY.read_text(encoding="utf-8"))

    def test_skill_points_to_the_table_by_title_not_line_number(self) -> None:
        section = supported_section(self.skill)
        self.assertIn(TABLE_TITLE, section)
        self.assertIn("[guidelines/summary.md](references/guidelines/summary.md)", section)
        self.assertNotIn("current.md", section)
        self.assertEqual(re.findall(r"\d+(?:~\d+)?행", section), [], "행 번호로 기재요령을 가리키는 표현")

    def test_each_supported_area_has_its_limit_in_the_summary_table(self) -> None:
        for (area_word, item_prefix), limit in EXPECTED_LIMITS.items():
            with self.subTest(area=area_word, item=item_prefix):
                matches = find_limit(self.summary_rows, area_word, item_prefix)
                self.assertEqual(len(matches), 1, f"요약 표에서 찾은 행: {matches}")
                self.assertEqual(matches[0], limit)

    @unittest.skipUnless(ORIGINAL_REGISTERED, "고등학교 기재요령 원문이 등록되지 않은 환경(배포본)")
    def test_each_supported_area_has_its_limit_in_the_original_table(self) -> None:
        rows = limit_rows(HIGH_CURRENT.read_text(encoding="utf-8"))
        for (area_word, item_prefix), limit in EXPECTED_LIMITS.items():
            with self.subTest(area=area_word, item=item_prefix):
                matches = find_limit(rows, area_word, item_prefix)
                self.assertEqual(len(matches), 1, f"원문 표에서 찾은 행: {matches}")
                self.assertEqual(matches[0], limit)

    def test_skill_states_the_same_limits(self) -> None:
        section = supported_section(self.skill)
        for phrase in (
            "한도 과목별 500자",
            "영역별 500자",
            "행특(300자)",
            "개인별 세특(500자)",
            "공통 500자·과목별 250자",
            "객관 기술 50자",
            "출결 특기사항(500자)",
            "학적 특기사항(500자)",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, section)

    def test_skill_does_not_claim_a_service_remarks_area(self) -> None:
        # 원문에는 봉사활동 특기사항 칸이 없다. 3학년 봉사 영역은 실적만 입력한다.
        section = supported_section(self.skill)
        self.assertNotIn("3학년 봉사 포함", section)
        self.assertIn("봉사활동 영역은 특기사항 없이 실적만 입력", section)
        self.assertEqual(find_limit(self.summary_rows, "창의적 체험활동", "봉사활동 특기사항"), [])


if __name__ == "__main__":
    unittest.main()
