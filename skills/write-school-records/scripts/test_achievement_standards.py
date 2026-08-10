#!/usr/bin/env python3

import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).parents[1]
CORPUS = SKILL_ROOT / "references" / "achievement-standards"
CORPUS_PRESENT = CORPUS.is_dir()

NEW_COURSES = {
    "korean": ["공통국어1", "공통국어2"],
    "social-studies": ["통합사회1", "통합사회2"],
    "history": ["한국사1", "한국사2"],
    "english": ["공통영어1", "공통영어2", "기본영어1", "기본영어2"],
    "math": ["공통수학1", "공통수학2", "기본수학1", "기본수학2"],
    "science": ["통합과학1", "통합과학2", "과학탐구실험1", "과학탐구실험2"],
    "information": ["정보", "인공지능_기초", "데이터_과학", "소프트웨어와_생활", "정보과학"],
    "classical-chinese": ["한문", "한문_고전_읽기", "언어생활과_한자"],
    "health": ["보건과"],
    "environment": ["생태와_환경"],
    "career": ["진로와_직업"],
    "french": ["프랑스어", "심화_프랑스어", "프랑스어_회화", "프랑스어권_문화"],
    "spanish": ["스페인어", "심화_스페인어", "스페인어_회화", "스페인어권_문화"],
    "chinese": ["중국어", "심화_중국어", "중국어_회화", "중국_문화"],
    "japanese": ["일본어", "심화_일본어", "일본어_회화", "일본_문화"],
    "russian": ["러시아어", "심화_러시아어", "러시아어_회화", "러시아_문화"],
    "arabic": ["아랍어", "심화_아랍어", "아랍어_회화", "아랍_문화"],
    "vietnamese": ["베트남어", "심화_베트남어", "베트남어_회화", "베트남_문화"],
}


