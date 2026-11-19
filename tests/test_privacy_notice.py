#!/usr/bin/env python3
"""개인정보 처리 안내(PRIVACY.md)가 두 판에 있고, 문서가 보증하는 사실이 코드와 맞는지 검사한다.

PRIVACY.md는 '수집·저장·전송을 하지 않는다', '스킬이 실행하는 스크립트는 네트워크에 접속하지 않는다',
'파일을 쓰는 스크립트는 둘이다' 같은 사실을 보증한다. 문서만 읽어서는 코드가 바뀐 것을 알 수 없으므로
스킬 스크립트의 소스를 읽어 같은 사실이 지켜지는지 확인한다. 이 확인은 소스를 정적으로 읽는 것이라
모든 우회를 막지는 못한다. 새 import나 쓰기 호출이 생기면 여기서 실패해 사람이 문서를 다시 확인하게 하는 것이 목적이다.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
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
FULL_NOTICE = PLUGIN_ROOT / "PRIVACY.md"
EDITION_NOTICE = EDITION / "PRIVACY.md"
REPOSITORY = "https://github.com/blueshadow62/korean-school-records-toolkit"
ANTHROPIC_POLICY = "https://www.anthropic.com/legal/privacy"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# 두 안내에 같은 문구로 들어 있어야 하는 문장. 두 판의 사실이 달라도 이 부분은 어긋나면 안 된다.
COMMON_PHRASES = (
    "이 플러그인은 입력한 자료를 수집하거나 저장하거나 외부로 보내지 않습니다. 제3자에게 제공하지 않으며, 사용 기록이나 분석 정보도 모으지 않습니다.",
    "학생 이름·학번·학교명은 입력할 필요가 없습니다. 초안을 쓰는 데 필요한 것은 학년, 영역, 과목(활동)명(행특은 제외)과 자료 내용입니다.",
    "식별 정보가 들어 있는 자료를 받았어도 초안에는 반영하지 않습니다.",
    "교사가 입력하는 내용을 플러그인이 막거나 걸러 낼 수는 없습니다.",
    f"Anthropic의 약관과 [개인정보처리방침]({ANTHROPIC_POLICY})",
    "- 학생 이름·학번·학교명 같은 학생을 알아볼 수 있는 정보는 빼고 입력하십시오.",
    "- 근무하시는 학교와 시도교육청의 개인정보 보호 규정과 AI 활용 지침을 확인하십시오.",
    f"저장소의 GitHub Issues({REPOSITORY}/issues)로 알려 주십시오. 실제 학생 정보는 이슈에 쓰지 마십시오.",
    "보안 문제는 [SECURITY.md](SECURITY.md)에 따라 알려 주십시오.",
    "## English summary",
    "Do not put real student data in an issue.",
)

# 디렉터리가 목록에 쓰는 항목은 plugin.json에만 쓴다. 마켓플레이스 항목에 쓰면 알 수 없는 항목으로 경고한다(공식 manifest 참조).
LISTING_FIELDS = {"icon", "documentationUrl", "supportUrl", "privacyPolicyUrl", "termsOfServiceUrl"}
# 문서 전용판 plugin.json이 가질 수 있는 항목. 훅·서버·명령·에이전트 같은 실행 구성 항목이 늘면 여기서 걸린다.
EDITION_MANIFEST_KEYS = {
    "$schema", "name", "displayName", "version", "description", "author", "homepage", "repository",
    "privacyPolicyUrl", "license", "keywords", "skills",
}

# 스킬이 실행하는 스크립트와, 그 가운데 파일을 쓰는 것(PRIVACY.md 「스크립트가 하는 일」 표와 같다).
SKILL_SCRIPTS = {
    "skills/write-school-records/scripts/analyze_record.py": False,
    "skills/write-school-records/scripts/compare_neis_counts.py": True,
    "skills/write-school-records/scripts/update_guidelines.py": True,
    "skills/korean-character-count/scripts/korean_character_count.js": False,
}
# analyze_record.py가 update_guidelines에서 가져오는 이름. 모두 읽기 함수다. 새 이름이 생기면 쓰기 함수가 아닌지 다시 본다.
ANALYZER_IMPORTS = {
    "LEVEL_DIRECTORIES", "GuidelineError", "has_registered_original", "load_manifest",
    "read_summary_metadata", "root_paths", "verify_manifest",
}

NETWORK_AND_PROCESS_MODULES = {
    "socket", "ssl", "http", "urllib", "ftplib", "smtplib", "telnetlib", "imaplib", "poplib", "nntplib", "xmlrpc",
    "asyncio", "selectors", "subprocess", "multiprocessing", "webbrowser", "ctypes", "importlib",
    "requests", "httpx", "aiohttp",
}
DYNAMIC_CALLS = {"eval", "exec", "__import__"}
OS_PROCESS_AND_ENVIRONMENT = {"system", "popen", "environ", "environb", "getenv", "putenv", "unsetenv", "startfile", "fork"}
FILE_METHODS = {"write_text", "write_bytes", "mkdir", "unlink", "rmdir", "rename", "touch", "symlink_to",
                "hardlink_to", "chmod", "write", "writelines", "truncate"}
OS_FILE_FUNCTIONS = {"replace", "rename", "renames", "remove", "removedirs", "unlink", "makedirs", "mkdir", "rmdir",
                     "symlink", "link", "truncate", "chmod", "chown", "utime"}
FILE_MODE = re.compile(r"[rwxabt+U]{1,4}")

JS_FORBIDDEN = re.compile(
    r"""require\(\s*["'](?:node:)?(?:http|https|http2|net|dgram|dns|tls|child_process|cluster|worker_threads|inspector|vm)["']\s*\)"""
    r"""|from\s+["'](?:node:)?(?:http|https|http2|net|dgram|dns|tls|child_process|cluster|worker_threads|inspector|vm)["']"""
    r"""|\bimport\s*\(|process\.env\b|\bfetch\s*\(|XMLHttpRequest|\bWebSocket\b|\beval\s*\(|new\s+Function\b"""
)
JS_WRITE = re.compile(
    r"\bfs\.(?:write|append|mkdir|unlink|rename|rm|rmdir|copyFile|cp|createWriteStream|truncate|chmod|chown|symlink|link|utimes|open)\w*"
    r"|\b(?:writeFileSync|writeFile|appendFileSync|appendFile|createWriteStream)\b"
)


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def english_summary(document: str) -> str:
    return document.split("## English summary", 1)[1]


def _mode_is_write(node: ast.Call, positions: tuple[int, ...]) -> bool:
    values = [node.args[i].value for i in positions
              if len(node.args) > i and isinstance(node.args[i], ast.Constant)]
    values += [keyword.value.value for keyword in node.keywords
               if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant)]
    return any(isinstance(v, str) and FILE_MODE.fullmatch(v) and set(v) & set("wax+") for v in values)


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def python_findings(source: str) -> tuple[list[str], list[str]]:
    """Return (network, process, environment findings; file-write findings) for Python source."""
    reach, writes = [], []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if module in NETWORK_AND_PROCESS_MODULES:
                    reach.append(f"import {alias.name}")
                if module in {"shutil", "tempfile"}:
                    writes.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[0]
            if module in NETWORK_AND_PROCESS_MODULES:
                reach.append(f"from {node.module} import …")
            if module in {"shutil", "tempfile"}:
                writes.append(f"from {node.module} import …")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id in DYNAMIC_CALLS:
                    reach.append(f"call {func.id}()")
                if func.id == "open" and _mode_is_write(node, (1,)):
                    writes.append("open(…, write mode)")
            elif isinstance(func, ast.Attribute):
                root = _root_name(func)
                if root == "os" and func.attr in OS_FILE_FUNCTIONS:
                    writes.append(f"os.{func.attr}()")
                if root in {"shutil", "tempfile"}:
                    writes.append(f"{root}.{func.attr}()")
                if func.attr in {"open", "fdopen"} and _mode_is_write(node, (0, 1)):
                    writes.append(f".{func.attr}(…, write mode)")
                if func.attr in FILE_METHODS and root not in {"sys"}:
                    writes.append(f".{func.attr}()")
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "os":
            if node.attr in OS_PROCESS_AND_ENVIRONMENT or node.attr.startswith(("exec", "spawn")):
                reach.append(f"os.{node.attr}")
    return reach, writes


