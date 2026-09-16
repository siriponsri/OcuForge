"""Versioned Global→ROI soft-triage contracts.

The decision consumes model, QC, OOD, calibration, protocol, and reviewer state. It does not
infer clinical meaning from GUI state or from a missing lesion annotation.
"""

from typing import Literal

from pydantic import Field, model_validator

from .models import ID, Prob, ProtocolRef, Strict


GLOBAL_NO_DR = "GLOBAL_NO_DR"
NO_SUPPORTED_LESION_IN_ROI = "NO_SUPPORTED_LESION_IN_ROI"
REVIEWER_CONTROLS = ["ACCEPT", "MARK_INCORRECT", "CORRECT_GRADE", "COMMENT", "INSPECT_ROI_ANYWAY"]


class TriagePolicy(Strict):
    schema_version: Literal["global_roi_triage_policy.v0.1"] = "global_roi_triage_policy.v0.1"
    policy_id: ID
    confidence_threshold: Prob | None = None
    threshold_status: Literal["UNSET_UNVALIDATED", "VALIDATED"] = "UNSET_UNVALIDATED"
    calibration_version: ID | None = None

    @model_validator(mode="after")
    def threshold_provenance(self):
        if self.confidence_threshold is None:
            if self.threshold_status != "UNSET_UNVALIDATED" or self.calibration_version is not None:
                raise ValueError("Unset triage threshold cannot claim validation")
        elif self.threshold_status != "VALIDATED" or not self.calibration_version:
            raise ValueError("A set triage threshold requires validation and calibration version")
        return self


class GlobalROITriageInput(Strict):
    schema_version: Literal["global_roi_triage_input.v0.1"] = "global_roi_triage_input.v0.1"
    image_id: ID
    in_scope: bool
    gradability: Literal["GRADABLE", "PARTIALLY_GRADABLE", "UNGRADABLE", "UNKNOWN"]
    predicted_grade: int = Field(ge=0, le=4)
    calibrated_confidence: Prob | None = None
    qc_uncertainty: bool = False
    ood_flag: bool = False
    grading_protocol: ProtocolRef | None = None
    reviewer_override: Literal["NONE", "OPEN_ROI_REVIEW", "INSPECT_ROI_ANYWAY"] = "NONE"


class TriageDecision(Strict):
    schema_version: Literal["global_roi_triage_decision.v0.1"] = "global_roi_triage_decision.v0.1"
    image_id: ID
    action: Literal["DEFAULT_SKIP_ROI_REVIEW", "OPEN_ROI_REVIEW"]
    reason_codes: list[
        Literal[
            "REVIEWER_OVERRIDE",
            "OUT_OF_SCOPE",
            "NOT_GRADABLE",
            "GRADE_REQUIRES_REVIEW",
            "LOW_CONFIDENCE",
            "QC_UNCERTAINTY",
            "OOD_FLAG",
            "PROTOCOL_UNKNOWN",
            "THRESHOLD_UNSET",
            "SAFE_GLOBAL_NO_DR"
        ]
    ] = Field(min_length=1)
    reviewer_controls: list[str] = Field(min_length=5)
    global_semantic: Literal["GLOBAL_NO_DR", "GLOBAL_DR_PRESENT_OR_UNCERTAIN"]

    @model_validator(mode="after")
    def controls_are_available(self):
        if self.reviewer_controls != REVIEWER_CONTROLS:
            raise ValueError("All reviewer controls must remain available")
        return self


class ROILesionReviewResult(Strict):
    schema_version: Literal["roi_lesion_review_result.v0.1"] = "roi_lesion_review_result.v0.1"
    roi_id: ID
    result: Literal["SUPPORTED_LESION_PRESENT", "NO_SUPPORTED_LESION_IN_ROI"]
    supported_classes: list[
        Literal[
            "MICROANEURYSM",
            "INTRARETINAL_HEMORRHAGE",
            "HARD_EXUDATE",
            "SOFT_EXUDATE"
        ]
    ] = Field(min_length=1)
    decision_threshold: Prob


def decide_global_to_roi(state: GlobalROITriageInput, policy: TriagePolicy) -> TriageDecision:
    """Apply the soft default gate while preserving reviewer override and controls."""

    semantic = GLOBAL_NO_DR if state.predicted_grade == 0 else "GLOBAL_DR_PRESENT_OR_UNCERTAIN"
    if state.reviewer_override != "NONE":
        return TriageDecision(
            image_id=state.image_id,
            action="OPEN_ROI_REVIEW",
            reason_codes=["REVIEWER_OVERRIDE"],
            reviewer_controls=REVIEWER_CONTROLS,
            global_semantic=semantic,
        )

    reasons = []
    if not state.in_scope:
        reasons.append("OUT_OF_SCOPE")
    if state.gradability != "GRADABLE":
        reasons.append("NOT_GRADABLE")
    if state.predicted_grade != 0:
        reasons.append("GRADE_REQUIRES_REVIEW")
    if state.qc_uncertainty:
        reasons.append("QC_UNCERTAINTY")
    if state.ood_flag:
        reasons.append("OOD_FLAG")
    if state.grading_protocol is None:
        reasons.append("PROTOCOL_UNKNOWN")
    if policy.confidence_threshold is None:
        reasons.append("THRESHOLD_UNSET")
    elif state.calibrated_confidence is None or state.calibrated_confidence < policy.confidence_threshold:
        reasons.append("LOW_CONFIDENCE")

    if reasons:
        return TriageDecision(
            image_id=state.image_id,
            action="OPEN_ROI_REVIEW",
            reason_codes=reasons,
            reviewer_controls=REVIEWER_CONTROLS,
            global_semantic=semantic,
        )
    return TriageDecision(
        image_id=state.image_id,
        action="DEFAULT_SKIP_ROI_REVIEW",
        reason_codes=["SAFE_GLOBAL_NO_DR"],
        reviewer_controls=REVIEWER_CONTROLS,
        global_semantic=GLOBAL_NO_DR,
    )


TRIAGE_TYPES = {
    "global_roi_triage_policy.v0.1": TriagePolicy,
    "global_roi_triage_input.v0.1": GlobalROITriageInput,
    "global_roi_triage_decision.v0.1": TriageDecision,
    "roi_lesion_review_result.v0.1": ROILesionReviewResult,
}
