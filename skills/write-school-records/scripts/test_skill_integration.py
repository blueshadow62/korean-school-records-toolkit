#!/usr/bin/env python3

import json
import unittest
from pathlib import Path


SKILL_TEXT = (Path(__file__).parents[1] / "SKILL.md").read_text(encoding="utf-8")
WRITING_QUALITY = json.loads(
    (Path(__file__).parents[1] / "references" / "writing-quality.json").read_text(encoding="utf-8")
)


class SkillIntegrationContractTests(unittest.TestCase):
    def test_general_count_requests_are_routed_to_the_bundled_count_skill(self) -> None:
        self.assertIn("일반 글자 수 요청에는 `korean-character-count`", SKILL_TEXT)

    def test_final_record_review_names_the_counting_skill(self) -> None:
        self.assertIn("korean-character-count", SKILL_TEXT)
        self.assertIn("analyze_record.py", SKILL_TEXT)

    def test_final_review_recounts_without_spell_dependency(self) -> None:
        self.assertIn("최종본을 `analyze_record.py`로 검사", SKILL_TEXT)

    def test_achievement_standards_reference_is_curriculum_basis_only(self) -> None:
        self.assertIn("achievement-standards/index.md", SKILL_TEXT)
        self.assertIn("교과별 성취수준 자료는 `curriculum_basis` 등급으로만 사용한다", SKILL_TEXT)
        self.assertIn("학생의 실제 성취를 이 자료로 새로 만들거나 단정하지 않으며", SKILL_TEXT)

    def test_generation_is_default_and_precedes_mechanical_checks(self) -> None:
        self.assertIn("생성 요청은 학생 자료 기반 초안 생성을 기본", SKILL_TEXT)
        self.assertLess(SKILL_TEXT.index("초안을 먼저 만들고"), SKILL_TEXT.index("`scripts/analyze_record.py`"))

    def test_four_internal_evidence_modes_preserve_generation_without_fact_invention(self) -> None:
        for mode in ("2. A:", "3. B:", "4. C:", "5. D:"):
            self.assertIn(mode, SKILL_TEXT)
        self.assertIn("A–D는 사용자 선택지가 아니라 학생별 생성 범위를 정하는 내부 분류", SKILL_TEXT)
        self.assertIn("`생성 불가`만으로 끝내지 않는다", SKILL_TEXT)
        self.assertIn("확인되지 않은 발표·보고서·리더십·수상·성과는 추가하지 않는다", SKILL_TEXT)

    def test_evidence_priority_and_lens_limits_are_explicit(self) -> None:
        self.assertIn("teacher_observation`, 검토된 `student_product`, 확인된 `assessment_result`", SKILL_TEXT)
        self.assertIn("학생의 실제 활동·역량보다 우선하지 않으며", SKILL_TEXT)

    def test_sentence_level_source_types_limit_claims(self) -> None:
        for source in ("teacher_observation", "student_product", "student_self_report", "assessment_result", "shared_class_context", "curriculum_basis", "supporting_lens"):
            self.assertIn(source, SKILL_TEXT)
        self.assertIn("결과물을 교사 관찰로, 자기보고를 지속 행동·태도로 확대하지 않는다", SKILL_TEXT)
        self.assertIn("참여 사실이 확인된 경우에만 개인 문장", SKILL_TEXT)

    def test_internal_modes_are_automatic_and_user_labels_are_safe(self) -> None:
        self.assertIn("사용자가 모드를 지정하지 않아도 자동 판정", SKILL_TEXT)
        self.assertIn("사용자에게 모드 선택을 묻지 않는다", SKILL_TEXT)
        self.assertIn("일반 생성·첨삭·엑셀 응답에는 A–D 코드나 내부 분류명을 표시하지 않는다", SKILL_TEXT)
        self.assertIn("A는 `[세특 초안]`, B는 `[세특 초안]`", SKILL_TEXT)
        self.assertIn("C는 `[세특 초안]`과 `교사 확인 사항`", SKILL_TEXT)
        self.assertIn("학생별 최소 정보가 없으면 C가 아니라 D", SKILL_TEXT)
        self.assertIn("[학생별 사실 미확인 — 그대로 입력하지 않는 작성 후보]", SKILL_TEXT)
        self.assertIn("D는 반드시", SKILL_TEXT)

    def test_generation_instruction_does_not_repeat_internal_codes(self) -> None:
        self.assertIn("생성 지시에서 사용자가 A–D 코드나 하향을 언급해도", SKILL_TEXT)
        self.assertIn("그 코드를 인용·반복하거나 판정 결과로 공개하지 않는다", SKILL_TEXT)
        self.assertIn("사용자가 생성 지시에서 코드를 언급한 것은 내부 판정 공개 요청이 아니므로", SKILL_TEXT)

    def test_general_language_replaces_internal_codes(self) -> None:
        for phrase in (
            "현재 자료만으로는 요청한 수준의 완성형 세특을 작성하기 어렵습니다.",
            "학생별 근거가 확인되지 않아 완성형 기록은 작성하지 않았습니다.",
            "현재 확인된 자료 범위에서 보수적으로 작성했습니다.",
            "추가 관찰 자료가 확인되면 내용을 보강할 수 있습니다.",
        ):
            self.assertIn(phrase, SKILL_TEXT)

    def test_explicit_diagnostic_request_is_the_only_code_disclosure_exception(self) -> None:
        self.assertIn("자동 판정 결과·근거 또는 스킬 검증을 명시적으로 요청한 경우에만", SKILL_TEXT)
        self.assertIn("내부 A–D를 별도로 보고할 수 있다", SKILL_TEXT)

    def test_generation_instruction_and_diagnostic_request_are_distinguished(self) -> None:
        self.assertIn("사용자가 생성 지시에서 코드를 언급한 것은 내부 판정 공개 요청이 아니므로", SKILL_TEXT)
        self.assertIn("자동 판정 결과·근거 또는 스킬 검증", SKILL_TEXT)

    def test_excel_hides_codes_except_in_explicit_diagnostic_sheet(self) -> None:
        self.assertIn("세특 초안·일반 검토 열, 사용자 요약·경고 문구, 파일명·시트명", SKILL_TEXT)
        self.assertIn("별도 진단 시트에 코드를 기록할 수 있다", SKILL_TEXT)

    def test_requested_mode_cannot_override_evidence_strength(self) -> None:
        self.assertIn("지정하더라도 근거 수준보다 높게 적용하지 않는다", SKILL_TEXT)
        self.assertIn("근거 없이 완성본·A·발표 수행·다른 학생과 같은 활동을 요청해도", SKILL_TEXT)
        self.assertIn("확인된 자료 범위로 자동 조정", SKILL_TEXT)

    def test_questions_seek_facts_without_blocking_generation(self) -> None:
        self.assertIn("완성형 사실의 내용이 크게 달라지고 입력만으로 판단할 수 없으며", SKILL_TEXT)
        self.assertIn("실제 발표 수행 여부, 결과물의 개인 귀속", SKILL_TEXT)
        self.assertIn("더 풍부한 문장을 만들기 위한 질문은 하지 않으며", SKILL_TEXT)
        self.assertIn("현재 근거로 가능한 보수적 초안", SKILL_TEXT)

    def test_batch_rows_are_classified_independently_without_mode_codes(self) -> None:
        self.assertIn("엑셀·표 일괄 작업에서는 각 행을 독립 판정", SKILL_TEXT)
        self.assertIn("학생별 질문으로 중단하지 않는다", SKILL_TEXT)
        self.assertIn("세특 초안·일반 검토 열, 사용자 요약·경고 문구, 파일명·시트명", SKILL_TEXT)
        self.assertIn("별도 검토 열·검토 시트", SKILL_TEXT)

    def test_ambiguous_presentation_material_stays_within_material_evidence(self) -> None:
        self.assertIn("결과물을 교사 관찰로, 자기보고를 지속 행동·태도로 확대하지 않는다", SKILL_TEXT)
        self.assertIn("발표 원고·자료의 구성은 사용할 수 있지만 실제 발표 수행은 교사 확인 전까지 제외한다", SKILL_TEXT)
        self.assertIn("실제 발표 수행 여부", SKILL_TEXT)

    def test_d_mode_blocks_finished_student_claims(self) -> None:
        self.assertIn("`D`에서는 학생을 주어로 하는 완성형 사실 서술을 출력하지 않는다", SKILL_TEXT)
        self.assertIn("대괄호 기반 작성 틀·표현 조각·관찰 포인트·교사 확인 질문만 제공", SKILL_TEXT)
        self.assertIn("경고를 붙여도 예시나 가정의 활동·성과·역량 문장을 재출력하지 않는다", SKILL_TEXT)

    def test_example_only_input_is_not_student_evidence(self) -> None:
        self.assertIn("학생별 사실 확인 전의 완성 예시는 문체 참고일 뿐 근거가 아니다", SKILL_TEXT)
        self.assertIn("이름·성별·과목·주제·일부 명사만 바꾸어 재출력하지 않고", SKILL_TEXT)
        self.assertIn("예시에서는 관찰 항목과 확인 질문만 추출한다", SKILL_TEXT)

    def test_real_student_evidence_replaces_example_text(self) -> None:
        self.assertIn("실제 `teacher_observation`, `student_product`, `assessment_result`가 제공되면", SKILL_TEXT)
        self.assertIn("예시가 아닌 그 근거만으로 새 문장을 구성한다", SKILL_TEXT)

    def test_d_mode_uses_the_required_nonfinal_warning(self) -> None:
        self.assertIn("학생별 관찰·결과가 확인되지 않았으므로 완성형 세특을 생성하지 않습니다.", SKILL_TEXT)

    def test_safety_critical_failures_override_the_repeat_threshold(self) -> None:
        self.assertIn("한 번만 확인되어도 즉시 수정하는 안전 오류", SKILL_TEXT)
        self.assertIn("문체·어미·표현 다양성 문제는 독립 사례 2회 이상 재현될 때 수정", SKILL_TEXT)

    def test_evidence_driven_sentence_structures_cover_ten_types(self) -> None:
        for structure_id in range(1, 11):
            self.assertIn(f"S{structure_id}.", SKILL_TEXT)
        self.assertIn("가장 구체적이고 확인 수준이 높은 핵심 근거", SKILL_TEXT)
        self.assertIn("구조 코드는 내부 계획에만 사용하고 결과에 노출하지 않는다", SKILL_TEXT)

    def test_structure_selection_rejects_random_rotation_and_synonym_swaps(self) -> None:
        self.assertIn("무작위 순환 배정이나 동의어 교체만으로 다양화하지 않는다", SKILL_TEXT)
        self.assertIn("근거가 하나뿐이면 복잡한 성장 서사를 만들지 않는다", SKILL_TEXT)
        self.assertIn("결과물만 있는 B 모드는 S4를 사용해도 교사 관찰로 확대하지 않으며", SKILL_TEXT)

    def test_abstract_competency_endings_require_observable_behavior(self) -> None:
        self.assertIn("추상 명사는 대응하는 행동이 먼저 드러나고", SKILL_TEXT)
        self.assertIn("행동만으로 충분하면 `역량을 보임`, `능력을 보임`, `과정을 드러냄`을 덧붙이지 않는다", SKILL_TEXT)

    def test_large_batches_have_review_warnings_not_forced_rewrites(self) -> None:
        self.assertIn("학생이 10명 이상이면", SKILL_TEXT)
        self.assertIn("첫 3어절 또는 마지막 서술어가 25%를 넘거나", SKILL_TEXT)
        self.assertIn("한 구조 유형이 40%를 넘거나", SKILL_TEXT)
        self.assertIn("중 하나가 20%를 넘으면 검토 경고", SKILL_TEXT)
        self.assertIn("이 기준은 재작성 명령이 아니며", SKILL_TEXT)

    def test_factuality_and_source_strength_precede_variety(self) -> None:
        self.assertIn(
            "학생별 사실 → 출처의 표현 강도 → 실제 수업 맥락 → 성취기준 연결 → 기재요령 → 문장 다양성",
            SKILL_TEXT,
        )
        self.assertIn("다양성을 위해 입력에 없는 질문·발표·피드백·협업·추가 탐구·진로 연계·성장·높은 성취·지속적 태도를 만들지 않는다", SKILL_TEXT)
        self.assertIn("예시 자료에서는 전개 순서와 사실·해석의 연결 방식만 참고하고", SKILL_TEXT)

    def test_sentence_quality_gate_requires_precision_cohesion_and_compression(self) -> None:
        self.assertIn("## 문장 품질 게이트", SKILL_TEXT)
        self.assertIn("writing-quality.json", SKILL_TEXT)
        self.assertEqual(1, WRITING_QUALITY["schema_version"])
        self.assertEqual(
            {"구체성", "응집성", "압축성"},
            set(WRITING_QUALITY["quality_dimensions"]),
        )
        self.assertEqual(
            ["대상", "방법", "판단 기준", "결과"],
            WRITING_QUALITY["required_evidence_fields"],
        )
        self.assertGreaterEqual(len(WRITING_QUALITY["rules"]), 6)


if __name__ == "__main__":
    unittest.main()
