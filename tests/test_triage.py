import json
from pathlib import Path

import jsonschema
import pytest

from eyes_contracts.models import ProtocolRef
from eyes_contracts.validators import validate
from eyes_contracts.triage import (
    CONFIRM_SUPPORTED_LESION,
    CORRECT_SUPPORTED_LESION,
    GLOBAL_NO_DR,
    NO_SUPPORTED_LESION_IN_ROI,
    UNKNOWN_OR_UNSUPPORTED_FINDING,
    GlobalROITriageInput,
    ROILesionReviewResult,
    ROILesionReviewResultV02,
    TriagePolicy,
    decide_global_to_roi,
)


def protocol():
    return ProtocolRef(protocol_id="ICO_2017_DR", version="0.1", config_sha256="a" * 64)


def state(**updates):
    values = {
        "image_id": "IMG_1",
        "in_scope": True,
        "gradability": "GRADABLE",
        "predicted_grade": 0,
        "calibrated_confidence": 0.95,
        "grading_protocol": protocol(),
    }
    values.update(updates)
    return GlobalROITriageInput(**values)


def test_unset_threshold_never_skips_roi_review():
    decision = decide_global_to_roi(state(), TriagePolicy(policy_id="POLICY_V1"))
    assert decision.action == "OPEN_ROI_REVIEW"
    assert "THRESHOLD_UNSET" in decision.reason_codes
    assert decision.global_semantic == GLOBAL_NO_DR
    assert "INSPECT_ROI_ANYWAY" in decision.reviewer_controls


def test_validated_threshold_can_default_skip_only_when_all_conditions_hold():
    policy = TriagePolicy(
        policy_id="POLICY_V1",
        confidence_threshold=0.95,
        threshold_status="VALIDATED",
        calibration_version="CAL_V1",
    )
    assert decide_global_to_roi(state(), policy).action == "DEFAULT_SKIP_ROI_REVIEW"
    assert decide_global_to_roi(state(calibrated_confidence=0.94), policy).action == "OPEN_ROI_REVIEW"
    assert decide_global_to_roi(state(ood_flag=True), policy).action == "OPEN_ROI_REVIEW"


def test_reviewer_override_bypasses_default_skip():
    policy = TriagePolicy(
        policy_id="POLICY_V1",
        confidence_threshold=0.95,
        threshold_status="VALIDATED",
        calibration_version="CAL_V1",
    )
    decision = decide_global_to_roi(state(reviewer_override="INSPECT_ROI_ANYWAY"), policy)
    assert decision.action == "OPEN_ROI_REVIEW"
    assert decision.reason_codes == ["REVIEWER_OVERRIDE"]


def test_threshold_validation_and_roi_negative_semantics():
    with pytest.raises(ValueError):
        TriagePolicy(policy_id="POLICY_V1", confidence_threshold=0.5)
    negative = ROILesionReviewResult(
        roi_id="ROI_1",
        result=NO_SUPPORTED_LESION_IN_ROI,
        supported_classes=["MICROANEURYSM", "INTRARETINAL_HEMORRHAGE", "HARD_EXUDATE", "SOFT_EXUDATE"],
        decision_threshold=0.9,
    )
    assert negative.result != GLOBAL_NO_DR


def model_suggestion(result="SUPPORTED_LESION_PRESENT", **updates):
    values = {
        "prediction_id": "PRED_001",
        "model_manifest_id": "MODEL_001",
        "result": result,
        # Keep the original v0.1 model-side shape, including its required class list.
        "supported_classes": ["MICROANEURYSM"],
        "decision_threshold": 0.9,
    }
    values.update(updates)
    return values


def review(decision, suggestion=None, **updates):
    values = {
        "roi_id": "ROI_1",
        "original_model_suggestion": suggestion or model_suggestion(),
        "reviewer_decision": decision,
    }
    values.update(updates)
    return ROILesionReviewResultV02(**values)


