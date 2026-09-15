# Backup and export

Before editing a task, retain its CVAT backup, task/project IDs, label/attribute mappings, ordered frame/image mapping, prediction JSONL and provenance sidecar in approved local storage.

After each session, save native annotation JSONL, explicit decision journal, session time summary, schema version and protocol hash. Export CVAT task backup through its UI and preserve the native export independently of CVAT.

Rehearsal: export the synthetic task, restore it to a separate local task, rebuild server ID mappings, re-export annotations and compare stable annotation IDs, coordinates and full history. Restoring the CVAT task alone does not restore an external sidecar. This live restore rehearsal remains an external acceptance check; the starter tests native JSONL roundtrip only.

Never copy local image backups into the Git repository or public artifact storage.
