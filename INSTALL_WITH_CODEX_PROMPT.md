# Codex 설치용 프롬프트

아래 프롬프트를 새 Codex 작업에 복사해 사용한다.

```text
다음 스킬 전용 플러그인 패키지를 안전하게 설치하고 검증하라.

플러그인 소스:
<plugin-root>

repo-local marketplace:
<repo-root>\.agents\plugins\marketplace.json

배포 압축:
<dist-root>\korean-school-records-toolkit-1.1.0.zip

요구 사항:
1. 패키지 경로, .codex-plugin/plugin.json, VERSION, checksums.sha256를 확인한다.
2. 포함 스킬이 write-school-records, korean-character-count, korean-spell-check 정확히 세 개인지 확인한다.
3. python .\scripts\verify_package.py로 manifest·파일 무결성·중복 이름·캐시·비밀정보 검사를 수행한다.
4. 사용자 설치 경로의 세 스킬 존재 여부와 현재 파일 해시를 기록한다.
5. 기존 설치본은 <backup-root>\korean-school-records-toolkit\<timestamp> 아래에 함께 백업한다.
6. 먼저 python .\scripts\manage_bundle.py --dry-run을 실행하고 추가·교체 대상을 보고한다.
7. dry-run이 정상일 때만 python .\scripts\manage_bundle.py --install을 실행한다.
8. 설치 후 python .\scripts\manage_bundle.py --verify를 실행하여 세 스킬 전체 해시를 확인한다.
9. 각 스킬의 기존 로컬 테스트를 실행한다. Node·Python·네트워크가 없어 실행하지 못한 테스트는 통과라고 하지 말고 이유를 기록한다.
10. 합성 자료로 학생부 초안, 글자 수·Byte 계산, 맞춤법 교정의 저위험 스모크 테스트를 각각 수행한다.
11. 세 대상 중 일부만 설치된 상태가 없는지 확인한다.
12. 어느 단계든 실패하면 python .\scripts\manage_bundle.py --rollback으로 세 스킬을 함께 복원하고 실패 상태를 보고한다.
13. 변경한 파일과 실제 경로, 백업 위치, 검증 결과를 요약한다.
14. 저장소를 수정했다면 Conventional Commit을 제안하고, 수정하지 않았다면 `수정 없음`으로 보고한다.

실제 학생 자료를 사용하거나 외부 맞춤법 검사기에 민감정보를 보내지 않는다. 존재하지 않는 Codex CLI 명령을 추측하지 않는다.
외부 실행 승인이 거부되거나 서비스 검사가 실패하면 검사 미완료로 기록하고, 맞춤법 오류 없음으로 보고하지 않는다.
```
