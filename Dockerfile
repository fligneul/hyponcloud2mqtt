FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY docker/healthcheck.py .

RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

RUN pip install .

# Create a non-root user and switch to it
RUN useradd --create-home appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 healthcheck.py

CMD ["hyponcloud2mqtt"]
