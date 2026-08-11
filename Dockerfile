# synapse-admin/ is a git subtree of upstream, forked so the session lives on the server rather than in
# the browser (see synapse-admin/src/storage.ts). We build it from source; the Python layer serves the
# build and owns the session file.

FROM node:22-alpine AS frontend
WORKDIR /build

# .yarn holds the pinned yarn 4.4.1 release, so the toolchain itself needs no network fetch.
COPY synapse-admin/.yarn .yarn
COPY synapse-admin/package.json synapse-admin/.yarnrc.yml synapse-admin/yarn.lock ./
RUN yarn config set enableTelemetry 0 \
 && yarn install --immutable --network-timeout=300000

COPY synapse-admin/ ./
RUN yarn build

FROM python:3.12-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

COPY --from=frontend /build/dist /app/static
ENV SYNAPSE_ADMIN_STATIC_DIR=/app/static
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080
CMD ["python", "-u", "-m", "openhost_synapse_admin.main"]
