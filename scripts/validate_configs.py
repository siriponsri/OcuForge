import json, tomllib
from pathlib import Path
import yaml
from eyes_contracts.models import DatasetManifest
from eyes_contracts.protocol import load_protocol
from eyes_detected.tiling.grid import PatchConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    count = 0
    for p in ROOT.rglob("*.toml"):
        if "artifacts" not in p.parts:
            tomllib.loads(p.read_text())
            count += 1
    for p in (ROOT / "eyes-detected-models/configs/datasets").glob("*.yaml"):
        DatasetManifest.model_validate(yaml.safe_load(p.read_text()))
        count += 1
    model = yaml.safe_load((ROOT / "eyes-detected-models/configs/models/attention_coral.yaml").read_text())
    PatchConfig(**model["patch"])
    load_protocol(ROOT / "eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json")
    for p in list(ROOT.glob("eyes-detected-*/compose.yaml")) + list(ROOT.glob("deploy/*/compose.yaml")):
        c = yaml.safe_load(p.read_text())
        assert c["services"]
        for service in c["services"].values():
            if "build" not in service:
                continue
            build = service["build"]
            assert (p.parent / build["context"] / build["dockerfile"]).is_file()
        count += 1
    for p in ROOT.glob("eyes-detected-models/configs/pipeline/extract-*.json"):
        cfg = json.loads(p.read_text())
        PatchConfig(**cfg["patch"])
        count += 1
    for p in ROOT.glob("eyes-detected-labeler/configs/projects/*.json"):
        data = json.loads(p.read_text())
        assert data["labels"]
        assert len({x["name"] for x in data["labels"]}) == len(data["labels"])
        count += 1
    print(f"PASS: {count} configuration files; Docker syntax parsing is separate from live Docker validation")


if __name__ == "__main__":
    main()
