#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from update_guidelines import anchor_index, heading_index, index_bytes, load_index_terms, root_paths, sha256_bytes


SCRIPT = Path(__file__).with_name("update_guidelines.py")


class UpdateGuidelinesCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "skill"
        self.input_dir = Path(self.temp.name) / "inputs"
        self.input_dir.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def write_input(self, name: str, text: str, encoding: str = "utf-8") -> Path:
        path = self.input_dir / name
        path.write_text(text, encoding=encoding)
        return path

    def import_version(self, path: Path, year: str, revision: str, *extra: str) -> subprocess.CompletedProcess[str]:
        return self.run_cli(
            "import",
            "--input", str(path),
            "--school-year", year,
            "--revision-date", revision,
            "--source-title", f"{year}학년도 학교생활기록부 기재요령",
            "--source-url", "https://example.invalid/guidelines",
            "--confirmed-official",
            *extra,
        )

    def test_register_activate_list_and_verify(self) -> None:
        first = self.write_input("2026.md", "# 공통\n\n## 세특\n내용\n")
        result = self.import_version(first, "2026", "2026-02-15", "--activate")
        self.assertEqual(result.returncode, 0, result.stderr)
        listed = self.run_cli("list")
        self.assertIn("2026_2026-02-15", listed.stdout)
        verified = self.run_cli("verify")
        self.assertEqual(verified.returncode, 0, verified.stderr)
        paths = root_paths(self.root)
        self.assertEqual(paths["current"].read_text(encoding="utf-8"), first.read_text(encoding="utf-8"))
        self.assertIn("| 2 | 세특 | 3 | 4 |", paths["index"].read_text(encoding="utf-8"))

    def test_multiple_revisions_and_rollback(self) -> None:
        first = self.write_input("a.md", "# 2026\n")
        second = self.write_input("b.md", "# 2027\n## 변경\n")
        self.assertEqual(self.import_version(first, "2026", "2026-02-15", "--activate").returncode, 0)
        self.assertEqual(self.import_version(second, "2027", "2027-02-15").returncode, 0)
        activated = self.run_cli("activate", "--version", "2027_2027-02-15")
        self.assertEqual(activated.returncode, 0, activated.stderr)
        rollback = self.run_cli("activate", "--version", "2026_2026-02-15")
        self.assertEqual(rollback.returncode, 0, rollback.stderr)
        self.assertEqual(root_paths(self.root)["current"].read_text(encoding="utf-8"), "# 2026\n")

    def test_duplicate_empty_heading_and_bad_date_are_rejected(self) -> None:
        valid = self.write_input("valid.md", "# 제목\n")
        self.assertEqual(self.import_version(valid, "2026", "2026-02-15").returncode, 0)
        duplicate = self.import_version(valid, "2026", "2026-02-15")
        self.assertEqual(duplicate.returncode, 2)
        empty = self.write_input("empty.md", "   \n")
        self.assertEqual(self.import_version(empty, "2027", "2027-02-15").returncode, 2)
        no_heading = self.write_input("no-heading.md", "본문만 있음\n")
        self.assertEqual(self.import_version(no_heading, "2027", "2027-03-01").returncode, 2)
        bad_date = self.import_version(valid, "2028", "2028-02-31")
        self.assertEqual(bad_date.returncode, 2)

    def test_missing_non_utf8_and_unconfirmed_activation_are_rejected(self) -> None:
        missing = self.run_cli(
            "import", "--input", str(self.input_dir / "missing.md"),
            "--school-year", "2027", "--revision-date", "2027-02-15", "--source-title", "x",
        )
        self.assertEqual(missing.returncode, 2)
        binary = self.input_dir / "binary.md"
        binary.write_bytes(b"# title\n\xff")
        bad_encoding = self.run_cli(
            "import", "--input", str(binary), "--school-year", "2027",
            "--revision-date", "2027-02-15", "--source-title", "x",
        )
        self.assertEqual(bad_encoding.returncode, 2)
        unconfirmed = self.write_input("unconfirmed.md", "# 제목\n")
        result = self.run_cli(
            "import", "--input", str(unconfirmed), "--school-year", "2027",
            "--revision-date", "2027-03-01", "--source-title", "x", "--activate",
        )
        self.assertEqual(result.returncode, 2)

    def test_tampered_hash_and_failed_activation_preserve_active_state(self) -> None:
        first = self.write_input("first.md", "# 유지\n")
        second = self.write_input("second.md", "# 새 버전\n")
        self.assertEqual(self.import_version(first, "2026", "2026-02-15", "--activate").returncode, 0)
        self.assertEqual(self.import_version(second, "2027", "2027-02-15").returncode, 0)
        paths = root_paths(self.root)
        archive = paths["versions"] / "2027_2027-02-15.md"
        archive.write_text("# 변조\n", encoding="utf-8")
        before = paths["current"].read_bytes()
        failed = self.run_cli("activate", "--version", "2027_2027-02-15")
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(paths["current"].read_bytes(), before)
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        self.assertEqual(manifest["active_version"], "2026_2026-02-15")

    def test_index_contains_deterministic_ranges_and_manifest_hash(self) -> None:
        source = self.write_input("source.md", "# 하나\n본문\n## 둘\n끝\n")
        self.assertEqual(self.import_version(source, "2026", "2026-04-01", "--activate").returncode, 0)
        paths = root_paths(self.root)
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        entry = manifest["versions"]["2026_2026-04-01"]
        self.assertEqual(entry["sha256"], sha256_bytes(paths["current"].read_bytes()))
        index = paths["index"].read_text(encoding="utf-8")
        self.assertIn("active_version=2026_2026-04-01", index)
        self.assertIn("| 1 | 하나 | 1 | 2 |", index)
        self.assertIn("| 2 | 둘 | 3 | 4 |", index)

    def test_same_year_revision_is_supported_and_verify_detects_current_tampering(self) -> None:
        first = self.write_input("revision-a.md", "# 2027 초판\n")
        second = self.write_input("revision-b.md", "# 2027 개정\n")
        self.assertEqual(self.import_version(first, "2027", "2027-02-15", "--activate").returncode, 0)
        self.assertEqual(self.import_version(second, "2027", "2027-06-01").returncode, 0)
        listed = self.run_cli("list")
        self.assertIn("2027_2027-02-15", listed.stdout)
        self.assertIn("2027_2027-06-01", listed.stdout)
        self.assertEqual(self.run_cli("verify").returncode, 0)
        paths = root_paths(self.root)
        paths["current"].write_text("# 변조\n", encoding="utf-8")
        failed = self.run_cli("verify")
        self.assertEqual(failed.returncode, 2)

    def test_update_metadata_preserves_version_active_date_and_hash(self) -> None:
        source = self.write_input("metadata.md", "# 원문\n")
        self.assertEqual(self.import_version(source, "2026", "2026-02-12", "--activate").returncode, 0)
        paths = root_paths(self.root)
        before_hash = sha256_bytes(paths["current"].read_bytes())
        result = self.run_cli("update-metadata", "--version", "2026_2026-02-12", "--source-url", "https://www.moe.go.kr/example")
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
        entry = manifest["versions"]["2026_2026-02-12"]
        self.assertEqual(entry["source_url"], "https://www.moe.go.kr/example")
        self.assertEqual(manifest["active_version"], "2026_2026-02-12")
        self.assertEqual(entry["revision_date"], "2026-02-12")
        self.assertEqual(entry["school_year"], "2026")
        self.assertEqual(before_hash, sha256_bytes(paths["current"].read_bytes()))

    def test_update_metadata_rejects_unknown_empty_and_non_https_without_changes(self) -> None:
        source = self.write_input("metadata-errors.md", "# 원문\n")
        self.assertEqual(self.import_version(source, "2026", "2026-02-12", "--activate").returncode, 0)
        paths = root_paths(self.root)
        before = paths["manifest"].read_bytes()
        for args in (
            ("--version", "missing", "--source-url", "https://example.invalid"),
            ("--version", "2026_2026-02-12", "--source-url", ""),
            ("--version", "2026_2026-02-12", "--source-url", "http://example.invalid"),
        ):
            self.assertEqual(self.run_cli("update-metadata", *args).returncode, 2)
            self.assertEqual(paths["manifest"].read_bytes(), before)

    def test_rebuild_index_keeps_manifest_and_current_unchanged(self) -> None:
        source = self.write_input("rebuild.md", "# 제목\n<table><tr><td>동아리활동</td></tr></table>\n")
        self.assertEqual(self.import_version(source, "2026", "2026-02-12", "--activate").returncode, 0)
        paths = root_paths(self.root)
        before_manifest = paths["manifest"].read_bytes()
        before_current = paths["current"].read_bytes()
        result = self.run_cli("rebuild-index")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(paths["manifest"].read_bytes(), before_manifest)
        self.assertEqual(paths["current"].read_bytes(), before_current)


