from __future__ import annotations

import importlib.util
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "korean_spell_check.py"
FIXTURES = Path(__file__).parent / "fixtures"

SPEC = importlib.util.spec_from_file_location("korean_spell_check_under_test", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT}")
spell_check = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = spell_check
SPEC.loader.exec_module(spell_check)


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class KoreanSpellCheckTests(unittest.TestCase):
    def test_p1_success_with_corrections(self) -> None:
        pages = spell_check.extract_result_payload(fixture("success_with_corrections.html"))
        issue = spell_check.build_issue(0, 0, 0, pages[0], pages[0]["errInfo"][0])

        self.assertEqual(issue.original, "할수")
        self.assertEqual(issue.suggestions, ["할 수"])
        self.assertEqual(issue.reason, "띄어쓰기 & 문맥\n확인")
        self.assertEqual((issue.start, issue.end), (0, 1))

    def test_p2_success_without_corrections(self) -> None:
        pages = spell_check.extract_result_payload(fixture("success_without_corrections.html"))
        self.assertEqual(pages, [])

    def test_p3_current_live_response_shape(self) -> None:
        pages = spell_check.extract_result_payload(fixture("current_response.html"))
        self.assertEqual(len(pages), 1)
        self.assertEqual([item["orgStr"] for item in pages[0]["errInfo"]], ["않갔지만", "갈꺼에요"])

    def test_p4_unexpected_html_or_json_is_a_parse_error(self) -> None:
        samples = [
            fixture("unexpected_response.html"),
            fixture("service_error_response.html"),
            "data = {\"unexpected\": true}; pageIdx = 0;",
            "data = [invalid json]; pageIdx = 0;",
        ]

        for sample in samples:
            with self.subTest(sample=sample[:40]):
                with self.assertRaises(spell_check.ResponseParseError):
                    spell_check.extract_result_payload(sample)

    def test_p5_http_and_network_errors_are_distinct(self) -> None:
        http_error = urllib.error.HTTPError(
            spell_check.DEFAULT_RESULTS_URL, 500, "server error", None, None
        )
        with patch.object(spell_check.urllib.request, "urlopen", side_effect=http_error):
            with self.assertRaises(spell_check.ServiceHttpError) as context:
                spell_check.fetch_spell_check_html("테스트")
        self.assertEqual(context.exception.status_code, 500)

        with patch.object(
            spell_check.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            with self.assertRaises(spell_check.ServiceNetworkError):
                spell_check.fetch_spell_check_html("테스트")

    def test_p6_empty_response_is_a_parse_error(self) -> None:
        for sample in ("", " \n\t"):
            with self.subTest(sample=repr(sample)):
                with self.assertRaises(spell_check.ResponseParseError):
                    spell_check.extract_result_payload(sample)

    def test_p7_captcha_or_block_is_not_success(self) -> None:
        with self.assertRaises(spell_check.ServiceBlockedError):
            spell_check.extract_result_payload(fixture("blocked_response.html"))

        forbidden = urllib.error.HTTPError(
            spell_check.DEFAULT_RESULTS_URL, 403, "forbidden", None, None
        )
        with patch.object(spell_check.urllib.request, "urlopen", side_effect=forbidden):
            with self.assertRaises(spell_check.ServiceBlockedError):
                spell_check.fetch_spell_check_html("테스트")

    def test_p8_empty_input_never_calls_the_network(self) -> None:
        def fail_if_called(*args: object, **kwargs: object) -> str:
            raise AssertionError("network requester must not be called")

        for sample in ("", " \n\t"):
            with self.subTest(sample=repr(sample)):
                with self.assertRaises(spell_check.InputTextError):
                    spell_check.check_text(sample, requester=fail_if_called)

    def test_p9_correct_sentence_is_success_with_zero_issues(self) -> None:
        report = spell_check.check_text(
            "오늘은 학교에서 과학 실험을 했습니다.",
            requester=lambda *args, **kwargs: fixture("success_without_corrections.html"),
        )
        self.assertEqual(report["corrected_text"], report["original_text"])
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["chunks"][0]["page_count"], 0)

    def test_p10_multiple_corrections_preserve_order_positions_and_unique_candidates(self) -> None:
        report = spell_check.check_text(
            "않갔고 갈꺼에요.",
            requester=lambda *args, **kwargs: fixture("multiple_corrections.html"),
        )

        self.assertEqual(report["corrected_text"], "안 갔고 갈 거예요.")
        self.assertEqual([issue.original for issue in report["issues"]], ["않갔고", "갈꺼에요"])
        self.assertEqual(report["issues"][0].suggestions, ["안 갔고"])
        self.assertEqual(report["issues"][1].suggestions, ["갈 거예요", "갈까예요"])
        self.assertEqual(
            [(issue.start, issue.end) for issue in report["issues"]],
            [(0, 2), (4, 7)],
        )


if __name__ == "__main__":
    unittest.main()
