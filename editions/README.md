# 판(edition) 폴더

이 폴더에는 저장소 루트의 전체판 플러그인(`korean-school-records-toolkit`)에서 만든 다른 판이 있다.

| 폴더 | 내용 |
|---|---|
| `korean-school-records-lite/` | 문서 전용판 플러그인. 스크립트 없이 `write-school-records` 스킬 문서와 참고 자료만 담는다. Claude 플러그인 디렉터리에는 이 폴더를 플러그인 경로로 제출한다. **직접 고치지 않는다.** |
| `source/` | 문서 전용판을 만드는 재료. 이름과 설명(`edition.json`), 바꿔 끼우는 문구(`changes.md`), 문서 전용판에만 있는 `README.md`·`SECURITY.md`. |

아이콘(`.claude-plugin/icon.png`)은 `source/`에 두지 않는다. 전체판 루트의 같은 파일이 원본이고, 빌드가 문서 전용판으로 바이트 그대로 옮긴다. 그림을 바꾸려면 전체판 루트의 파일을 바꾼 뒤 다시 만든다.

전체판이나 `source/`를 고친 뒤 저장소 루트에서 다시 만든다.

```sh
python scripts/build_directory_edition.py
python scripts/build_directory_edition.py --check
```

두 판의 차이와 검사 방법은 [docs/dev-vs-package.md](../docs/dev-vs-package.md)의 「전체판과 문서 전용판의 의도된 차이」에 있다.
