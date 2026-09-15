import hashlib, json
from pathlib import Path
from typing import Protocol
import numpy as np

REQUIRED = {
    "dataset_id",
    "image_id",
    "encoder_id",
    "encoder_weight_hash",
    "preprocessing_config_hash",
    "patch_geometry",
    "tensor_shape",
    "feature_dtype",
    "extraction_time",
    "git_sha",
    "docker_image",
}


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


class FeatureStore(Protocol):
    def put(self, features, metadata): ...
    def get(self, key, expected_metadata): ...


class NPZFeatureStore:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, features, metadata):
        if REQUIRED - set(metadata):
            raise ValueError("Incomplete feature provenance")
        if (
            list(features.shape) != metadata["tensor_shape"]
            or str(features.dtype) != metadata["feature_dtype"]
            or not np.isfinite(features).all()
        ):
            raise ValueError("Feature metadata mismatch")
        key = digest(metadata)
        np.savez_compressed(
            self.root / (key + ".npz"), features=features, metadata=json.dumps(metadata, sort_keys=True)
        )
        return key

    def get(self, key, expected_metadata):
        if key != digest(expected_metadata):
            raise ValueError("Encoder/preprocessing metadata mismatch; recompute features")
        with np.load(self.root / (key + ".npz"), allow_pickle=False) as data:
            meta = json.loads(str(data["metadata"]))
            features = data["features"].copy()
        if (
            digest(meta) != digest(expected_metadata)
            or list(features.shape) != meta["tensor_shape"]
            or str(features.dtype) != meta["feature_dtype"]
            or not np.isfinite(features).all()
        ):
            raise ValueError("Feature store metadata corrupted")
        return features
