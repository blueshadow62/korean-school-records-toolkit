import tempfile
import unittest
from pathlib import Path

from sync_readme_changelog import latest_entry, sync


class SyncReadmeChangelogTests(unittest.TestCase):
    def test_latest_entry_takes_the_first_heading(self) -> None:
        changelog = "# Changelog\n\n## Unreleased\n\n- a change\n\n## 1.1.0 — 2026-07-30\n\n- older\n"
        self.assertEqual("Unreleased", latest_entry(changelog))

    def test_sync_replaces_marker_block_and_reports_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changelog_path = root / "CHANGELOG.md"
            readme_path = root / "README.md"
            changelog_path.write_text("# Changelog\n\n## 1.1.1 — 2026-08-09\n\n- fix something\n", encoding="utf-8")
            readme_path.write_text(
                "# Title\n\n<!-- CHANGELOG:START -->\nold banner\n<!-- CHANGELOG:END -->\n\nbody\n",
                encoding="utf-8",
            )
            changed = sync(changelog_path, readme_path)
            self.assertTrue(changed)
            updated = readme_path.read_text(encoding="utf-8")
            self.assertIn("1.1.1 — 2026-08-09", updated)
            self.assertIn("body", updated)
            self.assertNotIn("old banner", updated)

    def test_sync_is_a_no_op_when_banner_already_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changelog_path = root / "CHANGELOG.md"
            readme_path = root / "README.md"
            changelog_path.write_text("# Changelog\n\n## Unreleased\n\n- a change\n", encoding="utf-8")
            readme_path.write_text(
                "# Title\n\n<!-- CHANGELOG:START -->\n"
                "> **최근 업데이트: Unreleased** — 자세한 변경 내역은 [CHANGELOG.md](CHANGELOG.md)를 확인하세요.\n"
                "<!-- CHANGELOG:END -->\n\nbody\n",
                encoding="utf-8",
            )
            changed = sync(changelog_path, readme_path)
            self.assertFalse(changed)

    def test_sync_requires_marker_pair_in_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            changelog_path = root / "CHANGELOG.md"
            readme_path = root / "README.md"
            changelog_path.write_text("# Changelog\n\n## Unreleased\n\n- a change\n", encoding="utf-8")
            readme_path.write_text("# Title\n\nno markers here\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                sync(changelog_path, readme_path)


if __name__ == "__main__":
    unittest.main()