def javascript_findings(source: str) -> tuple[list[str], list[str]]:
    """Return (network, process, environment findings; file-write findings) for JavaScript source."""
    return [m.group(0) for m in JS_FORBIDDEN.finditer(source)], [m.group(0) for m in JS_WRITE.finditer(source)]


def findings(relative: str) -> tuple[list[str], list[str]]:
    source = text(PLUGIN_ROOT / relative)
    return javascript_findings(source) if relative.endswith(".js") else python_findings(source)


class PrivacyNoticeTests(unittest.TestCase):
    def test_both_editions_have_a_notice_with_the_common_statements(self) -> None:
        for label, path in (("전체판", FULL_NOTICE), ("문서 전용판", EDITION_NOTICE)):
            self.assertTrue(path.is_file(), f"{label}에 PRIVACY.md가 없다")
            body = text(path)
            for phrase in COMMON_PHRASES:
                with self.subTest(edition=label, phrase=phrase[:40]):
                    self.assertTrue(phrase in body, f"{label} PRIVACY.md에 문구가 없다: {phrase[:60]}")

    def test_each_notice_is_linked_from_its_readme(self) -> None:
        for label, readme in (("전체판", PLUGIN_ROOT / "README.md"), ("문서 전용판", EDITION / "README.md")):
            with self.subTest(edition=label):
                self.assertTrue("(PRIVACY.md)" in text(readme), f"{label} README에서 PRIVACY.md로 가는 링크가 없다")

    def test_english_summary_is_english_and_follows_the_korean_text(self) -> None:
        for path in (FULL_NOTICE, EDITION_NOTICE):
            with self.subTest(path=path.name):
                body = text(path)
                self.assertEqual(1, body.count("## English summary"))
                self.assertIsNone(re.search(r"[가-힣]", english_summary(body)), "영어 요약에 한글이 섞였다")
                self.assertTrue("does not collect, store, or send the data that you enter" in english_summary(body))

    def test_notices_hold_no_email_address(self) -> None:
        for path in (FULL_NOTICE, EDITION_NOTICE):
            with self.subTest(path=path.name):
                self.assertEqual([], EMAIL.findall(text(path)))

    def test_relative_links_in_the_notices_resolve(self) -> None:
        for path in (FULL_NOTICE, EDITION_NOTICE):
            for target in BUILDER.MARKDOWN_LINK.findall(text(path)):
                if re.match(r"(?i)^(?:[a-z][a-z0-9+.-]*:|#)", target):
                    continue
                with self.subTest(path=path.name, target=target):
                    self.assertTrue((path.parent / target).is_file())

    def test_edition_notice_names_no_script_install_command_or_plugin_command(self) -> None:
        # 문서 전용판 문서에는 스크립트 이름과 설치·실행 명령을 두지 않는다(디렉터리 규칙과 같은 기준).
        body = text(EDITION_NOTICE)
        self.assertIsNone(BUILDER.SCRIPT_REFERENCE.search(body))
        self.assertIsNone(BUILDER.INSTALL_COMMAND.search(body))
        self.assertIsNone(re.search(r"claude +plugin|/plugin( |$)|--marketplace", body))

    def test_edition_has_nothing_that_could_collect_or_send_data(self) -> None:
        # 문서 전용판 PRIVACY.md의 '수단이 없다'는 문장의 근거: 실행 파일, 훅, 서버 설정, 실행 구성 항목이 없다.
        executable = {".py", ".js", ".mjs", ".cjs", ".sh", ".ps1", ".bat", ".cmd", ".exe"}
        files = BUILDER.folder_files(EDITION)
        self.assertEqual([], [name for name, path in files.items() if path.suffix.lower() in executable])
        self.assertEqual([], [name for name, path in files.items() if path.read_bytes()[:2] == b"#!"])
        self.assertEqual([], [name for name in files if set(Path(name).parts) & BUILDER.FORBIDDEN_NAMES])
        manifest = json.loads(text(EDITION / ".claude-plugin" / "plugin.json"))
        self.assertEqual(set(), set(manifest) - EDITION_MANIFEST_KEYS)
        self.assertEqual({".claude-plugin/plugin.json", ".claude-plugin/icon.png"},
                         {name for name in files if name.startswith(".claude-plugin/")})

    def test_manifest_privacy_urls_name_each_editions_own_notice(self) -> None:
        full = json.loads(text(PLUGIN_ROOT / ".claude-plugin" / "plugin.json"))
        edition = json.loads(text(EDITION / ".claude-plugin" / "plugin.json"))
        self.assertEqual(f"{REPOSITORY}/blob/master/PRIVACY.md", full.get("privacyPolicyUrl"))
        self.assertEqual(f"{REPOSITORY}/blob/master/editions/{edition['name']}/PRIVACY.md", edition.get("privacyPolicyUrl"))
        for url, notice in ((full["privacyPolicyUrl"], FULL_NOTICE), (edition["privacyPolicyUrl"], EDITION_NOTICE)):
            with self.subTest(url=url):
                self.assertTrue(url.startswith("https://"))
                self.assertEqual(notice, PLUGIN_ROOT / url.split("/blob/master/", 1)[1])
                self.assertTrue(notice.is_file())

    def test_marketplace_entries_do_not_carry_directory_listing_fields(self) -> None:
        marketplace = json.loads(text(PLUGIN_ROOT / ".claude-plugin" / "marketplace.json"))
        for entry in marketplace["plugins"]:
            with self.subTest(plugin=entry["name"]):
                self.assertEqual(set(), LISTING_FIELDS & set(entry))

    def test_full_notice_names_the_four_scripts_and_marks_the_two_that_write(self) -> None:
        body = text(FULL_NOTICE)
        rows = {line.split("`")[1]: line for line in body.split("\n") if line.startswith("| `skills/")}
        self.assertEqual(set(SKILL_SCRIPTS), set(rows))
        for relative, writes in SKILL_SCRIPTS.items():
            with self.subTest(script=relative):
                self.assertTrue(rows[relative].rstrip().endswith("| 있음 |" if writes else "| 없음 |"), rows[relative])


