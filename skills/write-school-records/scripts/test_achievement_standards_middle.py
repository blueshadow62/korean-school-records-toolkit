#!/usr/bin/env python3

import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).parents[1]
CORPUS = SKILL_ROOT / "references" / "achievement-standards-middle"
HIGH_CORPUS = SKILL_ROOT / "references" / "achievement-standards"
SUPPORT_FILES = {"index.md", "ATTRIBUTION.md"}

STANDARD_COUNTS = {
    "국어": 51,
    "사회_지리": 38,
    "사회_일반사회": 36,
    "역사": 40,
    "도덕": 22,
    "수학": 60,
    "과학": 87,
    "기술_가정": 52,
    "정보": 25,
    "체육": 51,
    "음악": 13,
    "미술": 13,
    "영어": 21,
    "생활_독일어": 15,
    "생활_프랑스어": 16,
    "생활_스페인어": 18,
    "생활_중국어": 17,
    "생활_일본어": 17,
    "생활_러시아어": 15,
    "생활_아랍어": 16,
    "생활_베트남어": 17,
    "한문": 12,
    "보건": 26,
    "환경": 19,
    "진로와_직업": 14,
}
# 새 개정 고시가 나오면 다시 대조하고 이 값을 바꾼다. 그전까지는 모든 교과가 이 판을 기준으로 한다.
LATEST_NOTICE = "제2026-1호 별책 3"
CODE = re.compile(r"\[\d{1,2}[^\]\s]{1,12}?\d{2}-\d{2}\]")


