# 설치 가이드

대상 플러그인 버전은 `2.0.0`이다.

## A. 플러그인 개요

이 패키지는 `write-school-records`, `korean-character-count`를 독립 스킬로 묶은 스킬 전용 플러그인이다. 앱 또는 MCP 연결은 포함하지 않는다.

## B. 사전 요구 사항

- `.codex-plugin/plugin.json`을 지원하는 Codex 환경
- 플러그인 또는 스킬 설치 위치에 대한 쓰기 권한
- `write-school-records`: Python 3 표준 라이브러리
- `korean-character-count`: Node.js 18 이상
- 관리자 배포는 워크스페이스 플러그인 정책 변경 권한 필요

이 빌드 환경에서는 `codex.exe` 실행이 Windows 앱 권한으로 거부되어 CLI 설치 명령을 직접 실행하지 못했다. 아래 명령 형태는 설치된 공식 `plugin-creator` 참고 문서에서 확인했으며 사용자는 자신의 터미널에서 `codex plugin --help`로 최종 확인해야 한다.

## C. 로컬 설치

### 현재 저장소에서 설치

이 GitHub 저장소는 단일 플러그인 루트이며 Codex marketplace wrapper를 포함하지 않는다. 아래 관리 스크립트로 두 스킬을 함께 설치한다. 한 스킬만 설치된 상태를 남기지 않으며 기존 설치본을 백업한다.

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

설치 순서는 플러그인 구조 검사, 기존 설치 확인, dry-run, 전체 staging, 백업, 일괄 반영, 설치 후 파일 해시 검증이다. 실패 시 반영된 두 스킬을 제거하고 기존 백업을 복원한다.

### Codex marketplace로 배포할 때

Codex marketplace 설치를 제공하려면 별도 marketplace 루트에 `.agents/plugins/marketplace.json`과 `plugins/korean-school-records-toolkit/` 구조를 만들어 이 저장소를 감싸야 한다. 현재 단일 플러그인 저장소를 marketplace 루트라고 가정해 `codex plugin marketplace add`를 실행하지 않는다. wrapper 저장소가 준비된 경우에만 해당 marketplace 이름으로 `codex plugin add korean-school-records-toolkit@<marketplace-name>`을 사용한다.

## D. 워크스페이스 설치

1. 관리자가 승인된 저장소의 플러그인 디렉터리를 사용한다.
2. 별도 marketplace wrapper의 `.agents/plugins/marketplace.json`과 플러그인 manifest를 검증한다.
3. wrapper marketplace를 현재 Codex가 지원하는 관리자 절차로 등록한다.
4. 패키지 marketplace 정책은 `AVAILABLE`로 제공된다.
5. 역할별 자동 설치가 필요하면 관리자가 지원되는 UI 또는 정책 파일에서 `INSTALLED_BY_DEFAULT`로 변경한다.
6. 포함된 독립 스킬 두 개와 이름을 확인한다.
7. 합성 자료만 사용하는 테스트 사용자로 저위험 검증한다.

현재 환경에서 워크스페이스 관리 UI의 실제 버튼명과 게시 권한은 확인하지 못했다. UI 명칭을 추측하지 말고 조직 관리자 문서와 현재 화면을 따른다.

## E. 업데이트

1. 새 패키지의 `VERSION`, `CHANGELOG.md`, `SOURCE_METADATA.json`을 확인한다.
2. `python .\scripts\verify_package.py`로 구조와 공개 출처 계약을 검증한다.
3. 변경된 스킬을 확인한다.
4. `--dry-run` 후 `--install`을 실행한다.
5. `--verify`와 각 스킬 회귀 테스트를 실행한다.
6. 별도 marketplace wrapper로 배포할 때는 `plugin-creator`의 cachebuster·재설치 흐름을 사용하고 marketplace 파일을 임의로 편집하지 않는다.

## F. 제거와 롤백

트랜잭션 번들 제거:

```powershell
python .\scripts\manage_bundle.py --uninstall
```

최근 백업으로 롤백:

```powershell
python .\scripts\manage_bundle.py --rollback
```

특정 백업을 선택하려면 `--backup "<backup-directory>"`를 추가한다. 롤백은 두 스킬을 동일 시점 상태로 복원한다. 별도 marketplace wrapper로 설치한 플러그인의 제거는 현재 `codex plugin --help`에서 확인되는 제거 명령 또는 관리자 UI를 사용한다.

## G. 설치 확인

학교생활기록부 기능:

> 합성 교사 관찰과 합성 결과물을 근거로 수학 세특 초안을 작성해 줘. 입력에 없는 사실은 추가하지 마.

글자 수 기능:

> “가나다 ABC 123”의 글자 수, UTF-8 Byte, NEIS 프로필 Byte를 계산해 줘.

## Codex 설치 프롬프트

완성된 복사용 프롬프트는 [INSTALL_WITH_CODEX_PROMPT.md](INSTALL_WITH_CODEX_PROMPT.md)에 있으며 아래 내용을 그대로 포함한다.

```text
<plugin-root>의 패키지를 읽고 INSTALL_WITH_CODEX_PROMPT.md의 검사·백업·dry-run·설치·검증·롤백 절차를 그대로 수행하라.
```

## 개인정보와 교육 기록

- 실제 학생 자료를 설치 시험에 사용하지 않는다.
- 패키지나 로그에 학생 이름·학번·학교명을 넣지 않는다.
- 생성 결과는 교사가 원자료와 활성 기재요령에 대조한다.

## Claude Code

Claude Code용 manifest, 개인 범위 설치, `claude plugin validate --strict`, `claude --plugin-dir` 검증 절차는 [README_CLAUDE_CODE.md](README_CLAUDE_CODE.md)를 따른다.
