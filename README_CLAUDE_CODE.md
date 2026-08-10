# Claude Code 설치

이 플러그인은 `write-school-records`, `korean-character-count`를 서로 독립된 Claude Code 스킬로 제공한다. 두 스킬의 공통 원본은 Codex 플러그인과 같으며 `.claude-plugin/plugin.json`만 Claude Code 전용 manifest로 사용한다.

## 요구 사항

- Claude Code 최신 버전
- `write-school-records`: Python 3 표준 라이브러리
- `korean-character-count`: Node.js 18 이상

## 로컬 검증

플러그인 루트에서 공식 manifest 검증을 실행한다.

```powershell
claude plugin validate . --strict
```

로컬 디렉터리를 설치하지 않고 시험한다.

```powershell
claude --plugin-dir .
```

Claude Code 안에서 `/help`로 다음 스킬이 표시되는지 확인한다.

```text
/korean-school-records-toolkit:write-school-records
/korean-school-records-toolkit:korean-character-count
```

파일을 수정한 뒤에는 Claude Code에서 `/reload-plugins`를 실행한다.

## 개인 범위 설치

Claude Code를 종료한 뒤 플러그인 디렉터리 전체를 다음 위치에 복사한다.

```text
%USERPROFILE%\.claude\skills\korean-school-records-toolkit
```

최종 구조는 다음과 같아야 한다.

```text
korean-school-records-toolkit/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── write-school-records/
│   │   └── SKILL.md
│   └── korean-character-count/
│       └── SKILL.md
└── LICENSE
```

다음 Claude Code 세션부터 `korean-school-records-toolkit@skills-dir` 플러그인으로 발견된다. 대상 디렉터리에 기존 설치가 있으면 먼저 별도 위치에 백업하고, 설치 후 위의 로컬 검증을 다시 실행한다.

## 사용 원칙

- 일반 글자 수 요청에는 `korean-character-count`만 사용한다.
- 학생부 작성·첨삭·기재요령 검증에는 `write-school-records`를 사용한다.
- 학생부 최종 검수에서는 사실 확인 후 분량을 다시 계산한다.
- 실제 학생 자료를 예제·테스트에 사용하지 않는다.

이 패키지는 Claude Code marketplace 등록을 포함하지 않는다. marketplace 배포가 필요하면 별도의 저장소와 marketplace manifest를 추가해야 한다.
