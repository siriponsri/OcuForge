.PHONY: test smoke docker-build
test:
	cd .. && python -m pytest
smoke:
	cd .. && python scripts/synthetic_roundtrip.py
docker-build:
	cd .. && docker compose -f eyes-detected-models/compose.yaml build cpu-test
