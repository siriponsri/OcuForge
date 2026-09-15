.PHONY: test smoke lint config docker-build
test:
	python -m pytest
smoke:
	python scripts/synthetic_roundtrip.py
lint:
	python -m ruff check .
config:
	python scripts/validate_configs.py
docker-build:
	docker compose -f eyes-detected-models/compose.yaml build cpu-test
