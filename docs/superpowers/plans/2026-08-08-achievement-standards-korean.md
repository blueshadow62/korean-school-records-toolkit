# write-school-records: 국어과 성취수준(A~E) 원문 참조 추가 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-only, verbatim reference corpus of the official 2022 개정 교육과정 국어과 A~E 성취수준 descriptors (all 10 courses: 공통국어1·2 + 8 선택과목) to the `write-school-records` skill, wired in as `curriculum_basis`-tier guidance only.

**Architecture:** Extract the 10 course sections verbatim (image lines stripped) from the single 15,467-line source file into 10 small per-course reference files plus one index file, all under the skill's dev source tree only (`skills/write-school-records/references/achievement-standards/`, which is outside any git repository). Wire a routing-table row and a `curriculum_basis`-only usage constraint into `SKILL.md`, and lock the constraint down with a documentation-contract test in `test_skill_integration.py`.

**Tech Stack:** Python 3 standard library (extraction script), the existing `unittest`-based documentation-contract test pattern already used in `test_skill_integration.py`.

## Global Constraints

- Source file (read-only, never modified): `<원본 자료 폴더>\통합본\2022 개정 교육과정에 따른 성취수준(통합본).md` (15,467 lines, UTF-8).
- **Do not commit anything under `skills/write-school-records/` to git.** That directory is outside any git repository (confirmed: `school-records-toolkit/` top level is not a git repo; only `plugins/korean-school-records-toolkit/` is). None of the tasks below touch `plugins/korean-school-records-toolkit/`, so none of them end with a `git commit` step — this is intentional, not an omission.
- Do not copy any extracted achievement-standard text into `plugins/korean-school-records-toolkit/skills/write-school-records/` (the public package). The source license from NCIC could not be confirmed as open (site footer: "Copyright(C) 2026 by NCIC. ALL RIGHTS RESERVED.") — see the spec's "저작권 확인 결과" section.
- Preserve source wording verbatim in the 10 course files — do not paraphrase or summarize achievement-level sentences.
- Spec: `docs/superpowers/specs/2026-08-08-achievement-standards-korean-design.md`.

## Course boundaries (verified via grep, 1-indexed, inclusive)

| # | 과목 | 시작 줄 | 끝 줄 | 파일명 |
|---|---|---|---|---|
| 1 | 공통국어1 | 444 | 1998 | `공통국어1.md` |
| 2 | 공통국어2 | 1999 | 4083 | `공통국어2.md` |
| 3 | 화법과 언어 | 4084 | 5320 | `화법과_언어.md` |
| 4 | 독서와 작문 | 5321 | 6536 | `독서와_작문.md` |
| 5 | 문학 | 6537 | 7991 | `문학.md` |
| 6 | 주제 탐구 독서 | 7992 | 9193 | `주제_탐구_독서.md` |
| 7 | 문학과 영상 | 9194 | 10700 | `문학과_영상.md` |
| 8 | 직무 의사소통 | 10701 | 11692 | `직무_의사소통.md` |
| 9 | 독서 토론과 글쓰기 | 11693 | 13008 | `독서_토론과_글쓰기.md` |
| 10 | 매체 의사소통 | 13009 | 15467 (EOF) | `매체_의사소통.md` |

Shared intro (Ⅰ. 성취수준 개발의 이해 + Ⅱ. 성취수준 활용, applies to all courses): lines 72–443.

---

### Task 1: Extract the 10 course files and the shared-intro block

**Files:**
- Create: `skills/write-school-records/references/achievement-standards/korean/공통국어1.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/공통국어2.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/화법과_언어.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/독서와_작문.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/문학.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/주제_탐구_독서.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/문학과_영상.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/직무_의사소통.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/독서_토론과_글쓰기.md`
- Create: `skills/write-school-records/references/achievement-standards/korean/매체_의사소통.md`
- Create (temporary, deleted at end of Task 3): `skills/write-school-records/references/achievement-standards/_shared_intro.txt`

**Interfaces:**
- Consumes: nothing (reads only the source file above).
- Produces: 10 files, each starting with its course's `Ⅲ.`–`Ⅹ.` heading line as the first non-blank line, with no `![image](...)` lines anywhere in the file. Task 2 (index.md) and Task 4 (SKILL.md) depend on these exact file paths and on the shared-intro text file.

- [ ] **Step 1: Run the extraction script**

