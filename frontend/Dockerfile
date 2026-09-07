# Build-only image: it produces dist/ and exits. Caddy serves the files,
# so nothing from Node runs in production.
FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_API_URL is inlined at build time, not read at runtime. Same-origin
# deployment means it's just /api/v1 — no host, no CORS.
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# The copy step in docker-compose lifts dist/ into the shared volume.
CMD ["sh", "-c", "rm -rf /out/* && cp -r /app/dist/* /out/"]
