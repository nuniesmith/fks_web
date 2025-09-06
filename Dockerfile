# Multi-stage Dockerfile extending shared Node.js template

# Build stage - using standard Node.js image
FROM node:22-alpine AS build

WORKDIR /app

# --- Build-time arguments (injected via docker build --build-arg or compose build args) ---
# These allow Vite to embed correct API / WS endpoints at build time. If not provided,
# the runtime container env alone will NOT influence already-built static assets.
ARG VITE_API_BASE_URL
ARG VITE_API_URL
ARG VITE_WS_BASE_URL
ARG VITE_DEFAULT_TRADING_MODE
ARG VITE_MOCK_SERVICES
ARG VITE_DEFAULT_RT_CHANNELS

# Expose them as environment variables for the build step (Vite only reads process.env.* at build time)
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
  VITE_API_URL=${VITE_API_URL} \
  VITE_WS_BASE_URL=${VITE_WS_BASE_URL} \
  VITE_DEFAULT_TRADING_MODE=${VITE_DEFAULT_TRADING_MODE} \
  VITE_MOCK_SERVICES=${VITE_MOCK_SERVICES} \
  VITE_DEFAULT_RT_CHANNELS=${VITE_DEFAULT_RT_CHANNELS}

# Copy package files for dependency caching
COPY package*.json ./

# Install dependencies deterministically with lockfile (includes dev deps for build)
ENV NODE_ENV=development npm_config_production=false
COPY package-lock.json ./
RUN set -eux; \
  npm install -g npm@latest; \
  success=0; \
  for i in 1 2 3; do \
    if npm ci --include=dev --no-audit --no-fund; then success=1; break; fi; \
    echo "npm ci attempt $i failed, retrying..." >&2; \
    rm -rf node_modules; \
    sleep 2; \
  done; \
  if [ "$success" -ne 1 ]; then echo 'npm ci failed after 3 attempts' >&2; exit 1; fi; \
  # Sanity check: ensure core deps present (react is a good proxy)
  [ -d node_modules/react ] || { echo 'react dependency missing after install' >&2; ls -al node_modules | head || true; exit 2; }; \
  # Fallback sanity: ensure build tools exist (prefer local but keep global for PATH)
  npm install -g typescript@5.9.2 vite@7.1.3; \
  npm cache clean --force >/dev/null 2>&1 || true

# Copy source and build
COPY . .
# The build will inline the VITE_* variables above. To verify, you can inspect dist assets for embedded URLs.
RUN npm run build

# Production stage - using nginx for serving
FROM nginx:1.27.1-alpine AS final

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Set service-specific environment variables
ENV SERVICE_NAME=fks-web \
  SERVICE_TYPE=web \
  SERVICE_PORT=80

# (Optional) Runtime overrides: you can still point the app to a different API without rebuild
# by opening DevTools console and executing: localStorage.setItem('fks_api_base_url','http://your-host:8000/api')

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

EXPOSE ${SERVICE_PORT}

# Create non-root user for nginx
RUN adduser -D -s /bin/sh -u 1088 nginx_user

# Use nginx as the entrypoint
CMD ["nginx", "-g", "daemon off;"]
