#!/usr/bin/env python3
"""Compare local text-count contracts with manually recorded NEIS values."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "neis-validation" / "cases.json"
HANGUL = re.compile(r"[가-힣]")
ASCII_ALNUM = re.compile(r"[A-Za-z0-9]")
UNIT_ALIASES = {
    "byte": "Byte",
    "bytes": "Byte",
    "글자": "글자",
    "문자": "글자",
    "character": "글자",
    "characters": "글자",
    "code point": "code point",
    "codepoint": "code point",
}


class CasesError(ValueError):
    """An expected, user-correctable cases-file error."""


def load_cases(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CasesError(f"사례 JSON을 읽을 수 없습니다: {path} ({error})") from error
    if not isinstance(payload, list):
        raise CasesError("사례 JSON의 최상위 값은 배열이어야 합니다.")
    required = {"id", "category", "description", "text", "guideline_basis", "actual_neis_value", "actual_neis_unit", "input_area", "measured_at", "notes"}
    ids: set[str] = set()
    for index, case in enumerate(payload, start=1):
        if not isinstance(case, dict) or not required.issubset(case):
            raise CasesError(f"사례 {index}에 필수 필드가 없습니다.")
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id.strip() or case_id in ids:
            raise CasesError(f"사례 {index}의 ID가 비어 있거나 중복됩니다.")
        if not isinstance(case["text"], str):
            raise CasesError(f"사례 {case_id}의 text는 문자열이어야 합니다.")
        value = case["actual_neis_value"]
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            raise CasesError(f"사례 {case_id}의 actual_neis_value는 0 이상 정수 또는 null이어야 합니다.")
        if value is not None and not isinstance(case["actual_neis_unit"], str):
            raise CasesError(f"사례 {case_id}의 actual_neis_unit은 문자열이어야 합니다.")
        if value is not None:
            if any(not isinstance(case.get(field), str) or not case[field].strip() for field in ("input_area", "measured_at")):
                raise CasesError(
                    f"사례 {case_id}의 실제값에는 input_area·measured_at 기록이 필요합니다."
                )
        ids.add(case_id)
    return payload


def guideline_simple_count(text: str) -> tuple[int | None, list[str]]:
    """Apply only the explicit 3/1/1 rule; leave other characters unclassified."""
    total = 0
    unsupported: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\r" and index + 1 < len(text) and text[index + 1] == "\n":
            total += 1
            index += 2
            continue
        if char in "\r\n":
            total += 1
        elif HANGUL.fullmatch(char):
            total += 3
        elif ASCII_ALNUM.fullmatch(char):
            total += 1
        else:
            unsupported.append(char)
        index += 1
    return (total if not unsupported else None), sorted(set(unsupported))


def calculate_case(case: dict[str, Any]) -> dict[str, Any]:
    text = case["text"]
    guideline_value, unsupported = guideline_simple_count(text)
    try:
        from analyze_record import analyze

        analyzed = analyze(text, field="other")
        analyze_codepoints = analyzed["metrics"]["unicode_characters"]
        analyze_bytes = analyzed["metrics"]["utf8_bytes"]
    except (ImportError, KeyError):
        analyze_codepoints = len(text.strip())
        analyze_bytes = len(text.strip().encode("utf-8"))

    return {
        "id": case["id"],
        "category": case["category"],
        "description": case["description"],
        "python_codepoints_including_whitespace": len(text),
        "python_codepoints_trimmed": len(text.strip()),
        "python_codepoints_without_whitespace": len("".join(text.split())),
        "utf8_bytes": len(text.encode("utf-8")),
        "analyze_record_codepoints": analyze_codepoints,
        "analyze_record_utf8_bytes": analyze_bytes,
        "guideline_simple_value": guideline_value,
        "guideline_simple_unsupported": unsupported,
        "actual_neis_value": case["actual_neis_value"],
        "actual_neis_unit": case["actual_neis_unit"],
        "input_area": case.get("input_area"),
        "measured_at": case.get("measured_at"),
    }


def comparable_values(result: dict[str, Any]) -> dict[str, int]:
    return {
        "code point": result["python_codepoints_including_whitespace"],
        "Byte": result["utf8_bytes"],
        "guideline simple": result["guideline_simple_value"],
        "analyze_record code point": result["analyze_record_codepoints"],
        "analyze_record Byte": result["analyze_record_utf8_bytes"],
    }


def compare_result(result: dict[str, Any]) -> dict[str, Any]:
    actual = result["actual_neis_value"]
    if actual is None:
        return {"status": "미측정", "matches": [], "differences": {}}
    unit = UNIT_ALIASES.get(str(result["actual_neis_unit"]).strip().lower())
    if unit == "글자":
        candidates = {
            key: value
            for key, value in comparable_values(result).items()
            if "code point" in key and value is not None
        }
    elif unit == "Byte":
        candidates = {
            key: value
            for key, value in comparable_values(result).items()
            if "Byte" in key and value is not None
        }
    else:
        candidates = {}
    matches = [key for key, value in candidates.items() if value == actual]
    differences = {key: actual - value for key, value in candidates.items() if value != actual}
    status = "규정상 계산 불명확" if result["guideline_simple_value"] is None else (
        "일치" if matches else ("판단 보류" if not candidates else "불일치")
    )
    return {"status": status, "matches": matches, "differences": differences}


def update_actual(path: Path, case_id: str, actual: int, unit: str, input_area: str, measured_at: str) -> str | None:
    if actual < 0:
        raise CasesError("actual 값은 0 이상이어야 합니다.")
    normalized_unit = UNIT_ALIASES.get(unit.strip().lower())
    if normalized_unit is None:
        raise CasesError("unit은 Byte, 글자 또는 code point 중 하나여야 합니다.")
    if not input_area.strip() or not measured_at.strip():
        raise CasesError("실제값 기록에는 input_area·measured_at이 모두 필요합니다.")
    cases = load_cases(path)
    for case in cases:
        if case["id"] == case_id:
            previous = case["actual_neis_value"]
            case["actual_neis_value"] = actual
            case["actual_neis_unit"] = normalized_unit
            case["input_area"] = input_area
            case["measured_at"] = measured_at
            _atomic_json_write(path, cases)
            return f"{case_id}: {previous!r} -> {actual} {normalized_unit}"
    raise CasesError(f"존재하지 않는 사례 ID입니다: {case_id}")


def _atomic_json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def markdown_report(results: list[dict[str, Any]]) -> str:
    lines = [
        "| ID | 분류 | 실제 NEIS | code point | UTF-8 | 기재요령 단순식 | 차이 | 상태 |",
        "| -- | -- | ------: | ---------: | ----: | -------: | -: | -- |",
    ]
    for result in results:
        comparison = compare_result(result)
        actual = result["actual_neis_value"]
        actual_display = "-" if actual is None else f"{actual} {result['actual_neis_unit']}"
        guideline = result["guideline_simple_value"]
        difference = "-" if actual is None else ", ".join(
            f"{key}:{value:+d}" for key, value in comparison["differences"].items()
        ) or "0"
        lines.append(
            f"| {result['id']} | {result['category']} | {actual_display} | "
            f"{result['python_codepoints_including_whitespace']} | {result['utf8_bytes']} | "
            f"{'미분류' if guideline is None else guideline} | {difference} | {comparison['status']} |"
        )
    measured = [result for result in results if result["actual_neis_value"] is not None]
    exact = sum(bool(compare_result(result)["matches"]) for result in measured)
    mismatches = [result["id"] for result in measured if compare_result(result)["status"] == "불일치"]
    newline = [result["id"] for result in results if result["category"] in {"줄바꿈", "행특"}]
    no_match = [result["id"] for result in measured if not compare_result(result)["matches"]]
    lines.extend([
        "",
        f"- 실제값 입력 사례: {len(measured)}건",
        f"- 하나 이상의 로컬 계산과 정확히 일치: {exact}건",
        f"- 불일치 사례: {', '.join(mismatches) or '없음'}",
        f"- 줄바꿈 사례: {', '.join(newline) or '없음'}",
        f"- 어느 계산 방식도 일치하지 않는 사례: {', '.join(no_match) or '없음'}",
        "- 실제값이 충분하지 않으면 최종 계산 계약 확정 불가.",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--record", metavar="ID")
    parser.add_argument("--actual", type=int)
    parser.add_argument("--unit")
    parser.add_argument("--input-area")
    parser.add_argument("--measured-at")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    try:
        if args.record is not None:
            if any(value is None for value in (args.actual, args.unit, args.input_area, args.measured_at)):
                raise CasesError("--record에는 --actual, --unit, --input-area, --measured-at이 함께 필요합니다.")
            print(update_actual(args.cases, args.record, args.actual, args.unit, args.input_area, args.measured_at))
        cases = load_cases(args.cases)
        results = [calculate_case(case) for case in cases]
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(markdown_report(results))
        return 0
    except (CasesError, OSError) as error:
        print(f"오류: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
