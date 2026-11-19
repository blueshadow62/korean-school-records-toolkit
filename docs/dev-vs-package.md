# 개발본과 배포본의 의도된 차이

이 프로젝트의 스킬은 세 위치에 존재한다. 내용은 개발본 → 배포본(전체판) → 문서 전용판의 순서로 흐른다.

| 경로 | 역할 |
| --- | --- |
| `skills/write-school-records/` | 저장소 밖의 개발본. 스킬의 원본이며 개발·검증과 설치 동기화에 사용한다. |
| `plugins/korean-school-records-toolkit/skills/write-school-records/` | Git으로 추적되는 배포본. 전체판 플러그인(`korean-school-records-toolkit`)에 포함되어 사용자에게 설치된다. |
| `plugins/korean-school-records-toolkit/editions/<이름>/` | 배포본에서 `scripts/build_directory_edition.py`로 만든 문서 전용판 플러그인. 스크립트가 없어 Claude 플러그인 디렉터리에 제출한다. 직접 고치지 않는다. 아래 「전체판과 문서 전용판의 의도된 차이」를 따른다. |

개발본과 배포본은 아래 차이를 제외하면 동일하게 유지한다.

## 의도된 차이

1. 개발본의 `SKILL.md`에는 `korean-spell-check` 연계가 있다. 15행의 맞춤법 점검 항목, `## 최종 검수 연계`의 3~5단계, 마지막의 `$korean-spell-check` 호출 예시가 이에 해당한다. 개발 환경에서는 해당 스킬을 함께 사용할 수 있으므로 최종 검수 선택지를 제공한다.
2. 배포본의 `SKILL.md`에는 위 연계를 포함하지 않는다. 배포 패키지에는 `korean-character-count`와 `write-school-records`만 포함되며, `korean-spell-check`는 포함되지 않기 때문이다.
3. 개발본의 `scripts/`에는 `sync_install.py`와 `test_sync_install.py`가 추가로 있다. 개발·설치 동기화용 파일이며 배포 패키지에는 필요하지 않다.
4. 개발본의 `scripts/`에는 `trim_achievement_examples.py`가 추가로 있다. 성취수준 코퍼스에서 예시 평가 도구 구간을 잘라내는 정비 도구이며, 스킬 실행 중에는 쓰이지 않는다. 같은 계열의 코퍼스 재현 도구는 저장소의 `tools/corpus/`에 있다.
5. 두 트리의 `scripts/test_skill_integration.py`가 다르다. 이 테스트가 각 트리의 `SKILL.md`를 검사하기 때문이며, 1·2번 차이의 직접적인 결과다. 개발본은 `korean-spell-check` 연계와 맞춤법·재계산 순서를 검증하고, 배포본은 연계 없이 `analyze_record.py`로 최종 확인하는 흐름을 검증한다. 한쪽 `SKILL.md`를 고치면 같은 트리의 이 테스트도 함께 고쳐야 한다.
6. 개발본에는 `references/writing-examples/`와 `scripts/test_writing_examples.py`, `references/university-guides/`와 `scripts/test_university_guides.py`가 추가로 있다. 세특 문체 참고 예시와 대학 학과 안내 원문으로, 원본에서 재배포를 허용하는 이용 조건을 확인하지 못해 로컬에서만 쓰고 배포 패키지에 넣지 않는다. 그래서 개발본 `SKILL.md`에 이 자료를 부르는 줄과 규칙이 더 있다.
7. 개발본에는 기재요령 원문 변환본과 그 색인·등록 기록이 추가로 있다: `references/guidelines/`와 `references/guidelines-middle/`의 `current.md`, `current.index.md`, `manifest.json`, `versions/*.md`. 원문이 공공누리 제4유형(출처표시·상업적 이용금지·변경금지)이고 변환본은 표를 다시 짜고 그림 링크를 지운 것이어서 배포 패키지에 넣지 않는다. 배포본은 같은 폴더의 `summary.md`(이 스킬이 쓴 핵심 규정 요약)로 동작하며, 원문 문구가 필요한 사용자는 교육부 원문을 Markdown으로 바꿔 `scripts/update_guidelines.py import`로 직접 등록한다. 개발본의 원문은 요약을 원문과 대조하는 테스트(`scripts/test_guideline_summary.py`의 원문 대조 묶음, `test_guidelines_high.py`·`test_guidelines_middle.py`의 원문 검사)에 쓰이며, 배포본에서는 이 테스트들이 건너뛰어진다. 배포본 `.gitignore`가 이 파일들을 제외하고, `scripts/verify_package.py`와 `tests/test_package.py`가 배포본에 원문이 없는지 검사한다. `tests/test_dev_package_sync.py`는 이 파일들을 경로 형식으로 가려 개발본에만 있는 파일로 허용한다.

## 의도되지 않은 차이 확인

두 트리를 비교할 때는 다음 명령을 사용한다. 이 환경에 `diff`가 없으면 같은 비교를 `git diff --no-index --quiet --`로 수행할 수 있다.

```sh
diff -rq skills/write-school-records plugins/korean-school-records-toolkit/skills/write-school-records
```

