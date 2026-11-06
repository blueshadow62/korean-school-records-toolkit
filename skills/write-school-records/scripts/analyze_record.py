#!/usr/bin/env python3
"""Run deterministic, non-regulatory checks on a Korean student-record draft."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

from update_guidelines import GuidelineError, load_manifest, root_paths, verify_manifest


ACTION_TERMS = (
    "분석",
    "비교",
    "조사",
    "수집",
    "선별",
    "해석",
    "설계",
    "실험",
    "관찰",
    "검증",
    "토론",
    "질문",
    "설명",
    "발표",
    "작성",
    "제작",
    "구현",
    "적용",
    "조율",
    "수정",
    "보완",
    "제안",
)

EVIDENCE_TERMS = (
    "보고서",
    "발표",
    "자료",
    "실험 결과",
    "산출물",
    "표",
    "그래프",
    "토론",
    "설문",
    "초안",
    "수정본",
    "작품",
    "코드",
    "모델",
    "기록",
    "피드백",
    "근거",
)

GROWTH_TERMS = (
    "수정",
    "보완",
    "개선",
    "향상",
    "변화",
    "재시도",
    "성찰",
    "반영",
    "피드백",
    "확장",
)

JUDGMENT_TERMS = (
    "우수",
    "탁월",
    "뛰어남",
    "돋보임",
    "성실",
    "적극적",
    "리더십",
    "모범",
    "열정",
)

ADMISSION_PATTERNS = {
    "합격 가능성": re.compile(r"합격\s*가능성"),
    "인재상 부합": re.compile(r"인재상.{0,12}부합|부합.{0,12}인재상"),
    "입시 유불리": re.compile(r"입시.{0,8}(유리|불리)|대입.{0,8}(유리|불리)"),
    "지원 대학": re.compile(r"지원\s*(대학|학과)|희망\s*대학"),
    "전공적합성 단정": re.compile(r"전공\s*적합성.{0,10}(우수|뛰어|탁월|높)"),
}

FUTURE_PATTERNS = {
    "근거 없는 기대": re.compile(r"기대됨|기대되는 학생|크게 발전할|크게 성장할"),
    "잠재력 단정": re.compile(r"잠재력이\s*(매우\s*)?(크|높)|성공할\s*것"),
}

CREATIVE_CONDITION_PATTERNS = {
    "학교 밖 활동": re.compile(r"학교\s*밖|교외\s*(?:활동|기관|교육)"),
    "자율동아리": re.compile(r"자율\s*동아리"),
    "학교스포츠클럽": re.compile(r"학교\s*스포츠\s*클럽"),
    "청소년단체활동": re.compile(r"청소년\s*단체"),
}

PLACEHOLDER_PATTERN = re.compile(r"\[?확인\s*필요|TODO|TBD|미상|임시\s*문구", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)01[016789][-.\s]?\d{3,4}[-.\s]?\d{4}(?!\d)")
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RESIDENT_ID_PATTERN = re.compile(r"(?<!\d)\d{6}[-\s]?\d{7}(?!\d)")
GENERIC_EVALUATION_PATTERN = re.compile(r"역량을\s*보임|능력을\s*보임|태도가\s*돋보임|우수함")
CHAINED_CONNECTIVE_PATTERN = re.compile(r"하며|하고|하여|해서")
BATCH_ENDING_PHRASES = ("역량을 보임", "능력을 보임", "과정을 드러냄")
BATCH_MINIMUM_ROWS = 10


def load_year_rules(school_year: str, skill_root: Path | None = None) -> dict[str, object]:
    """Load and validate analyzer rules for one school year."""
    root = skill_root.resolve() if skill_root else Path(__file__).resolve().parents[1]
    path = root / "references" / "guidelines" / "analyzer-rules" / f"{school_year}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"{school_year}학년도 분석 규칙 파일이 없습니다: {path}") from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"분석 규칙 파일을 읽을 수 없습니다: {path} ({error})") from error

    if data.get("schema_version") != 1 or str(data.get("school_year")) != school_year:
        raise ValueError(f"분석 규칙 파일의 schema_version 또는 school_year가 올바르지 않습니다: {path}")

    limits = data.get("field_neis_limits")
    pattern_specs = data.get("prohibited_patterns")
    if not isinstance(limits, dict) or not isinstance(pattern_specs, dict):
        raise ValueError(f"분석 규칙 파일에 field_neis_limits와 prohibited_patterns가 필요합니다: {path}")

    for field, limit in limits.items():
        if not isinstance(field, str) or not isinstance(limit, dict):
            raise ValueError(f"분석 규칙의 영역별 한도가 올바르지 않습니다: {path}")
        if not all(isinstance(limit.get(key), int) and limit[key] > 0 for key in ("korean_characters", "bytes")):
            raise ValueError(f"분석 규칙의 영역별 한도는 양의 정수여야 합니다: {path}")

    limits_v2 = data.get("field_limits_v2")
    if limits_v2 is not None and not isinstance(limits_v2, dict):
        raise ValueError(f"분석 규칙의 field_limits_v2가 올바르지 않습니다: {path}")

    compiled: dict[str, re.Pattern[str]] = {}
    for label, spec in pattern_specs.items():
        if not isinstance(label, str) or not isinstance(spec, dict) or not isinstance(spec.get("pattern"), str):
            raise ValueError(f"분석 규칙의 금지 표현 패턴이 올바르지 않습니다: {path}")
        flags = re.IGNORECASE if spec.get("ignore_case") is True else 0
        try:
            compiled[label] = re.compile(spec["pattern"], flags)
        except re.error as error:
            raise ValueError(f"분석 규칙의 정규식이 올바르지 않습니다: {label} ({error})") from error

    return {
        **data,
        "school_year": school_year,
        "prohibited_patterns": compiled,
    }


def count_terms(text: str, terms: Iterable[str]) -> dict[str, int]:
    return {term: text.count(term) for term in terms if term in text}


def approximate_sentence_count(text: str) -> int:
    if not text.strip():
        return 0
    endings = re.findall(
        r"(?:[.!?](?:\s|$)|(?:확인됨|향상됨|보임|수정함|보완함|분석함|작성함|발표함|함|임|됨)(?:\.?\s|$))",
        text.strip(),
    )
    return max(1, len(endings))


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").strip()


def resolve_field_limit(
    rules: dict[str, object],
    field: str,
    grade: int | None = None,
    subject_type: str | None = None,
    area: str | None = None,
) -> tuple[dict[str, object] | None, str | None]:
    legacy_limits = rules["field_neis_limits"]
    assert isinstance(legacy_limits, dict)
    limit = legacy_limits.get(field)
    label_prefix: str | None = None
    limits_v2 = rules.get("field_limits_v2")

    if isinstance(limits_v2, dict):
        if field == "subject" and isinstance(limits_v2.get("subject"), dict):
            subject_limits = limits_v2["subject"]
            limit_key = {
                "common": "common_combined",
                "vocational": "vocational_per_semester",
            }.get(subject_type, "default")
            limit = subject_limits.get(limit_key, limit)
            label_prefix = {
                "common_combined": "공통과목 1·2 합산",
                "vocational_per_semester": "전공실무과목 학기별",
                "default": "과목별 세부능력 및 특기사항",
            }[limit_key]
        elif field == "creative" and area and isinstance(limits_v2.get("creative"), dict):
            creative_limits = limits_v2["creative"]
            limit = creative_limits.get(area, limit)
            area_label = {
                "autonomy": "자율활동" if grade == 3 else "자율·자치활동",
                "club": "동아리활동",
                "service": "봉사활동",
                "career": "진로활동",
            }[area]
            label_prefix = f"창체 {area_label} 특기사항"
        elif field == "behavior":
            limit = limits_v2.get("behavior", limit)
            label_prefix = "행동특성 및 종합의견"

    if not isinstance(limit, dict):
        return None, None
    if label_prefix is None:
        label_prefix = {
            "subject": "과목별 세부능력 및 특기사항",
            "creative": "창의적 체험활동 특기사항",
            "behavior": "행동특성 및 종합의견",
        }.get(field)
    grade_prefix = f"{grade}학년 " if grade is not None else ""
    label = (
        f"{grade_prefix}{label_prefix} {limit['korean_characters']}자/{limit['bytes']}Byte"
        if label_prefix
        else None
    )
    return limit, label


def analyze(
    text: str,
    field: str = "other",
    target_chars: int | None = None,
    rules: dict[str, object] | None = None,
    grade: int | None = None,
    subject_type: str | None = None,
    area: str | None = None,
    combine_with_text: str | None = None,
) -> dict[str, object]:
    if rules is None:
        context = active_rule_context()
        rules = load_year_rules(context["school_year"])
    school_year = str(rules["school_year"])
    prohibited_patterns = rules["prohibited_patterns"]
    assert isinstance(prohibited_patterns, dict)

    normalized = normalize_text(text)
    action_counts = count_terms(normalized, ACTION_TERMS)
    evidence_counts = count_terms(normalized, EVIDENCE_TERMS)
    growth_counts = count_terms(normalized, GROWTH_TERMS)
    judgment_counts = count_terms(normalized, JUDGMENT_TERMS)

    warnings: list[str] = []
    if rules.get("reviewed") is False:
        warnings.append(
            f"{school_year} 분석 규칙은 이전 학년도에서 복사된 미검토 초안입니다. "
            "기재요령 「08 영역별 입력 가능 최대 글자수」와 대조 후 reviewed를 true로 바꾸세요."
        )
    if not normalized:
        warnings.append("문장이 비어 있습니다.")

    char_count = len(normalized)
    neis_bytes = len(normalized.encode("utf-8"))
    if target_chars is not None and char_count > target_chars:
        warnings.append(f"목표 글자 수를 {char_count - target_chars}자 초과했습니다.")

    field_limit, resolved_limit_label = resolve_field_limit(
        rules, field, grade=grade, subject_type=subject_type, area=area
    )
    if field_limit is not None and neis_bytes > field_limit["bytes"]:
        warnings.append(
            f"활성 기재요령의 {school_year} 참고 바이트 한도를 "
            f"{neis_bytes - field_limit['bytes']}Byte 초과했습니다"
            f"(한글 기준 {field_limit['korean_characters']}자, {field_limit['bytes']}Byte; "
            "실제 NEIS 입력값은 별도 확인 필요)."
        )

    combined_neis_bytes: int | None = None
    if field == "subject" and subject_type == "common":
        if combine_with_text is None:
            warnings.append(
                "공통과목 1·2는 합산 500자/1500Byte 한도이며, 이 점검은 현재 한 텍스트만 확인합니다."
            )
        else:
            combined_neis_bytes = neis_bytes + len(normalize_text(combine_with_text).encode("utf-8"))
            if field_limit is not None and combined_neis_bytes > field_limit["bytes"]:
                warnings.append(
                    "공통과목 1·2 합산 참고 바이트 한도를 "
                    f"{combined_neis_bytes - field_limit['bytes']}Byte 초과했습니다"
                    f"({combined_neis_bytes}/{field_limit['bytes']}Byte; 실제 NEIS 입력값은 별도 확인 필요)."
                )

    if field == "creative" and area == "service":
        if grade in (1, 2):
            warnings.append("봉사활동 특기사항 영역은 2026학년도 3학년에만 있음")
        warnings.append(
            "봉사활동 실적 활동내용은 실적별 50자/150Byte 이내의 객관적 내용만 기록하며, "
            "정성평가는 다른 영역에 기록해야 합니다."
        )

    action_total = sum(action_counts.values())
    evidence_total = sum(evidence_counts.values())
    growth_total = sum(growth_counts.values())
    judgment_total = sum(judgment_counts.values())

    if normalized and action_total == 0:
        warnings.append("학생이 실제로 한 행동을 보여 주는 동사가 거의 보이지 않습니다.")
    if judgment_total and evidence_total == 0:
        warnings.append("판단적 표현은 있으나 이를 뒷받침할 산출물·자료·과정 근거가 약합니다.")
    elif judgment_total > action_total + evidence_total:
        warnings.append("판단적 표현의 비중이 행동·근거 표현보다 높습니다.")
    if normalized and growth_total == 0:
        warnings.append("피드백, 수정, 성찰 또는 전후 변화가 필요한 기록인지 확인하세요.")

    if field == "subject" and not re.search(
        r"개념|성취|과제|탐구|자료|실험|측정|오차|조건|작품|표현|문제|코드|알고리즘|데이터|프로그래밍|컴퓨팅",
        normalized,
    ):
        warnings.append("교과세특인데 교과 개념·과제·탐구 방법이 충분히 드러나지 않습니다.")
    if field == "creative" and not re.search(r"역할|협력|조율|공동|기여|참여|기획|운영", normalized):
        warnings.append("창의적 체험활동에서 역할·상호작용·기여의 구체성을 확인하세요.")
    if field == "behavior" and not re.search(r"지속|꾸준|반복|학기|여러|매번|활동에서", normalized):
        warnings.append("행동특성 및 종합의견은 한 번의 인상보다 반복 관찰 근거가 적절한지 확인하세요.")

    admission_hits = [label for label, pattern in ADMISSION_PATTERNS.items() if pattern.search(normalized)]
    if admission_hits:
        warnings.append("공식 기록에서 입시·대학 맞춤 표현을 제거하세요: " + ", ".join(admission_hits))

    future_hits = [label for label, pattern in FUTURE_PATTERNS.items() if pattern.search(normalized)]
    if future_hits:
        warnings.append("미래 예측보다 현재까지 관찰된 변화로 바꾸세요: " + ", ".join(future_hits))

    prohibited_hits = [
        label for label, pattern in prohibited_patterns.items() if pattern.search(normalized)
    ]
    if prohibited_hits:
        warnings.append(
            f"{school_year} 기재요령상 금지 또는 조건 확인이 필요한 표현 후보입니다: "
            + ", ".join(prohibited_hits)
        )

    creative_condition_hits = (
        [
            label
            for label, pattern in CREATIVE_CONDITION_PATTERNS.items()
            if pattern.search(normalized)
        ]
        if field == "creative"
        else []
    )
    if creative_condition_hits:
        warnings.append(
            "창체의 영역·입력 조건을 활성 기재요령과 대조하세요: "
            + ", ".join(creative_condition_hits)
        )

    if PLACEHOLDER_PATTERN.search(normalized):
        warnings.append("확인 필요 또는 임시 문구가 남아 있습니다.")

    privacy_hits: list[str] = []
    if PHONE_PATTERN.search(normalized):
        privacy_hits.append("전화번호")
    if EMAIL_PATTERN.search(normalized):
        privacy_hits.append("이메일")
    if RESIDENT_ID_PATTERN.search(normalized):
        privacy_hits.append("주민등록번호 형태")
    if privacy_hits:
        warnings.append("불필요한 개인식별정보를 제거하세요: " + ", ".join(privacy_hits))

    repeated_intensifiers = len(re.findall(r"매우|아주|정말|대단히|굉장히", normalized))
    if repeated_intensifiers >= 3:
        warnings.append("강조 부사의 반복을 줄이고 구체적 근거로 바꾸세요.")

    if len(GENERIC_EVALUATION_PATTERN.findall(normalized)) >= 2:
        warnings.append("추상 평가를 반복하지 말고 구체적인 행동·방법·결과로 압축하세요.")
    if len(CHAINED_CONNECTIVE_PATTERN.findall(normalized)) >= 4:
        warnings.append("연결어가 연속됩니다. 핵심 수행별로 문장을 나누고 인과를 분명히 하세요.")

    signals = {
        "actions": action_counts,
        "evidence": evidence_counts,
        "growth": growth_counts,
        "judgments": judgment_counts,
        "admission": admission_hits,
        "future_prediction": future_hits,
        "prohibited": prohibited_hits,
        "creative_conditions": creative_condition_hits,
        "privacy": privacy_hits,
    }
    signals[f"prohibited_{school_year}"] = prohibited_hits

    return {
        "field": field,
        "rule_year": school_year,
        "metrics": {
            "unicode_characters": char_count,
            "characters_without_whitespace": len(re.sub(r"\s", "", normalized)),
            "count_contract": "Python Unicode code points after trimming outer whitespace",
            "utf8_bytes": neis_bytes,
            "neis_bytes": neis_bytes,
            "byte_contract": "UTF-8 encoded bytes after CRLF->LF normalization and outer-whitespace trim; matches the active guideline rule (Hangul 3B, ASCII 1B, Enter 1B) but actual NEIS entry values are not yet measured",
            "default_neis_byte_limit": field_limit["bytes"] if field_limit else None,
            "resolved_limit_label": resolved_limit_label,
            "combined_neis_bytes": combined_neis_bytes,
            "limit_contract": (
                "Reference limit from the active guideline; "
                "actual NEIS entry behavior requires separate verification"
                if field_limit
                else None
            ),
            "lines": normalized.count("\n") + (1 if normalized else 0),
            "approximate_sentences": approximate_sentence_count(normalized),
            "target_characters": target_chars,
        },
        "signals": signals,
        "warnings": warnings,
        "disclaimer": (
            f"{school_year} 기재요령의 일부를 기계적으로 점검하는 보조 도구이며 "
            "최종 준수 판정은 교사가 원자료와 학교 규정을 대조해 수행해야 합니다."
        ),
    }


def format_human(result: dict[str, object]) -> str:
    metrics = result["metrics"]
    signals = result["signals"]
    warnings = result["warnings"]
    assert isinstance(metrics, dict)
    assert isinstance(signals, dict)
    assert isinstance(warnings, list)

    lines = [
        "학교생활기록부 문장 기계 점검",
        f"- 영역: {result['field']}",
        f"- 유니코드 글자 수: {metrics['unicode_characters']}",
        f"- 공백 제외 글자 수: {metrics['characters_without_whitespace']}",
        f"- UTF-8 바이트 수: {metrics['utf8_bytes']}",
        f"- 추정 문장 수: {metrics['approximate_sentences']}",
    ]
    guideline = result.get("guideline")
    if isinstance(guideline, dict):
        lines.append(
            f"- 활성 기재요령: {guideline.get('active_version', '')} "
            f"({guideline.get('school_year', '')}학년도)"
        )
    if metrics["default_neis_byte_limit"] is not None:
        lines.append(
            f"- 활성 기재요령의 {result.get('rule_year', '')} 참고 바이트 한도: "
            f"{metrics['default_neis_byte_limit']}Byte (실제 NEIS 입력값 확인 필요)"
        )
    if metrics.get("resolved_limit_label") is not None:
        lines.append(f"- 적용 한도: {metrics['resolved_limit_label']}")
    if metrics.get("combined_neis_bytes") is not None:
        lines.append(f"- 공통과목 1·2 합산 UTF-8 바이트 수: {metrics['combined_neis_bytes']}")
    if metrics["target_characters"] is not None:
        lines.append(f"- 목표 글자 수: {metrics['target_characters']}")

    lines.extend(
        [
            "",
            "신호",
            f"- 행동: {', '.join(signals['actions']) or '없음'}",
            f"- 근거: {', '.join(signals['evidence']) or '없음'}",
            f"- 성장: {', '.join(signals['growth']) or '없음'}",
            f"- 판단: {', '.join(signals['judgments']) or '없음'}",
            f"- {result.get('rule_year', '')} 금지·조건부 후보: {', '.join(signals['prohibited']) or '없음'}",
            f"- 창체 조건 확인: {', '.join(signals['creative_conditions']) or '없음'}",
            "",
            "확인 사항",
        ]
    )
    lines.extend(f"- {warning}" for warning in warnings)
    if not warnings:
        lines.append("- 기계 규칙에서 발견한 경고가 없습니다. 교사가 사실과 현행 지침을 최종 확인하세요.")
    lines.extend(["", str(result["disclaimer"])])
    return "\n".join(lines)


def positive_int(value: str) -> int:
    """Reject length limits that cannot produce a meaningful check."""
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("양의 정수를 입력하세요.") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("0보다 큰 정수를 입력하세요.")
    return parsed


def read_utf8_text(path: Path) -> str:
    """Read an input file without exposing a traceback for expected input errors."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"UTF-8 텍스트 파일을 읽을 수 없습니다: {path} ({error})") from error


