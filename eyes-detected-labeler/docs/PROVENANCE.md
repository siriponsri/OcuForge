# Provenance

Six origins remain distinct: AI_SUGGESTED, CLINICIAN_CONFIRMED, CLINICIAN_CORRECTED, CLINICIAN_ADDED, EXPERT_ADJUDICATED, IMPORTED_PUBLIC_GT.

Review states are DRAFT, SUBMITTED, NEEDS_REVIEW, ADJUDICATED, LOCKED, REJECTED. History is append-only within lifecycle operations. A rejected object is a retained audit record, not a training target. Stable parent_prediction_id and parent_object_id preserve the offered candidate.

The native JSONL export and provenance sidecar are the stable boundary. No training dependency on CVAT exists. Local binary source assessments are not relabeled as any of these object origins unless a new actual annotation event occurs.
