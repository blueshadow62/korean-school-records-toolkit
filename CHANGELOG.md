# Changelog

## 3.1.1 — 2026-11-19

### 바뀌는 점

- **개인정보 처리 안내(`PRIVACY.md`)를 넣었다.** 전체판과 문서 전용판에 각각 있다. 이 플러그인은 입력한 자료를 수집하거나 저장하거나 외부로 보내지 않는다. 제3자에게 제공하지 않으며 사용 기록이나 분석 정보도 모으지 않는다. 스킬은 학생 이름·학번·학교명 없이 쓰도록 만들어졌고, 입력한 내용은 사용하는 AI 서비스의 방침을 따른다. 문의 창구도 적었다. 전체판은 스킬이 실행하는 스크립트 네 개가 하는 일도 밝힌다(네트워크에 접속하지 않고, 파일을 쓰는 스크립트는 둘이다). Claude 플러그인 디렉터리에 제출할 때 개인정보처리방침을 알려야 해서 넣었다.
- **README의 설치 안내를 교사 눈높이로 보완했다.** 첫 소개 문단 바로 뒤에 '빠른 설치'를 두고, 「설치」 절에 어느 판을 고를지, 전체판에 필요한 것(Python 3, Node.js 18 이상), Claude Code 대화 창에서 설치하는 방법(터미널을 쓰지 않는 방법), 터미널에서 설치하는 방법, 설치 확인, 새 버전으로 올리기, 지우기를 적었다. 명령 형식은 Claude Code 공식 문서로 확인했다. 한 번에 설치하는 명령은 버전 조건이 있어 함께 적었다(대화 창 2.1.275 이상, 터미널 2.1.292 이상).
- **3.1.0에서 올릴 때 할 일은 없다.** 스킬의 판단 규칙과 참조 자료는 3.1.0과 같다. `claude plugin update korean-school-records-toolkit@blueshadow62-school-records`로 올리고(문서 전용판은 이름을 `korean-school-records-lite@blueshadow62-school-records`로 바꾼다) Claude Code를 다시 시작하면 적용된다. 기재요령 원문을 직접 등록해 썼다면, 업데이트가 스킬 폴더를 교체하므로 원문을 다시 등록한다.

### Added

- `PRIVACY.md`(전체판)와 `editions/korean-school-records-lite/PRIVACY.md`(문서 전용판, 재료는 `editions/source/PRIVACY.md`). 한국어 본문 뒤에 영어 요약을 붙였다. 문서 전용판의 근거는 파일 구성(실행 파일, 훅, 서버 설정이 없음)이고, 전체판의 근거는 스킬 스크립트 소스 검색이다. 두 문서의 공통 문장(수집·저장·전송 금지, 학생 정보 안내, Anthropic 개인정보처리방침 주소, 권고, 문의 창구)은 같은 문구다. Anthropic의 자료 취급은 서술하는 대신 방침 주소를 링크한다.
- 두 `plugin.json`에 `privacyPolicyUrl`을 적었다. 디렉터리가 목록에 쓰는 공식 항목이며(공식 manifest 참조), 각 판의 `PRIVACY.md`가 있는 GitHub 주소다. 마켓플레이스 항목에는 넣지 않는다(항목에 쓰면 알 수 없는 항목으로 경고한다). `claude plugin validate --strict`는 두 판 모두 경고 없이 통과한다.
- `scripts/build_directory_edition.py`가 `PRIVACY.md`를 문서 전용판 전용 파일로 받아들이고(재료 `editions/source/PRIVACY.md`) 문서 전용판 `plugin.json`의 `privacyPolicyUrl`을 만든다. `--check`는 그 주소가 자기 폴더의 `PRIVACY.md`를 가리키는지 본다. `verify_package.py`는 전체판의 `PRIVACY.md`와 `privacyPolicyUrl`을 본다.
- `tests/test_privacy_notice.py`(15건): 두 판의 `PRIVACY.md`가 공통 문장·영어 요약·문의 창구를 담고 README에서 링크되는지, 이메일 주소와 스크립트 이름·설치 명령이 없는지, 문서 전용판에 실행 수단이 없는지, `privacyPolicyUrl`이 맞는지 본다. `PRIVACY.md`가 보증하는 사실은 스킬 스크립트의 소스로 확인한다: 스킬이 실행하는 스크립트는 네 개이고, 네트워크·외부 프로그램·환경 변수를 쓰지 않으며, 파일을 쓰는 스크립트는 `update_guidelines.py`와 `compare_neis_counts.py` 둘이다. 소스를 정적으로 읽는 검사라 모든 우회를 막지는 못하고, 새 import나 쓰기 호출이 생기면 실패해 문서를 다시 확인하게 한다.
- `tests/test_install_guide.py`(6건): README의 설치 안내가 manifest·마켓플레이스·`edition.json`의 이름으로 만든 명령을 모두 담는지, 버전 조건이 해당 명령 앞에 있는지, 다른 설치 문서가 README 「설치」를 가리키는지, 문서 전용판 문서에 플러그인 설치 명령이 없는지 본다.

