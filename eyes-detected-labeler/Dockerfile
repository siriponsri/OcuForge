FROM python:3.12.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
COPY eyes-detected-contracts /workspace/eyes-detected-contracts
COPY eyes-detected-labeler /workspace/eyes-detected-labeler
RUN python -m pip install ./eyes-detected-contracts ./eyes-detected-labeler
CMD ["python", "-m", "labeler_bridge.cli", "validate-schema"]
