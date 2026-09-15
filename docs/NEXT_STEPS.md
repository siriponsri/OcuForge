# Remaining acceptance work

1. Restore GitHub integration write access for siriponsri/OcuForge, then push the reviewed code with the user's existing authorization; never force push over new remote work.
2. Follow deploy/onprem/README.md on a hospital test host with synthetic fixtures. Verify Mongo authentication/volumes, CVAT share mapping and task lifecycle, firewall/TLS/egress, and full backup/restore.
3. Have the clinical owner approve protocol version and review SOP, then conduct an authorized local pilot. Keep hospital images, labels, derived features and weights on-premises.
4. Verify eligible public model/dataset sources and licenses, build the GPU image, test actual DINO and CUDA on the target host. Only public/synthetic jobs may run on Vast/RunPod; no automatic provisioning.
5. Measure clinical/research metrics, clinician workflow and data quality under a separate study before any clinical use. Synthetic smoke results do not establish clinical performance.
