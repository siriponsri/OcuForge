from eyes_contracts.models import Annotation, Prediction
from labeler_bridge.geometry.convert import to_cvat
from labeler_bridge.provenance.lifecycle import event, utcnow


def import_prediction(prediction, image, frame=0, label_ids=None, attribute_ids=None):
    """Return API-shaped CVAT payload plus mandatory provenance sidecar.
    Local synthetic IDs are used only when mappings are omitted for offline fixtures.
    """
    pred = Prediction.model_validate(prediction.model_dump())
    if pred.image_id != image.image_id:
        raise ValueError("Prediction/image mismatch")
    labels = label_ids or {name: i + 1 for i, name in enumerate(sorted({o.label for o in pred.objects}))}
    sidecar = {}
    shapes = []
    tags = []
    now = utcnow()
    for obj in pred.objects:
        aid = "ANN_" + pred.prediction_id + "_" + obj.object_id
        a = Annotation(
            annotation_id=aid,
            image_id=image.image_id,
            label=obj.label,
            geometry=obj.geometry,
            origin="AI_SUGGESTED",
            parent_prediction_id=pred.prediction_id,
            parent_object_id=obj.object_id,
            source_model_version=pred.model_manifest_id,
            annotator_id_hash="AI_SYSTEM",
            review_status="DRAFT",
            confidence_if_ai=obj.confidence,
            created_at=now,
            updated_at=now,
            history=[event("AI_SUGGESTED", "DRAFT", "AI_SYSTEM", "PROPOSE", now, obj.geometry, obj.label)],
        )
        shape = to_cvat(obj.geometry, image.width_px, image.height_px)
        attrs = attribute_ids or {obj.label: {"ed_annotation_id": 1}}
        if obj.label not in labels or "ed_annotation_id" not in attrs[obj.label]:
            raise ValueError("Missing CVAT label/attribute mapping")
        base = {
            "label_id": labels[obj.label],
            "frame": frame,
            "source": "auto",
            "attributes": [{"spec_id": attrs[obj.label]["ed_annotation_id"], "value": aid}],
        }
        if shape["type"] == "tag":
            tags.append(base)
        else:
            shapes.append({**base, **shape, "occluded": False, "outside": False, "rotation": 0, "z_order": 0})
        sidecar[aid] = a.model_dump(mode="json")
    return {"version": 0, "shapes": shapes, "tags": tags, "tracks": []}, sidecar