def schema_validate(record):
    root = Path(__file__).resolve().parents[1] / "eyes-detected-contracts" / "schemas"
    schema = json.loads((root / f"{record['schema_version']}.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(record, schema)


@pytest.mark.parametrize(
    "decision,suggestion,extra",
    [
        (CONFIRM_SUPPORTED_LESION, model_suggestion(), {}),
        (
            CORRECT_SUPPORTED_LESION,
            model_suggestion(result="NO_SUPPORTED_LESION_IN_ROI"),
            {"reviewer_supported_classes": ["HARD_EXUDATE"]},
        ),
        (
            UNKNOWN_OR_UNSUPPORTED_FINDING,
            model_suggestion(),
            {"reviewer_remark": "Not supported by the current taxonomy."},
        ),
        (
            NO_SUPPORTED_LESION_IN_ROI,
            model_suggestion(result="NO_SUPPORTED_LESION_IN_ROI"),
            {},
        ),
    ],
)
def test_v02_supports_exact_clinician_outcomes(decision, suggestion, extra):
    assert review(decision, suggestion, **extra).reviewer_decision == decision


@pytest.mark.parametrize(
    "decision", [CONFIRM_SUPPORTED_LESION, CORRECT_SUPPORTED_LESION, NO_SUPPORTED_LESION_IN_ROI]
)
@pytest.mark.parametrize("remark", ["", "   "])
def test_known_v02_outcomes_allow_empty_or_whitespace_remarks(decision, remark):
    extra = {"reviewer_supported_classes": ["MICROANEURYSM"]} if decision == CORRECT_SUPPORTED_LESION else {}
    assert review(decision, reviewer_remark=remark, **extra).reviewer_remark == remark


@pytest.mark.parametrize("remark", ["", "   ", "\t\n"])
def test_unknown_v02_outcome_requires_non_whitespace_remark(remark):
    with pytest.raises(ValueError, match="non-whitespace remark"):
        review(UNKNOWN_OR_UNSUPPORTED_FINDING, reviewer_remark=remark)
    assert review(UNKNOWN_OR_UNSUPPORTED_FINDING, reviewer_remark="Needs specialist review").reviewer_remark


@pytest.mark.parametrize(
    "decision", [CONFIRM_SUPPORTED_LESION, CORRECT_SUPPORTED_LESION, NO_SUPPORTED_LESION_IN_ROI]
)
@pytest.mark.parametrize("remark", [None, "", "   "])
def test_json_schema_and_pydantic_allow_known_remarks(decision, remark):
    extra = {"reviewer_supported_classes": ["MICROANEURYSM"]} if decision == CORRECT_SUPPORTED_LESION else {}
    record = review(decision, reviewer_remark=remark or "", **extra).model_dump(mode="json")
    if remark is None:
        record.pop("reviewer_remark")
    schema_validate(record)
    validated = validate(record)
    assert validated.reviewer_decision == decision
    assert validated.reviewer_remark == ("" if remark is None else remark)


@pytest.mark.parametrize("remark", [None, "", "   ", "\t\n"])
def test_json_schema_and_pydantic_reject_unknown_without_non_whitespace_remark(remark):
    record = {
        "schema_version": "roi_lesion_review_result.v0.2",
        "roi_id": "ROI_1",
        "original_model_suggestion": model_suggestion(),
        "reviewer_decision": UNKNOWN_OR_UNSUPPORTED_FINDING,
    }
    if remark is not None:
        record["reviewer_remark"] = remark
    with pytest.raises(jsonschema.ValidationError):
        schema_validate(record)
    with pytest.raises(ValueError, match="non-whitespace remark"):
        validate(record)


def test_json_schema_and_pydantic_accept_unknown_with_non_whitespace_remark():
    record = review(
        UNKNOWN_OR_UNSUPPORTED_FINDING, reviewer_remark="Needs specialist review"
    ).model_dump(mode="json")
    schema_validate(record)
    assert validate(record).reviewer_decision == UNKNOWN_OR_UNSUPPORTED_FINDING


@pytest.mark.parametrize(
    "decision,suggestion,extra",
    [
        (
            CONFIRM_SUPPORTED_LESION,
            model_suggestion(result="NO_SUPPORTED_LESION_IN_ROI"),
            {},
        ),
        (CORRECT_SUPPORTED_LESION, model_suggestion(), {}),
        (
            UNKNOWN_OR_UNSUPPORTED_FINDING,
            model_suggestion(),
            {"reviewer_supported_classes": ["MICROANEURYSM"], "reviewer_remark": "Unclear"},
        ),
        (
            NO_SUPPORTED_LESION_IN_ROI,
            model_suggestion(),
            {"reviewer_supported_classes": ["MICROANEURYSM"]},
        ),
    ],
)
def test_v02_rejects_invalid_semantic_combinations(decision, suggestion, extra):
    with pytest.raises(ValueError):
        review(decision, suggestion, **extra)


def test_v02_retains_original_model_result_and_provenance_separately():
    record = review(
        CORRECT_SUPPORTED_LESION,
        model_suggestion(result="NO_SUPPORTED_LESION_IN_ROI"),
        reviewer_supported_classes=["SOFT_EXUDATE"],
    )
    assert record.original_model_suggestion.result == "NO_SUPPORTED_LESION_IN_ROI"
    assert record.original_model_suggestion.prediction_id == "PRED_001"
    assert record.original_model_suggestion.model_manifest_id == "MODEL_001"
    dumped = record.model_dump(mode="json")
    assert dumped["original_model_suggestion"]["result"] == "NO_SUPPORTED_LESION_IN_ROI"
    assert dumped["reviewer_decision"] == CORRECT_SUPPORTED_LESION


def test_global_unknown_and_roi_negative_are_distinct_semantics():
    assert len({GLOBAL_NO_DR, UNKNOWN_OR_UNSUPPORTED_FINDING, NO_SUPPORTED_LESION_IN_ROI}) == 3
    assert review(UNKNOWN_OR_UNSUPPORTED_FINDING, reviewer_remark="Unclear")
    assert review(NO_SUPPORTED_LESION_IN_ROI, model_suggestion(result="NO_SUPPORTED_LESION_IN_ROI"))


def test_validate_accepts_v01_and_v02_but_rejects_unknown_version():
    legacy = ROILesionReviewResult(
        roi_id="ROI_1",
        result=NO_SUPPORTED_LESION_IN_ROI,
        supported_classes=["MICROANEURYSM"],
        decision_threshold=0.9,
    )
    current = review(CONFIRM_SUPPORTED_LESION)
    assert validate(legacy.model_dump()) == legacy
    assert validate(current.model_dump()) == current
    with pytest.raises(ValueError, match="Unsupported schema version"):
        validate(current.model_dump() | {"schema_version": "roi_lesion_review_result.v9"})


@pytest.mark.parametrize("record", [
    ROILesionReviewResult(
        roi_id="ROI_1",
        result=NO_SUPPORTED_LESION_IN_ROI,
        supported_classes=["MICROANEURYSM"],
        decision_threshold=0.9,
    ),
    review(CONFIRM_SUPPORTED_LESION),
])
def test_matching_triage_schema_accepts_record_and_rejects_extra_fields(record):
    root = Path(__file__).resolve().parents[1] / "eyes-detected-contracts" / "schemas"
    schema = json.loads((root / f"{record.schema_version}.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(record.model_dump(mode="json"), schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(record.model_dump(mode="json") | {"unexpected": "bad"}, schema)
