# syntax=docker/dockerfile:1

# Production image for the Nexus web SPA (React + TanStack Router, built with Vite).
# The API base URL is read from VITE_API_URL at BUILD time and baked into the
# static bundle. It must be provided as a build arg and point at the public API,
# e.g. --build-arg VITE_API_URL=https://api.example.com

########################################
# Stage 1 — builder: install and build with bun
########################################
FROM oven/bun:1 AS builder

WORKDIR /app

# Install dependencies against the committed lockfile for reproducible builds.
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Build the static bundle. VITE_API_URL is inlined into the output here.
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
COPY . .
RUN bun run build

########################################
# Stage 2 — runtime: serve dist/ with nginx
########################################
FROM nginx:1.27-alpine AS runtime

# SPA config with history fallback to index.html.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
