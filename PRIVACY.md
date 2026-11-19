# 개인정보 처리 안내 (Privacy)

이 문서는 전체판 플러그인 `korean-school-records-toolkit`(한국어 학교생활기록부 도구)에 적용됩니다. 스크립트가 없는 문서 전용판 `korean-school-records-lite`는 사실이 달라서 [별도 안내](editions/korean-school-records-lite/PRIVACY.md)를 둡니다. 작성일은 2026년 11월 19일입니다. 내용이 바뀌면 저장소의 `CHANGELOG.md`에 적습니다.

## 요약

- 이 플러그인은 입력한 자료를 수집하거나 저장하거나 외부로 보내지 않습니다. 제3자에게 제공하지 않으며, 사용 기록이나 분석 정보도 모으지 않습니다.
- 이 판에는 스크립트가 있습니다. 스킬이 실행하는 스크립트 네 개는 네트워크에 접속하지 않습니다. 입력한 학생 자료를 파일로 기록하는 스크립트도 없습니다.
- 교사가 대화에 입력한 내용은 사용하시는 AI 서비스 안에서 처리됩니다. 그 자료의 취급은 이 플러그인이 아니라 서비스 제공자의 약관과 개인정보처리방침, 그리고 사용하시는 요금제와 조직의 설정을 따릅니다.
- 학생 이름·학번·학교명 같은 학생을 알아볼 수 있는 정보는 빼고 입력하시기 바랍니다.

## 플러그인이 하지 않는 일

- 입력한 자료를 수집하거나 저장하거나 외부로 보내지 않습니다.
- 제3자에게 자료를 제공하지 않습니다.
- 사용 기록이나 분석 정보를 모으지 않습니다.
- 스킬이 실행하는 스크립트는 네트워크에 접속하지 않습니다.

2026년 11월 19일에 스킬 스크립트의 코드를 검색해 확인했습니다. 네트워크 호출, 외부 프로그램 실행, 환경 변수 읽기가 없습니다. 저장소의 자동 시험이 같은 내용을 계속 확인합니다(`tests/test_privacy_notice.py`).

## 스크립트가 하는 일

스킬이 실행하는 스크립트는 네 개입니다. Python 3 표준 라이브러리 또는 Node.js 표준 모듈로 쓰였고, Claude Code나 Codex가 실행되는 컴퓨터에서 실행됩니다.

| 스크립트 | 하는 일 | 파일 쓰기 |
|---|---|---|
| `skills/write-school-records/scripts/analyze_record.py` | 입력한 문장(`--text`, `--file`, `--batch`)의 글자 수·Byte와 금지 표현 후보 등을 점검해 화면에 출력합니다. | 없음 |
| `skills/korean-character-count/scripts/korean_character_count.js` | 입력한 문장(`--text`, `--file`, `--stdin`)의 글자 수·줄 수·Byte를 세어 화면에 출력합니다. | 없음 |
| `skills/write-school-records/scripts/update_guidelines.py` | 사용자가 기재요령 원문을 등록할 때 스킬 폴더 안 `references/guidelines/` 또는 `references/guidelines-middle/`에 그 파일과 등록 기록을 씁니다. | 있음 |
| `skills/write-school-records/scripts/compare_neis_counts.py` | 정비하는 사람이 NEIS에서 잰 값을 시험 사례 파일(`tests/neis-validation/cases.json`)에 기록하고, 계산값과 비교한 결과를 화면에 출력합니다. | 있음 |

- 입력한 학생 자료를 파일로 기록하는 스크립트는 없습니다. 파일을 쓰는 두 스크립트가 쓰는 것은 기재요령 원문의 등록 기록과 시험 사례 값입니다.
- 스크립트가 출력한 결과도 대화에 나타나는 내용이므로, 입력한 내용과 같게 아래 「입력한 내용의 처리」를 따릅니다.

스킬이 실행하지 않는 도구도 저장소에 있습니다. `scripts/`의 설치 관리·검증·빌드 스크립트와 `tools/corpus/`의 성취수준 자료 정비 도구는 설치하는 사람이나 정비하는 사람이 직접 실행합니다. 이 도구들은 학생 자료를 입력으로 받지 않습니다. `tools/corpus/convert_nkis_pdfs_v2.py`는 `npx`로 kordoc 패키지를 내려받아 실행합니다. `tools/corpus/`의 설명은 [SECURITY.md](SECURITY.md)에도 있습니다.

