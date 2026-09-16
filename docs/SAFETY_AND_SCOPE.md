# Safety and scope — OcuForge V3

OcuForge is research-only. Its outputs are not diagnoses, referrals, or production clinical decisions.

- Hospital/private images, labels, embeddings, predictions, checkpoints, backups, and derivatives stay on-premise.
- Public GPU is limited to reviewed public/synthetic training, extraction, and experiment compute.
- GitHub stores code, safe manifests, metadata, hashes, reports, and synthetic fixtures—not private or large artifacts.
- Binary `DR`/`no-DR` experience labels are never upgraded to ordinal grades or lesion masks.
- DME is separate; fundus/UWF evidence is not OCT-confirmed DME.
- MIL attention is aggregation evidence, not validated lesion localization.
- `NO_SUPPORTED_LESION_IN_ROI` is scoped to a selected ROI and supported taxonomy only.
- The existing `templates/` GUI is preserved; CVAT remains optional advanced infrastructure.
- Phase 2B live Mongo remains unresolved; Phase 2A does not make Phase 2 PASS.
- No R0/R1 execution, dataset download, training, or provider provisioning is part of the V3 reconciliation.
