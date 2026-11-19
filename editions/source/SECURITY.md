# 보안 문제 신고 (Security)

## 신고하는 곳

이 플러그인의 보안 문제를 찾으면 전체판 저장소의 GitHub Issues로 알려 주십시오. 문서 전용판도 같은 저장소에서 관리합니다.

1. https://github.com/blueshadow62/korean-school-records-toolkit/issues 에서 새 이슈를 엽니다.
2. 제목에 `[보안]`과 `라이트`를 붙입니다.
3. 공격 방법이나 시험용 입력값처럼 민감한 내용은 이슈에 바로 쓰지 않습니다. 영향받는 파일과 문제의 종류만 짧게 적고, 자세한 내용을 전할 비공개 방법을 요청합니다.

학생 이름·학번·학교명 같은 실제 학생 정보는 신고 내용에도 넣지 않습니다.

## 지원하는 판

최신 판만 고칩니다. 고친 내용은 저장소의 `CHANGELOG.md`에 적습니다.

## 이 플러그인이 하는 일과 하지 않는 일

- 이 판에는 스크립트와 실행 파일이 없습니다. 스킬 문서와 참고 자료(Markdown, JSON)만 들어 있습니다.
- 이 플러그인은 네트워크에 접속하지 않습니다. 입력한 학생 자료를 수집하거나 외부로 보내지 않습니다.
- 글자 수와 Byte는 Claude가 코드 실행 도구로 계산합니다. 계산에 쓰는 코드는 스킬 문서(`skills/write-school-records/SKILL.md`)에 적힌 몇 줄이며, 파일을 쓰거나 네트워크에 접속하지 않습니다.

## English summary

To report a security problem, open an issue at https://github.com/blueshadow62/korean-school-records-toolkit/issues. Put `[Security]` and `lite` in the title. Do not put exploit details or real student data in a public issue. Give the affected file and the type of problem, and ask for a private channel.

This edition contains no scripts and no executable files. It contains only the skill instructions and the reference documents (Markdown and JSON). The plugin does not connect to a network. It does not collect or send the data that you enter. Claude counts characters and bytes with its code execution tool. It uses the few lines of code that the skill instructions give. That code does not write files and does not connect to a network.
