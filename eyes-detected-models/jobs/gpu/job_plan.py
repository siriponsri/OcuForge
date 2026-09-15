"""Provider-neutral, dry-run Docker argv only. No provisioning or upload API."""

import argparse, json
from eyes_contracts.validators import read_records
from eyes_contracts.models import ImageManifest


def plan(provider, images, image_tag):
    if provider not in ["vast", "runpod", "onprem"]:
        raise ValueError("Unknown provider")
    if not images or not all(isinstance(x, ImageManifest) for x in images):
        raise ValueError("Image manifests required")
    if provider != "onprem" and any(not i.cloud_eligible or i.source_type == "LOCAL_PRIVATE" for i in images):
        raise ValueError("Private or ineligible data cannot enter cloud plan")
    # Starter jobs only run synthetic smoke; no data mounts or transfers are generated.
    if any(i.source_type != "SYNTHETIC" for i in images):
        raise ValueError(
            "Starter GPU adapter accepts synthetic fixtures only; real data job requires later implementation"
        )
    if not image_tag or image_tag.startswith("-"):
        raise ValueError("Invalid Docker image")
    return {
        "provider": provider,
        "status": "SCAFFOLDED_DRY_RUN",
        "provisioning": False,
        "upload": False,
        "argv": [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--gpus",
            "all",
            image_tag,
            "python",
            "-m",
            "eyes_detected.cli",
            "smoke-train",
            "--out",
            "/tmp/synthetic",
            "--protocol",
            "/workspace/eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json",
        ],
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=["vast", "runpod", "onprem"], required=True)
    p.add_argument("--images", required=True)
    p.add_argument("--image", default="ocuforge-gpu-research:0.1.0")
    a = p.parse_args()
    print(json.dumps(plan(a.provider, read_records(a.images), a.image), indent=2))
