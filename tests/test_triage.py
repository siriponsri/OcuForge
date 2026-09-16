import pytest

from eyes_contracts.models import ProtocolRef
from eyes_contracts.triage import (
    GLOBAL_NO_DR,
    NO_SUPPORTED_LESION_IN_ROI,
    GlobalROITriageInput,
    ROILesionReviewResult,
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
