# Changelog

## Unreleased

### Removed

- 배포본에서 교육부 기재요령 원문 변환본을 뺐다: `references/guidelines/`와 `references/guidelines-middle/`의 `current.md`, `current.index.md`, `manifest.json`, `versions/2026_2026-02-12.md`(8개 파일, 약 2.4MB). 원문은 공공누리 제4유형(출처표시·상업적 이용금지·변경금지)인데 변환본은 표를 다시 짜고 그림 링크를 지운 것이어서 권리 해석에 확인되지 않은 부분이 있었고, 변환본 하나하나가 플러그인 디렉터리 심사의 파일 크기 검토 기준(256KiB)을 넘었다. 또 스킬은 초안을 쓸 때 원문보다 직접 쓴 규정 요약을 주로 쓰고 있었다. 원문 변환본은 개발본에만 둔다.

### Fixed

- `analyze_record.py --area service`가 3학년 봉사활동을 '특기사항 500자/1,500Byte'로 점검하던 문제 수정. 기재요령은 3학년 봉사활동 영역에 실적만 입력하게 하고(훈령 제433호 제13조②), 최대 글자수 표에도 봉사활동 특기사항 칸이 없다. 이제 실적 한 건의 활동내용(50자/150Byte)으로 세고, 1·2학년이면 봉사활동이 각 영역과 연계해 운영된다고 알린다. 고·중 검사 규칙에서 원문에 없는 `service` 특기사항 한도를 지웠고, SKILL.md 「지원 영역」의 '3학년 봉사 포함, 영역별 500자' 표현도 고쳤다.
- `guidelines-middle/differences.md`가 최대 글자수를 모든 항목에 학년 단위로 적용하는 것처럼 쓰고, 영재·발명교육 기록 방식이 두 판에서 같다고 쓰던 문제 수정. 학년 단위는 표에 별표가 붙은 창체·독서·행특이고, 발명교육은 중학교판에서 관련 교과 세특 본문에 쓴다.
- 고등학교 `references/guidelines/ATTRIBUTION.md`의 원문 등록 명령이 실제 인자(`--input`, `--source-title` 필수)와 다르던 문제 수정.
- Git for Windows 기본값(`core.autocrlf=true`)으로 복제하면 기재요령 참조본이 CRLF로 바뀌어 manifest의 sha256 검증과 NEIS 표본 바이트 검사가 실패하던 문제 수정. `.gitattributes`로 텍스트 파일을 LF로 받게 했다. 저장소의 파일 내용은 바뀌지 않는다.
- `output-skeleton.md` 마지막 안내가 진단 시트에도 A–D 코드를 쓰지 않는다고 해 SKILL.md(요청 시 별도 진단 시트에 기록 가능)와 어긋나던 문제 수정. 진단 시트 골격에 `내부 판정` 열을 두고, 그 밖의 위치에는 쓰지 않는다고 적었다. 두 파일이 맞는지 검사하는 테스트를 추가했다.
- `output-skeleton.md` '활용 근거' 표의 자리표시 행에 든 `|`가 열 구분자로 읽혀 3열 표가 11칸으로 깨지던 문제 수정. 진단 시트와 같이 `·`로 나누고 '중 하나'를 붙였다. 이 파일의 모든 표에서 행의 칸 수가 머리글과 같은지 보는 테스트를 추가했다.
- `analyze_record.py` 오탐 수정. '시대·세대·현대·그대로·고대·연대'가 대학 약칭 후보로, '체육대회·수상 스포츠'가 대회·수상 후보로, '공익광고·교통사고'가 재학 학교 식별 후보로 잡히던 문제를 고쳤다. 연대·고대처럼 일반 낱말과 같은 약칭은 진학·입학·합격·지원 맥락에서만 잡는다. 고등학교판과 중학교판 규칙을 함께 고쳤고, 흔한 낱말과 실제 금지 후보를 고정하는 테스트를 추가했다.
- 근거 신호의 한 글자 낱말 '표'가 '발표·목표·표현'의 일부로 세어져, 판단 표현만 있는 기록에 '근거가 약함' 경고가 뜨지 않던 문제 수정. 한 글자 낱말은 낱말 단위로만 센다.
- 성장 표현이 없을 때의 경고가 피드백·성찰을 덧붙이도록 유도하던 문구를, 확인된 변화만 반영하라는 문구로 바꿨다. 봉사활동 영역 경고의 학년도를 고정 문자열 대신 규칙의 학년도로 표시한다.
- `intake-template.md` '필수·선택 필드'가 교사 관찰·결과물 요약 중 하나가 없으면 근거 없음(D)으로 보게 해, 소감문 같은 제한된 근거만으로도 보수적 초안을 쓰게 한 SKILL.md 「내부 근거 판정 A–D」와 어긋나던 문제 수정. 서식은 별도 문턱을 두지 않고 SKILL.md를 따르게 했으며, 행특은 과목·활동명 없이도 성립한다. 두 문서를 묶는 테스트를 추가했다.
- 행동 평가 사례(`tests/eval-cases/cases.json`)의 금지 문자열 검사가 출력 전체에 적용되어, 수상·토익·대학명을 초안에서 뺀 이유를 알리는 설명까지 실패로 잡던 문제 수정. SKILL.md는 제외한 사실과 이유를 알리게 하므로 채점 기준과 어긋났다. 기록 문장에 관한 금지 문자열은 새 필드 `must_not_include_in_draft`로 옮겨 초안 본문에만 적용하고, 내부 코드·라벨·질문 문구는 `must_not_include`로 출력 전체에서 검사한다. 초안 본문의 범위(라벨 뒤 첫 단락, `작성 틀` 절, 표의 `초안` 열, 이 영역이 없으면 출력 전체)를 `tests/eval-cases/README.md`에 적었고, `test_eval_cases.py`가 새 필드와 두 목록의 구분을 검사한다. `schema_version`은 2로 올렸다.

