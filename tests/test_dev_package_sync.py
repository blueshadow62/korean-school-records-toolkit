#!/usr/bin/env python3
"""docs/dev-vs-package.md에 기록된 의도된 차이 외에는 개발본과 배포본이 같아야 한다."""

import filecmp
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
        dev_only = {rel for rel in set(dev) - set(pkg) if not rel.startswith(LOCAL_ONLY_DIRS)}
        self.assertEqual(dev_only, ALLOWED_DEV_ONLY, "개발본에만 있는 파일")
        self.assertFalse([rel for rel in pkg if rel.startswith(LOCAL_ONLY_DIRS)], "배포본에 들어간 로컬 전용 자료")
        different = {rel for rel in pkg if not filecmp.cmp(pkg[rel], dev[rel], shallow=False)}
        self.assertEqual(different, ALLOWED_DIFFERENT, "문서화되지 않은 내용 차이")


if __name__ == "__main__":
    unittest.main()
