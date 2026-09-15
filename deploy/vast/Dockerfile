FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime
WORKDIR /app
ENV HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 WANDB_MODE=disabled
COPY eyes-detected-contracts /app/eyes-detected-contracts
COPY eyes-detected-models /app/eyes-detected-models
RUN pip install --no-cache-dir /app/eyes-detected-contracts /app/eyes-detected-models
RUN useradd --uid 10001 --create-home ocuforge
USER 10001:10001
ENTRYPOINT ["eyes-pipeline"]
