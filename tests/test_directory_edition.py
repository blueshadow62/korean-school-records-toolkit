#!/usr/bin/env python3
"""문서 전용판(editions/<이름>/)이 전체판에서 정해진 규칙으로 만들어졌고 디렉터리 제출 규칙에 맞는지 검사한다.

흐름은 개발본 → 전체판(저장소 루트) → 문서 전용판이다. 전체판에서 문서 전용판으로 갈 때의 의도된 차이는
docs/dev-vs-package.md와 editions/source/changes.md에 있다.
"""

from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = PLUGIN_ROOT / "scripts" / "build_directory_edition.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_directory_edition", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()
EDITION = BUILDER.edition_folder(PLUGIN_ROOT)
SKILL = "skills/write-school-records"
FENCE = re.compile(r"^\s*```")
# 스크립트·시험 자료·원문 등록에 관한 말. 문서 전용판에서 바꾸는 SKILL.md·참조 문서의 줄은 이 가운데 하나를 담아야 한다.
SCRIPT_TERMS = re.compile(
    r"scripts/|\.py\b|analyze_record|update_guidelines|compare_neis|korean-character-count|tests/|"
    r"analyzer-rules|index-terms|기계 점검|직접 등록|기재요령 등록|`--"
)
# 전체판과 글자 하나 다르지 않아야 하는 SKILL.md의 절: 공통 게이트, 학교급 확인, 근거 등급(작성 절차 안), 서술 구조, 품질 게이트.
PROTECTED_SECTIONS = ("현행 공통 준수 게이트", "학교급 확인", "작성 절차", "근거 기반 서술 구조", "문장 품질 게이트")
# 문서 전용판의 스킬 문서에 남으면 안 되는, 이 판에 없는 도구·자료의 이름.
ABSENT_TOOLS = ("analyze_record", "update_guidelines", "compare_neis", "korean-character-count", "tests/",
                "eval-cases", "neis-validation", "agents/openai.yaml")


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def sections(document: str) -> dict[str, str]:
    """'## ' 제목 단위로 나눈다. '### ' 소절은 위 절에 들어간다. 머리말(제목 앞)은 '' 키다."""
    result, title, lines = {}, "", []
    for line in document.split("\n"):
        if line.startswith("## "):
            result[title] = "\n".join(lines)
            title, lines = line[3:].strip(), []
        else:
            lines.append(line)
    result[title] = "\n".join(lines)
    return result


class EditionBuildTests(unittest.TestCase):
    def test_committed_edition_matches_a_fresh_build(self) -> None:
        # 전체판을 고치고 문서 전용판을 다시 만들지 않으면 여기서 잡힌다.
        problems = BUILDER.compare(BUILDER.build(PLUGIN_ROOT), EDITION)
        self.assertEqual([], problems, "python scripts/build_directory_edition.py로 다시 만든다")

    def test_check_passes_and_no_stale_edition_folder_remains(self) -> None:
        self.assertEqual([], BUILDER.check(PLUGIN_ROOT))

    def test_edition_follows_full_skill_changes_outside_the_replaced_parts(self) -> None:
        # 바꿔 끼우는 곳 밖의 전체판 수정은 문서 전용판에 그대로 들어간다.
        changes = BUILDER.load_changes(PLUGIN_ROOT)
        full = text(PLUGIN_ROOT / SKILL / "SKILL.md")
        edited = full.replace("## 학교급 확인\n", "## 학교급 확인\n\n새로 넣은 규칙 문장.\n", 1)
        self.assertIn("새로 넣은 규칙 문장.", BUILDER.apply_changes(f"{SKILL}/SKILL.md", edited, changes))

    def test_build_stops_when_a_replaced_part_of_the_full_skill_changes(self) -> None:
        # 바꿔 끼우는 문구가 전체판에서 바뀌면 조용히 넘어가지 않고 빌드가 멈춘다.
        changes = BUILDER.load_changes(PLUGIN_ROOT)
        full = text(PLUGIN_ROOT / SKILL / "SKILL.md")
        edited = full.replace("`scripts/analyze_record.py`를 단일 진입점으로", "`scripts/analyze_record.py`를 진입점으로", 1)
        self.assertNotEqual(full, edited)
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.apply_changes(f"{SKILL}/SKILL.md", edited, changes)

    def test_build_stops_on_duplicate_or_overlapping_find_text(self) -> None:
        change = BUILDER.Change("a.md", "같은 문장.", "바뀐 문장.", 1)
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.apply_changes("a.md", "같은 문장. 같은 문장.", [change])
        overlapping = [BUILDER.Change("a.md", "가나다", "x", 1), BUILDER.Change("a.md", "나다라", "y", 2)]
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.apply_changes("a.md", "가나다라", overlapping)

    def test_build_stops_on_a_skill_file_without_a_rule(self) -> None:
        # 스킬 폴더에 새 종류의 파일이 생기면 넣을지 뺄지 사람이 정하게 한다.
        for relative in ("references/figure.png", "notes.txt", "references/data.csv"):
            with self.subTest(relative=relative), self.assertRaises(BUILDER.BuildError):
                BUILDER.classify_skill_file(relative)
        self.assertEqual(False, BUILDER.classify_skill_file("scripts/analyze_record.py")[0])
        self.assertEqual(False, BUILDER.classify_skill_file("references/guidelines/current.md")[0])
        self.assertEqual(False, BUILDER.classify_skill_file("references/guidelines-middle/analyzer-rules/2026.json")[0])
        self.assertEqual(True, BUILDER.classify_skill_file("references/guidelines/summary.md")[0])

    def test_changes_file_parses_into_pairs(self) -> None:
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.parse_changes("````find a.md\n문장\n````\n")
        with self.assertRaises(BUILDER.BuildError):
            BUILDER.parse_changes("````replace\n문장\n````\n")
        pairs = BUILDER.parse_changes("설명\n\n````find a.md\n옛 문장\n````\n\n````replace\n새 문장\n````\n")
        self.assertEqual([("a.md", "옛 문장", "새 문장")], [(c.path, c.find, c.replace) for c in pairs])


class EditionContentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.full = text(PLUGIN_ROOT / SKILL / "SKILL.md")
        self.edition = text(EDITION / SKILL / "SKILL.md")
        self.changes = BUILDER.load_changes(PLUGIN_ROOT)

    def test_skill_md_differs_only_in_script_parts(self) -> None:
        skill_changes = [c for c in self.changes if c.path == f"{SKILL}/SKILL.md"]
        self.assertTrue(skill_changes)
        for change in skill_changes:
            for line in change.find.split("\n"):
                if line.strip() and not FENCE.match(line):
                    with self.subTest(line=line[:60]):
                        self.assertRegex(line, SCRIPT_TERMS, "스크립트와 관계없는 줄을 바꾸고 있다")
        full, edition = sections(self.full), sections(self.edition)
        self.assertEqual(list(full), list(edition), "절 구성이 전체판과 다르다")
        for title in PROTECTED_SECTIONS:
            with self.subTest(section=title):
                self.assertEqual(full[title], edition[title])

    def test_routing_quick_path_and_output_rules_match_the_full_skill(self) -> None:
        full, edition = sections(self.full), sections(self.edition)
        # 라우팅 표: 스킬 행동 검증 행만 다르다.
        rows = lambda body: [line for line in body.split("\n") if line.startswith("|") and "스킬 행동 검증" not in line]
        self.assertEqual(rows(full["최소 참조 라우팅"]), rows(edition["최소 참조 라우팅"]))
        # 빠른 경로: 5·7번(원문 등록과 스크립트 실행)만 다르다.
        items = lambda body: [line for line in body.split("\n") if re.match(r"[1-9]\. ", line) and line[0] not in "57"]
        self.assertEqual(items(full["빠른 경로"]), items(edition["빠른 경로"]))
        # 출력과 점검: 응답 순서와 최종 확인 목록은 같고, 그 뒤의 기계 점검 안내만 바뀐다.
        head_full = full["출력과 점검"].split("\n초안 생성 뒤에만 기계 점검이")[0]
        head_edition = edition["출력과 점검"].split("\n### 글자 수와 바이트 계산")[0]
        self.assertEqual(head_full, head_edition)

    def test_reference_variants_differ_only_in_script_parts(self) -> None:
        reference_changes = [c for c in self.changes if c.path.startswith(f"{SKILL}/references/")]
        self.assertTrue(reference_changes)
        for change in reference_changes:
            for line in change.find.split("\n"):
                if line.strip() and not FENCE.match(line):
                    with self.subTest(file=change.path, line=line[:60]):
                        self.assertRegex(line, SCRIPT_TERMS, "스크립트와 관계없는 줄을 바꾸고 있다")

    def test_edition_skill_documents_name_no_absent_tool(self) -> None:
        for relative, path in BUILDER.folder_files(EDITION / SKILL).items():
            if not relative.endswith(".md"):
                continue
            body = text(path)
            for name in ABSENT_TOOLS:
                with self.subTest(file=relative, name=name):
                    self.assertNotIn(name, body)

    def test_counting_rule_matches_the_full_checker(self) -> None:
        # 문서 전용판은 코드 실행 도구로 센다. 그 방법이 전체판 점검기의 정규화·계산과 같아야 한다.
        analyzer = text(PLUGIN_ROOT / SKILL / "scripts" / "analyze_record.py")
        self.assertIn('return text.replace("\\r\\n", "\\n").strip()', analyzer)
        self.assertIn("char_count = len(normalized)", analyzer)
        self.assertIn('neis_bytes = len(normalized.encode("utf-8"))', analyzer)
        self.assertIn('t = text.replace("\\r\\n", "\\n").strip()', self.edition)
        self.assertIn('print(len(t), len(t.encode("utf-8")))', self.edition)
        self.assertIn("글자 수는 기계로 점검하지 못했습니다.", self.edition)
        skeleton = text(EDITION / SKILL / "references" / "output-skeleton.md")
        self.assertIn("글자 수는 기계로 점검하지 못했습니다.", skeleton)
        self.assertIn("짐작한 값을 계산값처럼 적지 않는다", skeleton)

    def test_readme_carries_the_notices_the_listing_needs(self) -> None:
        readme = text(EDITION / "README.md")
        self.assertGreaterEqual(BUILDER.readme_words(readme), BUILDER.MIN_README_WORDS)
        for phrase in ("보조 초안", "고지 의무", "요약", "공식 효력은 교육부 원문에 있", "네트워크에 접속하지 않",
                       "수집하거나 외부로 보내지 않", "https://github.com/blueshadow62/korean-school-records-toolkit"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_license_covers_only_what_this_edition_holds(self) -> None:
        license_text = text(EDITION / "LICENSE")
        for phrase in ("CC BY-NC-SA 4.0", "류기현", "achievement-standards-middle", "Korea Open Government License Type 4",
                       "references/source-policy.md"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, license_text)
        self.assertNotIn("MIT", license_text)
        self.assertNotIn("skills/korean-character-count", license_text)

    def test_manifest_and_marketplace_entry(self) -> None:
        config = BUILDER.edition_config(PLUGIN_ROOT)
        manifest = json.loads(text(EDITION / ".claude-plugin" / "plugin.json"))
        self.assertEqual(config["name"], manifest["name"])
        self.assertEqual(EDITION.name, manifest["name"])
        self.assertEqual((PLUGIN_ROOT / "VERSION").read_text(encoding="utf-8").strip(), manifest["version"])
        self.assertNotIn("icon", manifest)
        self.assertEqual([], BUILDER.check_manifest(EDITION, PLUGIN_ROOT))
        marketplace = json.loads(text(PLUGIN_ROOT / ".claude-plugin" / "marketplace.json"))
        entry = next(e for e in marketplace["plugins"] if e["name"] == manifest["name"])
        self.assertEqual(f"./editions/{manifest['name']}", entry["source"])
        self.assertTrue((PLUGIN_ROOT / entry["source"] / ".claude-plugin" / "plugin.json").is_file())


class DirectoryRuleTests(unittest.TestCase):
    """디렉터리 개발자 포털의 파일 규칙(인증된 조직이 아닌 계정 기준)을 커밋된 폴더에 적용한다."""

    def test_committed_edition_follows_each_rule(self) -> None:
        for check in BUILDER.AUDITS:
            with self.subTest(rule=check.__name__):
                self.assertEqual([], check(EDITION))

    def test_file_count_and_size_are_within_limits(self) -> None:
        files = BUILDER.folder_files(EDITION)
        self.assertLessEqual(len(files), BUILDER.MAX_FILES)
        self.assertLess(max(path.stat().st_size for path in files.values()), BUILDER.MAX_FILE_BYTES)


class DirectoryRuleCatchesProblemsTests(unittest.TestCase):
    """규칙 검사가 실제로 문제를 잡는지 시험용 폴더로 확인한다."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / "sample-plugin"
        (self.folder / ".claude-plugin").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def put(self, relative: str, data: bytes) -> None:
        path = self.folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def test_rejects_files_outside_the_allowed_list(self) -> None:
        for relative in ("VERSION", "run.sh", "tool.py", "page.html", "icon.svg"):
            self.put(relative, b"x\n")
        self.put("notes.md", b"# ok\n")
        self.put("LICENSE", b"text\n")
        problems = BUILDER.check_file_types(self.folder)
        self.assertEqual(5, len(problems), problems)

    def test_rejects_shebang_nul_and_non_utf8(self) -> None:
        self.put("a.md", b"#!/bin/sh\necho\n")
        self.put("b.md", b"text\x00more\n")
        self.put("c.md", "한글".encode("cp949"))
        self.assertEqual(1, len(BUILDER.check_no_shebang(self.folder)))
        self.assertEqual(2, len(BUILDER.check_encoding(self.folder)))

    def test_rejects_large_files(self) -> None:
        self.put("big.md", b"a" * BUILDER.MAX_FILE_BYTES)
        self.put("small.md", b"a" * (BUILDER.MAX_FILE_BYTES - 1))
        self.assertEqual(1, len(BUILDER.check_limits(self.folder)))

    def test_rejects_package_manager_and_foreign_plugin_files(self) -> None:
        self.put("package.json", b"{}\n")
        self.put("pnpm-workspace.yaml", b"packages: []\n")
        self.put("nested/.claude-plugin/plugin.json", b"{}\n")
        self.put(".claude/skills/x/SKILL.md", b"---\n")
        self.put(".claude-plugin/notes.md", b"x\n")
        self.put(".mcp.json", b"{}\n")
        self.assertEqual(6, len(BUILDER.check_forbidden_files(self.folder)))

    def test_rejects_names_that_do_not_survive_windows_and_macos(self) -> None:
        # 마지막 이름은 '가'를 풀어쓴 꼴(NFD)이다.
        for relative in ("con.md", "a:b.md", "folder./x.md", "x /y.md", "가.md"):
            with self.subTest(relative=relative):
                self.assertTrue(BUILDER.portable_name_problems(relative))
        self.assertEqual([], BUILDER.portable_name_problems("references/achievement-standards/수학.md"))
        self.assertTrue(BUILDER.case_collisions(["a/Index.md", "a/index.md"]))

    def test_rejects_short_readme_and_counts_words_outside_code(self) -> None:
        self.put("README.md", ("짧은 설명입니다.\n\n```\n" + "코드 " * 100 + "\n```\n").encode("utf-8"))
        self.assertEqual(1, len(BUILDER.check_readme(self.folder)))
        self.assertEqual(2, BUILDER.readme_words(text(self.folder / "README.md")))

    def test_rejects_install_commands_script_names_and_environment_credentials(self) -> None:
        self.put("a.md", b"npx some-package@1.0.0\npip install x\n--registry https://example.org\n")
        self.put("b.md", b"python scripts/analyze_record.py --file x\n")
        self.put("c.md", b"curl -H \"Authorization: Bearer $GITHUB_TOKEN\"\nsee ~/.codex/auth.json\n")
        self.put("d.md", "Node.js 18 이상과 Python 3를 씁니다.\n".encode("utf-8"))
        commands = BUILDER.check_no_install_or_script_commands(self.folder)
        self.assertEqual(4, len(commands), commands)
        credentials = BUILDER.check_no_environment_credentials(self.folder)
        self.assertEqual(3, len(credentials), credentials)

    def test_rejects_broken_relative_links(self) -> None:
        self.put("README.md", b"[ok](docs/a.md) [web](https://example.org) [gone](docs/missing.md) [out](../x.md)\n")
        self.put("docs/a.md", b"[back](../README.md#top)\n")
        problems = BUILDER.check_links(self.folder)
        self.assertEqual(2, len(problems), problems)

    def test_rejects_mixed_writing_systems_in_display_name(self) -> None:
        self.assertEqual({"HANGUL"}, BUILDER.writing_systems("한국어 학교생활기록부 도구 라이트"))
        self.assertEqual(2, len(BUILDER.writing_systems("학교생활기록부 Lite")))
        self.assertIn("INVISIBLE", BUILDER.writing_systems("도구​"))


if __name__ == "__main__":
    unittest.main()
