#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from analyze_record import active_rule_context, analyze, load_year_rules, positive_int, read_utf8_text


class AnalyzeRecordTests(unittest.TestCase):
    def test_evidence_rich_subject_entry(self) -> None:
        result = analyze(
            "통계 자료의 출처를 비교하고 표본의 한계를 분석하여 보고서를 작성함. "
            "피드백을 반영해 그래프의 축을 수정하고 결론을 보완함.",
            field="subject",
        )
        warnings = " ".join(result["warnings"])
        self.assertNotIn("행동을 보여 주는 동사", warnings)
        self.assertNotIn("산출물·자료·과정 근거가 약합니다", warnings)

    def test_information_subject_evidence_is_not_misclassified_as_lacking_subject_context(self) -> None:
        result = analyze(
            "입력 데이터를 정제하고 알고리즘을 구현하여 테스트 결과를 코드로 기록함. "
            "오류를 수정해 처리 절차를 보완함.",
            field="subject",
        )
        self.assertNotIn("교과세특인데 교과 개념·과제·탐구 방법이 충분히 드러나지 않습니다", result["warnings"])

    def test_science_measurement_context_is_not_misclassified(self) -> None:
        result = analyze(
            "잎 면적 측정에서 촬영 거리와 조명 조건을 통제해 재측정하고 오차 원인을 설명함.",
            field="subject",
        )
        self.assertNotIn("교과세특인데 교과 개념·과제·탐구 방법이 충분히 드러나지 않습니다", result["warnings"])

    def test_vague_judgment_is_flagged(self) -> None:
        result = analyze("매우 성실하고 적극적이며 리더십이 뛰어남.", field="behavior")
        warnings = " ".join(result["warnings"])
        self.assertIn("근거가 약합니다", warnings)
        self.assertIn("반복 관찰", warnings)

    def test_admission_language_and_target_length_are_flagged(self) -> None:
        result = analyze(
            "지원 대학 인재상에 부합하여 합격 가능성이 높음.",
            field="other",
            target_chars=10,
        )
        warnings = " ".join(result["warnings"])
        self.assertIn("목표 글자 수", warnings)
        self.assertIn("입시·대학 맞춤 표현", warnings)

    def test_personal_identifiers_are_flagged(self) -> None:
        result = analyze("연락처 010-1234-5678, 이메일 student@example.com", field="other")
        warnings = " ".join(result["warnings"])
        self.assertIn("전화번호", warnings)
        self.assertIn("이메일", warnings)

    def test_2026_prohibited_candidates_are_flagged(self) -> None:
        result = analyze(
            "교내 경진대회에서 수상하고 방과후학교 K-MOOC 강좌를 수강함.",
            field="subject",
        )
        warnings = " ".join(result["warnings"])
        self.assertIn("금지 또는 조건 확인", warnings)
        self.assertIn("대회·수상", warnings)
        self.assertIn("K-MOOC·MOOC·KOCW", warnings)
        self.assertIn("방과후학교", warnings)

    def test_creative_condition_candidates_are_flagged_without_treating_them_as_automatic_bans(self) -> None:
        result = analyze(
            "학교 밖 기관의 자율동아리 활동과 학교스포츠클럽, 청소년단체 활동을 입력함.",
            field="creative",
        )
        warnings = " ".join(result["warnings"])
        self.assertIn("창체의 영역·입력 조건", warnings)
        self.assertEqual(
            result["signals"]["creative_conditions"],
            ["학교 밖 활동", "자율동아리", "학교스포츠클럽", "청소년단체활동"],
        )
        self.assertEqual(result["signals"]["prohibited_2026"], [])

    def test_reference_limit_is_field_specific_without_neis_equivalence_claim(self) -> None:
        result = analyze("가" * 301, field="behavior")
        warnings = " ".join(result["warnings"])
        self.assertIn("참고 바이트 한도", warnings)
        self.assertIn("실제 NEIS 입력값은 별도 확인 필요", warnings)
        self.assertEqual(result["metrics"]["neis_bytes"], 903)
        self.assertEqual(result["metrics"]["default_neis_byte_limit"], 900)
        self.assertIn("actual NEIS entry behavior", result["metrics"]["limit_contract"])

    def test_subject_limit_allows_500_korean_characters(self) -> None:
        result = analyze("가" * 500, field="subject")
        warnings = " ".join(result["warnings"])
        self.assertNotIn("참고 바이트 한도", warnings)

    def test_mixed_unicode_input_uses_documented_codepoint_and_utf8_contract(self) -> None:
        result = analyze("가A1 !\n🙂가", field="other")
        metrics = result["metrics"]
        self.assertEqual(metrics["unicode_characters"], 9)
        self.assertEqual(metrics["characters_without_whitespace"], 7)
        self.assertEqual(metrics["utf8_bytes"], 18)
        self.assertIn("code points", metrics["count_contract"])
        self.assertIn("UTF-8", metrics["byte_contract"])

    def test_target_length_must_be_positive(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("0")
        with self.assertRaises(argparse.ArgumentTypeError):
            positive_int("not-a-number")

    def test_repeated_generic_evaluation_and_connective_chains_are_flagged(self) -> None:
        result = analyze(
            "자료를 조사하며 비교하고 해석하여 표로 정리해서 분석 역량을 보임. "
            "결론을 작성하며 설명하고 수정하여 보완해서 문제 해결 능력을 보임.",
            field="subject",
        )
        warnings = " ".join(result["warnings"])
        self.assertIn("추상 평가를 반복", warnings)
        self.assertIn("연결어가 연속", warnings)

    def test_missing_file_has_actionable_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "UTF-8 텍스트 파일을 읽을 수 없습니다"):
            read_utf8_text(Path("missing-record.txt"))

    def test_active_guideline_requires_a_same_year_rule_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guidelines = root / "references" / "guidelines"
            versions = guidelines / "versions"
            versions.mkdir(parents=True)
            archive = versions / "2027_2027-02-01.md"
            archive.write_text("# 2027 기재요령\n", encoding="utf-8")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            (guidelines / "current.md").write_bytes(archive.read_bytes())
            (guidelines / "current.index.md").write_text(
                f"<!-- active_version=2027_2027-02-01 sha256={digest} -->\n",
                encoding="utf-8",
            )
            (guidelines / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "active_version": "2027_2027-02-01",
                        "versions": {
                            "2027_2027-02-01": {
                                "school_year": "2027",
                                "archive_path": "references/guidelines/versions/2027_2027-02-01.md",
                                "sha256": digest,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "2027.*규칙 파일"):
                active_rule_context(root)

    def test_year_rules_are_loaded_from_structured_json(self) -> None:
        rules = load_year_rules("2026")
        self.assertEqual("2026", rules["school_year"])
        self.assertEqual(1500, rules["field_neis_limits"]["subject"]["bytes"])
        self.assertIn("공인어학시험", rules["prohibited_patterns"])

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rule_dir = root / "references" / "guidelines" / "analyzer-rules"
            rule_dir.mkdir(parents=True)
            (rule_dir / "2027.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "school_year": "2027",
                        "field_neis_limits": {
                            "subject": {"korean_characters": 400, "bytes": 1200}
                        },
                        "prohibited_patterns": {
                            "테스트 후보": {"pattern": "TEST", "ignore_case": True}
                        },
                    }
                ),
                encoding="utf-8",
            )
            future_rules = load_year_rules("2027", root)
            self.assertEqual(1200, future_rules["field_neis_limits"]["subject"]["bytes"])
            self.assertIsNotNone(future_rules["prohibited_patterns"]["테스트 후보"].search("test"))


if __name__ == "__main__":
    unittest.main()
