import importlib
import io
import json
import socket
import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.encaps import encapsulate
from pydicom.filewriter import dcmwrite
from pydicom.uid import (
    ExplicitVRBigEndian,
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
    JPEGBaseline8Bit,
    SecondaryCaptureImageStorage,
)

ORIGINAL_SOCKET_CONNECT = socket.socket.connect


def load_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OCUFORGE_PRODUCT_DATA_ROOT", str(tmp_path / "runtime-data"))

    def local_only_connect(sock, address):
        host = address[0] if isinstance(address, tuple) else ""
        if host in {"127.0.0.1", "::1"}:
            return ORIGINAL_SOCKET_CONNECT(sock, address)
        raise RuntimeError("External network forbidden in backend tests")

    monkeypatch.setattr(socket.socket, "connect", local_only_connect)
    sys.modules.pop("product-runtime.app", None)
    module = importlib.import_module("product-runtime.app")
    return module, TestClient(module.app)


def dicom_bytes(module, transfer_syntax: str, *, patient_name: str | None = None) -> bytes:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = "1.2.826.0.1.3680043.10.543.2003"
    file_meta.TransferSyntaxUID = transfer_syntax
    file_meta.ImplementationClassUID = module.PYDICOM_IMPLEMENTATION_UID
    dataset = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = "1.2.826.0.1.3680043.10.543.2001"
    dataset.SeriesInstanceUID = "1.2.826.0.1.3680043.10.543.2002"
    dataset.Modality = "OP"
    dataset.ImageLaterality = "OD"
    dataset.Rows = 2
    dataset.Columns = 2
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.NumberOfFrames = 1
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    dataset.PixelSpacing = ["0.01", "0.01"]
    if patient_name:
        dataset.PatientName = patient_name
        dataset.PatientID = "PRIVATE-123"
    endian = ">" if transfer_syntax == str(ExplicitVRBigEndian) else "<"
    dataset.PixelData = np.asarray([0, 1, 2, 3], dtype=f"{endian}u2").tobytes()
    buffer = io.BytesIO()
    if transfer_syntax == str(ExplicitVRBigEndian):
        dcmwrite(buffer, dataset, force_encoding=True, little_endian=False, implicit_vr=False)
    else:
        dcmwrite(
            buffer,
            dataset,
            enforce_file_format=True,
            little_endian=True,
            implicit_vr=transfer_syntax == str(ImplicitVRLittleEndian),
        )
    return buffer.getvalue()


def compressed_dicom_bytes(module) -> bytes:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = "1.2.826.0.1.3680043.10.543.3003"
    file_meta.TransferSyntaxUID = JPEGBaseline8Bit
    file_meta.ImplementationClassUID = module.PYDICOM_IMPLEMENTATION_UID
    dataset = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = "1.2.826.0.1.3680043.10.543.3001"
    dataset.SeriesInstanceUID = "1.2.826.0.1.3680043.10.543.3002"
    dataset.Modality = "OP"
    dataset.Rows = 2
    dataset.Columns = 2
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.PixelData = encapsulate([b"not-a-jpeg-frame"])
    buffer = io.BytesIO()
    dcmwrite(buffer, dataset, enforce_file_format=True)
    return buffer.getvalue()


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    module, client = load_runtime(tmp_path, monkeypatch)
    yield module, client, tmp_path
    client.close()


