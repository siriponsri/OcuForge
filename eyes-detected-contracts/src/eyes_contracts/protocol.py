import json, hashlib
from pathlib import Path
from .models import ProtocolRef


def load_protocol(path):
    data = json.loads(Path(path).read_text())
    if sorted(x["value"] for x in data["grades"]) != list(range(5)):
        raise ValueError("Starter CORAL requires exactly grades 0..4; other scales require migration")
    if (
        data.get("ungradable_is_grade")
        or data.get("automatic_referral_enabled")
        or data.get("automatic_grade_from_lesions")
    ):
        raise ValueError("Unsupported automatic clinical rule")
    if not data.get("dme_separate_axis"):
        raise ValueError("DME must remain separate")
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ref = ProtocolRef(
        protocol_id=data["protocol_id"],
        version=data["version"],
        config_sha256=hashlib.sha256(canonical).hexdigest(),
    )
    return data, ref


def check_protocol(record, ref):
    current = record.grading_protocol if hasattr(record, "grading_protocol") else record.dr.grading_protocol
    if current != ref:
        raise ValueError("Protocol mismatch: retain historical labels; use explicit migration")
    return True