class SearchAnchorTests(unittest.TestCase):
    def terms(self) -> list[tuple[str, str]]:
        return [("creative", "자율·자치활동"), ("creative", "동아리활동"), ("subject", "세부능력 및 특기사항")]

    def test_markdown_headings_remain_and_html_cells_become_anchors(self) -> None:
        text = "# 창체\n<table>\n<tr><th>자율ㆍ자치활동</th><td>동아리활동</td></tr>\n</table>\n"
        rendered = index_bytes("v", "a" * 64, text, self.terms()).decode("utf-8")
        self.assertEqual(heading_index(text)[0]["title"], "창체")
        self.assertIn("| 1 | 창체 | 1 | 4 |", rendered)
        self.assertIn("| 자율·자치활동 | 자율·자치활동 | 3 | html-table-cell | body | 창체 |", rendered)
        self.assertIn("| 동아리활동 | 동아리활동 | 3 | html-table-cell | body | 창체 |", rendered)

    def test_strong_plain_labels_and_duplicate_counts(self) -> None:
        text = "<strong>세부능력 및 특기사항</strong>\n세부능력 및 특기사항\n<td>세부능력 및 특기사항</td>\n"
        anchors = anchor_index(text, self.terms())
        subject = [item for item in anchors if item["text"] == "세부능력 및 특기사항"]
        self.assertEqual([item["kind"] for item in subject], ["html-strong", "plain-label", "html-table-cell"])
        self.assertTrue(all(item["occurrences"] == 3 for item in subject))

    def test_excludes_explanations_numeric_and_empty_cells(self) -> None:
        text = "<td>500자</td>\n<td></td>\n<td>학생의 세부능력 및 특기사항을 구체적으로 작성한다.</td>\n"
        self.assertEqual(anchor_index(text, self.terms()), [])

    def test_markdown_heading_can_supply_a_configured_plain_label(self) -> None:
        text = "# 학교생활기록부 영역별 입력 가능 최대 글자수\n"
        anchors = anchor_index(text, [("limits", "입력 가능 최대 글자수")])
        self.assertEqual(anchors[0]["kind"], "plain-label")
        self.assertEqual(anchors[0]["line"], 1)

    def test_table_context_extends_without_reading_the_chapter(self) -> None:
        text = (
            "# 창체\n<table>\n<td>자율·자치활동</td>\n<td>동아리활동</td>\n"
            "<td>기준</td>\n</table>\n"
        )
        terms = [("creative", "자율·자치활동"), ("creative", "동아리활동")]
        anchors = anchor_index(text, terms)
        by_term = {item["text"]: item for item in anchors}
        self.assertEqual(by_term["자율·자치활동"]["range"], "1–6")
        self.assertEqual(by_term["동아리활동"]["range"], "1–6")

    def test_long_table_header_can_anchor_configured_term(self) -> None:
        text = "<table>\n<th>학교 밖 교육 기관에서 주최하고 주관한 체험활동의 조건</th>\n</table>\n"
        anchors = anchor_index(text, [("creative", "학교 밖 교육")])
        self.assertEqual(anchors[0]["line"], 2)
        self.assertEqual(anchors[0]["kind"], "html-table-cell")

    def test_missing_or_invalid_term_config_keeps_heading_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index-terms.json"
            self.assertEqual(load_index_terms(path), [])
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(load_index_terms(path), [])
        rendered = index_bytes("v", "b" * 64, "# 제목\n", [])
        self.assertIn("| 1 | 제목 | 1 | 1 |", rendered.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
