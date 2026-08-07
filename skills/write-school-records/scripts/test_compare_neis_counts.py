#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

from compare_neis_counts import (
    CasesError,
    calculate_case,
    compare_result,
    guideline_simple_count,
    load_cases,
    update_actual,
)


INPUT_AREA = "합성 테스트 입력란"
MEASURED_AT = "2026-07-23"


class CompareNeisCountsTests(unittest.TestCase):
    def test_sample_json_has_15_cases(self) -> None:
        path = Path(__file__).parents[1] / "tests" / "neis-validation" / "cases.json"
        cases = load_cases(path)
        self.assertEqual(len(cases), 15)
        self.assertTrue(all(case["actual_neis_value"] is None for case in cases))

    def test_missing_actual_is_not_failure(self) -> None:
        result = calculate_case({"id": "x", "category": "x", "description": "x", "text": "가", "actual_neis_value": None, "actual_neis_unit": None})
        self.assertEqual(compare_result(result)["status"], "미측정")

    def test_hangul_utf8_and_guideline_count(self) -> None:
        value, unsupported = guideline_simple_count("가")
        self.assertEqual((value, unsupported), (3, []))
        self.assertEqual(calculate_case({"id": "x", "category": "x", "description": "x", "text": "가", "actual_neis_value": None, "actual_neis_unit": None})["utf8_bytes"], 3)

    def test_ascii_letters_and_digits_use_one_byte_rule(self) -> None:
        self.assertEqual(guideline_simple_count("A1"), (2, []))

    def test_whitespace_views_are_distinct(self) -> None:
        result = calculate_case({"id": "x", "category": "x", "description": "x", "text": "  가\t나  ", "actual_neis_value": None, "actual_neis_unit": None})
        self.assertEqual(result["python_codepoints_including_whitespace"], 7)
        self.assertEqual(result["python_codepoints_trimmed"], 3)
        self.assertEqual(result["python_codepoints_without_whitespace"], 2)

    def test_crlf_and_lf_are_counted_as_enter_by_simple_rule(self) -> None:
        self.assertEqual(guideline_simple_count("가\r\n나")[0], 7)
        self.assertEqual(guideline_simple_count("가\n나")[0], 7)

    def test_recorded_byte_match(self) -> None:
        result = calculate_case({"id": "x", "category": "x", "description": "x", "text": "가", "actual_neis_value": 3, "actual_neis_unit": "Byte"})
        self.assertEqual(compare_result(result)["status"], "일치")

    def test_recorded_value_mismatch(self) -> None:
        result = calculate_case({"id": "x", "category": "x", "description": "x", "text": "가", "actual_neis_value": 1, "actual_neis_unit": "Byte"})
        self.assertEqual(compare_result(result)["status"], "불일치")

    def test_unknown_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(CasesError, "존재하지 않는"):
                update_actual(path, "missing", 1, "Byte", INPUT_AREA, MEASURED_AT)

    def test_negative_actual_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(CasesError, "0 이상"):
                update_actual(path, "x", -1, "Byte", INPUT_AREA, MEASURED_AT)

    def test_invalid_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(CasesError):
                load_cases(path)

    def test_record_updates_only_requested_case_atomically(self) -> None:
        cases = [
            {"id": "a", "category": "x", "description": "x", "text": "가", "guideline_basis": "x", "actual_neis_value": None, "actual_neis_unit": None, "input_area": None, "measured_at": None, "notes": ""},
            {"id": "b", "category": "x", "description": "x", "text": "나", "guideline_basis": "x", "actual_neis_value": None, "actual_neis_unit": None, "input_area": None, "measured_at": None, "notes": ""},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
            message = update_actual(path, "a", 3, "Byte", INPUT_AREA, MEASURED_AT)
            updated = load_cases(path)
            self.assertIn("None -> 3 Byte", message)
            self.assertEqual(updated[0]["actual_neis_value"], 3)
            self.assertEqual(updated[0]["input_area"], INPUT_AREA)
            self.assertEqual(updated[0]["measured_at"], MEASURED_AT)
            self.assertIsNone(updated[1]["actual_neis_value"])

    def test_existing_actual_change_reports_previous_value(self) -> None:
        case = {"id": "a", "category": "x", "description": "x", "text": "가", "guideline_basis": "x", "actual_neis_value": 2, "actual_neis_unit": "Byte", "input_area": INPUT_AREA, "measured_at": MEASURED_AT, "notes": ""}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps([case], ensure_ascii=False), encoding="utf-8")
            self.assertIn("2 -> 3 Byte", update_actual(path, "a", 3, "Byte", INPUT_AREA, MEASURED_AT))

    def test_actual_value_without_measurement_context_is_rejected(self) -> None:
        case = {"id": "a", "category": "x", "description": "x", "text": "가", "guideline_basis": "x", "actual_neis_value": 3, "actual_neis_unit": "Byte", "input_area": None, "measured_at": None, "notes": ""}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps([case], ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(CasesError, "input_area"):
                load_cases(path)


if __name__ == "__main__":
    unittest.main()
