import argparse, json
from pathlib import Path
from eyes_contracts.validators import read_records, write_records, training_annotations
from eyes_detected.data.registry import DatasetRegistry


def main():
    p = argparse.ArgumentParser(description="Eye Detected models research-only; shared contracts v0.1")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("validate-dataset")
    q.add_argument("path")
    q = sub.add_parser("smoke-train")
    q.add_argument("--out", default="artifacts/smoke")
    q.add_argument("--protocol", required=True)
    q.add_argument("--steps", type=int, default=5)
    q = sub.add_parser("patch-preview")
    q.add_argument("image")
    q.add_argument("--out", required=True)
    q = sub.add_parser("select-batch")
    q.add_argument("images")
    q.add_argument("features")
    q.add_argument("--n", type=int, required=True)
    q.add_argument("--out", required=True)
    q = sub.add_parser("training-ingest")
    q.add_argument("annotations")
    q.add_argument("images")
    q.add_argument("--allow-submitted", action="store_true")
    q = sub.add_parser("export-predictions")
    q.add_argument("input")
    q.add_argument("--out", required=True)
    a = p.parse_args()
    try:
        if a.command == "validate-dataset":
            print(DatasetRegistry().load(a.path).model_dump_json(indent=2))
        elif a.command == "smoke-train":
            from .smoke import smoke_train

            print(json.dumps(smoke_train(a.out, a.protocol, steps=a.steps), indent=2))
        elif a.command == "patch-preview":
            from PIL import Image
            from .tiling.grid import tile

            patches, meta = tile(Image.open(a.image))
            out = Path(a.out)
            out.mkdir(parents=True, exist_ok=True)
            for i, patch in enumerate(patches):
                Image.fromarray(patch).save(out / f"patch_{i:02}.png")
            (out / "coordinates.json").write_text(json.dumps(meta, indent=2))
            print("25 patches and coordinates written")
        elif a.command == "select-batch":
            import numpy as np
            from .active_learning.select import select_batch

            write_records(
                a.out, [select_batch(read_records(a.images), np.load(a.features, allow_pickle=False), a.n)]
            )
        elif a.command == "training-ingest":
            print(
                f"Eligible: {len(training_annotations(read_records(a.annotations), read_records(a.images), a.allow_submitted))}"
            )
        elif a.command == "export-predictions":
            from eyes_contracts.models import Prediction

            records = read_records(a.input)
            if not all(isinstance(x, Prediction) for x in records):
                raise ValueError("Expected prediction records")
            write_records(a.out, records)
    except (ValueError, RuntimeError, OSError) as e:
        p.exit(2, f"{e}\n")


if __name__ == "__main__":
    main()