### Changed

- `README_CLAUDE_CODE.md`, `USER_GUIDE.md`, `INSTALL.md`의 설치 설명을 README 「설치」와 맞췄다. 사용 설명서가 설치를 `README_CLAUDE_CODE.md`로 안내하고 그 문서가 다시 README로 넘기던 순환을 없앴다.

## 3.1.0 — 2026-11-19

### 바뀌는 점

- **두 가지 판이 생겼다.** 같은 학생부 스킬을 전체판(`korean-school-records-toolkit`)과 문서 전용판(`korean-school-records-lite`, 한국어 학교생활기록부 도구 라이트)으로 제공한다. 근거 판단, 학교급 확인, 응답 형식은 두 판이 같다. 다른 것은 스크립트다. 전체판은 Python·Node.js 스크립트로 글자 수와 NEIS Byte를 계산하고 기재요령 원문 등록과 NEIS 실측 대조도 지원한다. 문서 전용판은 스크립트 없이 문서(Markdown·JSON)로 이루어져 있고, 글자 수는 Claude의 코드 실행 도구가 같은 방식으로 계산한다. 코드를 실행할 수 없는 환경에서는 숫자를 짐작해 적는 대신 계산하지 못했다고 밝힌다. 둘 가운데 하나를 고른다. 함께 설치하면 같은 스킬이 두 개 보인다. 차이는 README의 「두 가지 판」 표에 있다.
- **Claude Code에서 이 저장소를 마켓플레이스로 설치할 수 있다.** 전체판은 `claude plugin marketplace add blueshadow62/korean-school-records-toolkit`와 `claude plugin install korean-school-records-toolkit@blueshadow62-school-records` 두 줄로 설치한다. 문서 전용판은 같은 마켓플레이스의 `korean-school-records-lite@blueshadow62-school-records`로 설치하고, 전체판을 이미 설치했다면 먼저 제거한다. 문서 전용판은 Claude 플러그인 디렉터리에 등록할 예정이며, 등록되면 claude.ai·Cowork에서도 설치할 수 있다.
- **3.0.0에서 올릴 때 할 일은 거의 없다.** 판단 규칙, 기재요령 요약, 성취수준 자료는 3.0.0과 같다. 새로 들어가거나 바뀐 스킬 파일은 두 개다: 글자 수 스킬의 `LICENSE`(원 저작물의 라이선스 전문)와 `references/source-policy.md`(제3자 자료의 출처 기록). 플러그인을 업데이트하면 된다. 기재요령 원문을 직접 등록해 썼다면, 업데이트가 스킬 폴더를 교체하므로 등록한 원문이 새 설치본에 없다. 이때는 `USER_GUIDE.md` 「기재요령 원문을 직접 등록하기」대로 다시 등록한다.
- **전체판 설치본에는 `editions/` 폴더(문서 전용판의 사본, 약 8MB)도 들어 있다.** 전체판에서는 쓰이지 않는다. Claude Code가 읽는 것은 전체판의 `skills/` 두 스킬이다.

