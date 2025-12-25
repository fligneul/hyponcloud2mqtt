# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Copy files required to install dependencies
COPY pyproject.toml .

# Copy source code
COPY src/ src/

# Install the package and its dependencies into a target directory
RUN pip install --prefix=/install .


# Stage 2: Runtime
FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the installed application from the builder stage
COPY --from=builder /install /usr/local
COPY docker/healthcheck.py .

# The healthcheck needs to be executable
RUN chmod +x healthcheck.py

# Create a non-root user and switch to it
RUN useradd --create-home appuser
USER appuser

# Set the PYTHONPATH to include the site-packages directory
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python3 healthcheck.py

CMD ["hyponcloud2mqtt"]