@unittest.skipUnless(CORPUS_PRESENT, "성취수준 코퍼스가 없는 환경")
class AchievementStandardsCorpusTests(unittest.TestCase):
    def test_all_course_files_are_descriptor_only(self) -> None:
        excluded = re.compile(r"성취수준 개발의 이해|성취수준 활용|예시.{0,20}평가|<img|!\[|image_[0-9]+", re.I)
        paths = sorted(
            path
            for path in CORPUS.rglob("*.md")
            if path.name not in {"index.md", "common.md", "ATTRIBUTION.md"}
        )
        self.assertEqual(224, len(paths))
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertGreater(len(text), 200)
                self.assertRegex(text, r"성취기준별 성취수준|영역별 성취수준")
                self.assertIsNone(excluded.search(text))

    def test_new_course_manifest_stays_complete(self) -> None:
        paths = [CORPUS / subject / f"{course}.md" for subject, courses in NEW_COURSES.items() for course in courses]
        self.assertEqual(57, len(paths))
        self.assertTrue(all(path.is_file() for path in paths))

    def test_all_index_links_resolve(self) -> None:
        for index in CORPUS.rglob("index.md"):
            for target in re.findall(r"\[[^]]+\]\(([^)]+\.md)\)", index.read_text(encoding="utf-8")):
                with self.subTest(index=index, target=target):
                    self.assertTrue((index.parent / target).is_file())

    def test_indexes_carry_public_source_notice(self) -> None:
        for path in [*CORPUS.rglob("index.md"), CORPUS / "common.md"]:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("공개 출처 안내", text)
                self.assertIn("NCIC 국가교육과정정보센터", text)

    def test_source_catalog_declares_public_distribution(self) -> None:
        catalog = json.loads((CORPUS / "sources.json").read_text(encoding="utf-8"))
        self.assertEqual("public", catalog["distribution"])

    def test_attribution_distinguishes_common_and_elective_sources(self) -> None:
        text = (CORPUS / "ATTRIBUTION.md").read_text(encoding="utf-8")
        self.assertIn("NCIC 국가교육과정정보센터", text)
        self.assertIn("NKIS 연구정보", text)
        self.assertIn("공공누리 제1유형", text)
        self.assertIn("공공누리 제2유형", text)

    def test_source_catalog_is_structured_and_covers_every_subject_index(self) -> None:
        catalog = json.loads((CORPUS / "sources.json").read_text(encoding="utf-8"))
        self.assertEqual(1, catalog["schema_version"])
        self.assertRegex(catalog["checked_on"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(2, catalog["rights_policies"]["ncic_kogl_type_2"]["kogl_type"])
        self.assertEqual(1, catalog["rights_policies"]["nkis_kogl_type_1"]["kogl_type"])

        subject_indexes = [path for path in CORPUS.rglob("index.md") if path != CORPUS / "index.md"]
        groups = catalog["groups"]
        sources = catalog["sources"]
        self.assertEqual(29, len(subject_indexes))
        self.assertEqual({path.parent.name for path in subject_indexes}, set(groups))
        referenced_source_ids: set[str] = set()
        for index in subject_indexes:
            group_id = index.parent.name
            with self.subTest(group_id=group_id):
                self.assertIn(f"<!-- source_group: {group_id} -->", index.read_text(encoding="utf-8"))
                group = groups[group_id]
                self.assertIn(group["achievement_level_scheme"], {"A~C", "A~E", "source-defined"})
                self.assertGreaterEqual(len(group["source_ids"]), 1)
                for source_id in group["source_ids"]:
                    referenced_source_ids.add(source_id)
                    self.assertIn(source_id, sources)
                    source = sources[source_id]
                    self.assertTrue(source["title"])
                    self.assertTrue(source["url"].startswith("https://ncic.re.kr/"))
                    self.assertRegex(source["posted_on"], r"^\d{4}-\d{2}-\d{2}$")
                    self.assertEqual("ncic", source["publisher_id"])
                    self.assertIn(source["publisher_id"], catalog["publishers"])
                    self.assertTrue(source["public_access"])
                    expected_status = "kogl_type_1" if source_id.startswith("ncic-2025-") else "kogl_type_2"
                    expected_policy = "nkis_kogl_type_1" if source_id.startswith("ncic-2025-") else "ncic_kogl_type_2"
                    self.assertEqual(expected_status, source["redistribution_status"])
                    self.assertEqual(expected_policy, source["rights_policy_id"])
                    self.assertIn(source["rights_policy_id"], catalog["rights_policies"])
        self.assertEqual(set(sources), referenced_source_ids)

    def test_common_background_exists_once_and_not_in_subject_indexes(self) -> None:
        self.assertEqual([CORPUS / "common.md"], list(CORPUS.rglob("common.md")))
        for index in CORPUS.rglob("index.md"):
            with self.subTest(index=index):
                self.assertNotIn("## 성취수준이란 (공통 배경)", index.read_text(encoding="utf-8"))

    def test_common_background_is_routed_from_index_and_skill(self) -> None:
        index_text = (CORPUS / "index.md").read_text(encoding="utf-8")
        self.assertIn("[공통 배경](common.md)", index_text)
        self.assertIn("[출처·이용조건 메타데이터](sources.json)", index_text)
        self.assertIn("[출처와 이용 안내](ATTRIBUTION.md)", index_text)
        self.assertNotIn("성취수준(A~E) 원문 색인", index_text)
        self.assertIn("achievement-standards/common.md", (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"))

    def test_subject_routing_covers_health_and_environment(self) -> None:
        catalog = json.loads((CORPUS / "sources.json").read_text(encoding="utf-8"))
        self.assertTrue({"health", "environment"} <= set(catalog["groups"]))

    def test_achievement_level_label_covers_three_and_five_levels(self) -> None:
        catalog = json.loads((CORPUS / "sources.json").read_text(encoding="utf-8"))
        schemes = {g["achievement_level_scheme"] for g in catalog["groups"].values()}
        self.assertTrue({"A~C", "A~E"} <= schemes)


if __name__ == "__main__":
    unittest.main()
