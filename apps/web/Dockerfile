# ─────────────────────────────────────────────
# Stage 1: Build
# ─────────────────────────────────────────────
FROM node:20-alpine AS builder

# Install pnpm
RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

WORKDIR /repo

# Copy workspace manifests first for layer caching
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/web/package.json ./apps/web/
COPY packages/ ./packages/

# Install only the web app and its workspace deps
RUN pnpm install --frozen-lockfile --filter daffodil-web...

# Copy web app source
COPY apps/web ./apps/web

# Build production bundle
WORKDIR /repo/apps/web
RUN pnpm run build

# ─────────────────────────────────────────────
# Stage 2: Serve with Nginx
# ─────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove default nginx site
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder
COPY --from=builder /repo/apps/web/dist /usr/share/nginx/html

# Nginx config with SPA fallback routing
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

# Install envsubst (gettext) for runtime port substitution
RUN apk add --no-cache gettext

EXPOSE 80

# Render injects $PORT at runtime; substitute it into nginx config then start nginx
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf && cp /tmp/default.conf /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]