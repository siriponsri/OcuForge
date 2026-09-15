from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    for args in [
        [
            "-m",
            "eyes_detected.cli",
            "smoke-train",
            "--protocol",
            str(ROOT / "eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json"),
            "--out",
            str(ROOT / "artifacts/smoke"),
        ],
        [
            "-m",
            "labeler_bridge.cli",
            "import-demo-predictions",
            "--smoke-dir",
            str(ROOT / "artifacts/smoke"),
            "--out",
            str(ROOT / "artifacts/roundtrip"),
        ],
        ["-m", "eyes_contracts.cli", "validate", str(ROOT / "artifacts/roundtrip/annotations.jsonl")],
        [
            "-m",
            "eyes_detected.cli",
            "training-ingest",
            str(ROOT / "artifacts/roundtrip/annotations.jsonl"),
            str(ROOT / "artifacts/smoke/images.jsonl"),
        ],
        [
            "-m",
            "labeler_bridge.cli",
            "import-batch",
            str(ROOT / "artifacts/smoke/annotation_batch.json"),
            str(ROOT / "artifacts/smoke/images.jsonl"),
        ],
    ]:
        subprocess.run([sys.executable, *args], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
