# Bridge API and provenance journal

`import_prediction(prediction, image, frame, label_ids, attribute_ids)` returns an API-shaped CVAT annotation payload and a sidecar keyed by immutable `ed_annotation_id`. The sidecar holds full history and parent model/object IDs. CVAT's generic `source` field alone is insufficient.

`export_annotations(payload, sidecar, images_by_frame, label_names, attribute_names, actor, decisions, grading_protocol=None)` returns validated native annotations. `decisions` maps annotation ID to CONFIRM, CORRECT, REJECT, ESCALATE or ADJUDICATE; additions use `new:<server-shape-id>` → ADD. Explicit journals are data-manager inputs in v0.1. The CVAT review_action attribute is a review aid; it is not silently trusted as an adjudicator identity.

Unchanged AI proposals remain AI_SUGGESTED. Deleted proposals require explicit REJECT and remain in the exported history. Geometry edits without CORRECT fail. Human additions start DRAFT. Use `transition(a, 'SUBMIT', actor)` then specialist ADJUDICATE and LOCK. Role/account authorization belongs to the local CVAT deployment; the offline bridge validates state, not a hospital IAM system.

For a DR tag, include `dr_grade` attribute and pass ProtocolRef from `eyes_contracts.protocol.load_protocol`. Values 0–4, UNGRADABLE and UNCERTAIN are distinct. Unknown grade fails export. Old grading revisions require an explicit versioned amendment rather than replacing the stored grade/protocol.

Save native annotations with `eyes_contracts.validators.write_records('annotations.jsonl', annotations)`. Validate with `eyes-contracts validate annotations.jsonl`. Train ingest requires the authoritative image manifest and checks split eligibility independently.

Mask representation: full-image row-major binary RLE, alternating zero/one run counts, beginning with a zero run (possibly length 0). CVAT payload appends inclusive crop bounding box; converter can expand cropped CVAT masks. Ellipse native representation is normalized x0,y0,x1,y1; rotated ellipses must be exported as masks. Floating point coordinate comparisons use a 1e-9 tolerance.
