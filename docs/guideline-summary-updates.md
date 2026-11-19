# 기재요령 요약 갱신 절차

새 학년도 기재요령이 나오거나 같은 학년도에 개정·정정본이 게시되면 아래 순서로 요약을 갱신한다. 대상 파일은 `skills/write-school-records/references/guidelines/summary.md`(고등학교)와 `skills/write-school-records/references/guidelines-middle/summary.md`(중학교), 그리고 같은 폴더의 `analyzer-rules/<학년도>.json`, 중학교 `differences.md`다.

## 누가

개발본(`skills/write-school-records/`, 원문 변환본이 있는 작업 트리)을 관리하는 사람이 한다. 배포본에는 원문이 없어 원문 대조 테스트가 돌지 않으므로 배포본에서 갱신하지 않는다. 갱신한 요약은 작성자와 다른 사람(또는 다른 계정의 검증 에이전트)이 추적표로 원문과 대조한 뒤 배포본에 반영한다.

## 무엇을 보고

1. 교육부 게시물의 새 원문 PDF(고등학교판·중학교판)와 게시일, 개정일, 근거 훈령 번호.
2. 개발본에 등록한 새 원문 변환본(`current.md`)과 색인(`current.index.md`).
3. 이전 학년도 원문과 장별 차이: 「작성 시 유의사항」, 「문의 방법」, 「처리요령」, 창체, 교과학습발달상황, 자유학기활동상황(중), 독서, 행특, 「영역별 입력 가능 최대 글자수」 표, 대입 관련 변경 표.
4. 이전 추적표(`reports/guideline-summary-trace-<날짜>.md`, 개발 저장소에만 있음)의 규칙별 근거 행.

## 절차

1. 개발본에 새 원문을 등록하고 활성화한다.
   ```bash
   python scripts/update_guidelines.py import --input <변환본.md> --school-year <학년도> --revision-date <개정일> --source-title "<제목>" --source-url "<주소>" --confirmed-official --activate
   python scripts/update_guidelines.py --level middle import --input <변환본.md> --school-year <학년도> --revision-date <개정일> --source-title "<제목>" --source-url "<주소>" --confirmed-official --activate
   ```
   변환은 `USER_GUIDE.md` 「기재요령 원문을 직접 등록하기」를 따르고, 쪽 묶음마다 원본 PDF와 글자 수를 대조해 빠진 쪽이 없는지 확인한다.
2. `analyzer-rules/<새 학년도>.json`이 이전 학년도 규칙을 복사한 미검토 초안(`reviewed: false`)으로 생긴다. 새 원문의 최대 글자수 표와 유의사항 장에 맞춰 한도와 금지 표현 이름을 고치고 `reviewed`를 `true`로 바꾼다.
3. `summary.md`를 고친다.
   - 머리말의 `school_year`, `revision_date`, `source_title`, `source_url`, `source_posted`, `directive`, `summary_written`을 새 원문에 맞춘다.
   - 바뀐 규칙을 고치고, 없어진 규칙은 지우고, 새 규칙은 같은 짜임(누가·누구에게·무엇을 쓸 수 있고 없는지·예외·한도)으로 더한다. 원문 해설 문장을 옮기지 않는다.
   - 인용한 훈령 조문은 새 원문에서 다시 옮긴다. 조문이 바뀌었으면 인용도 바꾼다.
   - 장 제목과 장 번호가 바뀌었으면 약칭 표와 각 규칙의 〔 〕 표기를 고친다.
   - 최대 글자수 표는 새 원문 표를 행 순서까지 그대로 옮긴다.
   - 기록 여부나 쓰는 위치를 가르는 조건(예외 기관, 인정 범위, 날짜 기준 등)은 '지원하지 않는 영역의 장에 있다'는 이유로 빼지 않는다. 지원 영역의 기록에 닿으면 넣는다. 원문의 기재예시를 실으면 '기재요령의 예시 문구'라고 표시한다.
4. 중학교 `differences.md`의 차이를 새 두 판으로 다시 확인한다.
5. 추적표를 새로 만든다. 규칙마다 원문 근거 행을 다시 찾고, 요약에 넣지 않은 규정과 이유를 적는다.
6. SKILL.md와 영역별 안내 문서의 규정 게이트, `output-skeleton.md`의 한도 문장이 새 요약과 어긋나지 않는지 본다. 게이트가 가리키는 요약 규칙 번호가 바뀌었으면 함께 고친다. 기재요령의 의무·권장과 이 스킬이 더 보수적으로 정한 '스킬 원칙'을 섞어 쓰지 않는다.

## 어떤 테스트로 확인하나

개발본에서 실행한다(원문이 있어야 원문 대조 테스트가 돈다).

```bash
python -m unittest discover -s scripts -p "test_*.py"
```

- `test_guideline_summary.py`: 요약 머리말이 등록된 원문의 학년도·개정일·제목·주소와 같은지, 최대 글자수 표의 모든 행이 원문 표와 같은지, 인용 조문이 원문과 글자 그대로 같은지, 장 제목과 금지 항목 이름이 원문에 있는지, 요약 표와 검사 규칙의 한도가 같은지 본다. 원문만 새 학년도로 바꾸고 요약을 고치지 않으면 여기서 실패한다. 기록 여부를 가르는 조건 문구 목록(`CONDITION_ANCHORS`)은 요약 규칙 줄과 원문 양쪽에 있어야 한다. 새 원문에서 조건이 바뀌어 실패하면 요약과 이 목록을 함께 고친다. 영역 안내 문서가 가리키는 규칙 번호가 요약에 있는지도 여기서 본다.
- `test_guidelines_high.py`, `test_guidelines_middle.py`: SKILL.md가 말하는 한도가 요약 표와 원문 표에 있는지, 차이 문서의 장 제목이 원문에 있는지 본다.
- `test_analyze_record.py`, `test_update_guidelines.py`: 원문이 없을 때 요약 기준으로 동작하는지, 원문을 등록하면 원문 기준으로 바뀌는지 본다.

배포본에 요약·검사 규칙·차이 문서를 옮긴 뒤 배포본에서 다음을 실행한다. 원문 대조 테스트는 건너뛰어지고 나머지는 모두 돈다.

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s skills/write-school-records/scripts -p "test_*.py"
python scripts/verify_package.py
```

`verify_package.py`와 `tests/test_package.py`는 배포본에 원문 변환본이 들어가지 않았는지, 요약 머리말과 그 학년도의 검사 규칙이 있는지 확인한다. 마지막으로 행동 평가 사례 가운데 규정 질문과 분량 기준을 쓰는 사례를 배포본으로 다시 실행해 응답이 새 요약을 따르는지 본다.
