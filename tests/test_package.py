#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MANAGER_PATH = PLUGIN_ROOT / "scripts" / "manage_bundle.py"


def load_manager():
    spec = importlib.util.spec_from_file_location("manage_bundle", MANAGER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PackageContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.install_root = self.root / "install" / "skills"
        self.backup_root = self.root / "backups"
        self.manager = load_manager()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_manager(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(MANAGER_PATH),
                *args,
                "--install-root",
                str(self.install_root),
                "--backup-root",
                str(self.backup_root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_expected_skills_are_unique_and_complete(self) -> None:
        skill_dirs = {
            path.name for path in (PLUGIN_ROOT / "skills").iterdir() if path.is_dir()
        }
        self.assertEqual(set(self.manager.SKILL_NAMES), skill_dirs)
        self.assertEqual(len(self.manager.SKILL_NAMES), len(set(self.manager.SKILL_NAMES)))

    def test_release_version_and_license(self) -> None:
        self.assertEqual("3.0.0", (PLUGIN_ROOT / "VERSION").read_text(encoding="utf-8").strip())
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual("3.0.0", manifest["version"])
        license_text = (
            PLUGIN_ROOT / "skills" / "write-school-records" / "LICENSE"
        ).read_text(encoding="utf-8")
        self.assertIn("CC BY-NC-SA 4.0", license_text)
        self.assertIn("류기현", license_text)

    def test_claude_code_manifest_and_install_commands(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual("korean-school-records-toolkit", manifest["name"])
        self.assertEqual("3.0.0", manifest["version"])
        self.assertEqual("./skills/", manifest["skills"])
        self.assertEqual(
            {"write-school-records", "korean-character-count"},
            {
                path.name
                for path in (PLUGIN_ROOT / "skills").iterdir()
                if path.is_dir()
            },
        )
        install_readme = (PLUGIN_ROOT / "README_CLAUDE_CODE.md").read_text(encoding="utf-8")
        self.assertIn("claude plugin validate . --strict", install_readme)
        self.assertIn("claude --plugin-dir .", install_readme)
        self.assertIn(
            "/korean-school-records-toolkit:write-school-records",
            install_readme,
        )

    def test_zip_artifacts_are_absent(self) -> None:
        self.assertFalse(any(PLUGIN_ROOT.rglob("*.zip")))
        self.assertFalse(any(PLUGIN_ROOT.rglob("*.zip.sha256")))

    def test_public_achievement_standards_include_attribution(self) -> None:
        corpus = PLUGIN_ROOT / "skills" / "write-school-records" / "references" / "achievement-standards"
        catalog = json.loads((corpus / "sources.json").read_text(encoding="utf-8"))
        attribution = (corpus / "ATTRIBUTION.md").read_text(encoding="utf-8")
        self.assertEqual("public", catalog["distribution"])
        self.assertIn("NCIC 국가교육과정정보센터", attribution)
        self.assertIn("공공누리 제1유형", attribution)
        self.assertIn("공공누리 제2유형", attribution)

    def test_public_middle_standards_include_attribution(self) -> None:
        corpus = PLUGIN_ROOT / "skills" / "write-school-records" / "references" / "achievement-standards-middle"
        catalog = json.loads((corpus / "sources.json").read_text(encoding="utf-8"))
        attribution = (corpus / "ATTRIBUTION.md").read_text(encoding="utf-8")
        self.assertEqual("public", catalog["distribution"])
        self.assertIn("NCIC 국가교육과정정보센터", attribution)
        self.assertIn("공공누리 제2유형", attribution)

    def test_guideline_originals_are_not_shipped_but_summaries_are(self) -> None:
        # 기재요령 원문(공공누리 제4유형) 변환본은 배포하지 않고, 이 스킬이 쓴 요약으로 동작한다.
        references = PLUGIN_ROOT / "skills" / "write-school-records" / "references"
        for folder, level in (("guidelines", "high"), ("guidelines-middle", "middle")):
            with self.subTest(folder=folder):
                directory = references / folder
                for name in ("current.md", "current.index.md", "manifest.json"):
                    self.assertFalse((directory / name).exists(), name)
                self.assertFalse(list((directory / "versions").glob("*")) if (directory / "versions").exists() else [])
                summary = (directory / "summary.md").read_text(encoding="utf-8")
                self.assertTrue(summary.startswith("---\ndocument: guideline-summary\n"))
                self.assertIn(f"school_level: {level}\n", summary)
                self.assertIn("공식 효력은 교육부 원문에 있다", summary)
                attribution = (directory / "ATTRIBUTION.md").read_text(encoding="utf-8")
                self.assertIn("공공누리 **제4유형**", attribution)
                self.assertIn("포함하지 않음", attribution)

    def test_record_checker_runs_on_the_summary_without_originals(self) -> None:
        scripts = PLUGIN_ROOT / "skills" / "write-school-records" / "scripts"
        for level, field, expected_limit in (("high", "subject", 1500), ("middle", "free_semester", 3000)):
            with self.subTest(level=level):
                result = subprocess.run(
                    [sys.executable, str(scripts / "analyze_record.py"), "--school-level", level, "--field", field,
                     "--text", "자료를 비교하고 결과를 표로 정리함.", "--json"],
                    capture_output=True, text=True, encoding="utf-8", check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual("summary", data["guideline"]["basis"])
                self.assertEqual("이 도구가 정리한 요약 기준(원문 미등록, 원문과 직접 대조하지 않음)", data["guideline"]["basis_note"])
                self.assertEqual(expected_limit, data["metrics"]["default_neis_byte_limit"])
                verify = subprocess.run(
                    [sys.executable, str(scripts / "update_guidelines.py"), "--level", level, "verify"],
                    capture_output=True, text=True, encoding="utf-8", check=False,
                )
                self.assertEqual(0, verify.returncode, verify.stderr)
                self.assertIn("등록된 원문 없음", verify.stdout)

    def test_public_metadata_omits_local_absolute_paths(self) -> None:
        metadata_text = (PLUGIN_ROOT / "SOURCE_METADATA.json").read_text(encoding="utf-8")
        self.assertNotIn("source_path", metadata_text)
        self.assertNotIn("C:\\\\Users\\\\", metadata_text)

    def test_dry_run_does_not_create_install_root(self) -> None:
        result = self.run_manager("--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("No files changed.", result.stdout)
        self.assertFalse(self.install_root.exists())

    def test_install_verify_and_second_install_are_idempotent(self) -> None:
        first = self.run_manager("--install")
        self.assertEqual(0, first.returncode, first.stderr)
        verify = self.run_manager("--verify")
        self.assertEqual(0, verify.returncode, verify.stderr)
        before = sorted(path.name for path in self.backup_root.iterdir())
        second = self.run_manager("--install")
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertIn("Already installed and verified", second.stdout)
        after = sorted(path.name for path in self.backup_root.iterdir())
        self.assertEqual(before, after)

    def test_uninstall_and_rollback_restore_both_skills(self) -> None:
        self.assertEqual(0, self.run_manager("--install").returncode)
        uninstall = self.run_manager("--uninstall")
        self.assertEqual(0, uninstall.returncode, uninstall.stderr)
        self.assertTrue(all(not (self.install_root / name).exists() for name in self.manager.SKILL_NAMES))
        rollback = self.run_manager("--rollback")
        self.assertEqual(0, rollback.returncode, rollback.stderr)
        self.assertEqual(0, self.run_manager("--verify").returncode)

    def test_partial_commit_failure_restores_previous_installations(self) -> None:
        for name in self.manager.SKILL_NAMES:
            target = self.install_root / name
            target.mkdir(parents=True)
            (target / "old.txt").write_text(f"old-{name}", encoding="utf-8")
        real_move = shutil.move
        staged_commits = 0

        def failing_move(source, destination, *args, **kwargs):
            nonlocal staged_commits
            if ".korean-school-records-stage-" in str(source):
                staged_commits += 1
                if staged_commits == 2:
                    raise OSError("simulated second-skill commit failure")
            return real_move(source, destination, *args, **kwargs)

        with mock.patch.object(self.manager.shutil, "move", side_effect=failing_move):
            with self.assertRaises(OSError):
                self.manager.install_bundle(self.install_root.resolve(), self.backup_root.resolve())
        for name in self.manager.SKILL_NAMES:
            self.assertEqual(
                f"old-{name}",
                (self.install_root / name / "old.txt").read_text(encoding="utf-8"),
            )

if __name__ == "__main__":
    unittest.main()
