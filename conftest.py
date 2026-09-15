import socket
from pathlib import Path
import pytest
from eyes_contracts.models import ImageManifest

ROOT = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise RuntimeError("Network forbidden in offline tests")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


@pytest.fixture
def image():
    return ImageManifest(
        image_id="SYNTH_001",
        dataset_id="synthetic_v1",
        relative_uri="images/SYNTH_001.png",
        file_sha256="a" * 64,
        width_px=80,
        height_px=48,
        split="TRAIN",
        source_type="SYNTHETIC",
    )


@pytest.fixture
def protocol():
    from eyes_contracts.protocol import load_protocol

    return load_protocol(ROOT / "eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json")[1]


@pytest.fixture
def prediction(image):
    from eyes_contracts.models import Prediction

    return Prediction(
        prediction_id="PRED_001",
        image_id=image.image_id,
        model_manifest_id="TINY_TEST",
        objects=[
            {
                "object_id": "POINT_001",
                "label": "microaneurysm",
                "geometry": {"type": "point", "coordinates_norm": [0.4, 0.6]},
                "confidence": 0.5,
                "generator_kind": "SYNTHETIC_FIXTURE",
            }
        ],
    )