### Added

- 기재요령 핵심 규정 요약 `references/guidelines/summary.md`(고등학교)와 `references/guidelines-middle/summary.md`(중학교). 교육부 「2026학년도 학교생활기록부 기재요령」(2026-02-12 개정)을 바탕으로 이 스킬이 직접 정리했다. 원문 해설을 옮기지 않고 영역별로 누가·누구에게·무엇을 쓸 수 있고 없는지·예외·한도를 규칙 목록과 표로 썼다. 훈령 조문은 인용 블록으로 구분해 원문 그대로 실었고, 각 규칙에 원문 장을 붙였다. 지원하지 않는 영역은 한도와 원문 위치만 적었다. 머리말에 학년도·원문 개정일·게시 주소·작성일을 기계가 읽을 수 있게 적었다.
- `scripts/test_guideline_summary.py`: 요약을 검사 규칙과 언제나 대조하고, 원문이 등록된 환경(개발본)에서는 최대 글자수 표의 모든 행, 인용 조문, 장 제목, 금지 항목 이름을 원문과 대조한다.
- 사용자 설명서에 「기재요령 원문을 직접 등록하기」 절 추가: 교육부 PDF를 kordoc 등으로 Markdown으로 바꾸는 방법, 변환에서 쪽이 빠졌는지 확인할 점, 등록·검증 명령, 재설치 때 등록한 원문이 새 설치본에 없다는 점.
- `docs/guideline-summary-updates.md`: 새 학년도 기재요령이 나왔을 때 누가, 무엇을 보고, 어떤 테스트로 요약을 갱신하는지.
- `verify_package.py`와 `tests/test_package.py`가 배포본에 원문 변환본이 없는지, 요약 머리말과 그 학년도의 검사 규칙이 있는지, 원문 없이 점검기와 `update_guidelines.py verify`가 요약 기준으로 동작하는지 검사한다. `.gitignore`가 사용자가 등록한 원문 파일을 제외한다.
- push와 pull request 때 Ubuntu·Windows에서 unittest, node 테스트, `verify_package.py`를 실행하는 GitHub Actions 작업 흐름(`.github/workflows/tests.yml`) 추가. Windows는 `PYTHONUTF8`과 `core.autocrlf`를 러너 기본값 그대로 두고 실행한다.
- 교과 안내 세 파일(`subject-humanities.md`, `subject-stem.md`, `subject-practical-arts.md`)에 '중학교 차이' 절 추가. 고등학교 기준인 세특 규정 게이트에서 중학교에서 뒤집히는 항목(입력 대상, 합산·학기별 한도, 소논문 예외, 능력단위)만 적고 `guidelines-middle/differences.md` 2절을 가리킨다.

