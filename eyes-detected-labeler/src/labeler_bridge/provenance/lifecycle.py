from datetime import datetime, timezone
from uuid import uuid4
from eyes_contracts.models import Annotation


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def event(origin, status, actor, action, timestamp, geometry=None, label=None):
    return {
        "event_id": "EV_" + uuid4().hex,
        "geometry_snapshot": geometry.model_dump() if hasattr(geometry, "model_dump") else geometry,
        "label_snapshot": label,
        "origin": origin,
        "review_status": status,
        "actor_id_hash": actor,
        "action": action,
        "timestamp": timestamp,
    }


def transition(
    annotation, action, actor, geometry=None, label=None, certainty="NOT_RECORDED", timestamp=None
):
    a = Annotation.model_validate(annotation.model_dump())
    d = a.model_dump()
    now = timestamp or utcnow()
    if a.review_status in ["LOCKED", "REJECTED"]:
        raise ValueError("Terminal annotation; create a versioned amendment")
    if action in ["CONFIRM", "CORRECT"]:
        if a.origin != "AI_SUGGESTED":
            raise ValueError("Confirm/correct requires AI suggestion")
        if action == "CORRECT" and geometry is None and label is None:
            raise ValueError("Correction requires geometry or label")
        d["origin"] = "CLINICIAN_" + ("CONFIRMED" if action == "CONFIRM" else "CORRECTED")
        d["review_status"] = "SUBMITTED"
    elif action == "REJECT":
        d["review_status"] = "REJECTED"
    elif action == "ESCALATE":
        d["review_status"] = "NEEDS_REVIEW"
        d["uncertain"] = True
    elif action == "ADJUDICATE":
        if a.origin == "AI_SUGGESTED" or a.review_status not in ["SUBMITTED", "NEEDS_REVIEW"]:
            raise ValueError("Human review required before adjudication")
        d.update(
            origin="EXPERT_ADJUDICATED",
            review_status="ADJUDICATED",
            adjudicator=actor,
            adjudication_timestamp=now,
            uncertain=False,
        )
    elif action == "LOCK":
        if a.review_status != "ADJUDICATED":
            raise ValueError("Adjudication required before lock")
        d["review_status"] = "LOCKED"
    elif action == "SUBMIT":
        if a.origin == "AI_SUGGESTED" or a.review_status != "DRAFT":
            raise ValueError("Only human draft can submit")
        d["review_status"] = "SUBMITTED"
    else:
        raise ValueError("Unknown action")
    if geometry is not None:
        if action not in ["CORRECT", "ADJUDICATE"]:
            raise ValueError("Geometry change requires correction action")
        d["geometry"] = geometry.model_dump() if hasattr(geometry, "model_dump") else geometry
    if label is not None:
        if action not in ["CORRECT", "ADJUDICATE"]:
            raise ValueError("Relabel requires correction")
        d["label"] = label
    d["annotator_id_hash"] = actor
    d["updated_at"] = now
    d["clinician_certainty"] = certainty
    d["history"].append(event(d["origin"], d["review_status"], actor, action, now, d["geometry"], d["label"]))
    return Annotation.model_validate(d)
