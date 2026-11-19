# 보안 문제 신고 (Security)

## 신고하는 곳

이 플러그인의 보안 취약점을 찾으면 이 저장소의 GitHub Issues로 알려 주십시오.

1. https://github.com/blueshadow62/korean-school-records-toolkit/issues 에서 새 이슈를 엽니다.
2. 제목에 `[보안]`을 붙입니다.
3. 공격 방법, 시험용 입력값, 비밀번호·토큰 같은 민감한 내용은 이슈에 바로 쓰지 않습니다. 영향받는 파일과 문제의 종류만 짧게 적고, 자세한 내용을 전할 비공개 방법을 요청합니다.

학생 이름·학번·학교명 같은 실제 학생 정보는 신고 내용에도 넣지 않습니다.

## 지원하는 판

최신 릴리스(`VERSION` 파일의 판)만 고칩니다. 고친 내용은 `CHANGELOG.md`에 적습니다.

## 이 플러그인이 하는 일과 하지 않는 일

- 두 스킬은 이 플러그인 폴더 안의 스크립트만 실행합니다. `write-school-records`는 Python 3 표준 라이브러리로 쓴 스크립트를, `korean-character-count`는 Node.js 스크립트(`scripts/korean_character_count.js`)를 씁니다.
- 스킬과 스크립트는 네트워크에 접속하지 않습니다. 입력한 학생 자료를 수집하거나 외부로 보내지 않습니다. 스크립트에는 네트워크 라이브러리 호출이 없습니다(2026-11-19 저장소의 Python·JavaScript 파일을 검색해 확인).
- 파일을 쓰는 스크립트는 두 개입니다. `update_guidelines.py`는 사용자가 기재요령 원문을 등록할 때 스킬 폴더 안 `references/guidelines/` 또는 `references/guidelines-middle/`에 그 파일과 등록 기록을 씁니다. `compare_neis_counts.py`는 정비하는 사람이 NEIS에서 잰 값을 시험 사례 파일에 기록할 때 씁니다.
- 저장소의 `tools/corpus/`는 성취수준 자료를 다시 만들 때 정비하는 사람이 직접 실행하는 도구이며, 스킬이 실행하지 않습니다. 이 가운데 `convert_nkis_pdfs_v2.py`는 `npx`로 kordoc 패키지를 내려받아 실행합니다.

## English summary

To report a security problem, open an issue at https://github.com/blueshadow62/korean-school-records-toolkit/issues and put `[Security]` in the title. Do not put exploit details, credentials, or real student data in a public issue. Give the affected file and the type of problem, and ask for a private channel.

The skills run only the scripts in this plugin folder (Python 3 standard library and Node.js). The skills and scripts do not connect to a network. They do not collect or send the data that you enter. The maintainer tool `tools/corpus/convert_nkis_pdfs_v2.py` is not run by the skills; it downloads and runs the kordoc package with `npx` when a maintainer rebuilds the achievement-standards corpus.
