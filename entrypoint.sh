#!/bin/bash
# Entrypoint script for fks_web

set -e

# Default values
SERVICE_NAME=${SERVICE_NAME:-fks_web}
SERVICE_PORT=${SERVICE_PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "Starting ${SERVICE_NAME} on ${HOST}:${SERVICE_PORT}"

# Run the service (Django ASGI)
exec python -m uvicorn src.config.asgi:application \
    --host "${HOST}" \
    --port "${SERVICE_PORT}" \
    --no-access-log \
    --log-level info
