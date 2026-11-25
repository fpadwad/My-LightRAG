"""Grounding, identity and pipeline checks for Fangzhi research extraction."""

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from lightrag.extraction.fangzhi import (
    FangzhiProfile,
    project_payload,
    validate_payload,
)

PROJECT = Path(__file__).resolve().parents[2]
PROFILE = PROJECT / "prompts" / "fangzhi"
RAW = "甲县妇女于上元祭祖。乙县妇女不行祭祖。"
METADATA = {
    "book_title": "演示方志",
    "edition": None,
    "locator": None,
    "source_region": "示例地区",
    "bibliographic_information": None,
    "existing_entities": [],
}


def demo():
    return json.loads((PROFILE / "demo_result.json").read_text(encoding="utf-8"))


class ResearchValidationTests(unittest.TestCase):
    def test_demo_is_grounded_and_has_two_local_groups(self):
        payload = demo()
        validate_payload(payload, RAW, METADATA, "DEMO", "B001")
        groups = [x for x in payload["entities"] if x["entity_name"] == "妇女"]
        self.assertEqual(len(groups), 2)
        self.assertNotEqual(groups[0]["entity_id"], groups[1]["entity_id"])

    def test_unknown_entity_type_fails(self):
        payload = demo()
        payload["entities"][0]["entity_type"] = "Other"
        with self.assertRaisesRegex(ValueError, "entity type"):
            validate_payload(payload)

    def test_native_output_cannot_silently_replace_research_output(self):
        with self.assertRaisesRegex(ValueError, "top-level"):
            validate_payload({"entities": [], "relationships": []})

    def test_dangling_reference_fails(self):
        payload = demo()
        payload["relationships"][0]["target_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "dangling"):
            validate_payload(payload)

    def test_wrong_relation_direction_fails(self):
        payload = demo()
        rel = payload["relationships"][0]
        rel["source_id"], rel["target_id"] = rel["target_id"], rel["source_id"]
        with self.assertRaisesRegex(ValueError, "direction"):
            validate_payload(payload)

    def test_derived_relation_cannot_be_extracted_as_content(self):
        payload = demo()
        payload["relationships"][0]["relation_type"] = "RECORDED_IN"
        with self.assertRaisesRegex(ValueError, "derived"):
            validate_payload(payload)

    def test_fabricated_record_quote_fails(self):
        payload = demo()
        payload["records"][0]["quote"] = "invented history"
        with self.assertRaisesRegex(ValueError, "source text"):
            validate_payload(payload, RAW, METADATA)

    def test_bibliographic_place_cannot_be_used_as_applicable_place(self):
        payload = demo()
        payload["records"][0]["context_evidence"]["applicable_place_ids"] = [
            {
                "evidence_type": "输入元数据",
                "quote": "示例地区",
                "locator": None,
                "metadata_field": "source_region",
            }
        ]
        with self.assertRaisesRegex(ValueError, "bibliographic"):
            validate_payload(payload, RAW, METADATA)

    def test_wrong_metadata_quote_fails(self):
        payload = demo()
        payload["entities"][6]["evidence"][0]["quote"] = "another book"
        with self.assertRaisesRegex(ValueError, "supplied metadata"):
            validate_payload(payload, RAW, METADATA)

    def test_local_entity_cannot_escape_its_record(self):
        payload = demo()
        payload["entities"][1]["identity_scope"]["key"] = "DEMO_B001_R002"
        with self.assertRaisesRegex(ValueError, "escaped"):
            validate_payload(payload)

    def test_duplicate_assertion_fails(self):
        payload = demo()
        duplicate = copy.deepcopy(payload["relationships"][0])
        duplicate["relation_id"] = "DEMO_B001_L005"
        payload["relationships"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate assertion"):
            validate_payload(payload)

    def test_projection_preserves_negative_assertion_and_roles(self):
        native = project_payload(demo())
        assertions = [x for x in native["entities"] if x["type"] == "RelationAssertion"]
        self.assertEqual(len(assertions), 4)
        self.assertTrue(any("【否定】" in x["description"] for x in assertions))
        labels = [x["name"] for x in native["entities"]]
        self.assertEqual(len(labels), len(set(labels)))
        groups = [x["name"] for x in native["entities"] if x["type"] == "SocialGroup"]
        self.assertNotEqual(groups[0], groups[1])
        self.assertFalse(
            any("PRACTICES_CUSTOM" in x["keywords"] for x in native["relationships"])
        )
        self.assertTrue(
            any("HAS_SUBJECT" in x["keywords"] for x in native["relationships"])
        )

    def test_archive_is_idempotent_and_retains_canonical_data(self):
        with tempfile.TemporaryDirectory() as temp:
            profile = FangzhiProfile(PROFILE, "system", "DEMO", {}, "digest")
            request = {
                "dataset_id": "DEMO",
                "batch_id": "B001",
                "metadata": METADATA,
                "chunk_id": "chunk-test",
                "source_file": "demo.txt",
            }
            for _ in range(2):
                profile.validate_and_archive(
                    json.dumps(demo(), ensure_ascii=False),
                    request,
                    RAW,
                    {"working_dir": temp, "workspace": "demo"},
                )
            archives = list(Path(temp).rglob("*.json"))
            self.assertEqual(len(archives), 1)
            saved = json.loads(archives[0].read_text(encoding="utf-8"))
            self.assertEqual(saved["result"], demo())
            self.assertEqual(saved["raw_text"], RAW)

    def test_batch_identity_includes_workspace_and_document(self):
        profile = FangzhiProfile(PROFILE, "system", "FZ001", {}, "digest")
        chunk = {"file_path": "demo.txt", "full_doc_id": "doc1"}
        first = profile.prepare_input("same-chunk", chunk, {"workspace": "a"})
        second = profile.prepare_input("same-chunk", chunk, {"workspace": "b"})
        third = profile.prepare_input(
            "same-chunk", {**chunk, "full_doc_id": "doc2"}, {"workspace": "a"}
        )
        self.assertEqual(len({x["batch_id"] for x in [first, second, third]}), 3)

    def test_metadata_lookup_does_not_guess_by_basename(self):
        profile = FangzhiProfile(
            PROFILE, "system", "FZ001", {"a/demo.txt": METADATA}, "digest"
        )
        request = profile.prepare_input("c", {"file_path": "b/demo.txt"}, {})
        self.assertIsNone(request["metadata"]["book_title"])

    def test_spouse_requires_canonical_id_order(self):
        payload = demo()
        payload["entities"] = payload["entities"][:2]
        for e in payload["entities"]:
            e["entity_type"] = "Person"
            e["identity_scope"] = {"level": "batch", "key": "DEMO_B001", "note": "test"}
        record = payload["records"][0]
        record["source_document_id"] = None
        record["main_entity_ids"] = [x["entity_id"] for x in payload["entities"]]
        record["context"] = {k: [] for k in record["context"]}
        record["context_evidence"] = {k: [] for k in record["context_evidence"]}
        payload["records"] = [record]
        payload["review_notes"] = [
            {
                "note_id": "DEMO_B001_N001",
                "issue_type": "元数据缺失",
                "message": "test",
                "entity_ids": [],
                "record_ids": [],
                "evidence": [],
            }
        ]
        rel = payload["relationships"][0]
        rel.update(
            source_id="DEMO_B001_E002",
            target_id="DEMO_B001_E001",
            relation_type="HAS_SPOUSE",
        )
        payload["relationships"] = [rel]
        with self.assertRaisesRegex(ValueError, "canonical"):
            validate_payload(payload)
        rel["source_id"], rel["target_id"] = rel["target_id"], rel["source_id"]
        validate_payload(payload)


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_parser_and_rebuild_understand_research_payload(self):
        from lightrag.operate import (
            _process_json_extraction_result,
            _rebuild_from_extraction_result,
        )

        raw = json.dumps(demo(), ensure_ascii=False)
        nodes, edges = await _process_json_extraction_result(raw, "c", 1, "demo.txt")
        rebuilt = await _rebuild_from_extraction_result(
            None, raw, "c", 1, {"file_path": "demo.txt"}
        )
        self.assertEqual((nodes, edges), rebuilt)
        self.assertEqual(len(nodes), 14)
        self.assertTrue(edges)

    async def test_real_extraction_driver_uses_chinese_profile_and_archives(self):
        from lightrag.operate import extract_entities

        async def fake_model(prompt, **kwargs):
            self.assertIn("古代方志", kwargs["system_prompt"])
            request = json.loads(prompt.split("\n", 1)[1])
            prefix = request["dataset_id"] + "_" + request["batch_id"]
            payload = json.loads(
                json.dumps(demo(), ensure_ascii=False).replace("DEMO_B001", prefix)
            )
            payload["dataset_id"], payload["batch_id"] = (
                request["dataset_id"],
                request["batch_id"],
            )
            return json.dumps(payload, ensure_ascii=False)

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "profile"
            directory.mkdir()
            for name in ("schema.md", "extraction_prompt.md"):
                (directory / name).write_text(
                    (PROFILE / name).read_text(encoding="utf-8"), encoding="utf-8"
                )
            (directory / "source_metadata.json").write_text(
                json.dumps({"demo.txt": METADATA}, ensure_ascii=False), encoding="utf-8"
            )
            llm = AsyncMock(side_effect=fake_model)
            config = {
                "role_llm_funcs": {"extract": llm},
                "entity_extract_max_gleaning": 1,
                "entity_extract_max_records": 100,
                "entity_extract_max_entities": 40,
                "addon_params": {},
                "llm_model_max_async": 1,
                "working_dir": temp,
                "workspace": "test",
                "tokenizer": None,
            }
            env = {
                "FANGZHI_SCHEMA_ENABLED": "true",
                "FANGZHI_PROFILE_DIR": str(directory),
                "FANGZHI_DATASET_ID": "FZ001",
            }
            with patch.dict(os.environ, env):
                result = await extract_entities(
                    {
                        "chunk-test": {
                            "content": RAW,
                            "full_doc_id": "doc-test",
                            "file_path": "demo.txt",
                            "chunk_order_index": 0,
                        }
                    },
                    config,
                )
            self.assertEqual(llm.await_count, 1)
            self.assertEqual(len(result[0][0]), 14)
            self.assertEqual(
                len(list((Path(temp) / "fangzhi_records").rglob("*.json"))), 1
            )

    async def test_disabled_adapter_preserves_native_driver(self):
        from lightrag.operate import extract_entities

        payload = {
            "entities": [
                {
                    "name": "Native",
                    "type": "Concept",
                    "description": "native description",
                }
            ],
            "relationships": [],
        }
        llm = AsyncMock(return_value=json.dumps(payload))
        config = {
            "role_llm_funcs": {"extract": llm},
            "entity_extract_max_gleaning": 0,
            "entity_extract_max_records": 100,
            "entity_extract_max_entities": 40,
            "entity_extraction_use_json": True,
            "addon_params": {},
            "llm_model_max_async": 1,
        }
        with patch.dict(os.environ, {"FANGZHI_SCHEMA_ENABLED": "false"}):
            result = await extract_entities(
                {
                    "chunk-native": {
                        "content": "Native",
                        "full_doc_id": "d",
                        "file_path": "demo.txt",
                    }
                },
                config,
            )
        self.assertEqual(list(result[0][0]), ["Native"])


if __name__ == "__main__":
    unittest.main()
