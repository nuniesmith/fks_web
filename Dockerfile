# Optimized multi-stage build for fks_web Python service
# Uses ML base image which already has sentence-transformers, langchain, chromadb, etc.
FROM nuniesmith/fks:docker-ml-latest AS builder

WORKDIR /app

# Upgrade pip, setuptools, and wheel (better caching with BuildKit)
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel

# Copy dependency files (for better layer caching)
COPY requirements.txt ./

# Base image already has: sentence-transformers, langchain, chromadb, ollama, TA-Lib, numpy, pandas
# Create a filtered requirements file without packages already in base image
RUN grep -v "^torch\|^transformers\|^sentence-transformers\|^langchain\|^chromadb\|^ollama\|^numpy\|^pandas\|^#" requirements.txt | grep -v "^$" > /tmp/web-requirements.txt || true

# Install web-specific dependencies (without ML packages already in base)
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --user --no-warn-script-location --no-cache-dir -r /tmp/web-requirements.txt || true

# Install torch/transformers separately ONLY if needed for RAG features
# These are ~2.5GB combined! Comment out these lines to save space.
# Set ENABLE_TRANSFORMERS=false to skip installation
ARG ENABLE_TRANSFORMERS=${ENABLE_TRANSFORMERS:-true}
RUN if [ "$ENABLE_TRANSFORMERS" = "true" ]; then \
        echo "Installing torch and transformers (this will add ~2.5GB)..." && \
        python -m pip install --user --no-warn-script-location --no-cache-dir "torch>=2.0.0" "transformers>=4.35.0" || \
        echo "⚠️  torch/transformers installation failed (RAG features may not work)"; \
    else \
        echo "⚠️  Skipping torch/transformers installation (RAG transformers will not work, but sentence-transformers still available)"; \
    fi

# Runtime stage - use slim Python but copy ML packages from builder if needed
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SERVICE_NAME=fks_web \
    SERVICE_PORT=8000 \
    PYTHONPATH=/app/src:/app \
    PATH=/home/appuser/.local/bin:$PATH

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first (before copying files)
RUN useradd -u 1000 -m -s /bin/bash appuser

# Copy Python packages from builder (includes ML packages from base image)
# Only copy what's needed - the builder stage has optimized packages
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Alternative: If you want to avoid ML packages entirely, use this instead:
# But this requires removing torch/sentence-transformers from requirements.txt
# and making RAG features optional

# Copy application source with correct ownership
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request,sys;port=os.getenv('SERVICE_PORT','8000');u=f'http://localhost:{port}/health';\
import urllib.error;\
try: urllib.request.urlopen(u,timeout=3);\
except Exception: sys.exit(1)" || exit 1

# Expose the service port
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
