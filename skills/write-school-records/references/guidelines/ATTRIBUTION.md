# 기재요령 원문 출처와 이용 안내

이 디렉터리의 `current.md`와 `versions/`는 교육부가 공개한 학교생활기록부 기재요령을 이 스킬에서 참조할 수 있는 형식으로 정리한 것이다.

## 출처 표시

> 본 저작물은 교육부에서 2026년 작성하여 공공누리 제4유형으로 개방한 「2026학년도 학교생활기록부 기재요령 안내」를 이용하였으며, 해당 저작물은 교육부 홈페이지(https://www.moe.go.kr)에서 무료로 내려받으실 수 있습니다.

- 원문 게시물: [2026학년도 학교생활기록부 기재요령 안내](https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=316&lev=0&statusYN=W&s=moe&m=030215&opType=N&boardSeq=105372)
- 등록일: 2026-02-19 / 담당부서: 교육부 교육과정운영지원과
- 이 스킬이 사용하는 것은 첨부파일 중 `2026 학교생활기록부 기재요령(고등학교).pdf`이다.

## 이용조건

공공누리 **제4유형**: 출처표시 + 상업적 이용금지 + 변경금지

- 출처를 표시해야 한다.
- 상업적 목적으로 이용할 수 없다.
- 원문을 변형하거나 2차적 저작물을 작성할 수 없다.

## 가공 내역

이 디렉터리의 파일은 원문 PDF를 그대로 담은 것이 아니라 아래와 같이 형식을 변환한 것이다. 조건을 판단할 때 이 사실을 함께 확인한다.

- PDF를 Markdown으로 변환했다.
- 표는 HTML `<table>` 구조로 재구성했다.
- 대상 파일이 없어 동작하지 않는 이미지 링크 129개를 제거했다.
- `current.index.md`는 위 변환본에서 생성한 색인이다.

본문 텍스트는 수정하지 않았다. 정확한 문구와 최신 게시 상태는 위 원문 게시물에서 다시 확인한다.

## 최신 원문으로 교체하기

학년도가 바뀌거나 개정본이 나오면 위 게시물에서 원문을 직접 내려받아 등록한다.

```bash
python scripts/update_guidelines.py import <파일 경로> --school-year <학년도> --revision-date <개정일>
python scripts/update_guidelines.py activate --version <버전>
python scripts/update_guidelines.py verify
```

활성 버전과 원문 주소는 `manifest.json`의 `source_url`, `source_title`에 기록된다.