### Added

- 이 저장소를 Claude Code 마켓플레이스로도 쓸 수 있게 `.claude-plugin/marketplace.json`(이름 `blueshadow62-school-records`)을 추가했다. README에 설치 명령 두 줄(`claude plugin marketplace add …`, `claude plugin install korean-school-records-toolkit@blueshadow62-school-records`)을 적었다.
- `SECURITY.md`: 보안 문제를 GitHub Issues로 신고하는 방법(민감한 내용은 공개 이슈에 쓰지 않고 비공개 전달 방법을 요청)과, 스킬이 네트워크에 접속하지 않고 입력 자료를 수집·전송하지 않는다는 사실, 파일을 쓰는 스크립트와 정비용 도구가 하는 일을 적었다.
- `skills/korean-character-count/LICENSE`: 이 스킬의 원 저작물(`NomaDamas/k-skill`의 `korean-character-count`)과 그 저장소의 MIT 라이선스 전문을 바꾸지 않고 실었고, 이 배포본에서 바꾼 내용(NEIS 줄바꿈 1Byte 등)을 적었다. 원 저장소의 저작권 표시에는 저작권자 이름이 없어 그대로 두었다.
- README에 '실행하는 것과 외부 연결' 절을 추가했다.
- `verify_package.py`와 `tests/test_package.py`가 마켓플레이스 파일(소유자 이름이 `plugin.json` 작성자와 같은지), `plugin.json`의 `homepage`·`repository`, 글자 수 스킬의 MIT 표시, `SECURITY.md`, README·USER_GUIDE의 AI 사용 안내를 검사한다.
- **문서 전용판 `korean-school-records-lite`(한국어 학교생활기록부 도구 라이트)**: Claude 플러그인 디렉터리 제출용 판을 `editions/korean-school-records-lite/`에 두었다. 디렉터리는 인증된 조직이 아닌 계정의 플러그인에서 Markdown·텍스트·JSON·YAML과 일부 그림 파일만 받으므로, 스크립트 없이 `write-school-records` 스킬 문서와 참고 자료(성취수준 자료, 기재요령 요약, 영역 안내)만 담았다. claude.ai·Cowork·Claude Code에서 쓴다. 전체판의 위치와 동작은 바뀌지 않는다.
  - 근거 판단, 공통 게이트, 학교급 확인, 라우팅, 응답 형식은 전체판과 같다. 스크립트에 관한 부분만 다르다: 글자 수·바이트는 코드 실행 도구로 `analyze_record.py`와 같은 방식(CRLF → LF, 앞뒤 공백 제거, 코드 포인트 수, UTF-8 길이)으로 계산하고, 실행할 수 없으면 짐작한 값을 적지 않고 `글자 수는 기계로 점검하지 못했습니다.`라고 밝힌다. 금지 표현은 요약의 공통 금지 절을 기준으로 직접 점검한다. 기재요령 원문 등록, NEIS 실측 대조, 스킬 행동 검증은 지원하지 않는다고 안내한다.
  - 넣지 않은 것: 스크립트, 시험 자료와 평가 사례, Codex 설정, 글자 수 계산 스킬, 검사 규칙 JSON(`analyzer-rules/`, 정규식이라 모델이 읽고 흉내 내면 정확하지 않다), 원문 색인 검색어(`index-terms.json`).
