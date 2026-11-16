#!/usr/bin/env python3
"""중학교 기재요령 참조본, 한도 규칙, 고·중 차이 정리가 서로 맞는지 확인한다."""

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
# differences.md가 가리키는 행과 그 행에 있어야 할 문구. 참조본을 다시 만들어 행이 밀리면 여기서 잡는다.
LINE_ANCHORS = {
    495: "01 학교생활기록부 작성 시 유의사항",
    513: "고등학교 관련 내용으로 생략",
    2079: "10 창의적 체험활동상황",
    2093: "중학교의 ‘창의적 체험활동상황’에는",
    2099: "특기사항은 모든 학생에 대해 입력하되",
    2212: "중학교 학생이 고등학교에서 주최하고 주관한 체험활동",
    2238: "해외에서 실시한 창의적 체험활동은 특기사항을 입력하지 않음",
    2295: "5가지 항목",
    2306: "자동으로 표기됨",
    2374: "청소년단체명만 입력할 수 있으며",
    2376: "학교스포츠클럽활동에 참여한 모든 학생",
    2628: "12 교과학습발달상황",
    2652: "특기할 만한 사항이 있는 과목 및 학생",
    2664: "자유학기에 이수한 과목의 ‘성취도’에는 ‘P’",
    3013: "학생참여형 수업",
    3025: "학업성적관리위원회",
    3031: "학생건강체력평가(PAPS) 1등급",
    3053: "다음의 항목은 입력할 수 없다",
    3153: "13 자유학기활동상황",
    3260: "중점 연계형 자유학기활동",
    3285: "14 독서활동상황",
    3331: "15 행동특성 및 종합의견",
    4448: "07 학교생활기록부 영역별 입력 가능 최대 글자수",
}


@unittest.skipUnless((MIDDLE / "manifest.json").is_file(), "중학교 기재요령이 등록되지 않은 환경")
class MiddleGuidelineTests(unittest.TestCase):
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

    def test_difference_line_references_point_to_the_right_text(self) -> None:
        for number, phrase in LINE_ANCHORS.items():
            with self.subTest(line=number):
                self.assertIn(phrase, self.lines[number - 1])
        differences = (MIDDLE / "differences.md").read_text(encoding="utf-8")
        # '495~536행'처럼 범위로 인용하면 시작 행만 확인한다.
        cited = {int(n) for n in re.findall(r"(?<![~\d])(\d{3,4})(?:~\d{3,4})?행", differences)}
        self.assertEqual(cited - set(LINE_ANCHORS), set(), "앵커 없이 인용한 행 번호")

    def test_limits_match_the_middle_table(self) -> None:
        table = "\n".join(self.lines[4448 - 1:4448 + 35])
        self.assertIn("<td>과목별 세부능력 및 특기사항</td><td>과목별 500자</td><td></td>", table)
        self.assertIn("<td>진로탐색활동 특기사항</td><td>1,000자</td>", table)
        self.assertIn("<td>행동특성 및 종합의견</td><td>300자</td>", table)
        self.assertNotIn("공통과목", table)
        limits = self.rules["field_limits_v2"]
        self.assertEqual(limits["subject"], {"default": {"korean_characters": 500, "bytes": 1500}})
        self.assertEqual((limits["free_semester"]["korean_characters"], limits["free_semester"]["bytes"]), (1000, 3000))
        self.assertEqual(limits["behavior"], {"korean_characters": 300, "bytes": 900})
        for area in ("autonomy", "club", "career"):
            self.assertEqual(limits["creative"][area]["korean_characters"], 500)

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
        rejected = self.run_analyzer("--school-level", "middle", "--field", "subject", "--subject-type", "common", "--text", "가")
        self.assertEqual(rejected.returncode, 2)
        high_only = self.run_analyzer("--field", "free_semester", "--text", "가")
        self.assertEqual(high_only.returncode, 2)

    def test_skill_sends_middle_drafts_here(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/guidelines-middle/current.index.md", skill)
        self.assertIn("[guidelines-middle/differences.md](references/guidelines-middle/differences.md)", skill)
        self.assertIn("[field-free-semester.md](references/field-free-semester.md)", skill)


if __name__ == "__main__":
    unittest.main()
