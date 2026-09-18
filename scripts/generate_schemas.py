import json
from pathlib import Path
from eyes_contracts.models import TYPES
from eyes_contracts.r3 import R3_TYPES
from eyes_contracts.triage import TRIAGE_TYPES

root = Path(__file__).resolve().parents[1] / "eyes-detected-contracts/schemas"
root.mkdir(exist_ok=True)
for version, model in {**TYPES, **TRIAGE_TYPES, **R3_TYPES}.items():
    (root / (version + ".schema.json")).write_text(
        json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8"
    )
