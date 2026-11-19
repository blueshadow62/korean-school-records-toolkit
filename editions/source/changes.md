# 문서 전용판에서 바꿔 끼우는 문구

`scripts/build_directory_edition.py`가 전체판의 파일을 문서 전용판으로 옮길 때 이 목록의 문구만 바꾼다. 나머지 내용은 전체판과 같다.

- `find` 블록의 문구는 전체판 파일에 정확히 한 번 나와야 한다. 없거나 두 번 이상 나오면 빌드가 멈춘다. 전체판 문구를 고치면 이 파일의 `find`도 함께 고친다.
- 블록 머리의 경로는 저장소(전체판) 루트 기준이며, 문서 전용판에서도 같은 상대 경로에 쓴다.
- SKILL.md와 참조 문서에서 바꾸는 곳은 스크립트·시험 자료·원문 등록에 관한 부분으로 한정한다. `tests/test_directory_edition.py`가 이를 검사한다.
- 블록은 네 개의 역따옴표로 연다. `find <경로>` 블록 바로 뒤에 `replace` 블록을 둔다.

## SKILL.md

### 설명(description): 원문 등록 요청을 호출 조건에서 뺀다

이 판에는 원문 등록 도구가 없다.

````find skills/write-school-records/SKILL.md
"학생부 금지사항·분량 점검", "새 학년도 기재요령 등록·활성화·롤백" 요청에 사용한다.
````

````replace
"학생부 금지사항·분량 점검" 요청에 사용한다.
````

### 빠른 경로 5번: 원문 등록 환경 안내

````find skills/write-school-records/SKILL.md
원문 변환본을 등록해 `scripts/update_guidelines.py verify`가 통과하는 환경에서는 문구 확인이 필요할 때 같은 폴더의 `current.index.md`로 원문 범위를 찾아 읽을 수 있다.
````

````replace
이 판에는 원문 변환본이 없고 원문을 등록하는 도구도 없다. 그래서 이 문서와 참조 파일에서 원문이 등록된 경우를 가정한 안내는 적용하지 않고 언제나 요약을 기준으로 판단한다.
````

### 빠른 경로 7번: 스크립트 실행

````find skills/write-school-records/SKILL.md
7. 스크립트는 생성 후 기계 점검 또는 기재요령 등록·목록·활성화·검증·롤백이 필요할 때만 실행한다. 생기부 최종본의 글자 수·바이트는 `scripts/analyze_record.py`를 단일 진입점으로 사용한다.
````

````replace
7. 이 판에는 실행할 스크립트가 없다. 글자 수·바이트는 아래 「글자 수와 바이트 계산」대로 코드 실행 도구로 계산하고, 금지 표현은 「금지 표현 점검」대로 요약을 기준으로 직접 점검한다. 기재요령 원문 등록·갱신, 실제 나이스 입력값 대조, 스킬 행동 검증은 이 판에서 지원하지 않는다(「이 판에서 지원하지 않는 기능」).
````

### 라우팅 표: 스킬 행동 검증 행

평가 사례(`tests/eval-cases/`)는 이 판에 넣지 않는다.

````find skills/write-school-records/SKILL.md
| 스킬 행동 검증(합성 케이스·채점 절차) | [tests/eval-cases/README.md](tests/eval-cases/README.md) |
````

````replace
| 스킬 행동 검증(합성 케이스·채점 절차) | 이 판에서는 지원하지 않는다. 「이 판에서 지원하지 않는 기능」대로 안내한다 |
````

### 지원 영역: 기재요령 원문 등록·갱신

````find skills/write-school-records/SKILL.md
기재요령 갱신 요청은 `scripts/update_guidelines.py`로 처리한다. 새 원문은 `import`, 버전 전환은 `activate`, 이전 버전 복귀는 같은 `activate --version`으로 수행하고, 작업 전후 `verify`를 실행한다. 중학교판은 모든 명령에 `--level middle`을 붙이며 고등학교판과 따로 관리된다. 공식 확인이 없는 원문은 기본적으로 활성화하지 않으며 결과에 `[확인 필요]`를 남긴다. 배포본에는 원문 변환본이 들어 있지 않아 요약 기준으로 동작한다. 원문 문구가 필요한 사용자는 교육부 PDF를 Markdown(.md)으로 바꿔 `import`로 등록할 수 있다(절차는 플러그인의 `USER_GUIDE.md`). 새 학년도 원문을 등록해도 요약과 검사 규칙은 자동으로 바뀌지 않는다.
````

