# 한국어 학교생활기록부 도구

<!-- CHANGELOG:START -->
> **최근 업데이트: 3.0.0** — 자세한 변경 내역은 [CHANGELOG.md](CHANGELOG.md)를 확인하세요.
<!-- CHANGELOG:END -->

현재 버전은 `3.0.0`이다.

교사가 확인한 관찰·평가 근거로 학교생활기록부 세특·창체·행특·중학교 자유학기활동 초안을 쓰고, 글자 수와 NEIS Byte를 계산하는 Claude Code·Codex 겸용 스킬 플러그인이다. 규정은 2026학년도 기재요령을 이 도구가 정리한 요약으로 판단하고(공식 효력은 교육부 원문에 있다), 2022 개정 교육과정 중·고등학교 성취수준을 참고한다. 초안 작성과 글자 수 계산은 서로 독립적으로 사용할 수 있다.

## 포함 스킬

| 스킬 | 역할 | 주요 호출 범위 |
|---|---|---|
| `write-school-records` | 실제 관찰·평가 근거 기반 학생부 초안·점검 | 세특, 창체 특기사항, 행특, 중학교 자유학기활동 특기사항, 기재요령·성취수준 참고 |
| `korean-character-count` | 결정론적 글자 수·줄 수·UTF-8/NEIS Byte 계산 | 분량 확인, 문장·셀별 집계, 최대 한도 검사 |
여러 기능을 함께 요청하면 `학생부 초안 → 글자 수·NEIS Byte 확인` 순서로 연계한다. 한 기능만 요청하면 다른 스킬을 강제로 실행하지 않는다.

## 사용 예시

### 학교생활기록부 작성

> 첨부한 학생별 교사 관찰과 결과물을 근거로 교과 세부능력 및 특기사항 초안을 작성해 줘. 사실이 확인되지 않는 내용은 추가하지 말고, 최종 문장의 글자 수와 NEIS Byte도 확인해 줘.

### 글자 수 확인

> 아래 문장의 글자 수와 NEIS 기준 Byte를 계산하고 1,500Byte 초과 여부를 알려줘.

### 통합 처리

> 첨부한 학생 자료로 세특 초안을 작성한 뒤 최종 글자 수와 NEIS Byte를 계산해 줘.

### 성취수준 찾기

> `[12화학03-03]` 성취기준의 수준별 설명을 찾아 줘.

> 중학교 `[9과02-01]` 성취기준의 수준별 설명을 보여 줘.

## 성취수준 자료 범위

| 학교급 | 들어 있는 자료 | 쓰는 때 |
|---|---|---|
| 고등학교 | 과목 파일 231개 | 학교급이 고등학교일 때 쓴다 |
| 중학교 | 17개 교과, 성취기준 711개 | 학교급이 중학교이거나 `[9…]` 코드가 있을 때 쓴다 |

초안을 요청할 때 학교급을 알 수 없으면 먼저 묻는다. `중2`, `고1`, 성취기준 코드, 고등학교에만 있는 과목명으로 알 수 있으면 묻지 않는다.

중학교 초안은 `2026 학교생활기록부 기재요령(중학교)`를 따른다. 한도는 과목별 세특 500자, 창체 영역별 500자, 행특 300자, 자유학기활동 영역별 1,000자다. 공통과목 1·2 합산, 모의고사, 재학 학교 식별 금지처럼 고등학교판에만 있는 규정은 적용하지 않는다. 중학교판 규정은 `skills/write-school-records/references/guidelines-middle/summary.md`에, 두 판의 차이는 같은 폴더의 `differences.md`에 정리했다.

## 안전 원칙

