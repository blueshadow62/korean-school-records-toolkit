#!/usr/bin/env python3

import json
import unittest
from pathlib import Path


CASES_PATH = Path(__file__).parents[1] / "tests" / "eval-cases" / "cases.json"
VALID_AREAS = {"subject", "creative", "behavior"}
VALID_GRADES = {"A", "B", "C", "D", "mixed"}
CODE_MARKERS = {"A 판정", "B 판정", "C 판정", "D 판정", "A 모드", "B 모드", "C 모드", "D 모드"}
D_REQUIRED_HEADER = "[학생별 사실 미확인 — 그대로 입력하지 않는 작성 후보]"
D_WARNING = "학생별 관찰·결과가 확인되지 않았으므로 완성형 {}을 생성하지 않습니다."
# 영역이 드러나지 않는 요청은 세특 문구를 쓰므로, 행특을 명시한 사례만 영역별 문구를 요구한다.
D_WARNINGS = tuple(D_WARNING.format(word) for word in ("세특", "창체 특기사항", "행동특성 및 종합의견"))
REQUIRED_FIELDS = (
    "id",
    "title",
    "area",
    "expected_internal_grade",
    "prompt",
    "must_include",
    "must_not_include",
    "checks",
    "rationale",
)


def load_cases() -> list:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return data["cases"]


class EvalCasesSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = load_cases()

    def test_file_is_valid_json_with_cases_list(self) -> None:
        self.assertIsInstance(self.cases, list)

    def test_at_least_twelve_cases(self) -> None:
        self.assertGreaterEqual(len(self.cases), 12)

    def test_ids_are_unique(self) -> None:
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)), "케이스 id가 중복되었다")

    def test_required_fields_present_on_every_case(self) -> None:
        for case in self.cases:
            for field in REQUIRED_FIELDS:
                self.assertIn(field, case, f"{case.get('id', '?')}에 '{field}' 필드가 없다")

    def test_area_values_are_valid(self) -> None:
        for case in self.cases:
            self.assertIn(case["area"], VALID_AREAS, f"{case['id']}의 area 값이 잘못됨")

    def test_expected_internal_grade_values_are_valid(self) -> None:
        for case in self.cases:
            self.assertIn(
                case["expected_internal_grade"],
                VALID_GRADES,
                f"{case['id']}의 expected_internal_grade 값이 잘못됨",
            )

    def test_prompt_and_lists_are_non_empty(self) -> None:
        for case in self.cases:
            self.assertTrue(case["prompt"].strip(), f"{case['id']}의 prompt가 비어 있음")
            self.assertIsInstance(case["must_include"], list)
            self.assertIsInstance(case["must_not_include"], list)
            self.assertIsInstance(case["checks"], list)
            self.assertGreater(len(case["checks"]), 0, f"{case['id']}의 checks가 비어 있음")
            self.assertTrue(case["rationale"].strip(), f"{case['id']}의 rationale이 비어 있음")

    def test_prompts_do_not_contain_placeholder_or_identifying_tokens(self) -> None:
        forbidden_tokens = ("OO", "학생1", "학생2", "{{", "}}", "학교명")
        for case in self.cases:
            for token in forbidden_tokens:
                self.assertNotIn(
                    token, case["prompt"], f"{case['id']}의 prompt에 자리표시자/식별 토큰이 있음"
                )

    def test_every_case_must_not_include_covers_internal_grade_codes(self) -> None:
        for case in self.cases:
            overlap = CODE_MARKERS.intersection(case["must_not_include"])
            self.assertTrue(
                overlap,
                f"{case['id']}의 must_not_include에 A–D 코드 표기 검사가 없음",
            )

    def test_d_cases_require_both_mandatory_warnings_in_must_include(self) -> None:
        # ANALYZE-* 케이스는 분석만 요청하는 시나리오라 초안 자체를 생성하지 않으므로
        # D 경고문 대상에서 제외한다(대신 새 초안 마커 금지를 별도로 검증한다).
        d_cases = [
            case
            for case in self.cases
            if case["expected_internal_grade"] == "D" and not case["id"].startswith("ANALYZE-")
        ]
        self.assertGreaterEqual(len(d_cases), 3, "D 케이스가 3건 미만임")
        for case in d_cases:
            self.assertIn(D_REQUIRED_HEADER, case["must_include"], f"{case['id']}(D)에 필수 머리 문구가 없음")
            self.assertTrue(
                set(D_WARNINGS) & set(case["must_include"]),
                f"{case['id']}(D)의 must_include에 필수 경고문이 없음",
            )

    def test_explicit_behavior_request_uses_the_behavior_warning(self) -> None:
        case = next(case for case in self.cases if case["id"].startswith("D-03"))
        self.assertIn(D_WARNING.format("행동특성 및 종합의견"), case["must_include"])
        self.assertNotIn(D_WARNING.format("세특"), case["must_include"])

    def test_grade_distribution_covers_all_required_situations(self) -> None:
        grades = [case["expected_internal_grade"] for case in self.cases]
        self.assertGreaterEqual(grades.count("A"), 2)
        self.assertGreaterEqual(grades.count("B"), 3)
        self.assertGreaterEqual(grades.count("C"), 2)
        self.assertGreaterEqual(grades.count("D"), 3)

    def test_batch_case_present_with_row_level_marker(self) -> None:
        mixed_cases = [case for case in self.cases if case["expected_internal_grade"] == "mixed"]
        self.assertEqual(len(mixed_cases), 1, "엑셀 일괄(mixed) 케이스는 정확히 1건이어야 함")
        batch = mixed_cases[0]
        self.assertIn("[학생별 근거 확인 필요]", batch["must_include"])

    def test_example_copy_case_bans_the_example_wording(self) -> None:
        copy_cases = [case for case in self.cases if case["id"].startswith("COPY-")]
        self.assertGreaterEqual(len(copy_cases), 1, "예시 복사 유도 케이스가 없음")
        for case in copy_cases:
            self.assertGreaterEqual(
                len(case["must_not_include"]) - len(CODE_MARKERS.intersection(case["must_not_include"])),
                2,
                f"{case['id']}가 예시 원문 표현을 충분히 금지하지 않음",
            )

    def test_forbidden_content_cases_present(self) -> None:
        forbid_cases = [case for case in self.cases if case["id"].startswith("FORBID-")]
        self.assertGreaterEqual(len(forbid_cases), 2, "금지사항 유도 케이스가 2건 미만임")

    def test_analysis_only_case_forbids_new_draft_marker(self) -> None:
        analysis_cases = [case for case in self.cases if case["id"].startswith("ANALYZE-")]
        self.assertGreaterEqual(len(analysis_cases), 1, "분석만 요청 케이스가 없음")
        for case in analysis_cases:
            self.assertIn("[세특 초안]", case["must_not_include"])


if __name__ == "__main__":
    unittest.main()