````replace
기재요령 원문 등록·활성화·롤백 요청은 이 판에서 지원하지 않는다. 이 판은 원문 변환본 없이 학교급별 요약으로 동작하며, 요청을 받으면 「이 판에서 지원하지 않는 기능」대로 안내한다.
````

### 출력과 점검: 기계 점검과 나이스 실측 대조

점검 스크립트 대신 코드 실행 도구로 계산하는 방법, 요약을 기준으로 금지 표현을 직접 점검하는 방법, 지원하지 않는 기능의 안내를 넣는다. 계산 방식은 전체판 `analyze_record.py`의 `normalize_text`와 글자 수·바이트 계산(`len`, UTF-8 길이)과 같다.

````find skills/write-school-records/SKILL.md
초안 생성 뒤에만 기계 점검이 유용한지 판단한다.

```bash
python scripts/analyze_record.py --file draft.txt --field subject --target-chars 500
```

중학교 기록은 `--school-level middle`을 붙여 중학교 기재요령과 한도로 점검하고, 자유학기활동은 `--field free_semester`로 점검한다. 학년·과목 유형·창체 영역이 확인되면 `--grade`, `--subject-type common|elective|vocational`(공통·전공실무는 고등학교만), `--area autonomy|club|career`(봉사활동 실적의 활동내용은 `service`, 실적별 50자)를 붙여 해당 한도로 점검하고, 공통과목 1·2 합산은 `--combine-with`, 10명 이상 배치의 반복률은 `--batch draft.tsv`로 확인한다. 출력은 등록된 원문(없으면 요약)과 검사 규칙의 학년도가 일치할 때만 제공하는 보조 신호이며, 원문이 없으면 '원문 미등록, 요약 기준'으로 표시된다. 최종 준수 판정은 교사가 원자료·학교 규정과 대조해 수행한다.

실제 NEIS 입력값 대조가 필요하면 기재요령상 실제 입력 가능한 문자로 만든 `tests/neis-validation` 합성 표본과 `scripts/compare_neis_counts.py`를 사용한다. 실제값이 충분히 수집되기 전에는 계산 계약을 확정하지 않으며, 검증되지 않은 계산값은 참고값으로 표시한다. NEIS 검증에는 실제 학생 기록을 사용하지 않고, 이모지·분해형 자모 같은 일반 Unicode 경계 사례는 생기부 계산 계약에서 제외한다.
````

````replace
### 글자 수와 바이트 계산

이 판에는 글자 수를 세는 스크립트가 없다. 글자 수와 바이트는 눈대중으로 세지 않고 코드 실행 도구로 계산한다. 초안·첨삭 응답의 「분량」 줄에는 이렇게 계산한 값만 적는다.

1. 계산 대상은 나이스에 입력할 초안 본문이다. 라벨(`[세특 초안]` 등), 제목, 표, 안내 문장, 분량 줄은 넣지 않는다. 본문이 여러 단락이면 단락 사이의 줄바꿈도 넣는다. 엑셀·표 일괄 작업은 행마다 따로 센다.
2. 계산 방식은 전체판 점검기와 같다. 줄바꿈을 LF로 통일하고(CRLF → LF) 앞뒤 공백을 걷어낸 뒤, 글자 수는 유니코드 문자(코드 포인트) 수, 바이트는 UTF-8로 인코딩한 길이로 센다. 이렇게 세면 한글 1자는 3Byte, 영문·숫자·공백 1자는 1Byte, 줄바꿈 하나는 1Byte다.

   ```python
   text = r"""여기에 초안 본문을 넣는다"""
   t = text.replace("\r\n", "\n").strip()
   print(len(t), len(t.encode("utf-8")))
   ```

   다른 언어로 계산해도 같은 규칙을 쓴다. JavaScript 문자열의 `length`는 코드 포인트 수가 아니므로 쓰지 않는다.