def test_fixture_ingestion_persists_lineage_jobs_and_quarantine(runtime):
    module, client, _ = runtime

    response = client.post("/api/fixtures/ingest", json={})
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "COMPLETED_WITH_ERRORS"
    assert result["counts"] == {
        "discovered": 3,
        "dicom_discovered": 2,
        "raster_discovered": 1,
        "accepted": 2,
        "accepted_cases": 3,
        "duplicates": 0,
        "unsupported": 0,
        "malformed": 1,
        "quarantined": 1,
        "failed": 0,
        "persisted": 4,
    }

    cases = client.get("/api/queue").json()
    frames = [case for case in cases if case["fileType"] == "DICOM" and case["qcStatus"] == "PASS"]
    assert [case["frame_number"] for case in frames] == [1, 2]
    assert len({case["id"] for case in frames}) == 2
    assert len({case["imageId"] for case in frames}) == 2
    assert all(case["sourceSha256"] == frames[0]["sourceSha256"] for case in frames)
    assert all(case["sourceReference"].endswith(f"#frame={case['frame_number']}") for case in frames)
    assert all("PatientName" not in json.dumps(case) for case in cases)
    assert all("PatientID" not in json.dumps(case) for case in cases)

    source_path = module.runtime.store.object_path(frames[0]["sourceObjectKey"])
    assert source_path.read_bytes()
    assert module.sha256_bytes(source_path.read_bytes()) == frames[0]["sourceSha256"]
    derivative_key = frames[0]["displayDerivativeUri"].removeprefix("/api/objects/")
    assert module.runtime.store.object_path(derivative_key).exists()

    job = client.get(f"/api/ingestion/{result['id']}")
    assert job.status_code == 200
    outcomes = {item["outcome"] for item in job.json()["items"]}
    assert outcomes == {"ACCEPTED", "MALFORMED"}

    repeated = client.post("/api/fixtures/ingest", json={}).json()
    assert repeated["counts"]["duplicates"] == 3
    assert repeated["counts"]["accepted"] == 0


def test_verified_transfer_syntaxes_are_exercised_and_compressed_is_not_claimed(runtime):
    module, client, tmp_path = runtime
    source = tmp_path / "transfer-syntaxes"
    source.mkdir()
    syntaxes = [str(ImplicitVRLittleEndian), str(ExplicitVRLittleEndian), str(ExplicitVRBigEndian)]
    for index, transfer_syntax in enumerate(syntaxes, start=1):
        patient_name = "Sensitive^Patient" if index == 1 else None
        (source / f"syntax-{index}.dcm").write_bytes(dicom_bytes(module, transfer_syntax, patient_name=patient_name))

    result = client.post("/api/ingestion", json={"source_reference": str(source)}).json()
    assert result["counts"]["accepted"] == 3
    assert {case["transfer_syntax_uid"] for case in result["cases"]} == set(syntaxes)

    health = client.get("/api/health").json()["dicom"]
    assert {item["uid"] for item in health["tested"]} == set(syntaxes)
    assert health["compressed_support"]["claimed"] is False
    assert not any(item["uid"].startswith("1.2.840.10008.1.2.4.") for item in health["tested"])
    assert "Sensitive^Patient" not in json.dumps(result["cases"])

    compressed = source / "compressed.dcm"
    compressed.write_bytes(compressed_dicom_bytes(module))
    quarantined = client.post("/api/ingestion", json={"source_reference": str(compressed)}).json()
    assert quarantined["counts"]["unsupported"] == 1
    assert quarantined["cases"][0]["quarantineCategory"] == "UNSUPPORTED"
    assert "1.2.840.10008.1.2.4.50" in quarantined["cases"][0]["quarantineReason"]


def test_readiness_and_object_store_are_local_and_immutable(runtime):
    module, client, tmp_path = runtime
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    readiness = client.post(
        "/api/readiness",
        json={"source_reference": str(source), "destination_reference": str(destination)},
    )
    assert readiness.status_code == 200
    assert readiness.json()["source"]["ready"] is True
    assert readiness.json()["destination"]["ready"] is True

    key = module.runtime.store.put_object("objects/test.bin", b"immutable")
    assert module.runtime.store.put_object(key, b"immutable") == key
    with pytest.raises(ValueError, match="Immutable object conflict"):
        module.runtime.store.put_object(key, b"changed")
    with pytest.raises(ValueError, match="Unsafe object key"):
        module.runtime.store.put_object("../escape.bin", b"bad")


def test_api_persists_configurable_root_and_queue_state(runtime):
    module, client, tmp_path = runtime
    health = client.get("/api/health").json()
    assert Path(health["data_root"]) == (tmp_path / "runtime-data").resolve()
    client.post("/api/fixtures/ingest", json={})
    case = next(item for item in client.get("/api/queue").json() if item["qcStatus"] == "PASS")
    updated = client.post(f"/api/cases/{case['id']}/ai")
    assert updated.status_code == 200
    assert updated.json()["derived_queue_status"] == "AI_PROCESSED"
    assert client.get("/api/queue", params={"status": "AI_PROCESSED"}).json()[0]["id"] == case["id"]