### Changed

- 기재요령 판단의 기준을 원문 변환본에서 학교급별 요약으로 바꿨다. 사용자에게 달라지는 점: 규정 판단과 분량 기준은 요약으로 하며, 답변의 기준 줄에 `요약 기준(원문 미대조)`을 적고 원문을 실제로 읽어 대조했을 때만 `원문 대조`라고 쓴다. 요약에 없는 세부 규정(예: 독서활동상황의 기재 방법)은 지어내지 않고 원문의 해당 장을 안내한다. `analyze_record.py`는 원문이 등록되지 않았으면 요약 머리말의 학년도로 검사 규칙을 고르고 출력에 `원문 미등록, 요약 기준`을 밝힌다(JSON은 `guideline.basis`가 `summary`). 원문을 등록했으면 지금처럼 활성 버전과 해시를 검증하고, 해시가 틀리면 오류다. `update_guidelines.py list`·`verify`는 원문이 없는 상태를 오류 대신 요약 기준 동작으로 안내한다.
- SKILL.md, `source-policy.md`, `output-skeleton.md`, 영역별 안내 문서, `ATTRIBUTION.md`가 요약을 기준으로 가리키고, 원문이 등록된 환경에서만 문구 확인에 원문 색인을 쓰게 고쳤다. `differences.md`와 `field-free-semester.md`의 원문 행 번호 참조를 장 제목과 요약 절 번호로 바꿨다. 원문 표를 읽는 테스트는 원문이 등록된 환경에서만 돌고, 같은 사실을 요약 표에서 확인하는 테스트를 더했다.
- `write-school-records` SKILL.md에서 여러 번 반복되던 규칙을 한 곳에 모았다. 근거 없는 완성형 기록 금지와 필수 경고 문구는 「내부 근거 판정 A–D」의 D 항목에, 내부 A–D 코드를 드러내지 않는 규칙은 같은 절의 한 문단에 둔다. 규칙의 뜻과 강도, 경고 문구는 바꾸지 않았다.
- 판정별 라벨, 근거 부족을 알리는 일반 문장, 응답에 쓰지 않는 내부 명칭처럼 응답 형식에 속하는 세부를 `references/output-skeleton.md`로 옮겼다. SKILL.md 「출력과 점검」은 초안·첨삭·작성 지원으로 답하기 전에 이 파일을 반드시 읽게 한다. `output-skeleton.md`의 최대 글자수 표 안내도 장 번호 대신 표 제목으로 가리킨다.
- 배포본 SKILL.md 라우팅 표의 세 행(교사 자료 입력 형식, 응답 골격, 스킬 행동 검증)을 개발본과 같은 위치로 옮겼다.
- `test_skill_integration.py`가 옮겨 간 문구를 `output-skeleton.md`에서 검사하고, SKILL.md가 출력 전에 이 파일을 읽게 하는지와 합친 규칙이 한 번만 나오는지 검사한다.
- SKILL.md 코드 규칙 문단에, 교사가 말한 `성취수준 A`·`성취도 B`는 내부 근거 등급이 아니라 평가 결과 자료로 다룬다는 문장을 추가했다. 두 체계가 같은 글자를 쓰기 때문이다.
- `sentence-structures.md` 첫머리에 두 번 나오던 '구조 코드는 결과에 노출하지 않는다' 문장을 하나로 줄였다.
- 서식 없이 붙여넣은 교사 메모의 교사 관찰 인정 범위를 넓혔다. 이전에는 '관찰함'·'확인함'이라고 쓴 부분만 교사 관찰로 보아, 교사가 자기 수업에서 본 행동을 평소 말투로 적어도 초안의 모든 문장에 `[확인 필요]`가 붙고 직접 관찰 여부를 되물었다. 이제 교사가 자기 수업·학급·담당 활동에서 본 학생의 행동을 적은 메모는 표지가 없어도 교사 관찰로 본다. 전해 들은 서술, 학생이 쓴 글(소감문·자기평가·활동지의 자기 서술), 교사가 볼 수 없는 내면·가정 사정과 교사가 없던 자리의 일, 행동 없는 평가·인상, 누가 보았는지 알 수 없는 서술은 계속 교사 관찰로 보지 않는다. 메모보다 강한 해석과 메모에 없는 사실을 쓰지 않는 규칙은 바꾸지 않았다. 규칙은 SKILL.md 「작성 절차」 한 곳에 두고, 「빠른 경로」 3번과 `intake-template.md`의 매핑 규칙 3번·서식 안내가 그것을 가리킨다. 문구 검사 테스트와 행동 평가 사례 3건(표지 없는 메모 2건, 전해 들은 말과 학생 글이 섞인 메모 1건, 모두 22건)을 추가했다.

