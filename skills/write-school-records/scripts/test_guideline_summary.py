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


# 기록 여부·위치를 가르는 조건 문구(2026-11-19 독립 검증 보고서 A1~A7, B1과 '넣지 않은 규정' 재검토).
# (요약 규칙 번호, 그 규칙 줄에 있어야 하는 요약 구절, 원문에 있어야 하는 구절). 비교는 squash로 한다.
CONDITION_ANCHORS = {
    "high": [
        ("2-12", "공공성을 가진 기관에 한함", "공공성을 가진 기관에 한함"),
        ("2-12", "일반고 직업계열 학과 운영교에 한해", "일반고 직업계열학과 운영교에 한하여 기재 가능"),
        ("4-6", "미이수 처리하고", "해당 과목을 미이수 처리하고"),
        ("4-6", "세특은 쓰지 않는다", "과목별 세부능력 특기사항은 미기재"),
        ("4-6", "공동교육과정 과목을 이수하지 못한 학생의 성적을 산출하지 않고 학생부 기재에서 제외한다", "공동교육과정 미이수 학생의 경우 성적 미산출 및 학생부 기재 제외"),
        ("4-18", "교육 수료증이 발급되는 과정", "교육 수료증이 발급되는"),
        ("4-18", "학교가 자체로 실시한 과정은 들지 않는다", "학교 자체 실시 과정 제외"),
        ("4-20", "17개 교과군 가운데 하나", "17개 교과군 중에서"),
        ("4-21", "단순 독후활동 외의 교육활동", "단순 독후활동(감상문 작성 등) 외 교육활동"),
        ("4-22", "이수 내용만 문장으로 쓴다", "문장으로 이수 내용만을 입력한다"),
        ("5-8", "병원학교·원격수업기관에서 한 활동 내용이 있으면", "원격수업기관의 활동 내용이 있는 경우"),
        ("5-8", "현장체험학습(수련활동 등) 기간에 참여하지 않은 학생", "현장체험학습(수련활동 등) 기간 동안 미참여 학생"),
        ("5-16", "3학년은 3월 1일부터 졸업일까지", "3학년은 3월 1일부터 졸업일까지"),
        ("5-16", "재선출일", "재선출일"),
        ("5-19", "학교장이 승인한 활동만 인정한다", "학교장이 승인한 경우만 인정"),
        ("5-19", "학교 밖에서 조직된 스포츠클럽은 학교스포츠클럽으로 인정하지 않는다", "학교 이외에서 조직된 스포츠클럽은 인정하지 않는다"),
        ("5-28", "물품이나 현금을 단순히 기부한 것", "물품 및 현금의 단순 기부"),
    ],
    "middle": [
        ("4-16", "교육 수료증이 발급되는 과정", "교육 수료증이 발급되는"),
        ("4-16", "학교가 자체로 실시한 과정은 들지 않는다", "학교자체 실시 과정 제외"),
        ("4-17", "단순 독후활동 외의 교육활동", "단순 독후활동(감상문 작성 등) 외 교육활동"),
        ("4-17", "자유학기활동상황", "자유학기활동상황 등)에 입력할 수 있다"),
        ("4-18", "이수 내용만 문장으로 쓴다", "문장으로 이수 내용만을 입력한다"),
        ("4-18", "그 과목 관련 내용을 일절 쓰지 않는다", "해당 과목 관련 내용을 일절 기재하지"),
        ("5-8", "병원학교·원격수업기관에서 한 활동 내용이 있으면", "원격수업기관의 활동 내용이 있는 경우"),
        ("5-16", "3학년은 3월 1일부터 졸업일까지", "3학년은 3월 1일부터 졸업일까지"),
        ("5-16", "재선출일", "재선출일"),
        ("5-21", "학교장이 승인한 기간에 한 것으로 한정", "학교장이 승인한 기간에 수행한 것으로 한정한다"),
        ("5-21", "학교장이 승인한 활동만 인정한다", "학교장이 승인한 경우만 인정"),
        ("5-21", "학교 밖에서 조직된 스포츠클럽은 학교스포츠클럽으로 인정하지 않는다", "학교 이외에서 조직된 스포츠클럽은 인정하지 않는다"),
        ("5-29", "물품이나 현금을 단순히 기부한 것", "물품 및 현금의 단순 기부"),
        ("6-6", "병원학교·원격수업기관에서 한 활동 내용이 있으면", "원격수업기관의 활동 내용이 있는 경우"),
    ],
}