class ScriptFactsTests(unittest.TestCase):
    """PRIVACY.md 「스크립트가 하는 일」의 사실을 스킬 스크립트의 소스로 확인한다."""

    def test_the_skills_run_exactly_the_four_scripts_the_notice_lists(self) -> None:
        found = {
            path.relative_to(PLUGIN_ROOT).as_posix()
            for path in (PLUGIN_ROOT / "skills").rglob("*")
            if path.is_file() and "scripts" in path.parts
            and path.suffix in {".py", ".js", ".mjs", ".cjs", ".sh", ".ps1"}
            and not path.name.startswith("test_") and not path.name.endswith(".test.js")
        }
        self.assertEqual(set(SKILL_SCRIPTS), found, "스킬에 스크립트가 늘거나 줄었다. PRIVACY.md의 표와 사실을 다시 확인한다")

    def test_scripts_have_no_network_process_or_environment_use(self) -> None:
        for relative in SKILL_SCRIPTS:
            with self.subTest(script=relative):
                self.assertEqual([], findings(relative)[0])

    def test_only_the_two_named_scripts_write_files(self) -> None:
        for relative, writes in SKILL_SCRIPTS.items():
            with self.subTest(script=relative):
                found = findings(relative)[1]
                self.assertEqual(writes, bool(found), found)

    def test_analyzer_imports_only_read_functions_from_the_registration_tool(self) -> None:
        tree = ast.parse(text(PLUGIN_ROOT / "skills/write-school-records/scripts/analyze_record.py"))
        imported = {alias.name for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module == "update_guidelines" for alias in node.names}
        self.assertEqual(ANALYZER_IMPORTS, imported)

    def test_source_checks_catch_violations(self) -> None:
        # 검사가 비어 있지 않은지 합성 소스로 확인한다.
        reach = ("import urllib.request", "from http import client", "import subprocess", "import os\nos.system('x')",
                 "import os\nx = os.environ['A']", "import os\nx = os.getenv('A')", "x = __import__('socket')",
                 "import importlib")
        for source in reach:
            with self.subTest(source=source):
                self.assertTrue(python_findings(source)[0])
        writes = ("open('a', 'w')", "open('a', mode='ab')", "from pathlib import Path\nPath('a').write_text('x')",
                  "from pathlib import Path\nPath('a').open('w')", "import os\nos.replace('a', 'b')", "import shutil",
                  "import tempfile", "handle.write('x')", "Path('a').mkdir()")
        for source in writes:
            with self.subTest(source=source):
                self.assertTrue(python_findings(source)[1])
        clean = ("import json, re, sys\nprint(json.dumps({}))", "open('a')", "open('a', mode='rb')",
                 "text.replace('a', 'b')", "import sys\nsys.stdout.write('x')", "from pathlib import Path\nPath('a').read_text()",
                 "from pathlib import Path\nPath('a').open('r')")
        for source in clean:
            with self.subTest(source=source):
                self.assertEqual(([], []), python_findings(source))
        for source in ('const http = require("node:https");', 'fetch("x")', "process.env.A", "eval('1')",
                       'import("x")', 'const c = require("child_process");'):
            with self.subTest(source=source):
                self.assertTrue(javascript_findings(source)[0])
        for source in ('fs.writeFileSync("a", "b")', "fs.appendFileSync(p, d)", "fs.mkdirSync(p)", "fs.createWriteStream(p)"):
            with self.subTest(source=source):
                self.assertTrue(javascript_findings(source)[1])
        self.assertEqual(([], []), javascript_findings('const fs = require("node:fs");\nfs.readFileSync(0, "utf8");'))


if __name__ == "__main__":
    unittest.main()
