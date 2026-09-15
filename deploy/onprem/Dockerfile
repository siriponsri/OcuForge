FROM python:3.12.11-slim
WORKDIR /app
COPY eyes-detected-contracts /app/eyes-detected-contracts
COPY eyes-detected-labeler /app/eyes-detected-labeler
COPY deploy/onprem /app/deploy/onprem
RUN pip install --no-cache-dir /app/eyes-detected-contracts /app/eyes-detected-labeler
RUN useradd --uid 10001 --create-home ocuforge
USER 10001:10001
CMD ["eyes-local", "health"]
