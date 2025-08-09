# ------------------------------------------------------------------
# 1. Builder stage – installs UV & resolves dependencies
# ------------------------------------------------------------------
FROM python:3.13-bookworm AS builder

# Install system build tools
RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install UV
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev   # <-- only prod deps


# ------------------------------------------------------------------
# 2. Production stage – minimal runtime
# ------------------------------------------------------------------
FROM python:3.13-slim-bookworm AS production

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

# Copy the virtual-env from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Copy source code
WORKDIR /app
COPY src ./src
COPY data ./data      

# Make sure ingestion script is executable
RUN chmod +x src/data_ingestion/pipeline.py

USER app
EXPOSE 8080

# Default: run ingestion
ENTRYPOINT ["python", "-m", "src.data_ingestion.pipeline"]
