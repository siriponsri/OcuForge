import ast, json, subprocess, sys
from pathlib import Path
import pytest
from eyes_detected.smoke import smoke_train
from eyes_contracts.validators import read_records
from eyes_contracts.models import TYPES

ROOT = Path(__file__).resolve().parents[1]


def test_track_separation():
    for folder, forbidden in [
        ("eyes-detected-models", {"labeler_bridge"}),
        ("eyes-detected-labeler", {"eyes_detected"}),
        ("eyes-detected-contracts", {"eyes_detected", "labeler_bridge", "torch"}),
    ]:
        for p in (ROOT / folder / "src").rglob("*.py"):
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    assert not {x.name.split(".")[0] for x in node.names} & forbidden
                if isinstance(node, ast.ImportFrom):
                    assert (node.module or "").split(".")[0] not in forbidden


@pytest.mark.parametrize("module", ["eyes_contracts.cli", "eyes_detected.cli", "labeler_bridge.cli"])
def test_cli_help(module):
    assert subprocess.run([sys.executable, "-m", module, "--help"], capture_output=True).returncode == 0


def test_cpu_smoke(tmp_path):
    summary = smoke_train(tmp_path, ROOT / "eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json", steps=2)
    assert summary["weights_updated"] and not summary["scientific_result_eligible"]
    assert len(read_records(tmp_path / "predictions.jsonl")) == 10
    for name in ["model_manifest.json", "experiment_run.json", "annotation_batch.json"]:
        assert read_records(tmp_path / name)


def test_schema_drift():
    for version, cls in TYPES.items():
        schema = json.loads(
            (ROOT / "eyes-detected-contracts/schemas" / f"{version}.schema.json").read_text(encoding="utf-8")
        )
        assert schema == cls.model_json_schema()


def test_gpu_plan_blocks_private(image):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "gpu_plan", ROOT / "eyes-detected-models/jobs/gpu/job_plan.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    private = image.model_copy(update={"source_type": "LOCAL_PRIVATE", "cloud_eligible": False})
    with pytest.raises(ValueError):
        module.plan("vast", [private], "test-image")
    result = module.plan("runpod", [image.model_copy(update={"cloud_eligible": True})], "test-image")
    assert not result["upload"] and not result["provisioning"]


def test_gitignore_keeps_data_source_module(tmp_path):
    import shutil

    if shutil.which("git") is None:
        pytest.skip("Git is optional for installed-package validation")
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    shutil.copyfile(ROOT / ".gitignore", tmp_path / ".gitignore")
    source = "eyes-detected-models/src/eyes_detected/data/registry.py"
    result = subprocess.run(["git", "check-ignore", "--no-index", source], cwd=tmp_path, capture_output=True)
    assert result.returncode == 1
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "data/patient.png"], cwd=tmp_path, capture_output=True
    )
    assert result.returncode == 0