```bash
cd "<repo>\skills\write-school-records"
mkdir -p references/achievement-standards/korean
python3 - <<'PY'
from pathlib import Path

SRC = Path(r"<원본 자료 폴더>\통합본\2022 개정 교육과정에 따른 성취수준(통합본).md")
OUT_DIR = Path("references/achievement-standards/korean")
SHARED_OUT = Path("references/achievement-standards/_shared_intro.txt")

COURSES = [
    (444, 1998, "공통국어1.md"),
    (1999, 4083, "공통국어2.md"),
    (4084, 5320, "화법과_언어.md"),
    (5321, 6536, "독서와_작문.md"),
    (6537, 7991, "문학.md"),
    (7992, 9193, "주제_탐구_독서.md"),
    (9194, 10700, "문학과_영상.md"),
    (10701, 11692, "직무_의사소통.md"),
    (11693, 13008, "독서_토론과_글쓰기.md"),
    (13009, 15467, "매체_의사소통.md"),
]
SHARED_INTRO = (72, 443)

lines = SRC.read_text(encoding="utf-8").splitlines()

def clean(chunk_lines):
    return [ln for ln in chunk_lines if not ln.strip().startswith("![image]")]

for start, end, filename in COURSES:
    chunk = clean(lines[start - 1:end])
    out_path = OUT_DIR / filename
    out_path.write_text("\n".join(chunk) + "\n", encoding="utf-8")
    print(f"{filename}: {len(chunk)} lines")

start, end = SHARED_INTRO
shared_chunk = clean(lines[start - 1:end])
SHARED_OUT.write_text("\n".join(shared_chunk) + "\n", encoding="utf-8")
print(f"_shared_intro.txt: {len(shared_chunk)} lines")
PY
```

Expected output: 11 lines printed (10 course files + the shared intro), each with a nonzero line count, e.g. `공통국어1.md: 1523 lines`.

- [ ] **Step 2: Confirm the 10 files and the shared-intro file exist**

```bash
ls -la references/achievement-standards/korean/
ls -la references/achievement-standards/_shared_intro.txt
```

Expected: 10 files under `korean/`, plus the one file directly under `achievement-standards/`.

---

### Task 2: Verify extraction boundaries (no bleed, no leftover image lines, real headings)

**Files:**
- Read only: the 10 files and `_shared_intro.txt` from Task 1.

**Interfaces:**
- Consumes: file paths produced by Task 1.
- Produces: a pass/fail confirmation gate for Task 3. Do not proceed to Task 3 until every check below passes.

- [ ] **Step 1: Check no file contains an image placeholder line**

```bash
cd "<repo>\skills\write-school-records"
grep -rl '^!\[image\]' references/achievement-standards/ || echo "PASS: no image lines"
```

Expected: `PASS: no image lines`. If grep prints file paths instead, Task 1's `clean()` filter did not run correctly on that file — re-run Task 1.

- [ ] **Step 2: Check each course file starts with its own heading and does not contain the next course's heading (no bleed-over)**

```bash
python3 - <<'PY'
from pathlib import Path

OUT_DIR = Path("references/achievement-standards/korean")
CHECKS = [
    ("공통국어1.md", "공통국어1 성취수준", "Ⅳ. 공통국어2 성취수준"),
    ("공통국어2.md", "공통국어2 성취수준", "Ⅲ. 화법과 언어 성취수준"),
    ("화법과_언어.md", "화법과 언어 성취수준", "Ⅳ. 독서와 작문 성취수준"),
    ("독서와_작문.md", "독서와 작문 성취수준", "Ⅴ. 문학 성취수준"),
    ("문학.md", "문학 성취수준", "Ⅵ. 주제 탐구 독서 성취수준"),
    ("주제_탐구_독서.md", "주제 탐구 독서 성취수준", "Ⅶ. 문학과 영상 성취수준"),
    ("문학과_영상.md", "문학과 영상 성취수준", "Ⅷ. 직무 의사소통 성취수준"),
    ("직무_의사소통.md", "직무 의사소통 성취수준", "Ⅸ. 독서 토론과 글쓰기 성취수준"),
    ("독서_토론과_글쓰기.md", "독서 토론과 글쓰기 성취수준", "Ⅹ. 매체 의사소통 성취수준"),
    ("매체_의사소통.md", "매체 의사소통 성취수준", None),
]

failures = []
for filename, must_contain, must_not_contain in CHECKS:
    text = (OUT_DIR / filename).read_text(encoding="utf-8")
    if must_contain not in text:
        failures.append(f"{filename}: missing expected heading text {must_contain!r}")
    if must_not_contain and must_not_contain in text:
        failures.append(f"{filename}: bled into next course, found {must_not_contain!r}")

if failures:
    print("FAIL:")
    for f in failures:
        print(" -", f)
    raise SystemExit(1)
print(f"PASS: all {len(CHECKS)} course files verified")
PY
```

