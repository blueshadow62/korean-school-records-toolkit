# Changelog

## Unreleased

### Fixed

- 성취수준 영어 파일 4개의 내용이 과목과 어긋나 있던 문제 수정. `공통영어1.md`에 공통영어2, `공통영어2.md`에 기본영어1, `기본영어1.md`에 기본영어2가 들어 있었고 공통영어1 자료가 빠져 있었다.
- `세계사.md`, `역사로_탐구하는_현대_세계.md`, `미디어_영어.md`에 성취수준 표 대신 들어 있던 보고서 서술 장을 해당 과목의 표로 교체.
- 코드로 찾지 못하던 `[12물에03-03]`, `[12영Ⅱ-01-01]`, `[12스생2-01-01]` 표기 수정. 고친 내용은 각 파일 첫머리에 적었다.
- 표 밖으로 밀려 수준 설명과 떨어져 있던 성취기준 134개(43개 파일)를 수준 행의 첫 칸으로 되돌림. 글자는 바꾸지 않았다.
- 사용자 설명서의 NEIS 줄바꿈 바이트 안내를 2byte에서 1byte로 수정하고, `docs/how-it-works.html`의 성취수준 자료 수를 현재 값으로 수정.

### Added

- 중학교 성취수준 자료 추가: 17개 교과, 성취기준 711개. 학교급이 중학교이거나 `[9…]` 코드가 있을 때 쓴다. 문구는 제2026-1호 별책 3과 코드별로 대조했다.
- 중학교 초안 지원: 활성 기재요령이 고등학교판이므로 결과에 `중학교 기재요령 미확인`을 표시하고, 금지 사항은 고등학교판 기준으로 보수적으로 적용하며, 글자 수 한도는 `[확인 필요]`로 둔다.
- README와 사용자 설명서에 성취수준 자료의 범위와 사용법 안내 추가.
- 성취수준 과목 7개 추가: 언어생활 탐구, 여행지리, 사회문제 탐구, 금융과 경제생활, 기후변화와 지속가능한 세계, 경제 수학, 세계 문화와 영어.
- 파일 이름과 코드 접두, 같은 본문 파일, 서술 장 혼입을 잡는 성취수준 테스트 추가.

### Changed

- 초안을 요청할 때 학교급을 알 수 없으면 먼저 묻는다. 학년, 성취기준 코드, 고등학교에만 있는 과목명으로 알 수 있으면 묻지 않고, 일괄 작업은 처음에 한 번만 묻는다.
- 평가 사례에 학교급을 밝히고 학교급 사례 3건을 추가했다.
- 응답 안내: 근거표의 출처 유형을 일반 언어로 적고, 스크립트 이름·파일 경로·manifest·버전 문자열을 쓰지 않으며, 초안 라벨을 `[세특 초안]`, `[창체 초안]`, `[행특 초안]`, `[작성 지원]`으로 고정. 활동지·소감문의 자기보고는 학생의 진술로 쓴다. 근거가 없을 때의 작성 틀과 경고 문구를 영역에 맞춘다.

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