@unittest.skipUnless(CORPUS.is_dir(), "중학교 성취수준 자료가 없는 환경")
class MiddleAchievementStandardsTests(unittest.TestCase):
    def course_paths(self):
        return sorted(path for path in CORPUS.glob("*.md") if path.name not in SUPPORT_FILES)

    def test_every_expected_course_exists_and_nothing_else(self) -> None:
        self.assertEqual(set(STANDARD_COUNTS), {path.stem for path in self.course_paths()})

    def test_course_files_hold_descriptors_only(self) -> None:
        excluded = re.compile(r"성취수준 개발의 이해|성취수준 활용|예시.{0,20}평가|<img|!\[|image_[0-9]+", re.I)
        for path in self.course_paths():
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("## 1. 성취기준별 성취수준", text)
                self.assertIn("## 2. 영역별 성취수준", text)
                self.assertIsNone(excluded.search(text))

    def test_standard_counts_and_school_level_of_codes(self) -> None:
        for path in self.course_paths():
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                table = text[text.index("## 1. 성취기준별 성취수준"):]
                codes = set(CODE.findall(table))
                self.assertEqual(STANDARD_COUNTS[path.stem], len(codes))
                # 보고서 원문의 오기 하나를 빼면 모두 중학교 코드여야 한다.
                self.assertEqual(set(), {code for code in codes if not code.startswith("[9")} - {"[6국05-07]"})

    def test_every_course_states_the_latest_notice_checked(self) -> None:
        for path in self.course_paths():
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn(LATEST_NOTICE, text[:text.index("## 1. 성취기준별 성취수준")])
                self.assertNotIn("미대조", text)

    def test_known_source_issues_are_written_down(self) -> None:
        korean = (CORPUS / "국어.md").read_text(encoding="utf-8")
        self.assertIn("`[6국05-07]`", korean)
        self.assertIn("`[9국05-07]`", korean)
        for name, code in (
            ("생활_독일어", "[9생독05-04]"),
            ("생활_일본어", "[9생일05-05]"),
            ("생활_베트남어", "[9생베05-05]"),
        ):
            self.assertIn(code, (CORPUS / f"{name}.md").read_text(encoding="utf-8"))
        # 고시 별책과 낱말이 다른 성취기준은 표를 고치는 대신 머리에 적어 둔다.
        for name, code in (
            ("기술_가정", "[9기가03-03]"),
            ("미술", "[9미02-01]"),
            ("보건", "[9보02-02]"),
            ("사회_일반사회", "[9사(일사)01-03]"),
            ("사회_일반사회", "[9사(일사)11-03]"),
            ("생활_러시아어", "[9생러05-03]"),
            ("생활_독일어", "[9생독03-02]"),
            ("음악", "[9음02-05]"),
        ):
            with self.subTest(code=code):
                text = (CORPUS / f"{name}.md").read_text(encoding="utf-8")
                self.assertIn(f"| `{code}` |", text[:text.index("## 1. 성취기준별 성취수준")])

    def test_split_files_hold_only_their_own_codes(self) -> None:
        prefixes = {
            "사회_지리": "[9사(지리)",
            "사회_일반사회": "[9사(일사)",
            "생활_독일어": "[9생독",
            "생활_프랑스어": "[9생프",
            "생활_스페인어": "[9생스",
            "생활_중국어": "[9생중",
            "생활_일본어": "[9생일",
            "생활_러시아어": "[9생러",
            "생활_아랍어": "[9생아",
            "생활_베트남어": "[9생베",
        }
        for name, prefix in prefixes.items():
            with self.subTest(name=name):
                text = (CORPUS / f"{name}.md").read_text(encoding="utf-8")
                table = text[text.index("## 1. 성취기준별 성취수준"):]
                self.assertTrue(all(code.startswith(prefix) for code in CODE.findall(table)))

    def test_index_lists_every_course_and_links_resolve(self) -> None:
        index = (CORPUS / "index.md").read_text(encoding="utf-8")
        for path in self.course_paths():
            self.assertIn(f"]({path.name})", index)
        for target in re.findall(r"\]\(([^)#]+)\)", index):
            with self.subTest(target=target):
                self.assertTrue((CORPUS / target).exists())

    def test_usage_terms_and_their_limit_are_stated(self) -> None:
        attribution = (CORPUS / "ATTRIBUTION.md").read_text(encoding="utf-8")
        self.assertIn("공공누리 제2유형", attribution)
        self.assertIn("게시물별 표시는 개별로 확인하지 못했", attribution)
        index = (CORPUS / "index.md").read_text(encoding="utf-8")
        self.assertIn("공개 출처 안내", index)
        self.assertNotIn("로컬 전용", index)

    def test_catalog_is_public_and_covers_every_course(self) -> None:
        catalog = json.loads((CORPUS / "sources.json").read_text(encoding="utf-8"))
        self.assertEqual("public", catalog["distribution"])
        for source in catalog["sources"].values():
            self.assertEqual("kogl_type_2", source["redistribution_status"])
            self.assertEqual("ncic-site-policy", source["rights_basis"])
        self.assertEqual(set(STANDARD_COUNTS), set(catalog["groups"]))
        for name, group in catalog["groups"].items():
            with self.subTest(name=name):
                self.assertIn(group["achievement_level_scheme"], {"A~C", "A~E"})
                self.assertEqual([], group["amended_by_unchecked"])
                self.assertIn(LATEST_NOTICE, group["curriculum_edition_checked"])
                for source_id in group["source_ids"]:
                    self.assertTrue(catalog["sources"][source_id]["url"].startswith("https://ncic.re.kr/"))

    def test_high_school_corpus_stays_free_of_middle_school_codes(self) -> None:
        for path in HIGH_CORPUS.rglob("*.md"):
            with self.subTest(path=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"\[9[가-힣]")

    def test_skill_routes_here_only_on_explicit_request(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        row = next(line for line in skill.splitlines() if "achievement-standards-middle/index.md" in line)
        self.assertIn("중학교라고 명시", row)
        self.assertIn("명시가 없으면 고등학교 자료를 쓴다", row)
        self.assertIn("중학교 세특 문장 생성과 분량 판단은 하지 않는다", row)
        self.assertIn("achievement-standards/index.md", skill)

    def test_not_copied_into_public_package(self) -> None:
        plugin = SKILL_ROOT.parents[1] / "plugins" / "korean-school-records-toolkit"
        if plugin.is_dir():
            self.assertFalse((plugin / "skills" / "write-school-records" / "references" / CORPUS.name).exists())


if __name__ == "__main__":
    unittest.main()
