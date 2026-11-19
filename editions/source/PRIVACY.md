# 개인정보 처리 안내 (Privacy)

이 문서는 문서 전용판 플러그인 `korean-school-records-lite`(한국어 학교생활기록부 도구 라이트)에 적용됩니다. 작성일은 2026년 11월 19일입니다. 내용이 바뀌면 저장소의 `CHANGELOG.md`에 적습니다.

## 요약

- 이 플러그인은 입력한 자료를 수집하거나 저장하거나 외부로 보내지 않습니다. 제3자에게 제공하지 않으며, 사용 기록이나 분석 정보도 모으지 않습니다.
- 교사가 대화에 입력한 내용은 사용하시는 Claude 서비스 안에서 처리됩니다. 그 자료의 취급은 이 플러그인이 아니라 Anthropic의 약관과 개인정보처리방침, 그리고 사용하시는 요금제와 조직의 설정을 따릅니다.
- 학생 이름·학번·학교명 같은 학생을 알아볼 수 있는 정보는 빼고 입력하시기 바랍니다.

## 플러그인이 하지 않는 일

이 판에는 Markdown·JSON·라이선스 문서와 그림 파일(PNG) 하나가 들어 있습니다. 실행 파일, 스크립트, 서버, 외부 서비스 연결(커넥터)이 없으므로 플러그인이 스스로 자료를 모으거나 저장하거나 보낼 수단이 없습니다.

- 입력한 자료를 수집하거나 저장하거나 외부로 보내지 않습니다.
- 제3자에게 자료를 제공하지 않습니다.
- 사용 기록이나 분석 정보를 모으지 않습니다.
- 네트워크에 접속하지 않습니다.

2026년 11월 19일에 이 판의 파일 종류와 스킬 문서의 내용을 검색해 확인했습니다. 저장소의 자동 검사가 이 판을 만들 때마다 파일 종류를 다시 확인합니다.

## 학생 정보를 다루는 방식

이 스킬은 교사가 대화에 입력한 학생 관찰·평가 내용을 바탕으로 문장을 씁니다. 스킬 지침의 [개인정보 안내](skills/write-school-records/references/intake-template.md)는 다음과 같이 정합니다.

- 학생 이름·학번·학교명은 입력할 필요가 없습니다. 초안을 쓰는 데 필요한 것은 학년, 영역, 과목(활동)명(행특은 제외)과 자료 내용입니다.
- 식별 정보가 들어 있는 자료를 받았어도 초안에는 반영하지 않습니다.
- 초안을 마무리하는 최종 검수에서 금지 표현, 개인정보, 근거 부족을 점검합니다.

이것은 스킬이 Claude에게 주는 작성 지침입니다. 교사가 입력하는 내용을 플러그인이 막거나 걸러 낼 수는 없습니다. 학생을 알아볼 수 있는 정보를 입력하지 않는 일은 교사께 달려 있습니다.

## 글자 수와 바이트 계산

글자 수와 바이트는 Claude의 코드 실행 도구로 계산합니다. 계산에는 스킬 문서(`skills/write-school-records/SKILL.md`)에 적힌 몇 줄의 코드를 씁니다. 이 코드는 글자 수와 바이트를 세어 화면에 보여 줍니다. 파일을 쓰거나 네트워크에 접속하지 않습니다. 계산하려고 초안 본문을 코드 실행 도구에 넣게 되므로, 그 도구가 돌아가는 환경의 자료 취급은 아래 「입력한 내용의 처리」를 따릅니다.

## 입력한 내용의 처리

교사가 대화에 입력한 내용은 사용하시는 Claude 서비스 안에서 처리됩니다. 그 자료의 취급은 이 플러그인이 아니라 Anthropic의 약관과 [개인정보처리방침](https://www.anthropic.com/legal/privacy), 그리고 사용하시는 요금제와 조직의 설정을 따릅니다. 이 문서는 그 내용을 설명하지 않습니다. 쓰시는 서비스의 방침을 직접 확인해 주십시오.

## 교사께 권하는 것

- 학생 이름·학번·학교명 같은 학생을 알아볼 수 있는 정보는 빼고 입력하십시오.
- 근무하시는 학교와 시도교육청의 개인정보 보호 규정과 AI 활용 지침을 확인하십시오.

## 문의와 정정 요청

이 문서에 대한 문의와 정정 요청은 저장소의 GitHub Issues(https://github.com/blueshadow62/korean-school-records-toolkit/issues)로 알려 주십시오. 실제 학생 정보는 이슈에 쓰지 마십시오. 보안 문제는 [SECURITY.md](SECURITY.md)에 따라 알려 주십시오.

## English summary

This document applies to the documents-only edition of the plugin, `korean-school-records-lite`. It was written on 19 November 2026. The maintainer records each change to this document in `CHANGELOG.md` in the repository.

The plugin contains Markdown, JSON, and license documents and one PNG image. It has no script, no executable file, no server, and no connector. The plugin does not collect, store, or send the data that you enter. It does not give data to a third party. It does not collect usage or analytics data. It does not connect to a network.

The skill helps a teacher write school-record text from the teacher's own observations. The skill instructions say that a student's name, student number, and school name are not necessary. They also say that Claude must not use such identifying information in a draft. The plugin cannot stop a teacher from entering it. Do not enter it.

To count characters and bytes, Claude runs a few lines of code from the skill instructions in its code execution tool. The code counts and shows the result. It does not write files and does not connect to a network.

The data that you enter in the conversation is processed inside the Claude service that you use. The terms and the privacy policy of Anthropic (https://www.anthropic.com/legal/privacy) and the settings of your plan or organization apply to that data. This document does not describe them. Read them yourself.

Check the privacy rules and the AI-use guidance of your school and education office.

To ask a question or to request a correction, open an issue at https://github.com/blueshadow62/korean-school-records-toolkit/issues. Do not put real student data in an issue.
