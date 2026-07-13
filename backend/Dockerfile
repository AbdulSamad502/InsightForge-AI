# ════════════════════════════════════════════════════════════
# Stage 1 — Builder: install all Python dependencies
# ════════════════════════════════════════════════════════════
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps for psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into a separate location
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ════════════════════════════════════════════════════════════
# Stage 2 — Runtime: lean production image
# ════════════════════════════════════════════════════════════
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system deps only (no build tools)
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p app/storage/uploads app/storage/reports \
    app/storage/exports app/storage/temp logs

# Non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--log-level", "info"]