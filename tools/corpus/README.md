# 성취수준 코퍼스 재현 도구

원본 PDF/HWPX에서 성취수준 코퍼스를 재변환하고 전수 검증하기 위한 도구 모음입니다.

## 스크립트

- `convert_nkis_pdfs_v2.py`: NKIS PDF를 kordoc v4를 사용해 Markdown으로 변환합니다.
- `slice_kordoc_courses.py`: 변환된 Markdown을 과목별 코퍼스 파일로 분할하고 검증합니다.
- `verify_corpus_against_pdfs.py`: 코퍼스 187개를 원본 PDF와 셀 단위로 대조합니다.
- `verify_corpus_against_hwpx.py`: 코퍼스 37개를 원본 HWPX/HWP와 셀 단위로 대조합니다.

## 파이프라인

변환 → 분할 → 검증 순서로 실행합니다. 검증은 원본 형식에 따라 PDF 검증과 HWPX/HWP 검증을 각각 실행합니다.

## 실행 명령

아래 명령은 실제 동작이 확인된 실행 형식입니다.

```text
python tools/corpus/convert_nkis_pdfs_v2.py --pdf-root "<원본 PDF 폴더>" --output "<출력 MD 폴더>" --npx "C:/nvm4w/nodejs/npx.cmd"
python tools/corpus/slice_kordoc_courses.py --md-root "<출력 MD 폴더>" --corpus "plugins/korean-school-records-toolkit/skills/write-school-records/references/achievement-standards" --skip-list rebuild-report.json --git-root plugins/korean-school-records-toolkit --apply --report slice-all.tsv
python tools/corpus/verify_corpus_against_pdfs.py --corpus "<코퍼스 경로>" --pdf-root "<원본 PDF 폴더>" --map slice-all.tsv --report verify-corpus.tsv
python tools/corpus/verify_corpus_against_hwpx.py --corpus "<코퍼스 경로>" --list protected37.txt --hwpx <원본 hwpx/hwp 파일들> --report verify-hwpx.tsv
```

## 의존성

- Python 패키지: `pdfplumber`, `olefile`
- Node.js의 `npx`(kordoc v4용)

## 알려진 함정

1. Windows에서는 `shutil.which("npx")`가 실패할 수 있으므로 `--npx`로 `npx.cmd` 경로를 직접 넘겨야 합니다.
2. 검증 기준선에는 반드시 `git show HEAD:`를 사용해야 합니다. 작업 트리와 비교하면 도구가 자기 이전 출력과 비교하게 되어 검증이 무의미해집니다.

## 마지막 검증 결과

224개 파일의 25,486셀 전부가 원본과 일치했으며, 누락은 0개였습니다.