Expected: `PASS: all 10 course files verified`. If it fails, re-check the corresponding line range in the boundary table against a fresh `grep -n` on the source file before re-running Task 1.

- [ ] **Step 3: Manually spot-read the tail of the largest file for OCR garbage**

`매체_의사소통.md` is the file closest to the end of a 15,467-line OCR'd document, and is the most likely place for scan artifacts. Read the last ~40 lines and confirm they read as legitimate 예시 평가 도구 content (rubric tables, "채점 기준" text), not garbled characters or an unrelated trailing section.

```bash
tail -n 40 references/achievement-standards/korean/매체_의사소통.md
```

Read the output. If it looks garbled or clearly off-topic, stop and re-examine the source file around line 15467 before continuing.

---

### Task 3: Write index.md (shared intro + per-course routing table), remove the temp file

**Files:**
- Create: `skills/write-school-records/references/achievement-standards/index.md`
- Delete: `skills/write-school-records/references/achievement-standards/_shared_intro.txt` (its content is folded into `index.md` in this task)

**Interfaces:**
- Consumes: `_shared_intro.txt` content from Task 1; the 10 filenames from the boundary table.
- Produces: `references/achievement-standards/index.md` — the path Task 4's `SKILL.md` routing row points to. Must contain a markdown table listing all 10 course names mapped to their `korean/<file>.md` path, since Task 5's test asserts on this table's presence.

- [ ] **Step 1: Read the shared-intro text to use as the file's opening section**

```bash
cd "<repo>\skills\write-school-records"
cat references/achievement-standards/_shared_intro.txt
```

- [ ] **Step 2: Write `index.md`**

Create the file with this structure. The `<...>` placeholder below is intentional, not a shortcut: it is ~370 lines of the same uncertain-license source text this whole plan keeps out of the public git repo (see Global Constraints), so it cannot be hardcoded into this plan file, which itself lives in the public repo. Paste in the literal output of Step 1 verbatim, do not summarize. The table below must be included exactly as shown so Task 5's test can assert on it:

```markdown
# 국어과 성취수준(A~E) 원문 색인

2022 개정 교육과정 국어과 공통·선택과목 성취수준 연구보고서 원문(교육부 계열, 로컬 전용 — 공개 저장소에는 포함하지 않음)의 과목별 안내다. 학생의 실제 성취를 이 자료로 새로 만들거나 단정하지 않으며, 교사가 확인한 사실을 서술할 때 공식 어휘·강도를 맞추는 `curriculum_basis` 등급 참고 자료로만 사용한다.

## 성취수준이란 (공통 배경)

<여기에 Step 1에서 읽은 _shared_intro.txt 내용을 그대로 붙여넣는다>

## 과목별 파일

| 과목 | 파일 |
|---|---|
| 공통국어1 | [korean/공통국어1.md](korean/공통국어1.md) |
| 공통국어2 | [korean/공통국어2.md](korean/공통국어2.md) |
| 화법과 언어 | [korean/화법과_언어.md](korean/화법과_언어.md) |
| 독서와 작문 | [korean/독서와_작문.md](korean/독서와_작문.md) |
| 문학 | [korean/문학.md](korean/문학.md) |
| 주제 탐구 독서 | [korean/주제_탐구_독서.md](korean/주제_탐구_독서.md) |
| 문학과 영상 | [korean/문학과_영상.md](korean/문학과_영상.md) |
| 직무 의사소통 | [korean/직무_의사소통.md](korean/직무_의사소통.md) |
| 독서 토론과 글쓰기 | [korean/독서_토론과_글쓰기.md](korean/독서_토론과_글쓰기.md) |
| 매체 의사소통 | [korean/매체_의사소통.md](korean/매체_의사소통.md) |
```

- [ ] **Step 3: Remove the temporary shared-intro file**

```bash
rm references/achievement-standards/_shared_intro.txt
```

- [ ] **Step 4: Verify the final directory layout**

```bash
find references/achievement-standards -type f | sort
```

Expected: exactly 11 files — `index.md` plus the 10 files under `korean/`. No `_shared_intro.txt`.

