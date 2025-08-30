# Multi-stage Dockerfile extending shared Node.js template

# Build stage - using standard Node.js image
FROM node:22-alpine AS build

WORKDIR /app

# Copy package files for dependency caching
COPY package*.json ./

# Install dependencies with updated npm
RUN npm cache clean --force && \
    npm install -g npm@latest && \
    npm install --no-audit --no-fund --legacy-peer-deps

# Copy source and build
COPY . .
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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

EXPOSE ${SERVICE_PORT}

# Create non-root user for nginx
RUN adduser -D -s /bin/sh -u 1088 nginx_user

# Use nginx as the entrypoint
CMD ["nginx", "-g", "daemon off;"]