## 2.2.0 — 2026-11-18

### Fixed

- 성취수준 영어 파일 4개의 내용이 과목과 어긋나 있던 문제 수정. `공통영어1.md`에 공통영어2, `공통영어2.md`에 기본영어1, `기본영어1.md`에 기본영어2가 들어 있었고 공통영어1 자료가 빠져 있었다.
- `세계사.md`, `역사로_탐구하는_현대_세계.md`, `미디어_영어.md`에 성취수준 표 대신 들어 있던 보고서 서술 장을 해당 과목의 표로 교체.
- 코드로 찾지 못하던 `[12물에03-03]`, `[12영Ⅱ-01-01]`, `[12스생2-01-01]` 표기 수정. 고친 내용은 각 파일 첫머리에 적었다.
- 표 밖으로 밀려 수준 설명과 떨어져 있던 성취기준 134개(43개 파일)를 수준 행의 첫 칸으로 되돌림. 글자는 바꾸지 않았다.
- 사용자 설명서의 NEIS 줄바꿈 바이트 안내를 2byte에서 1byte로 수정하고, `docs/how-it-works.html`의 성취수준 자료 수를 현재 값으로 수정.
- `test_update_guidelines.py`가 `PYTHONUTF8` 없이 Windows 기본 콘솔(cp949)에서 실행하면 2건이 오류로 끝나던 문제 수정. `update_guidelines.py`의 UTF-8 출력을 로캘 인코딩으로 읽고 있었다.

### Added

- 중학교 성취수준 자료 추가: 17개 교과, 성취기준 711개. 학교급이 중학교이거나 `[9…]` 코드가 있을 때 쓴다. 문구는 제2026-1호 별책 3과 코드별로 대조했다.
- 중학교 기재요령 반영: 교육부 「2026학년도 학교생활기록부 기재요령 안내」의 중학교판(공공누리 제4유형)을 `references/guidelines-middle/`에 등록했다. 중학교 초안은 이 기준과 한도(과목별 세특 500자, 창체 영역별 500자, 행특 300자)를 쓰고, 고등학교판에만 있는 규정(공통과목 합산, 모의고사, 재학 학교 식별 금지, 소논문 예외 과목)은 적용하지 않는다. 두 판의 차이는 `differences.md`에 정리했다.
- 중학교 자유학기활동 특기사항 초안 지원(진로탐색·주제선택, 3학년은 예술·체육·동아리 추가, 영역별 1,000자).
- `update_guidelines.py --level middle`, `analyze_record.py --school-level middle`과 `--field free_semester` 추가. 옵션을 주지 않으면 고등학교 기준으로 기존과 같게 동작한다.
- README와 사용자 설명서에 성취수준 자료의 범위와 사용법 안내 추가.
- 성취수준 과목 7개 추가: 언어생활 탐구, 여행지리, 사회문제 탐구, 금융과 경제생활, 기후변화와 지속가능한 세계, 경제 수학, 세계 문화와 영어.
- 파일 이름과 코드 접두, 같은 본문 파일, 서술 장 혼입을 잡는 성취수준 테스트 추가.

### Changed

- SKILL.md 「지원 영역」이 고등학교 기재요령의 한도를 행 번호 대신 '학교생활기록부 영역별 입력 가능 최대 글자수' 표 제목으로 가리킨다. 새 학년도 기재요령을 활성화해도 위치가 어긋나지 않는다. 그 표에 각 영역의 한도가 있는지 확인하는 `test_guidelines_high.py`를 추가했다.
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