---

### Task 4: Wire the reference into SKILL.md

**Files:**
- Modify: `skills/write-school-records/SKILL.md`

**Interfaces:**
- Consumes: `references/achievement-standards/index.md` path from Task 3.
- Produces: two exact substrings in `SKILL.md` that Task 5's test asserts on verbatim:
  1. `"[achievement-standards/index.md](references/achievement-standards/index.md)"`
  2. `"국어 성취수준 자료는 \`curriculum_basis\` 등급으로만 사용한다."`

- [ ] **Step 1: Add a row to the existing "최소 참조 라우팅" table**

Find this table in `SKILL.md` (currently the last row is the source-policy row):

```
| 현행 규정·출처·자료 시점 질문 | [source-policy.md](references/source-policy.md) |
```

Add a new row directly after it:

```
| 국어 성취수준(A~E) 공식 서술과 대조 | [achievement-standards/index.md](references/achievement-standards/index.md)에서 과목을 확인한 뒤 해당 과목 파일만 읽는다 |
```

- [ ] **Step 2: Add the usage-constraint paragraph**

Find this existing paragraph in `SKILL.md` (currently right after the routing table):

```
기재요령 갱신 요청은 `scripts/update_guidelines.py`로 처리한다.
```

Insert a new paragraph directly before it:

```
국어 성취수준 자료는 `curriculum_basis` 등급으로만 사용한다. 학생의 실제 성취를 이 자료로 새로 만들거나 단정하지 않으며, 교사가 확인한 사실을 서술할 때 공식 어휘·강도를 맞추는 용도로만 쓴다.
```

- [ ] **Step 3: Verify both strings landed correctly**

```bash
cd "<repo>\skills\write-school-records"
grep -F "achievement-standards/index.md" SKILL.md
grep -F 'curriculum_basis` 등급으로만 사용한다' SKILL.md
```

Expected: one match each.

---

### Task 5: Add the documentation-contract test

**Files:**
- Modify: `skills/write-school-records/scripts/test_skill_integration.py`
- Test: same file (this project's convention is documentation-contract tests co-located in this one file — see the existing `SkillIntegrationContractTests` class)

**Interfaces:**
- Consumes: `SKILL_TEXT` module-level constant already defined at the top of this file (`SKILL_TEXT = (Path(__file__).parents[1] / "SKILL.md").read_text(encoding="utf-8")`).
- Produces: nothing consumed by later tasks — this is the last content task.

- [ ] **Step 1: Write the failing test**

Add this method to the existing `SkillIntegrationContractTests` class (place it after `test_spell_then_count_order_is_explicit`, matching the file's existing style of one method per contract):

```python
    def test_achievement_standards_reference_is_curriculum_basis_only(self) -> None:
        self.assertIn("achievement-standards/index.md", SKILL_TEXT)
        self.assertIn("국어 성취수준 자료는 `curriculum_basis` 등급으로만 사용한다", SKILL_TEXT)
        self.assertIn("학생의 실제 성취를 이 자료로 새로 만들거나 단정하지 않으며", SKILL_TEXT)
```

- [ ] **Step 2: Run the test to verify it currently passes**

(Task 4 already added the text this test checks for, so this confirms Task 4 landed correctly rather than testing a fail-first cycle — that's expected here since Task 4 and Task 5 both encode the same contract.)

```bash
cd "<repo>\skills\write-school-records\scripts"
python -m unittest test_skill_integration.SkillIntegrationContractTests.test_achievement_standards_reference_is_curriculum_basis_only -v
```

Expected: `ok`, 1 test run.

---

### Task 6: Full regression run

**Files:** none (verification only).

- [ ] **Step 1: Run the full write-school-records test suite**

```bash
cd "<repo>\skills\write-school-records\scripts"
python -m unittest test_analyze_record test_compare_neis_counts test_sync_install test_update_guidelines test_skill_integration -v
```

Expected: all tests pass (75 tests before this plan; 76 after Task 5 adds one).

- [ ] **Step 2: Confirm nothing was written to the public package or to git**

```bash
cd "<repo>\plugins\korean-school-records-toolkit"
git status --short
```

Expected: empty output (no changes) — this plan does not touch anything under `plugins/korean-school-records-toolkit/`.

```bash
find "<repo>\plugins\korean-school-records-toolkit\skills\write-school-records" -iname "achievement-standards"
```

Expected: no output (the reference folder must not exist in the public package copy).