- `scripts/build_directory_edition.py`: 전체판에서 문서 전용판을 만든다. 허용된 문서만 옮기고 `editions/source/changes.md`의 문구만 바꿔 끼우며, 바꿔 끼우는 문구가 전체판에서 바뀌었거나 규칙이 정해지지 않은 파일이 생기면 멈춘다. `--check`는 커밋된 폴더가 빌드 결과와 같은지와 디렉터리 파일 규칙(파일 종류·크기·개수, `#!`, UTF-8·NUL, 패키지 관리자 설정, 설치·실행 명령, 환경 변수 표현, 링크, 아이콘, `plugin.json`)을 본다.
- `tests/test_directory_edition.py`(31건): 위 일치와 규칙, 규칙 검사가 실제로 문제를 잡는지, SKILL.md가 스크립트에 관한 부분만 다른지, 계산 방식이 점검기와 같은지, 문서 전용판의 README·LICENSE·`plugin.json`·마켓플레이스 항목, 두 판의 아이콘을 검사한다. `tests/test_dev_package_sync.py`는 문서 전용판의 문서가 바꿔 끼운 파일을 빼면 개발본과 같은지 본다. CI에 `build_directory_edition.py --check` 단계를 더했다.
- 두 판의 `.claude-plugin/icon.png`에 같은 아이콘(1024×1024 PNG)을 넣었다. 전체판 루트의 파일이 원본이고 `build_directory_edition.py`가 문서 전용판으로 바이트 그대로 옮긴다. `--check`·`verify_package.py`·`tests/test_directory_edition.py`가 두 판의 아이콘이 있고 서로 같은지, 정사각 PNG이며 한 변이 512~2048픽셀이고 2MiB 미만인지 본다. 기본 위치라 `plugin.json`에 `icon`을 쓰지 않으며, `claude plugin validate`의 `ICON_MISSING` 경고가 사라졌다(이 명령은 아이콘이 있는지는 보지만 크기는 보지 않는다). 디렉터리의 목록 아이콘은 개발자 포털에서 처음 저장·제출할 때 정해지고, 나중에 파일을 바꿔도 달라지지 않는다.

### Changed

- 작성자 표기를 'Local education tooling team'에서 GitHub 계정명 `blueshadow62`(주소 `https://github.com/blueshadow62`)로 바꿨다: 두 `plugin.json`의 `author`, Codex `interface.developerName`, `marketplace.json`의 `owner`.
- README 첫 소개 문단에 지원 영역(세특·창체·행특·중학교 자유학기활동), 규정 판단의 기준(이 도구가 정리한 2026학년도 기재요령 요약, 공식 효력은 원문), 참고하는 성취수준(2022 개정 중·고등학교)을 적어 GitHub 저장소 설명과 맞췄다.
- `.claude-plugin/marketplace.json`에 문서 전용판을 두 번째 항목(`source`: `./editions/korean-school-records-lite`)으로 넣고, 두 항목의 `description`으로 전체판과 문서 전용판을 구분했다. 전체판을 설치하면 `editions/` 폴더의 사본도 함께 내려받지만 Claude Code는 전체판의 `skills/` 두 스킬만 읽는다(로컬 마켓플레이스 설치로 확인). `verify_package.py`가 두 항목과 문서 전용판을 확인하고, 한국어 오류 문장이 Windows 기본 로캘에서도 출력되도록 표준 출력을 UTF-8로 맞췄다.
- README에 「두 가지 판」 절(차이 표와 각 판의 설치 방법)을, USER_GUIDE·INSTALL·`docs/how-it-works.html`·`docs/dev-vs-package.md`에 문서 전용판 안내를 넣었다. `README_CLAUDE_CODE.md`의 '마켓플레이스 등록을 포함하지 않는다'는 문장이 마켓플레이스 파일을 넣은 뒤로 맞지 않아 고쳤다.
- `.claude-plugin/plugin.json`에 `homepage`(GitHub Pages 문서)와 `repository`(GitHub 저장소)를 넣었다.
- 루트 `LICENSE`가 중학교 성취수준 자료(NCIC, 공공누리 제2유형), 글자 수 스킬의 원 저작물, 기재요령 원문의 게시 주소, 제3자 자료를 바탕으로 쓴 참조 파일(`holistic-evaluation.md`, `major-*.md`)을 함께 밝힌다. `SOURCE_METADATA.json`에 글자 수 스킬의 원 저장소와 라이선스를 적었다.
- `references/source-policy.md`에 제3자 자료를 바탕으로 쓴 파일의 원자료, 옮긴 정도(원자료와 문장 대조 결과), 이용 조건 확인 상태를 적었다.
- README와 USER_GUIDE의 AI 활용 안내를 보완했다: 출력은 교사가 사실과 규정을 대조하기 전의 보조 초안이고, 기재요령은 AI 생성 자료를 그대로 입력하지 않도록 하며, 학교·교육청의 AI 활용 지침과 학생·보호자 고지 의무를 확인하라는 내용이다. USER_GUIDE 라이선스 표의 글자 수 스킬 저작권 표기를 원 저장소 기준으로 고쳤다.

