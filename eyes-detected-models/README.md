# Track A · Model research

Deterministic patches, cached features, attention pooling and ordinal grading. CPU smoke uses TinyTestEncoder only.

Research-only · contract version v0.1 · no weights, hospital data or credentials.

Run from the **parent workspace root**, after [installation](../docs/START_HERE_TH.md):

```bash
python -m eyes_detected.cli smoke-train --protocol eyes-detected-contracts/protocols/ico_2017_dr.v0.1.json --out artifacts/smoke
python -m pytest
```

Configuration and examples live in this package; model code depends on the shared contracts package and never on the
labeler implementation. See the [V3 system architecture](../docs/diagrams/ocuforge-system-architecture.svg).

See [implementation status](../docs/IMPLEMENTATION_STATUS.md), [safety](../docs/SAFETY_AND_SCOPE.md) and [Thai quickstart](QUICKSTART_TH.md).

Docker validation from workspace root:

```bash
docker compose -f eyes-detected-models/compose.yaml config --quiet
docker compose -f eyes-detected-labeler/compose.yaml config --quiet
```
