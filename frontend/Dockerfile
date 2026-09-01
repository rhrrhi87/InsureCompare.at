# File: frontend/Dockerfile
# Multi-stage build: compile the Vite SPA, then serve it as static files.

# =============================================================================
# Stage 1 - build
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /build

# Install dependencies first to maximise Docker layer caching
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

# Copy source and build
COPY . .
ENV NODE_ENV=production
RUN npm run build

# =============================================================================
# Stage 2 - runtime (nginx serves the static dist/)
# =============================================================================
FROM nginx:1.27-alpine AS runtime

# Strip the default nginx config and supply our SPA-aware one.
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /build/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
