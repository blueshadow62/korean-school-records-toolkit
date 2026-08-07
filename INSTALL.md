# 설치 가이드

대상 플러그인 버전은 `1.1.0`이다.

## A. 플러그인 개요

이 패키지는 `write-school-records`, `korean-character-count`, `korean-spell-check`를 독립 스킬로 묶은 스킬 전용 플러그인이다. 앱 또는 MCP 연결은 포함하지 않는다. 맞춤법 스킬만 공개 Nara/PNU 검사 표면에 네트워크로 접근하며, 민감한 학생 자료를 외부 서비스에 보내지 않아야 한다.

## B. 사전 요구 사항

- `.codex-plugin/plugin.json`과 repo-local marketplace를 지원하는 Codex 환경
- 플러그인 또는 스킬 설치 위치에 대한 쓰기 권한
- `write-school-records`: Python 3 표준 라이브러리
- `korean-character-count`: Node.js 18 이상
- `korean-spell-check`: Python 3.10 이상, 인터넷 연결, 공개 검사기 사용 정책 준수
- 관리자 배포는 워크스페이스 플러그인 정책 변경 권한 필요

이 빌드 환경에서는 `codex.exe` 실행이 Windows 앱 권한으로 거부되어 CLI 설치 명령을 직접 실행하지 못했다. 아래 명령 형태는 설치된 공식 `plugin-creator` 참고 문서에서 확인했으며 사용자는 자신의 터미널에서 `codex plugin --help`로 최종 확인해야 한다.

## C. 로컬 설치

### 공식 플러그인 설치

배포 압축을 원하는 디렉터리에 풀면 루트에 `.agents/plugins/marketplace.json`과 `plugins/korean-school-records-toolkit`가 있어야 한다. 현재 개발 루트를 직접 사용할 경우 경로는 다음과 같다.

```powershell
codex plugin marketplace add "<repo-root>"
codex plugin add korean-school-records-toolkit@personal
```

설치 후 새 Codex 작업을 열어 세 스킬이 보이는지 확인한다. CLI가 위 명령을 지원하지 않으면 실행을 중단하고 `codex plugin --help` 결과에 맞춰야 하며, 존재하지 않는 명령으로 대체하지 않는다.

### 트랜잭션형 스킬 번들 설치

공식 플러그인 등록을 사용할 수 없는 환경에서는 아래 관리 스크립트로 세 스킬을 함께 설치할 수 있다. 한 스킬만 설치된 상태를 남기지 않으며 기존 설치본을 백업한다.

```powershell
python .\scripts\verify_package.py
python .\scripts\manage_bundle.py --dry-run
python .\scripts\manage_bundle.py --install
python .\scripts\manage_bundle.py --verify
```

임시 위치에 시험하려면 모든 명령에 다음 옵션을 붙인다.

```powershell
--install-root "<temporary-skill-root>" --backup-root "<temporary-backup-root>"
```

설치 순서는 패키지 무결성 검사, 기존 설치 확인, dry-run, 전체 staging, 백업, 일괄 반영, 설치 후 SHA-256 검증이다. 실패 시 반영된 세 스킬을 제거하고 기존 백업을 복원한다.

## D. 워크스페이스 설치

1. 관리자가 배포 압축을 승인된 내부 저장소에 해제한다.
2. `.agents/plugins/marketplace.json`과 플러그인 manifest를 검증한다.
3. repo-local marketplace를 현재 Codex가 지원하는 관리자 절차로 등록한다.
4. 패키지 marketplace 정책은 `AVAILABLE`로 제공된다.
5. 역할별 자동 설치가 필요하면 관리자가 지원되는 UI 또는 정책 파일에서 `INSTALLED_BY_DEFAULT`로 변경한다.
6. 포함된 독립 스킬 세 개와 이름을 확인한다.
7. 합성 자료만 사용하는 테스트 사용자로 저위험 검증한다.

현재 환경에서 워크스페이스 관리 UI의 실제 버튼명과 게시 권한은 확인하지 못했다. UI 명칭을 추측하지 말고 조직 관리자 문서와 현재 화면을 따른다.

## E. 업데이트

1. 새 패키지의 `VERSION`, `CHANGELOG.md`, `SOURCE_METADATA.json`을 확인한다.
2. `checksums.sha256`을 검증한다.
3. 변경된 스킬을 확인한다.
4. `--dry-run` 후 `--install`을 실행한다.
5. `--verify`와 각 스킬 회귀 테스트를 실행한다.
6. 공식 marketplace 플러그인을 업데이트할 때는 `plugin-creator`의 cachebuster·재설치 흐름을 사용하고 marketplace 파일을 임의로 편집하지 않는다.

## F. 제거와 롤백

트랜잭션 번들 제거:

```powershell
python .\scripts\manage_bundle.py --uninstall
```

최근 백업으로 롤백:

```powershell
python .\scripts\manage_bundle.py --rollback
```

특정 백업을 선택하려면 `--backup "<backup-directory>"`를 추가한다. 롤백은 세 스킬을 동일 시점 상태로 복원한다. 공식 플러그인 제거는 현재 `codex plugin --help`에서 확인되는 제거 명령 또는 관리자 UI를 사용한다.

## G. 설치 확인

학교생활기록부 기능:

> 합성 교사 관찰과 합성 결과물을 근거로 수학 세특 초안을 작성해 줘. 입력에 없는 사실은 추가하지 마.

글자 수 기능:

> “가나다 ABC 123”의 글자 수, UTF-8 Byte, NEIS 프로필 Byte를 계산해 줘.

맞춤법 기능:

> “학생은 자료를 꼼꼼이 살펴 보았다.”를 의미를 바꾸지 않고 교정하고 변경 이유를 알려줘.

맞춤법 테스트는 합성 문장만 사용하고, 공개 검사기 연결이 불가능하면 네트워크 기능을 통과했다고 보고하지 않는다.

## Codex 설치 프롬프트

완성된 복사용 프롬프트는 [INSTALL_WITH_CODEX_PROMPT.md](INSTALL_WITH_CODEX_PROMPT.md)에 있으며 아래 내용을 그대로 포함한다.

```text
<plugin-root>의 패키지를 읽고 INSTALL_WITH_CODEX_PROMPT.md의 검사·백업·dry-run·설치·검증·롤백 절차를 그대로 수행하라.
```

## 개인정보와 교육 기록

- 실제 학생 자료를 설치 시험에 사용하지 않는다.
- 패키지나 로그에 학생 이름·학번·학교명을 넣지 않는다.
- 맞춤법 검사 전에 외부 전송 가능 여부와 개인정보 포함 여부를 확인한다.
- 외부 실행 승인이 거부되거나 서비스가 실패하면 검사 미완료로 처리하며, 오류 없음으로 보고하지 않는다.
- 생성 결과는 교사가 원자료와 활성 기재요령에 대조한다.

## Claude Code

Claude Code용 manifest, 개인 범위 설치, `claude plugin validate --strict`, `claude --plugin-dir` 검증 절차는 [README_CLAUDE_CODE.md](README_CLAUDE_CODE.md)를 따른다.
