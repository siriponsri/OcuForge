FROM python:3.12.10-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace
COPY eyes-detected-contracts /workspace/eyes-detected-contracts
COPY eyes-detected-models /workspace/eyes-detected-models
COPY eyes-detected-labeler /workspace/eyes-detected-labeler
COPY requirements-dev.txt pyproject.toml conftest.py /workspace/
COPY scripts /workspace/scripts
COPY tests /workspace/tests
FROM base AS cpu-test
RUN python -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu && python -m pip install ./eyes-detected-contracts ./eyes-detected-models ./eyes-detected-labeler -r requirements-dev.txt
ENV EYES_DOCKER_IMAGE=ocuforge-cpu-test:0.1.0
CMD ["python", "scripts/synthetic_roundtrip.py"]
FROM cpu-test AS dev
CMD ["bash"]
FROM base AS gpu-research
RUN python -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124 && python -m pip install ./eyes-detected-contracts ./eyes-detected-models ./eyes-detected-labeler
ENV EYES_DOCKER_IMAGE=ocuforge-gpu-research:0.1.0
CMD ["python", "-m", "eyes_detected.cli", "--help"]