3. 한도는 학교급에 맞는 요약의 「영역별 입력 가능 최대 글자수」 표에서 찾는다. 고등학교 공통과목 1·2 합산 한도는 두 과목 본문의 바이트를 더해 비교한다.
4. 바이트 계산값은 기재요령의 바이트 규칙을 따른 참고값이다. 실제 나이스 입력값과의 대조가 끝나지 않았으므로 참고값으로 표시한다.
5. 코드 실행 도구를 쓸 수 없거나 실행에 실패하면 값을 짐작해 적지 않는다. 「분량」 줄에 `글자 수는 기계로 점검하지 못했습니다.`라고 적고, 한도만 적으며, 한도 초과 여부는 확인하지 못했다고 쓴다.

### 금지 표현 점검

이 판에는 금지 표현을 찾는 점검기가 없다. 초안·첨삭·점검 때 학교급에 맞는 요약의 「2. 모든 항목에서 쓸 수 없는 것」, 해당 영역 절에서 쓸 수 없다고 정한 내용, 영역 파일의 규정 게이트를 기준으로 문장을 직접 대조한다. 요약이 나눈 묶음(시험·대회·상, 외부 실적, 배경 정보, 이름)을 하나씩 빠짐없이 본다. 근거 없는 수식어와 판단 표현은 「문장 품질 게이트」로 보고, 10명 이상 배치의 문장 반복은 「근거 기반 서술 구조」가 가리키는 기준으로 검토한다. 점검 결과는 교사가 대조할 보조 신호이며, 최종 준수 판정은 교사가 원자료·학교 규정과 대조해 수행한다.

### 이 판에서 지원하지 않는 기능