def read_batch_tsv(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames is None:
                raise ValueError(f"TSV 파일에 머리글 행이 없습니다: {path}")
            draft_column = "초안" if "초안" in reader.fieldnames else "draft" if "draft" in reader.fieldnames else None
            if draft_column is None:
                raise ValueError(f"TSV 머리글에 '초안' 또는 'draft' 열이 필요합니다: {path}")
            return [row.get(draft_column) or "" for row in reader]
    except ValueError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError(f"UTF-8 TSV 파일을 읽을 수 없습니다: {path} ({error})") from error


def analyze_batch(
    texts: list[str],
    *,
    field: str,
    target_chars: int | None,
    rules: dict[str, object],
    grade: int | None,
    subject_type: str | None,
    area: str | None,
) -> dict[str, object]:
    rows = [
        {
            "row": index,
            **analyze(
                text,
                field=field,
                target_chars=target_chars,
                rules=rules,
                grade=grade,
                subject_type=subject_type,
                area=area,
            ),
        }
        for index, text in enumerate(texts, start=2)
    ]
    warnings: list[str] = []
    notes = ["문장 구조 유형(S1–S10) 비율은 텍스트만으로 기계적으로 판정할 수 없어 계산하지 않았습니다."]
    if len(texts) < BATCH_MINIMUM_ROWS:
        notes.append("배치 반복률 기준은 10명 이상일 때만 적용하므로 경고를 계산하지 않았습니다.")
        return {"rows": rows, "batch_warnings": warnings, "notes": notes}

    token_rows = [normalize_text(text).split() for text in texts]
    first_three = Counter(" ".join(tokens[:3]) for tokens in token_rows if tokens)
    final_tokens = Counter(tokens[-1] for tokens in token_rows if tokens)
    row_count = len(texts)

    if first_three:
        phrase, count = first_three.most_common(1)[0]
        if count / row_count > 0.25:
            warnings.append(
                f"검토 경고: 동일한 첫 3어절 '{phrase}'이 {count}/{row_count}행({count / row_count:.1%})으로 25%를 초과합니다."
            )
    if final_tokens:
        predicate, count = final_tokens.most_common(1)[0]
        if count / row_count > 0.25:
            warnings.append(
                f"검토 경고: 동일한 마지막 서술어 '{predicate}'가 {count}/{row_count}행({count / row_count:.1%})으로 25%를 초과합니다."
            )

    normalized_endings = [normalize_text(text).rstrip(".!?。！？").rstrip() for text in texts]
    for phrase in BATCH_ENDING_PHRASES:
        count = sum(text.endswith(phrase) for text in normalized_endings)
        if count / row_count > 0.20:
            warnings.append(
                f"검토 경고: '{phrase}' 종결이 {count}/{row_count}행({count / row_count:.1%})으로 20%를 초과합니다."
            )
    return {"rows": rows, "batch_warnings": warnings, "notes": notes}


def format_batch_human(result: dict[str, object]) -> str:
    rows = result["rows"]
    warnings = result["batch_warnings"]
    notes = result["notes"]
    assert isinstance(rows, list)
    assert isinstance(warnings, list)
    assert isinstance(notes, list)
    lines = ["학교생활기록부 배치 기계 점검", "행\t글자\t바이트\t경고"]
    for row in rows:
        metrics = row["metrics"]
        lines.append(
            f"{row['row']}\t{metrics['unicode_characters']}\t{metrics['neis_bytes']}\t{len(row['warnings'])}"
        )
    lines.extend(["", "배치 검토 경고"])
    lines.extend(f"- {warning}" for warning in warnings)
    if not warnings:
        lines.append("- 배치 반복률 기준을 초과한 항목이 없습니다.")
    lines.extend(["", "참고"])
    lines.extend(f"- {note}" for note in notes)
    if rows:
        lines.extend(["", str(rows[0]["disclaimer"])])
    return "\n".join(lines)


def active_rule_context(skill_root: Path | None = None) -> dict[str, str]:
    """Verify the active guideline and refuse stale analyzer rules."""
    root = skill_root.resolve() if skill_root else Path(__file__).resolve().parents[1]
    paths = root_paths(root)
    try:
        manifest = load_manifest(paths)
        verify_manifest(paths, manifest)
    except GuidelineError as error:
        raise ValueError(f"활성 기재요령을 검증할 수 없습니다: {error}") from error

    active = manifest["active_version"]
    entry = manifest["versions"][active]
    school_year = str(entry.get("school_year", ""))
    load_year_rules(school_year, root)
    return {
        "active_version": str(active),
        "school_year": school_year,
        "source_title": str(entry.get("source_title", "")),
        "source_url": str(entry.get("source_url", "")),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="점검할 문장")
    source.add_argument("--file", type=Path, help="UTF-8 텍스트 파일")
    source.add_argument("--batch", type=Path, help="초안 또는 draft 열이 있는 UTF-8 TSV 파일")
    parser.add_argument(
        "--field",
        choices=("subject", "creative", "behavior", "other"),
        default="other",
        help="기재 영역",
    )
    parser.add_argument(
        "--target-chars", type=positive_int, help="사용자가 지정한 양의 목표 글자 수"
    )
    parser.add_argument("--grade", type=int, choices=(1, 2, 3), help="학년별 규칙 선택")
    parser.add_argument(
        "--subject-type",
        choices=("common", "elective", "vocational"),
        default="elective",
        help="교과 유형별 한도 선택",
    )
    parser.add_argument(
        "--area",
        choices=("autonomy", "club", "service", "career"),
        help="창체 세부 영역별 한도 선택",
    )
    parser.add_argument("--combine-with", type=Path, help="공통과목 1·2 합산 점검용 UTF-8 텍스트 파일")
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    return parser.parse_args()


def main() -> int:
    # Windows 기본 콘솔(cp949)에서 한글 출력이 깨지지 않도록 UTF-8로 고정한다.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    if args.area is not None and args.field != "creative":
        print("오류: --area는 --field creative에서만 사용할 수 있습니다.", file=sys.stderr)
        return 2
    if args.combine_with is not None and (args.field != "subject" or args.subject_type != "common"):
        print("오류: --combine-with는 공통과목 교과 점검에서만 사용할 수 있습니다.", file=sys.stderr)
        return 2
    if args.batch is not None and args.combine_with is not None:
        print("오류: --batch와 --combine-with는 함께 사용할 수 없습니다.", file=sys.stderr)
        return 2
    try:
        guideline = active_rule_context()
        if args.batch is not None:
            texts = read_batch_tsv(args.batch)
        else:
            text = args.text if args.text is not None else read_utf8_text(args.file)
            combine_with_text = read_utf8_text(args.combine_with) if args.combine_with else None
    except ValueError as error:
        print(f"오류: {error}", file=sys.stderr)
        return 2
    rules = load_year_rules(guideline["school_year"])
    if args.batch is not None:
        result = analyze_batch(
            texts,
            field=args.field,
            target_chars=args.target_chars,
            rules=rules,
            grade=args.grade,
            subject_type=args.subject_type,
            area=args.area,
        )
        for row in result["rows"]:
            row["guideline"] = guideline
    else:
        result = analyze(
            text,
            field=args.field,
            target_chars=args.target_chars,
            rules=rules,
            grade=args.grade,
            subject_type=args.subject_type,
            area=args.area,
            combine_with_text=combine_with_text,
        )
        result["guideline"] = guideline
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_batch_human(result) if args.batch is not None else format_human(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