## 3.0.0 — 2026-11-19

### 바뀌는 점

- **기재요령 원문이 빠지고 요약으로 동작한다.** 플러그인에 들어 있던 교육부 기재요령 원문 변환본(고등학교판·중학교판)을 뺐다. 쓸 수 있는 것과 없는 것, 쓰는 사람, 분량 한도는 이 도구가 원문을 바탕으로 정리한 핵심 규정 요약으로 판단한다. 답변과 글자 수 점검 결과에는 `이 도구가 정리한 요약 기준(교육부 2026학년도 학교생활기록부 기재요령(고등학교), 2026년 2월 12일 개정판 바탕, 원문과 직접 대조하지 않음)`처럼 무엇을 근거로 했는지가 적힌다. 요약에 없는 세부 규정은 지어내지 않고 원문의 해당 장을 안내한다. 공식 효력은 교육부 원문에 있다.
- **원문 문구까지 대조하려면** 교육부 게시물의 PDF를 Markdown으로 바꿔 직접 등록할 수 있다. 방법은 `USER_GUIDE.md` 「기재요령 원문을 직접 등록하기」에 있다. 등록하지 않아도 모든 기능을 쓸 수 있다.
- **봉사활동 점검이 바뀌었다.** `analyze_record.py --area service`는 3학년 봉사활동을 '특기사항 500자/1,500Byte'로 세던 것을, 봉사활동 실적 한 건의 활동내용 '50자/150Byte'로 센다. 기재요령은 3학년 봉사활동 영역에 특기사항 없이 실적만 입력하게 한다.
- **2.2.0에서 올릴 때 할 일**
  - 대부분은 플러그인을 업데이트(다시 설치)하는 것으로 끝난다.
  - 2.2.0 설치본의 원문 파일(`current.md` 등)을 직접 읽거나 고쳐 쓰던 경우, 새 설치본에는 그 파일이 없다. 필요하면 위 방법으로 원문을 등록한다. 업데이트하면 스킬 폴더가 교체되므로 전에 등록하거나 고친 원문도 다시 등록해야 한다.
  - `analyze_record.py`의 결과를 다른 프로그램이 읽는 경우: 원문이 없으면 JSON의 `guideline.basis`가 `summary`, `active_version`이 `null`이고 `basis_note`에 기준 메모가 들어간다. `--area service`의 한도 값도 위처럼 바뀐다.
  - `update_guidelines.py list`·`verify`는 원문이 없으면 오류 대신 '등록된 원문 없음'과 요약 기준 동작을 안내한다.

### Removed

- 배포본에서 교육부 기재요령 원문 변환본을 뺐다: `references/guidelines/`와 `references/guidelines-middle/`의 `current.md`, `current.index.md`, `manifest.json`, `versions/2026_2026-02-12.md`(8개 파일, 약 2.4MB). 원문은 공공누리 제4유형(출처표시·상업적 이용금지·변경금지)인데 변환본은 표를 다시 짜고 그림 링크를 지운 것이어서 권리 해석에 확인되지 않은 부분이 있었고, 변환본 하나하나가 플러그인 디렉터리 심사의 파일 크기 검토 기준(256KiB)을 넘었다. 또 스킬은 초안을 쓸 때 원문보다 직접 쓴 규정 요약을 주로 쓰고 있었다. 원문 변환본은 개발본에만 둔다.

