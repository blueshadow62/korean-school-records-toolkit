# Changelog

## 2.1.0 — 2026-08-30

### Fixed

- `korean-character-count` `neis` 프로필의 줄바꿈 바이트를 2B에서 1B로 수정해 2026 기재요령(한글 3Byte, 영문·숫자 1Byte, 엔터 1Byte) 및 `analyze_record.py`와 일치시킴.
- `analyze_record.py`·`update_guidelines.py`가 Windows 기본 콘솔(cp949)에서 한글을 깨뜨리지 않도록 UTF-8 출력으로 고정.

### Changed

- `write-school-records` SKILL.md의 S1–S10 서술 구조 절을 `references/sentence-structures.md`로 분리.
- 두 스킬의 NEIS 바이트 교차검증 테스트, JS 단위 테스트, 개발본/배포본 드리프트 테스트 추가.

### Added

- 금지 표현 점검 보강: 대학 약칭(서울대 등), 공인어학시험 한글 표기(토익 등), 사교육·강사, 재학 학교 식별 후보. 연결어미·인용어미 오탐 방지 테스트 포함.
- `update_guidelines.py import/activate`가 새 학년도 분석 규칙을 이전 학년도에서 `reviewed: false`로 복사하고, 점검기는 미검토 규칙 경고를 출력.
- `analyze_record.py`에 `--grade`, `--subject-type`, `--area`, `--combine-with`(공통과목 합산), `--batch`(10행 이상 반복률 검토 경고) 추가. 규칙 파일에 `field_limits_v2` 블록 추가(기존 키 유지).
- `references/intake-template.md`(교사 입력 형식·엑셀 열→출처 유형 매핑), `references/output-skeleton.md`(응답 골격·D 판정 작성 틀), SKILL.md 「지원 영역」 표.
- `tests/eval-cases/` 합성 행동 평가 케이스 15건과 채점 절차, 스키마 테스트.

## 2.0.0 — 2026-08-10

### Removed

- Remove the bundled `korean-spell-check` skill and all external spell-check service dependencies.
- Remove ZIP generation and all previously generated ZIP artifacts; distribute the repository plugin directory directly.
- Remove the redundant single-skill installer, one-time achievement-corpus normalizer, generated checksum inventory, README banner automation, and duplicate HTML user guide.

### Changed

- Record common/core achievement-standards materials as NCIC KOGL Type 2 and elective materials as NKIS KOGL Type 1.
- Update manifests, installation flows, documentation, and verification contracts for the two-skill bundle.
- Use Node.js `util.parseArgs()` for the character-count CLI instead of a custom option parser.

### Fixed

- Track the public achievement-standards corpus in Git so GitHub distributions include all source files.

## 1.2.0 — 2026-08-10

### Added

- Include the 2022 revised curriculum achievement-standards reference corpus in the public plugin.
- Add separate attribution guidance for common/core subjects listed by NCIC and elective subjects published as KOGL Type 1 through NKIS.

### Changed

- Relicense `write-school-records` from the restrictive internal-use notice to MIT, keeping the Copyright © 2026 blueshadow62 attribution.
- Relicense `write-school-records` again, from MIT to CC BY-NC-SA 4.0, and disclose the real author identity (© 2026 류기현, 부산 동아공고) in place of the `blueshadow62` handle. `korean-character-count` and `korean-spell-check` are unaffected (third-party sourced, remain MIT, no named copyright holder).
- Add a notice recommending users confirm their own 시도교육청 AI usage guidelines before use.

## 1.1.0 — 2026-07-30

### Added

- Add a Claude Code plugin manifest that reuses the existing three-skill layout.
- Add Claude Code personal installation and local validation instructions.
- Build a separate deterministic Claude Code ZIP without changing the three skill payloads.

### Unchanged

- Preserve the Codex plugin manifest, marketplace identity, and installation flow.
- Preserve all three skill names, behavior, scripts, references, and safety contracts.

## 1.0.1 — 2026-07-26

### Added

- Add the `write-school-records` copyright and authorized-internal-use notice.
- Add the recovered `korean-spell-check` P1–P10 fixture regression suite.

### Fixed

- Reject empty and whitespace-only spell-check input without a network request.
- Distinguish spell-check service failure from a successful check with no issues.
- Classify HTTP, network, parsing, and blocked-service failures.
- Normalize duplicate correction candidates while preserving order.

### Security / Safety

- Treat denied approval and incomplete inspection as unfinished, never as success or no spelling errors.
- Do not present the original text as a completed correction after service failure.

### Unchanged

- Preserve `write-school-records` functionality and active guidelines.
- Preserve the `korean-character-count` payload.
- Preserve the plugin ID, display name, and installation interface.

## 1.0.0 — 2026-07-24

- Package `write-school-records`, `korean-character-count`, and `korean-spell-check` as three independent skills in one Codex plugin.
- Add official plugin manifest and repo-local marketplace entry.
- Add transactional bundle management, package verification, integrity metadata, and installation guidance.
