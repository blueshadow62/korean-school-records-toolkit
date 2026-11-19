#!/usr/bin/env python3
"""중학교 기재요령 요약, 한도 규칙, 고·중 차이 정리가 서로 맞는지 확인한다.

원문 변환본이 등록된 환경(개발본·사용자 등록)에서는 차이 문서가 가리키는 장 제목과 한도 표를
원문과도 대조한다. 원문이 없는 배포본에서는 그 대조만 건너뛰고 나머지는 모두 실행한다.
"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from update_guidelines import load_manifest, root_paths, verify_manifest


SKILL_ROOT = Path(__file__).resolve().parents[1]
MIDDLE = SKILL_ROOT / "references" / "guidelines-middle"
HIGH_RULES = SKILL_ROOT / "references" / "guidelines" / "analyzer-rules" / "2026.json"
ANALYZE = Path(__file__).with_name("analyze_record.py")
ORIGINAL_REGISTERED = (MIDDLE / "manifest.json").is_file() and (MIDDLE / "current.md").is_file()
LIMIT_TITLE = "07 학교생활기록부 영역별 입력 가능 최대 글자수"


def normalize_title(value: str) -> str:
    value = value.replace("ㆍ", "·").replace("･", "·")
    value = re.sub(r"^\d+(?:-\d+)?\s*", "", value.strip())
    return re.sub(r"\s+", "", value)


def original_headings(lines: list[str]) -> set[str]:
    return {normalize_title(match.group(1)) for line in lines for match in [re.match(r"^#{1,6}\s+(.+?)\s*$", line)] if match}


@unittest.skipUnless(ORIGINAL_REGISTERED, "중학교 기재요령 원문이 등록되지 않은 환경(배포본)")
class MiddleOriginalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = (MIDDLE / "current.md").read_text(encoding="utf-8").splitlines()
        self.rules = json.loads((MIDDLE / "analyzer-rules" / "2026.json").read_text(encoding="utf-8"))

    def test_active_middle_reference_verifies_on_its_own(self) -> None:
        paths = root_paths(SKILL_ROOT, "middle")
        manifest = load_manifest(paths)
        verify_manifest(paths, manifest)
        entry = manifest["versions"][manifest["active_version"]]
        self.assertIn("(중학교)", entry["source_title"])
        self.assertTrue(entry["confirmed_official"])
        self.assertEqual(entry["school_year"], "2026")

    def test_difference_chapter_titles_exist_in_the_original(self) -> None:
        differences = (MIDDLE / "differences.md").read_text(encoding="utf-8")
        cited = re.findall(r"「(\d+ [^「」]+)」", differences)
        self.assertGreaterEqual(len(cited), 7)
        headings = original_headings(self.lines)
        for title in cited:
            with self.subTest(title=title):
                self.assertIn(normalize_title(title), headings)

    def test_limits_match_the_middle_table(self) -> None:
        start = next(index for index, line in enumerate(self.lines) if line.strip() == f"# {LIMIT_TITLE}")
        table = "\n".join(self.lines[start:start + 35])
        self.assertIn("<td>과목별 세부능력 및 특기사항</td><td>과목별 500자</td><td></td>", table)
        self.assertIn("<td>진로탐색활동 특기사항</td><td>1,000자</td>", table)
        self.assertIn("<td>행동특성 및 종합의견</td><td>300자</td>", table)
        self.assertNotIn("공통과목", table)
        self.assertNotIn("봉사활동 특기사항", table)


class MiddleRulesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = json.loads((MIDDLE / "analyzer-rules" / "2026.json").read_text(encoding="utf-8"))

    def test_middle_rule_limits(self) -> None:
        limits = self.rules["field_limits_v2"]
        self.assertEqual(limits["subject"], {"default": {"korean_characters": 500, "bytes": 1500}})
        self.assertEqual((limits["free_semester"]["korean_characters"], limits["free_semester"]["bytes"]), (1000, 3000))
        self.assertEqual(limits["behavior"], {"korean_characters": 300, "bytes": 900})
        for area in ("autonomy", "club", "career"):
            self.assertEqual(limits["creative"][area]["korean_characters"], 500)

    def test_differences_cite_chapters_not_line_numbers(self) -> None:
        differences = (MIDDLE / "differences.md").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"\d{3,4}(?:~\d{3,4})?행", differences), [], "행 번호 인용")
        self.assertNotIn("current.md", differences)
        self.assertIn("[summary.md](summary.md)", differences)

    def test_high_only_prohibitions_are_not_applied_to_middle(self) -> None:
        high = json.loads(HIGH_RULES.read_text(encoding="utf-8"))["prohibited_patterns"]
        middle = self.rules["prohibited_patterns"]
        for label in ("모의고사·전국연합학력평가", "재학 학교 식별 후보"):
            with self.subTest(label=label):
                self.assertIn(label, high)
                self.assertNotIn(label, middle)
        self.assertEqual(set(high) - set(middle), {"모의고사·전국연합학력평가", "재학 학교 식별 후보"})

    def run_analyzer(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ANALYZE), *args],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )

    def test_analyzer_uses_middle_limits_and_rejects_high_only_options(self) -> None:
        result = self.run_analyzer("--school-level", "middle", "--field", "free_semester", "--text", "프로그램에서 순서를 고쳐 다시 시연함.", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["metrics"]["default_neis_byte_limit"], 3000)
        self.assertEqual(data["guideline"]["school_level"], "middle")
        self.assertEqual(data["guideline"]["basis"], "original" if ORIGINAL_REGISTERED else "summary")
        rejected = self.run_analyzer("--school-level", "middle", "--field", "subject", "--subject-type", "common", "--text", "가")
        self.assertEqual(rejected.returncode, 2)
        high_only = self.run_analyzer("--field", "free_semester", "--text", "가")
        self.assertEqual(high_only.returncode, 2)

    def test_subject_guides_state_middle_differences_from_section_2(self) -> None:
        # 교과 안내의 규정 게이트는 고등학교 기준이므로, 중학교에서 뒤집히는 항목을 differences.md 2절에 근거해 적는다.
        differences = (MIDDLE / "differences.md").read_text(encoding="utf-8")
        section_2 = differences.split("## 2.", 1)[1].split("## 3.", 1)[0]
        for fact in ("특기할 만한 사항이 있는 과목·학생에 입력", "모든 과목·모든 학생에 입력", "합산·학기별 규정 없음", "예외 없이 금지"):
            self.assertIn(fact, section_2)
        for name in ("subject-humanities.md", "subject-stem.md", "subject-practical-arts.md"):
            with self.subTest(name=name):
                text = (SKILL_ROOT / "references" / name).read_text(encoding="utf-8")
                gate, rest = text.split("## 2026 세특 규정 게이트", 1)[1].split("## 중학교 차이", 1)
                self.assertIn("공통과목 1·2는 합산 500자", gate)
                middle = rest.split("\n## ", 1)[0]
                self.assertIn("[guidelines-middle/differences.md](guidelines-middle/differences.md) 2절", middle)
                self.assertIn("[guidelines-middle/summary.md](guidelines-middle/summary.md) 4절", middle)
                self.assertIn("특기할 만한 사항이 있는 과목·학생에 입력", middle)
                self.assertIn("자유학기 과목은 모든 과목·모든 학생에 입력", middle)
                self.assertIn("공통과목 1·2 합산과 전공실무과목 학기별 규정은 없다", middle)
                self.assertIn("연구보고서(소논문)는 예외 없이 금지", middle)

    def test_skill_sends_middle_drafts_here(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("[guidelines-middle/summary.md](references/guidelines-middle/summary.md)", skill)
        self.assertIn("[guidelines-middle/differences.md](references/guidelines-middle/differences.md)", skill)
        self.assertIn("[field-free-semester.md](references/field-free-semester.md)", skill)
        free_semester = (SKILL_ROOT / "references" / "field-free-semester.md").read_text(encoding="utf-8")
        self.assertNotIn("current.md", free_semester)
        self.assertIn("[guidelines-middle/summary.md](guidelines-middle/summary.md) 6절", free_semester)


if __name__ == "__main__":
    unittest.main()
