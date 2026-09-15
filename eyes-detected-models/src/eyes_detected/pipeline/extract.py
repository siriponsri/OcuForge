import json, os, subprocess
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict
import torch
from PIL import Image
from eyes_detected.pipeline.data import load_images, safe_path, sha256
from eyes_detected.tiling.grid import PatchConfig, tile, normalize
from eyes_detected.features.store import NPZFeatureStore, digest


def configured_value(config, key):
    env_key = config.get(f"{key}_env")
    if env_key:
        value = os.environ.get(env_key)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {env_key}")
        return value
    if key not in config:
        raise ValueError(f"Missing encoder configuration: {key}")
    return config[key]


def configured_bool(config, key):
    value = configured_value(config, key)
    if isinstance(value, bool):
        return value
    if str(value).lower() in ["1", "true", "yes"]:
        return True
    if str(value).lower() in ["0", "false", "no"]:
        return False
    raise ValueError(f"Boolean configuration required: {key}")


def state_hash(model):
    import hashlib

    h = hashlib.sha256()
    for key, value in model.state_dict().items():
        h.update(key.encode())
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def extract(manifest, data_root, out, config_path, dataset_path=None, cloud=False):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    images, dataset = load_images(manifest, dataset_path, cloud)
    device = config.get("device", "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable; no silent CPU fallback")
    kind = config["encoder"]
    torch.manual_seed(config.get("seed", 42))
    torch.set_num_threads(config.get("cpu_threads", 1))
    if kind == "tiny-test":
        if any(i.source_type != "SYNTHETIC" for i in images):
            raise ValueError("TinyTestEncoder accepts SYNTHETIC only")
        from eyes_detected.encoders.tiny_test_encoder import TinyTestEncoder

        encoder = TinyTestEncoder(config.get("dim", 16))
        weight_hash = state_hash(encoder)
    elif kind == "dinov3_vitb16":
        from eyes_detected.encoders.dinov3_adapter import DINOv3Adapter

        encoder = DINOv3Adapter(
            configured_value(config, "repo_path"),
            configured_value(config, "weights_path"),
            configured_value(config, "weights_sha256"),
            configured_bool(config, "license_reviewed"),
        )
        weight_hash = encoder.weight_hash
    else:
        raise ValueError("Unknown encoder; no fallback")
    encoder = encoder.to(device).eval().requires_grad_(False)
    docker_image = (
        configured_value(config, "docker_image")
        if "docker_image_env" in config or "docker_image" in config
        else "UNSPECIFIED"
    )
    patch_cfg = PatchConfig(**config.get("patch", {}))
    batch_size = config.get("patch_batch_size", 8)
    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("patch_batch_size must be positive")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    store = NPZFeatureStore(out / "shards")
    rows = []
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        git_sha = "UNCOMMITTED"
    for im in images:
        path = safe_path(data_root, im.relative_uri)
        if sha256(path) != im.file_sha256:
            raise ValueError("Image hash mismatch")
        with Image.open(path) as img:
            if img.size != (im.width_px, im.height_px) or img.mode != "RGB":
                raise ValueError("Image dimensions/RGB mismatch")
            patches, geometry = tile(img, patch_cfg)
        tensor = torch.from_numpy(normalize(patches, patch_cfg))
        chunks = []
        with torch.inference_mode():
            for start in range(0, len(tensor), batch_size):
                chunks.append(encoder(tensor[start : start + batch_size].to(device)).cpu())
        features = torch.cat(chunks).numpy()
        if features.ndim != 2 or len(features) != patch_cfg.grid**2:
            raise ValueError("Encoder output must be [patches,features]")
        meta = {
            "dataset_id": im.dataset_id,
            "image_id": im.image_id,
            "image_sha256": im.file_sha256,
            "encoder_id": encoder.encoder_id,
            "encoder_weight_hash": weight_hash,
            "preprocessing_config_hash": digest(asdict(patch_cfg)),
            "patch_geometry": geometry,
            "tensor_shape": list(features.shape),
            "feature_dtype": str(features.dtype),
            "extraction_time": datetime.now(timezone.utc).isoformat(),
            "git_sha": git_sha,
            "docker_image": docker_image,
        }
        key = store.put(features, meta)
        rows.append({"image_id": im.image_id, "key": key, "metadata": meta})
        # Progress checkpoint contains metadata only, enabling diagnosis of interrupted extraction.
        tmp = out / "index.partial.json"
        tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (out / "index.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (out / "index.partial.json").unlink(missing_ok=True)
    (out / "extraction_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return {
        "images": len(rows),
        "encoder": encoder.encoder_id,
        "weight_hash": weight_hash,
        "index": str(out / "index.json"),
    }
