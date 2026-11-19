#!/usr/bin/env python3
"""docs/dev-vs-package.md에 기록된 의도된 차이 외에는 개발본과 배포본이 같아야 한다."""

import filecmp
import json
import re
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = PLUGIN_ROOT / "skills" / "write-school-records"
DEV = PLUGIN_ROOT.parents[1] / "skills" / "write-school-records"

# docs/dev-vs-package.md의 의도된 차이 목록. 여기에 없는 차이는 드리프트다.
ALLOWED_DIFFERENT = {"SKILL.md", "scripts/test_skill_integration.py"}
ALLOWED_DEV_ONLY = {
    "scripts/sync_install.py",
    "scripts/test_sync_install.py",
    "scripts/test_university_guides.py",
    "scripts/test_writing_examples.py",
    "scripts/trim_achievement_examples.py",
}
# 재배포 조건을 확인하지 못해 개발본에만 두는 자료 폴더.
LOCAL_ONLY_DIRS = ("references/writing-examples/", "references/university-guides/")
# 기재요령 원문 변환본(공공누리 제4유형)과 그 보관본·색인·등록 기록. 개발본에만 두고 배포본은 요약(summary.md)으로 동작한다.
GUIDELINE_ORIGINAL = re.compile(r"^references/guidelines(?:-middle)?/(?:current\.md|current\.index\.md|manifest\.json|versions/[^/]+\.md)$")
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}


def walk(root: Path) -> dict[str, Path]:
    return {
        p.relative_to(root).as_posix(): p
        for p in root.rglob("*")
        if p.is_file() and not (IGNORED_DIRS & set(p.relative_to(root).parts))
    }


@unittest.skipUnless(DEV.exists(), "개발본이 이 저장소 옆에 없음")
class DevPackageSyncTests(unittest.TestCase):
    def test_only_documented_differences_exist(self) -> None:
        pkg, dev = walk(PACKAGE), walk(DEV)
        self.assertEqual(set(pkg) - set(dev), set(), "배포본에만 있는 파일")
        dev_only = {
            rel for rel in set(dev) - set(pkg)
            if not rel.startswith(LOCAL_ONLY_DIRS) and not GUIDELINE_ORIGINAL.match(rel)
        }
        self.assertEqual(dev_only, ALLOWED_DEV_ONLY, "개발본에만 있는 파일")
        self.assertFalse([rel for rel in pkg if GUIDELINE_ORIGINAL.match(rel)], "배포본에 들어간 기재요령 원문 변환본")
        self.assertTrue([rel for rel in dev if GUIDELINE_ORIGINAL.match(rel)], "개발본의 기재요령 원문 변환본이 없다")
        self.assertFalse([rel for rel in pkg if rel.startswith(LOCAL_ONLY_DIRS)], "배포본에 들어간 로컬 전용 자료")
        different = {rel for rel in pkg if not filecmp.cmp(pkg[rel], dev[rel], shallow=False)}
        self.assertEqual(different, ALLOWED_DIFFERENT, "문서화되지 않은 내용 차이")


# 문서 전용판은 배포본(전체판)에서 scripts/build_directory_edition.py로 만든다. 흐름은 개발본 → 전체판 → 문서 전용판이다.
EDITION_CONFIG = PLUGIN_ROOT / "editions" / "source" / "edition.json"
EDITION_CHANGES = PLUGIN_ROOT / "editions" / "source" / "changes.md"


@unittest.skipUnless(DEV.exists(), "개발본이 이 저장소 옆에 없음")
class DevToDirectoryEditionTests(unittest.TestCase):
    def test_edition_documents_equal_the_dev_source_except_documented_variants(self) -> None:
        name = json.loads(EDITION_CONFIG.read_text(encoding="utf-8"))["name"]
        edition = walk(PLUGIN_ROOT / "editions" / name / "skills" / "write-school-records")
        prefix = "skills/write-school-records/"
        changes_text = EDITION_CHANGES.read_text(encoding="utf-8")
        variants = {path[len(prefix):] for path in re.findall(r"(?m)^````find (\S+)$", changes_text) if path.startswith(prefix)}
        self.assertIn("SKILL.md", variants)
        dev = walk(DEV)
        for rel, path in edition.items():
            if rel in variants:
                continue
            with self.subTest(file=rel):
                self.assertIn(rel, dev, "문서 전용판에만 있는 파일")
                # 문서 전용판은 LF로 쓰고 개발본 작업 폴더는 CRLF일 수 있으므로 줄바꿈은 맞춰 비교한다.
                self.assertEqual(dev[rel].read_bytes().replace(b"\r\n", b"\n"), path.read_bytes().replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main()