`__pycache__` 경로는 비교 결과에서 무시한다. 그 밖의 차이는 먼저 이 문서의 의도된 차이인지 확인하고, 해당하지 않으면 드리프트로 조사한다.

## 전체판과 문서 전용판의 의도된 차이

문서 전용판은 Claude 플러그인 디렉터리 제출용이다. 디렉터리는 인증된 조직이 아닌 계정의 플러그인에서 Markdown·텍스트·JSON·YAML과 일부 그림 파일만 받으므로(2026-11-19 개발자 포털 검사 메시지), 스크립트 없이 문서만 담는다. 플러그인 이름과 표시 이름은 `editions/source/edition.json`에 있고, 폴더는 `editions/<이름>/`이다.

1. 넣지 않는 것: 스킬의 `scripts/`, `tests/`, `agents/openai.yaml`(Codex 전용), 기재요령 폴더의 `analyzer-rules/`(점검 스크립트의 검사 규칙)와 `index-terms.json`(원문 등록 도구의 색인 검색어), `korean-character-count` 스킬, 전체판 루트의 `VERSION`·`.codex-plugin/`·`scripts/`·`tests/`·`tools/`·`docs/` 등. 검사 규칙은 정규식이라 모델이 읽고 흉내 내면 정확하지 않으므로 참조 자료로도 두지 않고, 금지 표현은 요약의 공통 금지 절을 기준으로 모델이 직접 점검한다.
2. 바꿔 끼우는 것: `editions/source/changes.md`의 목록대로 `SKILL.md`, `references/output-skeleton.md`, `references/field-free-semester.md`, `references/source-policy.md`, `references/guidelines/ATTRIBUTION.md`, `references/guidelines-middle/ATTRIBUTION.md`, 루트 `LICENSE`의 정해진 문구만 바꾼다. 스킬 문서에서 바꾸는 곳은 스크립트·시험 자료·원문 등록에 관한 부분이다. 글자 수·바이트는 코드 실행 도구로 계산하게 하며(계산 방식은 `analyze_record.py`의 `normalize_text`와 같다), 코드를 실행할 수 없으면 계산하지 못했다고 밝히게 한다. 원문 등록, NEIS 실측 대조, 스킬 행동 검증은 지원하지 않는다고 안내하게 한다.
3. 문서 전용판에만 있는 것: `README.md`, `SECURITY.md`(원본은 `editions/source/`), `.claude-plugin/plugin.json`(이름·표시 이름·설명은 `edition.json`에서, 버전은 `VERSION`에서, 작성자·주소·라이선스는 전체판 `plugin.json`에서 가져온다).
4. 그 밖의 참조 문서(성취수준 자료, 기재요령 요약, 영역 안내 등)는 배포본과 같은 파일이다. 줄바꿈은 LF로 쓴다.
5. 아이콘 `.claude-plugin/icon.png`는 두 판이 같은 파일이다. 전체판 루트의 파일이 원본이고, 빌드가 문서 전용판으로 바이트 그대로 옮긴다(`editions/source/`에는 두지 않는다). 디렉터리 기준은 정사각 PNG, 한 변 512~2048픽셀, 2MB 미만이다. 이 기본 위치에 있으면 `plugin.json`에 `icon`을 쓰지 않아도 디렉터리 검사가 찾는다. 그림을 바꾸려면 전체판 루트의 파일을 바꾸고 문서 전용판을 다시 만든다.

전체판을 고친 뒤에는 문서 전용판을 다시 만든다. 커밋된 폴더가 빌드 결과와 다르면 `tests/test_directory_edition.py`, `scripts/verify_package.py`, CI의 `--check` 단계가 실패한다. 전체판에서 바꿔 끼우는 문구가 바뀌면 빌드가 멈추므로 `changes.md`도 함께 고친다.

```sh
python scripts/build_directory_edition.py          # editions/<이름>/을 다시 만든다
python scripts/build_directory_edition.py --check  # 빌드 결과와 같은지, 디렉터리 파일 규칙에 맞는지만 본다
```

`tests/test_directory_edition.py`는 빌드 결과와의 일치, 파일 종류·크기·개수, `#!` 파일, UTF-8과 NUL, 패키지 관리자 설정 파일, 다른 `.claude-plugin` 폴더, Windows·macOS에서 유지되지 않는 이름, README 낱말 수, 설치·실행 명령과 스크립트 이름, 환경 변수·자격 증명 표현, 상대 링크, `plugin.json`, 아이콘(두 판이 같은 파일인지, 정사각 PNG·한 변 512~2048픽셀·2MiB 미만인지), 마켓플레이스 항목을 검사한다. `claude plugin validate`는 아이콘이 있는지는 보지만 크기는 보지 않으므로 이 검사가 필요하다. SKILL.md가 전체판과 스크립트에 관한 부분만 다른지(공통 게이트·학교급 확인·작성 절차·서술 구조·품질 게이트 절은 같은지)도 검사한다. `tests/test_dev_package_sync.py`는 문서 전용판의 문서가 바꿔 끼운 파일을 빼면 개발본과 같은지 본다.