## 학생 정보를 다루는 방식

이 스킬은 교사가 대화에 입력한 학생 관찰·평가 내용을 바탕으로 문장을 씁니다. 스킬 지침의 [개인정보 안내](skills/write-school-records/references/intake-template.md)는 다음과 같이 정합니다.

- 학생 이름·학번·학교명은 입력할 필요가 없습니다. 초안을 쓰는 데 필요한 것은 학년, 영역, 과목(활동)명(행특은 제외)과 자료 내용입니다.
- 식별 정보가 들어 있는 자료를 받았어도 초안에는 반영하지 않습니다.
- 초안을 마무리하는 최종 검수에서 금지 표현, 개인정보, 근거 부족을 점검합니다.

이것은 스킬이 AI에게 주는 작성 지침입니다. 교사가 입력하는 내용을 플러그인이 막거나 걸러 낼 수는 없습니다. 학생을 알아볼 수 있는 정보를 입력하지 않는 일은 교사께 달려 있습니다.

## 입력한 내용의 처리

교사가 대화에 입력한 내용은 사용하시는 AI 서비스 안에서 처리됩니다. 그 자료의 취급은 이 플러그인이 아니라 서비스 제공자의 약관과 개인정보처리방침, 그리고 사용하시는 요금제와 조직의 설정을 따릅니다. Claude Code를 쓰시면 Anthropic의 약관과 [개인정보처리방침](https://www.anthropic.com/legal/privacy)을, Codex를 쓰시면 그 서비스의 약관과 개인정보처리방침을 확인해 주십시오. 이 문서는 그 내용을 설명하지 않습니다.

## 교사께 권하는 것

- 학생 이름·학번·학교명 같은 학생을 알아볼 수 있는 정보는 빼고 입력하십시오.
- 근무하시는 학교와 시도교육청의 개인정보 보호 규정과 AI 활용 지침을 확인하십시오.

## 문의와 정정 요청

이 문서에 대한 문의와 정정 요청은 저장소의 GitHub Issues(https://github.com/blueshadow62/korean-school-records-toolkit/issues)로 알려 주십시오. 실제 학생 정보는 이슈에 쓰지 마십시오. 보안 문제는 [SECURITY.md](SECURITY.md)에 따라 알려 주십시오.

## English summary

This document applies to the full edition of the plugin, `korean-school-records-toolkit`. The documents-only edition has its own notice in `editions/korean-school-records-lite/PRIVACY.md`. It was written on 19 November 2026. The maintainer records each change to this document in `CHANGELOG.md`.

The plugin does not collect, store, or send the data that you enter. It does not give data to a third party. It does not collect usage or analytics data.

The skills run four scripts: three in Python and one in Node.js. They use only the standard library of the language. They run on the computer where Claude Code or Codex runs. The scripts have no network call, no call to an external program, and no read of environment variables. No script records the student data that you enter. Two scripts write files in the skill folder. `update_guidelines.py` writes the guideline text that a user registers. `compare_neis_counts.py` writes NEIS test values into a test-case file. The maintainer tools in `scripts/` and `tools/corpus/` are not run by the skills. They do not take student data as input. The tool `tools/corpus/convert_nkis_pdfs_v2.py` downloads and runs the kordoc package with `npx`.

The skill helps a teacher write school-record text from the teacher's own observations. The skill instructions say that a student's name, student number, and school name are not necessary. They also say that the AI must not use such identifying information in a draft. The plugin cannot stop a teacher from entering it. Do not enter it.

The data that you enter in the conversation, and the output of the scripts, are processed inside the AI service that you use. The terms and the privacy policy of that service apply, and so do the settings of your plan or organization. For Claude Code, read the terms and the privacy policy of Anthropic (https://www.anthropic.com/legal/privacy). For Codex, read the terms and the privacy policy of that service. This document does not describe them.

Check the privacy rules and the AI-use guidance of your school and education office.

To ask a question or to request a correction, open an issue at https://github.com/blueshadow62/korean-school-records-toolkit/issues. Do not put real student data in an issue.
