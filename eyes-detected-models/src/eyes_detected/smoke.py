"""Real CPU forward/backward on explicitly synthetic RGB images; no accuracy claim."""

import hashlib, json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from eyes_contracts.models import ImageManifest, Prediction, ModelManifest, ExperimentRun
from eyes_contracts.protocol import load_protocol
from eyes_contracts.validators import write_records
from eyes_detected.tiling.grid import PatchConfig, tile, normalize
from eyes_detected.encoders.tiny_test_encoder import TinyTestEncoder
from eyes_detected.mil.attention import AttentionMIL
from eyes_detected.ordinal.coral import loss, predict, class_probabilities
from eyes_detected.features.store import NPZFeatureStore, digest
from eyes_detected.active_learning.select import select_batch
from eyes_detected.ood.prototype import PrototypeOOD


def smoke_train(out, protocol_path, seed=42, steps=5):
    if not 1 <= steps <= 100:
        raise ValueError("Smoke steps must be 1..100; no full training")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "images").mkdir(exist_ok=True)
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    config = PatchConfig(canvas=64, grid=5, patch=16)
    _, protocol = load_protocol(protocol_path)
    images = []
    arrays = []
    geometry = []
    for i in range(10):
        rgb = rng.integers(0, 256, (48, 80, 3), dtype=np.uint8)
        path = out / "images" / f"SYNTH_{i:03}.png"
        Image.fromarray(rgb).save(path)
        images.append(
            ImageManifest(
                image_id=f"SYNTH_{i:03}",
                dataset_id="synthetic_v1",
                file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                relative_uri=f"images/{path.name}",
                patient_pseudo_id=f"SYNTH_P_{i}",
                eye_id=f"SYNTH_E_{i}",
                visit_id=f"SYNTH_V_{i}",
                width_px=80,
                height_px=48,
                split="TRAIN",
                source_type="SYNTHETIC",
                cloud_eligible=True,
            )
        )
        patches, meta = tile(rgb, config)
        arrays.append(normalize(patches, config))
        geometry.append(meta)
    x = torch.from_numpy(np.stack(arrays))
    encoder = TinyTestEncoder()
    mil = AttentionMIL()
    optimizer = torch.optim.Adam(list(encoder.parameters()) + list(mil.parameters()), lr=0.01)
    grades = torch.arange(10) % 5
    lesions = torch.randint(0, 2, (10, 7)).float()
    qc = torch.randint(0, 2, (10,)).float()
    losses = []
    initial = [p.detach().clone() for p in mil.parameters()]
    for _ in range(steps):
        optimizer.zero_grad()
        features = encoder(x.flatten(0, 1)).reshape(10, 25, -1)
        result = mil(features)
        total = (
            loss(result["dr_logits"], grades)
            + 0.2 * F.binary_cross_entropy_with_logits(result["lesion_logits"], lesions)
            + 0.1 * F.binary_cross_entropy_with_logits(result["qc_logits"], qc)
        )
        if not torch.isfinite(total):
            raise RuntimeError("Non-finite training loss")
        total.backward()
        optimizer.step()
        losses.append(float(total.detach()))
    if not any(not torch.equal(a, b) for a, b in zip(initial, mil.parameters())):
        raise RuntimeError("Weights did not update")
    with torch.no_grad():
        features = encoder(x.flatten(0, 1)).reshape(10, 25, -1)
        result = mil(features)
        g, prob = predict(result["dr_logits"])
        cp = class_probabilities(prob)
        confidence = cp.gather(1, g[:, None]).squeeze(1)
    h = hashlib.sha256()
    for name, model in [("encoder", encoder), ("mil", mil)]:
        for key, value in model.state_dict().items():
            h.update((name + key).encode())
            h.update(value.numpy().tobytes())
    weight_hash = h.hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        git_sha = "UNCOMMITTED_STARTER"
    model = ModelManifest(
        model_manifest_id="TINY_TEST_001",
        name="Synthetic Attention MIL CORAL",
        version="0.1.0",
        architecture="TinyTestEncoder + AttentionMIL + CORAL + 7 lesion + QC heads",
        encoder=encoder.encoder_id,
        weight_hash=weight_hash,
        training_run_id="SYNTHETIC_CPU_001",
        training_dataset_ids=["synthetic_v1"],
        known_limitations=[
            "Random synthetic labels; no clinical validity",
            "No trained lesion localizer",
            "No DINOv3 inference",
        ],
        intended_research_use="Offline engineering smoke only",
        calibration_version=None,
        ood_method="prototype_distance_uncalibrated",
        created_at=now,
    )
    ood = PrototypeOOD(result["embedding"][:2].numpy(), threshold=1.0).score(result["embedding"].numpy())
    preds = []
    names = [
        "microaneurysm",
        "hard_exudate",
        "intraretinal_hemorrhage",
        "vb_irma",
        "nv",
        "vitreous_hemorrhage",
        "retinal_detachment",
    ]
    for i, im in enumerate(images):
        # Fixture geometry is explicitly independent of model outputs, never fake localization.
        preds.append(
            Prediction(
                prediction_id=f"PRED_SYNTH_{i:03}",
                image_id=im.image_id,
                model_manifest_id=model.model_manifest_id,
                dr={
                    "grade": int(g[i]),
                    "ordinal_probs": prob[i].tolist(),
                    "confidence": float(confidence[i]),
                    "grading_protocol": protocol,
                },
                lesion_presence=dict(zip(names, result["lesion_logits"][i].sigmoid().tolist())),
                gradability_probability=float(result["qc_logits"][i].sigmoid()),
                objects=[
                    {
                        "object_id": "TEST_POINT",
                        "label": "microaneurysm",
                        "geometry": {"type": "point", "coordinates_norm": [0.4, 0.6]},
                        "confidence": 0.5,
                        "generator_kind": "SYNTHETIC_FIXTURE",
                    }
                ],
                evidence={"patch_scores": result["attention"][i].tolist()},
                ood=ood[i],
            )
        )
    store = NPZFeatureStore(out / "features")
    keys = []
    for i, im in enumerate(images):
        meta = {
            "dataset_id": im.dataset_id,
            "image_id": im.image_id,
            "encoder_id": encoder.encoder_id,
            "encoder_weight_hash": weight_hash,
            "preprocessing_config_hash": digest(asdict(config)),
            "patch_geometry": geometry[i],
            "tensor_shape": list(features[i].shape),
            "feature_dtype": "float32",
            "extraction_time": now,
            "git_sha": git_sha,
            "docker_image": os.environ.get("EYES_DOCKER_IMAGE", "NOT_CONTAINERIZED"),
        }
        key = store.put(features[i].numpy(), meta)
        store.get(key, meta)
        keys.append({"key": key, "metadata": meta})
    write_records(out / "images.jsonl", images)
    write_records(out / "predictions.jsonl", preds)
    write_records(out / "model_manifest.json", [model])
    batch = select_batch(images, result["embedding"].numpy(), 3)
    write_records(out / "annotation_batch.json", [batch])
    run = ExperimentRun(
        run_id="SYNTHETIC_CPU_001",
        timestamp=now,
        git_sha=git_sha,
        docker_image=os.environ.get("EYES_DOCKER_IMAGE", "NOT_CONTAINERIZED"),
        config_hash=digest(
            {
                "patch": asdict(config),
                "seed": seed,
                "steps": steps,
                "loss_weights": [1, 0.2, 0.1],
                "grading_protocol": protocol.model_dump(),
            }
        ),
        dataset_manifest_ids=["synthetic_v1"],
        model_manifest_parent=None,
        random_seed=seed,
        gpu_name="CPU",
        cuda_version=None,
        framework_version=torch.__version__,
        metrics_path="smoke_metrics.json",
        artifact_path=".",
        status="COMPLETED",
    )
    write_records(out / "experiment_run.json", [run])
    (out / "feature_index.json").write_text(json.dumps(keys, indent=2), encoding="utf-8")
    (out / "patch_geometry.json").write_text(json.dumps(geometry, indent=2), encoding="utf-8")
    summary = {
        "encoder": encoder.encoder_id,
        "steps": steps,
        "losses": losses,
        "weights_updated": True,
        "scientific_result_eligible": False,
        "images": len(images),
        "predictions": len(preds),
        "selected": batch.requested_n,
    }
    (out / "smoke_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
