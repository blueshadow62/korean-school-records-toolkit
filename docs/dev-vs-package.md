# 개발본과 배포본의 의도된 차이

이 프로젝트의 스킬은 두 위치에 존재한다.

| 경로 | 역할 |
| --- | --- |
| `skills/write-school-records/` | 저장소 밖의 개발본. 개발·검증과 설치 동기화에 사용한다. |
| `plugins/korean-school-records-toolkit/skills/write-school-records/` | Git으로 추적되는 배포본. 플러그인에 포함되어 사용자에게 설치된다. |

두 트리는 아래 차이를 제외하면 동일하게 유지한다.

## 의도된 차이

1. 개발본의 `SKILL.md`에는 `korean-spell-check` 연계가 있다. 15행의 맞춤법 점검 항목, `## 최종 검수 연계`의 3~5단계, 마지막의 `$korean-spell-check` 호출 예시가 이에 해당한다. 개발 환경에서는 해당 스킬을 함께 사용할 수 있으므로 최종 검수 선택지를 제공한다.
2. 배포본의 `SKILL.md`에는 위 연계를 포함하지 않는다. 배포 패키지에는 `korean-character-count`와 `write-school-records`만 포함되며, `korean-spell-check`는 포함되지 않기 때문이다.
3. 개발본의 `scripts/`에는 `sync_install.py`와 `test_sync_install.py`가 추가로 있다. 개발·설치 동기화용 파일이며 배포 패키지에는 필요하지 않다.
4. 개발본의 `scripts/`에는 `trim_achievement_examples.py`가 추가로 있다. 성취수준 코퍼스에서 예시 평가 도구 구간을 잘라내는 정비 도구이며, 스킬 실행 중에는 쓰이지 않는다. 같은 계열의 코퍼스 재현 도구는 저장소의 `tools/corpus/`에 있다.
5. 두 트리의 `scripts/test_skill_integration.py`가 다르다. 이 테스트가 각 트리의 `SKILL.md`를 검사하기 때문이며, 1·2번 차이의 직접적인 결과다. 개발본은 `korean-spell-check` 연계와 맞춤법·재계산 순서를 검증하고, 배포본은 연계 없이 `analyze_record.py`로 최종 확인하는 흐름을 검증한다. 한쪽 `SKILL.md`를 고치면 같은 트리의 이 테스트도 함께 고쳐야 한다.

## 의도되지 않은 차이 확인

두 트리를 비교할 때는 다음 명령을 사용한다. 이 환경에 `diff`가 없으면 같은 비교를 `git diff --no-index --quiet --`로 수행할 수 있다.

```sh
diff -rq skills/write-school-records plugins/korean-school-records-toolkit/skills/write-school-records
```

`__pycache__` 경로는 비교 결과에서 무시한다. 그 밖의 차이는 먼저 이 문서의 의도된 차이인지 확인하고, 해당하지 않으면 드리프트로 조사한다.
