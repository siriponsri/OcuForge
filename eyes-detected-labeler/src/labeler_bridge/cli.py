import argparse, json
from pathlib import Path
from eyes_contracts.models import POLICY
from eyes_contracts.validators import read_records, write_records, validate_batch
from labeler_bridge.import_predictions.bridge import import_prediction
from labeler_bridge.export_annotations.bridge import export_annotations, session_summary
from labeler_bridge.provenance.lifecycle import transition
from labeler_bridge.cvat_client.client import CVATClient


def main():
    p = argparse.ArgumentParser(description="CVAT bridge; shared contracts v0.1; synthetic offline demo")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-schema")
    sub.add_parser("health")
    q = sub.add_parser("bootstrap-project")
    q.add_argument("spec")
    q = sub.add_parser("import-batch")
    q.add_argument("batch")
    q.add_argument("images")
    q = sub.add_parser("import-demo-predictions")
    q.add_argument("--smoke-dir", required=True)
    q.add_argument("--out", required=True)
    q = sub.add_parser("import-payload")
    q.add_argument("task_id", type=int)
    q.add_argument("payload")
    q = sub.add_parser("fetch-annotations")
    q.add_argument("task_id", type=int)
    q.add_argument("--out", required=True)
    a = p.parse_args()
    try:
        if a.command == "validate-schema":
            print(json.dumps(POLICY, indent=2))
        elif a.command == "health":
            print(json.dumps(CVATClient().health()))
        elif a.command == "bootstrap-project":
            print(
                json.dumps(
                    CVATClient().create_project(json.loads(Path(a.spec).read_text(encoding="utf-8")))
                )
            )
        elif a.command == "import-batch":
            batch = validate_batch(read_records(a.batch)[0], read_records(a.images))
            print(f"VALID batch {batch.batch_id}: {batch.requested_n}")
        elif a.command == "import-payload":
            print(
                json.dumps(
                    CVATClient().import_annotations(
                        a.task_id, json.loads(Path(a.payload).read_text(encoding="utf-8"))
                    )
                )
            )
        elif a.command == "fetch-annotations":
            Path(a.out).write_text(
                json.dumps(CVATClient().get_annotations(a.task_id), indent=2), encoding="utf-8"
            )
        elif a.command == "import-demo-predictions":
            root = Path(a.smoke_dir)
            out = Path(a.out)
            out.mkdir(parents=True, exist_ok=True)
            im = read_records(root / "images.jsonl")[0]
            pred = read_records(root / "predictions.jsonl")[0]
            payload, sidecar = import_prediction(pred, im)
            (out / "cvat_import.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
            (out / "provenance_sidecar.json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
            aid = next(iter(sidecar))
            payload["shapes"][0]["points"][0] += 1
            annotations = export_annotations(
                payload,
                sidecar,
                {0: im},
                {1: "microaneurysm"},
                {1: "ed_annotation_id"},
                "SYNTHETIC_REVIEWER",
                {aid: "CORRECT"},
            )
            corrected = annotations[0]
            adjudicated = transition(corrected, "ADJUDICATE", "SYNTHETIC_EXPERT")
            locked = transition(adjudicated, "LOCK", "SYNTHETIC_EXPERT")
            write_records(out / "annotations.jsonl", [locked])
            (out / "session_summary.json").write_text(
                json.dumps(session_summary([locked], 60, synthetic_demo=True), indent=2), encoding="utf-8"
            )
            print("Synthetic correction + adjudication + lock exported; no live CVAT called")
    except (ValueError, RuntimeError, OSError, KeyError) as e:
        p.exit(2, f"{e}\n")


if __name__ == "__main__":
    main()
