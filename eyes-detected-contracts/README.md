# Shared contracts

Stable JSON/Pydantic interfaces for both tracks. Structural schemas plus semantic validators.

Research-only · contract version v0.1 · no weights, hospital data or credentials.

Run from the **parent workspace root**, after [installation](../docs/START_HERE_TH.md):

```bash
python -m eyes_contracts.cli validate eyes-detected-contracts/examples/image_manifest.json
python -m pytest
```

Configuration and examples live in this package. Models and labeler consume these contracts, while the two feature
packages remain independent. See the [V3 system architecture](../docs/diagrams/ocuforge-system-architecture.svg).

See [implementation status](../docs/IMPLEMENTATION_STATUS.md), [safety](../docs/SAFETY_AND_SCOPE.md) and [Thai quickstart](QUICKSTART_TH.md).

Docker validation from workspace root:

```bash
docker compose -f eyes-detected-models/compose.yaml config --quiet
docker compose -f eyes-detected-labeler/compose.yaml config --quiet
```