# 영역 문서의 게이트가 가리키는 규칙 번호. (문서, 시작 제목, 끝 제목, 번호를 찾을 요약의 학교급)
RULE_POINTER_SECTIONS = [
    (name, start, end, level)
    for name in ("subject-humanities.md", "subject-stem.md", "subject-practical-arts.md", "field-creative.md")
    for start, end, level in (("규정 게이트", "## 중학교 차이", "high"), ("## 중학교 차이", "\n## ", "middle"))
]
RULE_NUMBER_RE = re.compile(r"(?<![\d.\-])(\d{1,2}-\d{1,2})(?![\d\-])")


def rule_line(text: str, rule: str) -> str:
    """요약에서 규칙 번호가 붙은 줄(목록 항목이나 표 행) 하나를 돌려준다."""
    lines = [line for line in text.splitlines() if f"**{rule}**" in line]
    if len(lines) != 1:
        raise AssertionError(f"규칙 {rule}의 줄이 {len(lines)}개다")
    return lines[0]


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

    def test_conditions_that_decide_the_record_are_in_their_rules(self) -> None:
        for level, anchors in CONDITION_ANCHORS.items():
            text = summary_text(level)
            for rule, phrase, _ in anchors:
                with self.subTest(level=level, rule=rule, phrase=phrase):
                    self.assertIn(squash(phrase), squash(rule_line(text, rule)))

    def test_guide_documents_point_to_rules_that_exist(self) -> None:
        # 영역 문서의 게이트는 요약 규칙 번호를 가리킨다. 요약 번호가 바뀌면 여기서 드러난다.
        rules = {level: set(re.findall(r"\*\*(\d+-\d+)\*\*", summary_text(level))) for level in LEVELS}
        for name, start, end, level in RULE_POINTER_SECTIONS:
            text = (SKILL_ROOT / "references" / name).read_text(encoding="utf-8")
            body = text.split(start, 1)[1].split(end, 1)[0]
            numbers = RULE_NUMBER_RE.findall(body)
            with self.subTest(name=name, section=start):
                self.assertTrue(numbers, "게이트가 요약 규칙 번호를 가리키지 않는다")
                for number in numbers:
                    self.assertIn(number, rules[level], f"{name}의 {number}가 {level} 요약에 없다")

    def test_skill_principles_are_kept_apart_from_guideline_rules(self) -> None:
        # 검증 보고서 B2·B3: 기재요령의 권장·유의 조항과 스킬이 더 보수적으로 정한 원칙을 섞지 않는다.
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        gate = skill.split("## 현행 공통 준수 게이트", 1)[1].split("\n## ", 1)[0]
        self.assertIn("`스킬 원칙`은 이 스킬이 기재요령보다 보수적으로 정한 작업 원칙이다", gate)
        self.assertIn("(기재요령 1-9, 1-10)", gate)
        self.assertIn("AI 생성문은 윤문 보조안일 뿐이며, 교사가 사실·과장·금지사항을 최종 대조하기 전에는 입력용 확정문으로 제시하지 않는다(스킬 원칙)", gate)
        behavior = (SKILL_ROOT / "references" / "field-behavior.md").read_text(encoding="utf-8")
        self.assertIn("누가기록은 권장 사항이며 전국 공통의 필수 절차가 아니다. (고 6-3, 중 7-3)", behavior)
        self.assertIn("기재요령 위반이라고 안내하지 않는다", behavior)
        for level, rule in (("high", "6-3"), ("middle", "7-3")):
            with self.subTest(level=level):
                self.assertIn("권한다", rule_line(summary_text(level), rule))
        differences = (SKILL_ROOT / "references" / "guidelines-middle" / "differences.md").read_text(encoding="utf-8")
        banned = differences.split("같은 기재 금지 사항", 1)[1].split("\n\n", 1)[0]
        self.assertNotIn("AI", banned)
        self.assertIn("보조 수단으로 쓰는 것 자체를 금지하지는 않는다", differences)


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

    def test_conditions_that_decide_the_record_appear_in_the_original(self) -> None:
        # 요약에 넣은 조건이 등록된 원문에도 있는지 본다. 새 학년도 원문을 등록했을 때 빠지거나 바뀐 조건이 여기서 드러난다.
        original = squash(self.normalized)
        for rule, _, phrase in CONDITION_ANCHORS[self.level]:
            with self.subTest(rule=rule, phrase=phrase):
                self.assertIn(squash(phrase), original)


@unittest.skipUnless(original_registered("high"), "고등학교 기재요령 원문이 등록되지 않은 환경(배포본)")
class HighSummaryOriginalTests(SummaryOriginalMixin, unittest.TestCase):
    level = "high"


@unittest.skipUnless(original_registered("middle"), "중학교 기재요령 원문이 등록되지 않은 환경(배포본)")
class MiddleSummaryOriginalTests(SummaryOriginalMixin, unittest.TestCase):
    level = "middle"


if __name__ == "__main__":
    unittest.main()
