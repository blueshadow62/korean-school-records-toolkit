#!/usr/bin/env python3
"""korean-character-count(neis)와 analyze_record.py의 바이트 계산이 같은 계약을 따르는지 대조한다."""

import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

from analyze_record import analyze, load_year_rules

SKILL_ROOT = Path(__file__).resolve().parents[1]
JS = SKILL_ROOT.parent / "korean-character-count" / "scripts" / "korean_character_count.js"
CASES = SKILL_ROOT / "tests" / "neis-validation" / "cases.json"
def find_node():
    """PATH에 없더라도 nvm-windows·기본 설치 경로에서 node를 찾는다."""
    found = shutil.which("node")
    if found:
        return found
    candidates = [
        os.environ.get("NVM_SYMLINK"),
        os.environ.get("NVM_HOME"),
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "nodejs",
        Path(r"C:\nvm4w\nodejs"),
    ]
    for directory in candidates:
        if not directory:
            continue
        for name in ("node.exe", "node"):
            exe = Path(directory) / name
            if exe.exists():
                return str(exe)
    return None


NODE = find_node()


@unittest.skipUnless(NODE and JS.exists() and CASES.exists(), "node 또는 korean-character-count 스크립트가 없음")
class NeisByteConsistencyTests(unittest.TestCase):
    def js_neis_bytes(self, text: str) -> int:
        out = subprocess.run(
            [NODE, str(JS), "--stdin", "--profile", "neis"],
            input=text.encode("utf-8"), capture_output=True, check=True,
        ).stdout.decode("utf-8")
        return json.loads(out)["counts"]["bytes_neis"]

    def test_synthetic_cases_agree_between_both_skills(self) -> None:
        rules = load_year_rules("2026")
        for case in json.loads(CASES.read_text(encoding="utf-8")):
            # analyze_record는 앞뒤 공백을 제거하고 CRLF를 LF로 정규화한 뒤 계산한다.
            text = case["text"].replace("\r\n", "\n").strip()
            with self.subTest(case=case["id"]):
                py = analyze(text, field="subject", rules=rules)["metrics"]["neis_bytes"]
                self.assertEqual(py, self.js_neis_bytes(text))

    def test_line_break_counts_one_byte_like_the_guideline(self) -> None:
        self.assertEqual(self.js_neis_bytes("가\n나"), 7)
        self.assertEqual(self.js_neis_bytes("가\r\n나"), 7)


if __name__ == "__main__":
    unittest.main()
