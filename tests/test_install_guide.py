#!/usr/bin/env python3
"""전체판 README의 설치 안내가 실제 이름·명령 형식과 맞고, 다른 설치 문서와 어긋나지 않는지 검사한다.

설치 안내는 터미널에 익숙하지 않은 교사가 따라 하는 첫 문서다. 플러그인 이름, 마켓플레이스 이름, 명령 형식, 버전 조건이
manifest와 공식 문서의 형식에서 벗어나면 안 된다. 명령 형식은 Claude Code 공식 문서
(https://code.claude.com/docs/en/plugins/install)로 2026-11-19에 확인했다.
"""

from __future__ import annotations

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


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


BUILDER = load_builder()
EDITION = BUILDER.edition_folder(PLUGIN_ROOT)
README = text(PLUGIN_ROOT / "README.md")
MANIFEST = json.loads(text(PLUGIN_ROOT / ".claude-plugin" / "plugin.json"))
MARKETPLACE = json.loads(text(PLUGIN_ROOT / ".claude-plugin" / "marketplace.json"))
FULL = MANIFEST["name"]
LITE = BUILDER.edition_config(PLUGIN_ROOT)["name"]
MARKET = MARKETPLACE["name"]
SOURCE = MANIFEST["repository"].removeprefix("https://github.com/")


def section(document: str, title: str) -> str:
    """'## ' 제목 하나의 본문. '### ' 소절은 이 절에 들어간다."""
    match = re.search(rf"(?ms)^## {re.escape(title)}\n(.*?)(?=^## |\Z)", document)
    assert match, f"README에 '## {title}' 절이 없다"
    return match.group(1)


def before(command: str, width: int = 200) -> str:
    index = README.index(command)
    return README[max(0, index - width):index]


class InstallGuideTests(unittest.TestCase):
    def test_quick_install_follows_the_intro_and_points_to_the_install_section(self) -> None:
        intro = README.index("교사가 확인한 관찰·평가 근거로")
        quick, skills = README.index("## 빠른 설치"), README.index("## 포함 스킬")
        self.assertLess(intro, quick)
        self.assertLess(quick, skills)
        body = section(README, "빠른 설치")
        for command in (f"claude plugin marketplace add {SOURCE}", f"claude plugin install {FULL}@{MARKET}"):
            with self.subTest(command=command):
                self.assertTrue(command in body, f"빠른 설치에 명령이 없다: {command}")
        self.assertTrue("(#설치)" in body)
        self.assertTrue("Python 3" in body and "Node.js 18 이상" in body)

    def test_install_section_gives_every_command_for_the_documented_ways(self) -> None:
        body = section(README, "설치")
        required = (
            # 대화 창 안(슬래시 형식)
            f"/plugin marketplace add {SOURCE}",
            f"/plugin install {FULL}@{MARKET}",
            f"/plugin install {LITE}@{MARKET}",
            f"/plugin install {FULL} --marketplace {SOURCE}",
            # 터미널(셸 형식)
            f"claude plugin marketplace add {SOURCE}",
            f"claude plugin install {FULL}@{MARKET}",
            f"claude plugin install {FULL} --marketplace {SOURCE}",
            # 확인·업데이트·지우기·다시 불러오기
            "claude plugin list",
            f"claude plugin update {FULL}@{MARKET}",
            f"claude plugin uninstall {FULL}@{MARKET}",
            f"claude plugin marketplace remove {MARKET}",
            "/reload-plugins",
        )
        for command in required:
            with self.subTest(command=command):
                self.assertTrue(command in body, f"설치 절에 명령이 없다: {command}")
        # 문서 전용판 이름은 대화 창 설치, 터미널 설치, 업데이트, 지우기 설명에 각각 나온다.
        self.assertGreaterEqual(body.count(f"{LITE}@{MARKET}"), 4)
        for skill in (f"/{FULL}:write-school-records", f"/{FULL}:korean-character-count", f"/{LITE}:write-school-records"):
            with self.subTest(skill=skill):
                self.assertTrue(skill in body, f"설치 확인에 스킬 이름이 없다: {skill}")

    def test_version_conditions_sit_next_to_the_one_step_commands(self) -> None:
        # 대화 창의 한 번에 설치는 2.1.275 이상, 셸의 한 번에 설치는 2.1.292 이상이다(공식 문서, 2026-11-19).
        self.assertTrue("2.1.275" in before(f"/plugin install {FULL} --marketplace {SOURCE}"))
        self.assertTrue("2.1.292" in before(f"claude plugin install {FULL} --marketplace {SOURCE}"))

    def test_install_section_states_what_each_edition_needs_and_how_to_choose(self) -> None:
        body = section(README, "설치")
        for phrase in ("둘 가운데 하나만 설치한다", "기계 점검 스크립트와 글자 수 스킬이 필요할 때",
                       "문서(스킬 지침)만 필요하거나 Python·Node.js가 없을 때", "Python 3", "Node.js 18 이상",
                       "https://code.claude.com/docs/en/plugins/install", "https://code.claude.com/docs/en/setup"):
            with self.subTest(phrase=phrase):
                self.assertTrue(phrase in body, f"설치 절에 문구가 없다: {phrase}")

    def test_other_install_documents_point_to_the_readme_install_section(self) -> None:
        pointer = "[README.md](README.md) 「설치」"
        for name in ("README_CLAUDE_CODE.md", "USER_GUIDE.md", "INSTALL.md"):
            with self.subTest(document=name):
                self.assertTrue(pointer in text(PLUGIN_ROOT / name), f"{name}에서 README 「설치」로 가는 안내가 없다")
        # 사용 설명서가 설치를 다시 README_CLAUDE_CODE.md로 돌리면 안 내 문서끼리 서로를 가리키게 된다.
        guide_intro = text(PLUGIN_ROOT / "USER_GUIDE.md").split("\n", 3)[2]
        self.assertFalse("README_CLAUDE_CODE" in guide_intro)

    def test_documents_only_edition_gives_no_plugin_install_command(self) -> None:
        # 문서 전용판 문서에는 설치·실행 명령을 두지 않는다(저장소 방침). 기존 디렉터리 검사는 npx·pip 같은 패키지 설치 명령만
        # 막으므로 플러그인 설치 명령은 여기서 따로 막는다. claude plugin validate가 README에 설치 줄을 넣으라고 조언하지만 따르지 않는다.
        found = []
        for relative, path in BUILDER.folder_files(EDITION).items():
            if relative.endswith(".md"):
                for number, line in enumerate(text(path).split("\n"), 1):
                    if re.search(r"claude +plugin|/plugin( |$)|--marketplace|marketplace add", line):
                        found.append(f"{relative}:{number}")
        self.assertEqual([], found)


if __name__ == "__main__":
    unittest.main()
