"""Pin the v1.1 vocabulary and the actual native extraction instructions."""

import copy
import json
from pathlib import Path

import pytest

from lightrag.extraction.fangzhi import project_payload, validate_payload, vocabulary
from lightrag.prompt import PROMPTS

PROFILE = Path(__file__).resolve().parents[2] / "prompts" / "fangzhi"


def test_native_drivers_use_all_v11_entity_and_relation_definitions():
    schema = (PROFILE / "entity_relation_types_v1.1.md").read_text(encoding="utf-8")
    entity_section, relation_section = schema.split("## 二、关系类型")
    entity_rows = [x for x in entity_section.splitlines() if x.startswith("|")][2:]
    relation_rows = [x for x in relation_section.splitlines() if x.startswith("|")][2:]
    guidance = PROMPTS["default_entity_types_guidance"]
    assert len(entity_rows) == 15
    assert len(relation_rows) == 45
    assert all(row in guidance for row in entity_rows)
    for key in ("entity_extraction_system_prompt", "entity_extraction_json_system_prompt"):
        rendered = PROMPTS[key].format(
            entity_types_guidance=guidance, language="Chinese", examples="",
            max_total_records=100, max_entity_records=40,
            tuple_delimiter="<|#|>", completion_delimiter="<|COMPLETE|>",
        )
        assert all(row in rendered for row in relation_rows)
        assert "时间与节令" not in rendered
        assert "制度与职官" not in rendered


def test_v11_endpoint_rules_keep_calendar_and_office_separate():
    vocab = vocabulary()
    assert len(vocab["entity_types"]) == 15
    assert len(vocab["content_relations"]) == 37
    assert vocab["content_relations"]["HOLDS_OFFICE"] == [
        [["Person"], ["OfficialPosition"]]
    ]
    assert vocab["content_relations"]["ASSOCIATED_WITH_CALENDAR"] == [
        [["CulturalPractice"], ["CalendarTerm"]]
    ]
    assert vocab["content_relations"]["HAS_COMPONENT_ACTIVITY"] == [
        [["CulturalPractice"], ["CulturalPractice"]],
        [["HistoricalEvent"], ["HistoricalEvent"]],
    ]


def test_calendar_context_projects_as_calendar_not_historical_time():
    payload = json.loads((PROFILE / "demo_result.json").read_text(encoding="utf-8"))
    validate_payload(payload)
    result = project_payload(payload)
    calendar_ids = {
        e["entity_id"] for e in payload["entities"] if e["entity_type"] == "CalendarTerm"
    }
    assert calendar_ids
    calendar_edges = [
        edge for edge in result["relationships"]
        if any(ident in edge["target"] or ident in edge["source"] for ident in calendar_ids)
    ]
    assert any("HAS_APPLICABLE_CALENDAR" in edge["keywords"] for edge in calendar_edges)
    assert all("HAS_APPLICABLE_TIME" not in edge["keywords"] for edge in calendar_edges)


def test_holds_office_rejects_institution_as_the_target():
    payload = json.loads((PROFILE / "demo_result.json").read_text(encoding="utf-8"))
    for number, name, typ in [(998, "某人", "Person"), (999, "某职", "OfficialPosition")]:
        entity = copy.deepcopy(payload["entities"][0])
        entity.update(entity_id=f"DEMO_B001_E{number}", entity_name=name, entity_type=typ)
        entity["attributes"] = {}
        payload["entities"].append(entity)
        payload["records"][0]["main_entity_ids"].append(entity["entity_id"])
    relation = copy.deepcopy(payload["relationships"][0])
    relation.update(relation_id="DEMO_B001_L999", source_id="DEMO_B001_E998",
                    target_id="DEMO_B001_E999", relation_type="HOLDS_OFFICE")
    payload["relationships"].append(relation)
    validate_payload(payload)
    payload["entities"][-1]["entity_type"] = "InstitutionalConcept"
    with pytest.raises(ValueError):
        validate_payload(payload)
