from eyes_contracts.models import Annotation
from labeler_bridge.geometry.convert import from_cvat
from labeler_bridge.provenance.lifecycle import transition, event, utcnow


def export_annotations(
    payload, sidecar, images_by_frame, label_names, attribute_names, actor, decisions, grading_protocol=None
):
    """Explicit decision journal is mandatory; untouched AI never becomes human GT.
    Keys for additions: new:<CVAT server shape id>. Deletions need REJECT by old ID.
    """
    if payload.get("tracks"):
        raise ValueError("Video tracks unsupported in image starter")
    out = []
    seen = set()
    for raw in payload.get("shapes", []) + [
        {**t, "type": "tag", "points": []} for t in payload.get("tags", [])
    ]:
        im = images_by_frame[raw["frame"]]
        label = label_names[raw["label_id"]]
        attrs = {
            attribute_names[a["spec_id"]]: a["value"]
            for a in raw.get("attributes", [])
            if a["spec_id"] in attribute_names
        }
        aid = attrs.get("ed_annotation_id", "")
        geom = from_cvat(raw, im.width_px, im.height_px)
        grade_fields = {}
        if label == "dr_grade":
            if grading_protocol is None:
                raise ValueError("DR grading export requires frozen protocol reference")
            grade_value = attrs.get("dr_grade", "UNSET")
            if grade_value == "UNSET":
                raise ValueError("Clinician grade has not been set")
            if grade_value not in ["0", "1", "2", "3", "4", "UNGRADABLE", "UNCERTAIN"]:
                raise ValueError("Invalid clinician grade")
            grade_fields = {
                "grading_protocol": grading_protocol,
                "dr_grade": int(grade_value) if grade_value.isdigit() else None,
                "gradability": "UNGRADABLE" if grade_value == "UNGRADABLE" else "UNKNOWN",
                "uncertain": grade_value == "UNCERTAIN",
            }
        if aid:
            if aid not in sidecar or aid in seen:
                raise ValueError("Unknown or duplicate provenance ID")
            a = Annotation.model_validate(sidecar[aid])
            seen.add(aid)
            if a.image_id != im.image_id:
                raise ValueError("Frame/image identity changed")
            if label == "dr_grade" and (
                a.dr_grade != grade_fields["dr_grade"] or a.grading_protocol != grading_protocol
            ):
                raise ValueError(
                    "Grading revision requires versioned manual amendment; never overwrite old protocol"
                )
            import numpy as np

            geometry_changed = (
                a.geometry.type != geom.type
                or a.geometry.mask_rle != geom.mask_rle
                or a.geometry.mask_size != geom.mask_size
                or len(a.geometry.coordinates_norm) != len(geom.coordinates_norm)
                or not np.allclose(a.geometry.coordinates_norm, geom.coordinates_norm, atol=1e-9, rtol=0)
            )
            changed = a.label != label or geometry_changed
            action = decisions.get(aid)
            if changed and action not in ["CORRECT", "ADJUDICATE"]:
                raise ValueError("Edited geometry requires explicit CORRECT decision")
            if action:
                a = transition(
                    a, action, actor, geometry=geom if changed else None, label=label if changed else None
                )
        else:
            key = "new:" + str(raw.get("id", ""))
            if decisions.get(key) != "ADD":
                raise ValueError("Manual addition requires ADD journal entry")
            aid = "ANN_MANUAL_" + im.image_id + "_" + str(raw["id"])
            now = utcnow()
            a = Annotation(
                annotation_id=aid,
                image_id=im.image_id,
                label=label,
                geometry=geom,
                origin="CLINICIAN_ADDED",
                annotator_id_hash=actor,
                review_status="DRAFT",
                created_at=now,
                updated_at=now,
                history=[event("CLINICIAN_ADDED", "DRAFT", actor, "ADD", now, geom, label)],
                **grade_fields,
            )
        out.append(a)
    for aid, record in sidecar.items():
        if aid in seen:
            continue
        if decisions.get(aid) != "REJECT":
            raise ValueError("Deleted candidate requires REJECT event; provenance cannot disappear")
        out.append(transition(Annotation.model_validate(record), "REJECT", actor))
    return out


def session_summary(annotations, active_seconds, synthetic_demo=False):
    if active_seconds <= 0:
        raise ValueError("Positive active annotation seconds required")
    actions = [e.action for a in annotations for e in a.history]
    offered = sum(bool(a.parent_prediction_id) for a in annotations)
    return {
        "images": len({a.image_id for a in annotations}),
        "active_annotation_seconds": active_seconds,
        "ai_objects_offered": offered,
        "ai_objects_confirmed": actions.count("CONFIRM"),
        "ai_objects_corrected": actions.count("CORRECT"),
        "ai_objects_rejected": actions.count("REJECT"),
        "human_objects_added": actions.count("ADD"),
        "adjudication_events": actions.count("ADJUDICATE"),
        "acceptance_rate": actions.count("CONFIRM") / offered if offered else None,
        "annotation_yield_per_hour": sum(
            a.review_status in ["SUBMITTED", "ADJUDICATED", "LOCKED"] for a in annotations
        )
        * 3600
        / active_seconds,
        "synthetic_demo": synthetic_demo,
    }
