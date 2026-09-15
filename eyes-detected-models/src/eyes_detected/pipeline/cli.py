import argparse, json
from eyes_detected.pipeline.data import audit
from eyes_detected.pipeline.extract import extract
from eyes_detected.pipeline.train import train
from eyes_detected.pipeline.evaluate import infer


def main():
    p = argparse.ArgumentParser(description="Local/offline feature → MIL training → held-out evaluation")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ["audit", "extract", "train", "evaluate", "predict"]:
        q = sub.add_parser(name)
        for arg in ["manifest", "out"]:
            q.add_argument("--" + arg, required=True)
        q.add_argument("--dataset")
        q.add_argument("--cloud", action="store_true")
        if name in ["audit", "extract"]:
            q.add_argument("--data-root", required=True)
        if name in ["extract", "train"]:
            q.add_argument("--config", required=True)
        if name in ["train", "evaluate", "predict"]:
            q.add_argument("--features", required=True)
        if name in ["train", "evaluate"]:
            q.add_argument("--targets", required=True)
        if name == "train":
            q.add_argument("--protocol", required=True)
            q.add_argument("--resume")
        if name in ["evaluate", "predict"]:
            q.add_argument("--checkpoint", required=True)
            q.add_argument("--split", default="TEST" if name == "evaluate" else "ALL")
    a = p.parse_args()
    try:
        common = {"dataset_path": a.dataset, "cloud": a.cloud}
        if a.command == "audit":
            r = audit(a.manifest, a.data_root, a.out, **common)
        elif a.command == "extract":
            r = extract(a.manifest, a.data_root, a.out, a.config, **common)
        elif a.command == "train":
            r = train(a.manifest, a.targets, a.features, a.out, a.config, a.protocol, a.resume, **common)
        else:
            r = infer(
                a.manifest,
                a.features,
                a.checkpoint,
                a.out,
                a.split,
                a.targets if a.command == "evaluate" else None,
                **common,
            )
        print(json.dumps(r, indent=2))
    except (ValueError, RuntimeError, OSError, KeyError):
        p.exit(
            2,
            "Pipeline failed. Inspect local inputs/configuration; no patient paths or credentials logged.\n",
        )


if __name__ == "__main__":
    main()
