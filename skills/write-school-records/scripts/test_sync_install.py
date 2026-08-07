#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from sync_install import main


class SyncInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=Path.home())
        root = Path(self.temp.name)
        self.source = root / "source" / "write-school-records"
        self.install = root / "home" / ".codex" / "skills" / "write-school-records"
        self.backups = root / "backups"
        (self.source / "scripts").mkdir(parents=True)
        (self.source / "SKILL.md").write_text("# 기준본\n", encoding="utf-8")
        (self.source / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self, mode: str) -> list[str]:
        return [
            "--source", str(self.source),
            "--install-dir", str(self.install),
            "--backup-dir", str(self.backups),
            mode,
        ]

    def run_cli(self, args: list[str]) -> int:
        return main(args)

    def test_dry_run_does_not_write(self) -> None:
        self.assertEqual(self.run_cli(self.args("--dry-run")), 0)
        self.assertFalse(self.install.exists())

    def test_install_then_verify(self) -> None:
        self.assertEqual(self.run_cli(self.args("--install")), 0)
        self.assertEqual(self.run_cli(self.args("--verify")), 0)
        self.assertTrue((self.install / "scripts" / "tool.py").exists())

    def test_verify_detects_change_and_install_creates_backup(self) -> None:
        self.assertEqual(self.run_cli(self.args("--install")), 0)
        (self.install / "SKILL.md").write_text("변조\n", encoding="utf-8")
        self.assertEqual(self.run_cli(self.args("--verify")), 2)
        self.assertEqual(self.run_cli(self.args("--install")), 0)
        self.assertTrue(list(self.backups.rglob("SKILL.md")))

    def test_install_path_outside_home_is_rejected(self) -> None:
        outside = Path.home().parent / "Public" / "not-a-codex-install"
        args = ["--source", str(self.source), "--install-dir", str(outside), "--dry-run"]
        self.assertEqual(self.run_cli(args), 2)

    def test_source_and_install_must_differ(self) -> None:
        args = ["--source", str(self.source), "--install-dir", str(self.source), "--dry-run"]
        self.assertEqual(self.run_cli(args), 2)


if __name__ == "__main__":
    unittest.main()