이 판은 스크립트를 넣지 않은 문서 전용판이다. 다음 요청을 받으면 이 판에서는 지원하지 않는다고 짧게 알리고, 필요하면 스크립트가 들어 있는 전체판(`korean-school-records-toolkit`, https://github.com/blueshadow62/korean-school-records-toolkit)을 쓰도록 안내한다. 없는 기능을 흉내 내어 결과를 지어내지 않는다.

- 기재요령 원문 등록·활성화·검증·롤백: 이 판은 학교급별 요약으로 판단한다. 원문 문구는 교육부 게시물의 원문에서 확인하도록 안내한다.
- 실제 나이스 입력값 대조: 이 판의 바이트 값은 위 계산 방식의 참고값이다.
- 스킬 행동 검증(합성 사례 실행과 채점): 평가 사례와 채점 절차는 전체판에 있다.
- 학생부 기록이 아닌 일반 글의 글자 수·줄 수 계산: 이 판에는 글자 수 계산 스킬이 없다.
````

### 최종 검수 3번: 최종 재계산

````find skills/write-school-records/SKILL.md
3. 최종본을 `analyze_record.py`로 검사해 글자 수·바이트를 다시 확인한다.
````

````replace
3. 최종본의 글자 수·바이트를 「글자 수와 바이트 계산」대로 다시 계산한다. 코드 실행 도구를 쓸 수 없으면 계산하지 못했다고 적는다.
````

### 최종 검수 끝: 글자 수 스킬 연계

이 판에는 `korean-character-count` 스킬이 없다.

````find skills/write-school-records/SKILL.md
다른 스킬의 설치 경로를 import하거나 복사하지 않는다. 일반 글자 수 요청에는 `korean-character-count`를 사용한다.
````

````replace
다른 스킬의 설치 경로를 import하거나 복사하지 않는다.
````

## 참조 문서

### output-skeleton.md: 분량 줄의 계산

````find skills/write-school-records/references/output-skeleton.md
참고용 계산은 `scripts/analyze_record.py`(중학교는 `--school-level middle`)로 재확인한다. 계산을 실행하지 못했으면 `글자 수는 기계로 점검하지 못했습니다.`라고 적는다.
````

````replace
글자 수·Byte 값은 [SKILL.md](../SKILL.md) 「글자 수와 바이트 계산」대로 코드 실행 도구로 계산한 값만 적고, 바이트 값에는 참고값이라고 표시한다. 계산을 실행하지 못했으면 글자 수·나이스 Byte 줄에 값 대신 `글자 수는 기계로 점검하지 못했습니다.`라고 적고 한도만 적으며, 한도 초과 여부 줄에는 확인하지 못했다고 쓴다. 짐작한 값을 계산값처럼 적지 않는다.
````

### field-free-semester.md: 자유학기활동 분량 점검

````find skills/write-school-records/references/field-free-semester.md
기계 점검은 `python scripts/analyze_record.py --school-level middle --field free_semester --file draft.txt`로 한다.
````

````replace
글자 수·Byte는 [SKILL.md](../SKILL.md) 「글자 수와 바이트 계산」대로 계산한다.
````

### source-policy.md: 원문 등록

````find skills/write-school-records/references/source-policy.md
- 원문 변환본(`current.md`)은 배포본에 들어 있지 않다. 사용자가 교육부 원문을 Markdown으로 바꿔 `scripts/update_guidelines.py import`로 등록하고 검증을 통과했으면, 문구 확인에 그 원문을 쓰고 요약과 다르게 읽히면 원문을 따른다. 등록된 원문도 교육부 PDF를 변환한 것이므로 정확한 문구와 최신 게시 상태는 교육부 원문에서 다시 확인한다.
````

````replace
- 원문 변환본은 이 판(문서 전용판)에 들어 있지 않고, 원문을 등록하는 도구도 없다. 문구 확인이 필요하면 교육부 게시물의 원문에서 확인하도록 안내한다. 원문을 등록해 문구까지 대조하는 기능은 스크립트가 들어 있는 전체판에 있다.
````

### guidelines/ATTRIBUTION.md: 이 폴더의 파일

검사 규칙(`analyzer-rules/`)과 색인 검색어(`index-terms.json`)는 스크립트만 쓰므로 이 판에 넣지 않는다.

````find skills/write-school-records/references/guidelines/ATTRIBUTION.md
| `analyzer-rules/` | `scripts/analyze_record.py`가 쓰는 학년도별 검사 규칙(한도·금지 표현 후보) | 포함 |
| `index-terms.json` | 원문을 등록할 때 색인을 만드는 검색어 목록 | 포함 |
| `current.md`, `versions/`, `current.index.md`, `manifest.json` | 원문 PDF를 Markdown으로 바꾼 변환본, 그 보관본과 색인, 등록 기록 | **포함하지 않음.** 개발본에만 있거나 사용자가 직접 등록한다 |
````

````replace
| `analyzer-rules/`, `index-terms.json` | 전체판의 점검 스크립트가 쓰는 검사 규칙과 원문 등록 도구가 쓰는 색인 검색어 | **포함하지 않음.** 이 판(문서 전용판)에는 스크립트가 없다 |
| `current.md`, `versions/`, `current.index.md`, `manifest.json` | 원문 PDF를 Markdown으로 바꾼 변환본, 그 보관본과 색인, 등록 기록 | **포함하지 않음.** 개발본에만 있다. 원문을 직접 등록하는 기능은 전체판에 있다 |
````

### guidelines/ATTRIBUTION.md: 원문 등록 명령

````find skills/write-school-records/references/guidelines/ATTRIBUTION.md
## 원문을 직접 등록하거나 새 학년도로 바꾸기

교육부 게시물에서 원문 PDF를 받아 Markdown(`.md`)으로 바꾼 뒤 등록한다. 변환 방법과 확인할 점은 플러그인 저장소의 `USER_GUIDE.md` 「기재요령 원문을 직접 등록하기」를 따른다.

```bash
python scripts/update_guidelines.py import --input <변환한 .md 파일> --school-year <학년도> --revision-date <개정일 YYYY-MM-DD> --source-title "<원문 제목>" --source-url "<게시물 주소>" --confirmed-official
python scripts/update_guidelines.py activate --version <학년도>_<개정일>
python scripts/update_guidelines.py verify
```

활성 버전과 원문 주소는 이 폴더의 `manifest.json`에 기록된다. 원문을 등록해도 `summary.md`와 `analyzer-rules/`는 자동으로 바뀌지 않는다. 새 학년도 원문이면 요약과 검사 규칙을 따로 갱신해야 하며, 그 절차는 플러그인 저장소의 `docs/guideline-summary-updates.md`에 있다.
````

````replace
## 원문을 직접 등록하거나 새 학년도로 바꾸기

이 판(문서 전용판)에는 원문을 등록하는 도구가 없다. 원문 문구까지 대조하려면 스크립트가 들어 있는 전체판(https://github.com/blueshadow62/korean-school-records-toolkit)을 쓴다. `summary.md`는 원문이 바뀌어도 저절로 바뀌지 않으며, 새 학년도 요약은 플러그인 갱신으로 받는다. 요약을 갱신하는 절차는 플러그인 저장소의 `docs/guideline-summary-updates.md`에 있다.
````

### guidelines-middle/ATTRIBUTION.md: 이 폴더의 파일

````find skills/write-school-records/references/guidelines-middle/ATTRIBUTION.md
| `analyzer-rules/` | `scripts/analyze_record.py --school-level middle`이 쓰는 학년도별 검사 규칙 | 포함 |
| `index-terms.json` | 원문을 등록할 때 색인을 만드는 검색어 목록 | 포함 |
| `current.md`, `versions/`, `current.index.md`, `manifest.json` | 원문 PDF를 Markdown으로 바꾼 변환본, 그 보관본과 색인, 등록 기록 | **포함하지 않음.** 개발본에만 있거나 사용자가 직접 등록한다 |
````

````replace
| `analyzer-rules/`, `index-terms.json` | 전체판의 점검 스크립트가 쓰는 검사 규칙과 원문 등록 도구가 쓰는 색인 검색어 | **포함하지 않음.** 이 판(문서 전용판)에는 스크립트가 없다 |
| `current.md`, `versions/`, `current.index.md`, `manifest.json` | 원문 PDF를 Markdown으로 바꾼 변환본, 그 보관본과 색인, 등록 기록 | **포함하지 않음.** 개발본에만 있다. 원문을 직접 등록하는 기능은 전체판에 있다 |
````

### guidelines-middle/ATTRIBUTION.md: 원문 등록 명령

````find skills/write-school-records/references/guidelines-middle/ATTRIBUTION.md
## 원문을 직접 등록하거나 새 학년도로 바꾸기

교육부 게시물에서 원문 PDF를 받아 Markdown(`.md`)으로 바꾼 뒤 등록한다. 중학교판은 모든 명령에 `--level middle`을 붙인다. 변환 방법과 확인할 점은 플러그인 저장소의 `USER_GUIDE.md` 「기재요령 원문을 직접 등록하기」를 따른다.

```bash
python scripts/update_guidelines.py --level middle import --input <변환한 .md 파일> --school-year <학년도> --revision-date <개정일 YYYY-MM-DD> --source-title "<원문 제목>" --source-url "<게시물 주소>" --confirmed-official
python scripts/update_guidelines.py --level middle activate --version <학년도>_<개정일>
python scripts/update_guidelines.py --level middle verify
```

활성 버전과 원문 주소는 이 폴더의 `manifest.json`에 기록된다. 고등학교판(`references/guidelines/`)과 따로 관리한다. 원문을 등록해도 `summary.md`, `differences.md`, `analyzer-rules/`는 자동으로 바뀌지 않는다. 새 학년도 원문이면 요약과 검사 규칙을 따로 갱신해야 하며, 그 절차는 플러그인 저장소의 `docs/guideline-summary-updates.md`에 있다.
````

````replace
## 원문을 직접 등록하거나 새 학년도로 바꾸기

이 판(문서 전용판)에는 원문을 등록하는 도구가 없다. 원문 문구까지 대조하려면 스크립트가 들어 있는 전체판(https://github.com/blueshadow62/korean-school-records-toolkit)을 쓴다. `summary.md`와 `differences.md`는 원문이 바뀌어도 저절로 바뀌지 않으며, 새 학년도 요약은 플러그인 갱신으로 받는다. 요약을 갱신하는 절차는 플러그인 저장소의 `docs/guideline-summary-updates.md`에 있다.
````

## LICENSE

### 머리말과 글자 수 스킬 항목

이 판에는 `korean-character-count` 스킬이 없으므로 그 항목을 빼고, 이 판이 무엇인지 적는다. 나머지 고지는 전체판과 같다.

````find LICENSE
Korean School Records Toolkit — license notice

This distribution bundles two independent local skills.

- korean-character-count: derived from the `korean-character-count` skill in https://github.com/NomaDamas/k-skill (MIT License). The upstream copyright notice, the MIT permission notice, and the list of changes are in `skills/korean-character-count/LICENSE`.
````

````replace
Korean School Records Toolkit Lite (korean-school-records-lite) — license notice

This is the documents-only edition of korean-school-records-toolkit (https://github.com/blueshadow62/korean-school-records-toolkit). It holds one skill, write-school-records, and its reference documents. It does not hold scripts or the korean-character-count skill.

````