### Fixed

- `analyze_record.py --area service`가 3학년 봉사활동을 '특기사항 500자/1,500Byte'로 점검하던 문제 수정. 기재요령은 3학년 봉사활동 영역에 실적만 입력하게 하고(훈령 제433호 제13조②), 최대 글자수 표에도 봉사활동 특기사항 칸이 없다. 이제 실적 한 건의 활동내용(50자/150Byte)으로 세고, 1·2학년이면 봉사활동이 각 영역과 연계해 운영된다고 알린다. 고·중 검사 규칙에서 원문에 없는 `service` 특기사항 한도를 지웠고, SKILL.md 「지원 영역」의 '3학년 봉사 포함, 영역별 500자' 표현도 고쳤다.
- `guidelines-middle/differences.md`가 최대 글자수를 모든 항목에 학년 단위로 적용하는 것처럼 쓰고, 영재·발명교육 기록 방식이 두 판에서 같다고 쓰던 문제 수정. 학년 단위는 표에 별표가 붙은 창체·독서·행특이고, 발명교육은 중학교판에서 관련 교과 세특 본문에 쓴다.
- 고등학교 `references/guidelines/ATTRIBUTION.md`의 원문 등록 명령이 실제 인자(`--input`, `--source-title` 필수)와 다르던 문제 수정.
- 기재요령 요약에 기록 여부·위치를 가르는 조건이 빠져 교사가 틀린 기록을 쓸 수 있던 문제 수정(독립 검증 결과 반영). 고등학교: 1·2학년 미이수 과목의 세특 미기재와 3학년 공동교육과정 미이수 학생의 기재 제외(4-6), 학교 밖 교육기관 유형 가운데 지역사회기관(공공성을 가진 기관)과 기업(특성화고·산업수요 맞춤형 고교·일반고 직업계열 학과 운영교)의 제한(2-12), 현장실습의 운영 형태별 입력 위치와 과목 세특 필수 네 항목(4-20, 신규), 현장체험학습 미참여 학생의 별도 창체 활동(5-8). 두 학교급: 순회교육·위탁교육기관·병원학교·원격수업기관의 활동 자료를 쓰는 예외(창체, 중학교 자유학기 포함), 발명교육은 수료증이 발급되는 발명교육센터 과정만 인정하고 학교 자체 과정은 제외, 단순 독후활동 외의 독서 관련 교육활동을 도서명과 함께 다른 영역에 쓰는 조건(신규, 중학교는 자유학기활동상황 포함), 학교 밖에서 조직된 스포츠클럽 불인정과 학교장 승인 실적만 인정, 임원 재임기간의 날짜 기준, 위탁학생의 성적 미산출 과목은 세특에 이수 내용만 쓰는 규칙(신규), 물품·현금 단순 기부는 어느 항목에도 쓰지 않는 규칙(신규).
- 1-9의 내부 참조 오류를 고치고(세 행위는 1-6, 1-7, 1-9), 원문 해설 구절을 그대로 옮긴 문장(고 4-2, 중 4-3)을 다시 썼다. 공식 기재예시는 '기재요령의 예시 문구'로 표시했다.
- 기재요령의 권장·유의 조항과 이 스킬이 더 보수적으로 정한 원칙이 섞여 있던 문제 수정. SKILL.md 「현행 공통 준수 게이트」의 항목마다 근거를 `기재요령 n-m`(요약 규칙 번호)과 `스킬 원칙`으로 표시했다. 행특의 부정적 행동 누가기록은 기재요령에서 권장 사항이라고 밝히고, 관찰 기록이 있을 때만 쓰는 것은 스킬 원칙으로 나눴다(`field-behavior.md`). `guidelines-middle/differences.md` 1절은 생성형 AI 조항을 기재 금지 목록에서 떼어 기본 원칙으로 옮겼다(보조 수단 사용 자체는 금지하지 않고, 그대로 입력하지 않도록 유의하며 최종 입력 전에 철저히 확인).
- 영역 안내 문서(`field-creative.md`, `field-free-semester.md`, 교과 안내 세 파일)의 규정 게이트가 위 조건을 담고 요약 규칙 번호를 가리키게 했다. `differences.md`에 새 규칙의 학교급 차이를 더했다.
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
- `scripts/test_guideline_summary.py`: 요약을 검사 규칙과 언제나 대조하고, 원문이 등록된 환경(개발본)에서는 최대 글자수 표의 모든 행, 인용 조문, 장 제목, 금지 항목 이름을 원문과 대조한다. 기록 여부를 가르는 조건 문구(미이수, 기관 유형 제한, 수료증 과정, 현장실습, 독서, 위탁, 기관 자료 예외, 재임기간, 스포츠클럽, 기부)가 해당 규칙 줄에 있는지 언제나 검사하고, 원문이 등록되었으면 그 조건이 원문에도 있는지 본다. 영역 안내 문서가 가리키는 규칙 번호가 요약에 있는지, 기재요령 조항과 스킬 원칙이 구분되어 있는지도 검사한다.
- 사용자 설명서에 「기재요령 원문을 직접 등록하기」 절 추가: 교육부 PDF를 kordoc 등으로 Markdown으로 바꾸는 방법, 변환에서 쪽이 빠졌는지 확인할 점, 등록·검증 명령, 재설치 때 등록한 원문이 새 설치본에 없다는 점.
- `docs/guideline-summary-updates.md`: 새 학년도 기재요령이 나왔을 때 누가, 무엇을 보고, 어떤 테스트로 요약을 갱신하는지.
- `verify_package.py`와 `tests/test_package.py`가 배포본에 원문 변환본이 없는지, 요약 머리말과 그 학년도의 검사 규칙이 있는지, 원문 없이 점검기와 `update_guidelines.py verify`가 요약 기준으로 동작하는지 검사한다. `.gitignore`가 사용자가 등록한 원문 파일을 제외한다.
- push와 pull request 때 Ubuntu·Windows에서 unittest, node 테스트, `verify_package.py`를 실행하는 GitHub Actions 작업 흐름(`.github/workflows/tests.yml`) 추가. Windows는 `PYTHONUTF8`과 `core.autocrlf`를 러너 기본값 그대로 두고 실행한다.
- 교과 안내 세 파일(`subject-humanities.md`, `subject-stem.md`, `subject-practical-arts.md`)에 '중학교 차이' 절 추가. 고등학교 기준인 세특 규정 게이트에서 중학교에서 뒤집히는 항목(입력 대상, 합산·학기별 한도, 소논문 예외, 능력단위)만 적고 `guidelines-middle/differences.md` 2절을 가리킨다.

### Changed

- 기재요령 판단의 기준을 원문 변환본에서 학교급별 요약으로 바꿨다. 사용자에게 달라지는 점: 규정 판단과 분량 기준은 요약으로 하며, 답변의 기준 줄에 `이 도구가 정리한 요약 기준(교육부 … 개정판 바탕, 원문과 직접 대조하지 않음)`을 적고, 원문을 실제로 읽어 대조했을 때만 `… 개정 원문과 대조함`이라고 쓴다. 요약에 없는 세부 규정(예: 독서활동상황의 기재 방법)은 지어내지 않고 원문의 해당 장을 안내한다. `analyze_record.py`는 원문이 등록되지 않았으면 요약 머리말의 학년도로 검사 규칙을 고르고, 출력에 같은 뜻의 기준 줄(바탕이 된 기재요령의 학년도·학교급·개정일 포함)을 적는다(JSON은 `guideline.basis`가 `summary`, `active_version`이 `null`, `basis_note`에 기준 메모). 원문을 등록했으면 지금처럼 활성 버전과 해시를 검증하고, 해시가 틀리면 오류다. `update_guidelines.py list`·`verify`는 원문이 없는 상태를 오류 대신 요약 기준 동작으로 안내한다.
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