- 이 도구의 출력은 교사가 사실과 규정을 대조하기 전의 보조 초안이다. 기재요령은 AI로 생성한 자료를 서술형 항목에 그대로 입력하지 않도록 하고, 윤문 같은 보조 수단으로 썼다면 최종 입력 전에 허위·과장 여부와 유의사항 준수를 철저히 확인하게 한다.
- 이 도구를 활용하실 때에는 근무하시는 학교·시도교육청의 AI 활용 지침과, 학생·보호자에게 AI 사용 사실을 알려야 하는지(고지 의무)를 확인하시기 바랍니다. 참고로 Anthropic 사용 정책은 입학 허가·순위 결정, 입학·졸업을 정하는 평가의 채점 같은 교육 분야 결정에 AI를 쓰면 자격 있는 사람의 검토와 당사자에 대한 AI 사용 고지를 요구한다.
- `write-school-records`는 CC BY-NC-SA 4.0 라이선스(© 2026 류기현, 부산 동아공고)이며, 비영리 목적에 한해 원저작자 표시·동일조건변경허락 조건으로 자유롭게 사용·수정·재배포할 수 있다. 상업적 이용은 금지되며 문의는 이 저장소의 GitHub Issue로 한다.
- 실제 학생 자료를 예제·테스트·패키지에 포함하지 않는다.
- 배포 전 학생 이름, 학번, 학교명 등 개인정보를 제거한다.
- 테스트에는 합성 자료만 사용한다.
- 학생부 결과는 교사가 원자료와 학교 규정에 대조해 최종 확인한다.
- 플러그인은 학생 사실을 임의로 만들지 않는다.
- 분량 계산은 기록의 사실성을 대신하지 않는다.
- 성취수준 참고 자료의 공통과목·중고 합본과목은 NCIC 공공누리 제2유형, 선택과목은 NKIS 공공누리 제1유형 조건을 따른다. 자세한 출처 표시는 `skills/write-school-records/references/achievement-standards/ATTRIBUTION.md`를 따른다.
- 중학교 성취수준 자료는 NCIC 저작권 정책의 공공누리 제2유형 조건을 따른다. 게시물별 표시는 개별로 확인하지 못했다. 자세한 출처 표시는 `skills/write-school-records/references/achievement-standards-middle/ATTRIBUTION.md`를 따른다.
- 기재요령 원문은 이 패키지에 들어 있지 않다. `references/guidelines/summary.md`(고등학교)와 `references/guidelines-middle/summary.md`(중학교)는 교육부 원문을 바탕으로 이 도구가 직접 정리한 **핵심 규정 요약**이며, 도구는 이 요약으로 규정을 판단한다. 공식 효력을 갖는 것은 교육부 배포 원문이며, 내용이 다르면 원문을 따른다. 본 저작물은 교육부에서 2026년 작성하여 공공누리 제4유형(출처표시+상업적 이용금지+변경금지)으로 개방한 「2026학년도 학교생활기록부 기재요령 안내」를 이용하였으며, 해당 저작물은 교육부 홈페이지(https://www.moe.go.kr)에서 무료로 내려받으실 수 있다. 요약의 성격과 이용 조건은 각 폴더의 `ATTRIBUTION.md`를 따른다. 원문 문구까지 대조하려면 교육부 원문을 Markdown으로 바꿔 직접 등록할 수 있다([USER_GUIDE.md](USER_GUIDE.md) 「기재요령 원문을 직접 등록하기」).

## 두 가지 판

이 저장소는 같은 학생부 스킬을 두 가지 판으로 제공한다. 둘 가운데 하나만 설치한다. 함께 설치하면 같은 스킬이 두 개 보인다.

| 구분 | 전체판 | 문서 전용판 |
|---|---|---|
| 플러그인 이름 | `korean-school-records-toolkit` | `korean-school-records-lite`(한국어 학교생활기록부 도구 라이트) |
| 위치 | 저장소 루트 | [`editions/korean-school-records-lite/`](editions/korean-school-records-lite/) |
| 쓰는 곳 | Claude Code, Codex | claude.ai, Cowork, Claude Code |
| 학생부 초안·첨삭·점검 | 있음 | 있음(근거 판단, 공통 게이트, 학교급 확인, 응답 형식이 전체판과 같다) |
| 글자 수·NEIS Byte | 점검 스크립트(`analyze_record.py`)로 계산 | Claude의 코드 실행 도구로 같은 방식으로 계산하고, 실행할 수 없으면 계산하지 못했다고 밝힌다 |
| 금지 표현 점검 | 스크립트의 기계 점검과 요약 대조 | 요약을 기준으로 Claude가 직접 대조 |
| 글자 수 계산 스킬(`korean-character-count`) | 있음 | 없음 |
| 기재요령 원문 등록·NEIS 실측 대조 | 있음 | 없음 |
| 실행하는 것 | Python·Node.js 스크립트 | 없음(Markdown·JSON 문서만 들어 있다) |

문서 전용판은 Claude 플러그인 디렉터리에 등록할 예정이다. 전체판 폴더에서 `scripts/build_directory_edition.py`로 만들며 직접 고치지 않는다. 두 판의 의도된 차이는 [docs/dev-vs-package.md](docs/dev-vs-package.md)에 있다.

## 설치

전체판은 Claude Code에서 이 저장소를 마켓플레이스로 추가한 뒤 설치한다.

```bash
claude plugin marketplace add blueshadow62/korean-school-records-toolkit
claude plugin install korean-school-records-toolkit@blueshadow62-school-records
```

Codex 설치·업데이트·제거 절차는 [INSTALL.md](INSTALL.md)를 따른다. Claude Code 설치와 로컬 검증은 [README_CLAUDE_CODE.md](README_CLAUDE_CODE.md)를 따른다.

문서 전용판은 디렉터리에 등록되면 claude.ai·Cowork·Claude Code의 디렉터리에서 설치한다. 그 전에 Claude Code에서 시험하려면 같은 마켓플레이스에서 `korean-school-records-lite@blueshadow62-school-records`를 설치한다. 전체판을 이미 설치했다면 먼저 제거한다.

## 실행하는 것과 외부 연결

- 두 스킬은 이 플러그인 폴더 안의 스크립트만 실행한다. `write-school-records`는 Python 3 표준 라이브러리 스크립트를, `korean-character-count`는 Node.js 스크립트를 쓴다.
- 스킬과 스크립트는 네트워크에 접속하지 않고, 입력한 학생 자료를 수집하거나 외부로 보내지 않는다.
- 파일을 쓰는 스크립트는 기재요령 원문 등록 도구(`update_guidelines.py`, 스킬 폴더 안 `references/guidelines*/`에 씀)와 정비용 NEIS 실측값 기록 도구(`compare_neis_counts.py`)다.
- `tools/corpus/`는 정비하는 사람이 성취수준 자료를 다시 만들 때 직접 실행하는 도구이며 스킬이 실행하지 않는다. 그 가운데 `convert_nkis_pdfs_v2.py`는 `npx`로 kordoc 패키지를 내려받아 실행한다.
- 문서 전용판에는 스크립트가 없다. 글자 수·Byte는 Claude의 코드 실행 도구가 스킬 문서에 적힌 몇 줄의 코드로 계산하며, 그 코드는 파일을 쓰거나 네트워크에 접속하지 않는다.
- 보안 문제 신고와 자세한 설명은 [SECURITY.md](SECURITY.md)를 따른다.

## 더 읽을 문서

| 문서 | 내용 |
|---|---|
| [USER_GUIDE.md](USER_GUIDE.md) | 실제로 어떻게 요청하고 쓰는지 |
| [docs/how-it-works.html](docs/how-it-works.html) | 이 도구가 왜 이렇게 판단하는지를 쉬운 말로 설명. 내려받아 브라우저로 연다 |
| [docs/dev-vs-package.md](docs/dev-vs-package.md) | 개발본·배포본(전체판)·문서 전용판의 의도된 차이 (기여자용) |
| [editions/korean-school-records-lite/README.md](editions/korean-school-records-lite/README.md) | 문서 전용판 안내(디렉터리 목록에 쓰이는 설명) |
