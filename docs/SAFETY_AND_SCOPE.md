# Safety and scope

Research-only engineering starter. AI predictions and candidate lesions are not confirmed diagnosis. No clinical accuracy, novelty, referral or time-saving claim is made.

- Every distributed fixture is synthetic. Raw hospital images, patient identifiers, credentials, weights and large artifacts are excluded.
- No automatic dataset download, cloud upload, provider provisioning or paid API call exists.
- Local private manifests reject cloud_eligible=true in this starter. GPU job planning accepts synthetic records only.
- GitHub is code/config source of truth. Google Drive is used only as project documentation context; no legacy dataset or checkpoint is copied. Hugging Face access is limited to public model/dataset metadata and license inspection.
- MMRDR lesion presence is not pixel ground truth. MIL attention remains separate evidence and cannot become lesion annotations.
- Local binary DR/no-DR assessment cannot be upgraded to ordinal or adjudicated labels.
- DME is separate from DR. No fundus-only OCT-confirmed DME field exists.
- CVAT token comes from an environment variable. Bridge uses local endpoint allowlist and rejects redirects; errors do not echo credentials.
- Adjudication records an additional event. Rejected/deleted candidates remain in the audit export. Locked labels require a versioned amendment.
- Sentinel data is evaluation-only. A label's review state does not override its split.

Automated scans detect common secret formats and forbidden binaries; they do not constitute enterprise DLP. The package is safe to distribute because its inputs are generated synthetic fixtures and reviewed text, not because regex can certify arbitrary hospital files.

Before actual clinician use: verify local CVAT deployment, account roles, TLS for network access, backups, task-to-image mapping, protocol adoption and data governance. These are next-stage integration work, not claimed as completed here.
