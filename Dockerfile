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

# Copy only the build inputs, never `.yarn` again: that directory now holds the resolved PnP packages,
# and overwriting it with the repo's (which has just the yarn release + sdks) breaks the build.
COPY synapse-admin/src ./src
COPY synapse-admin/public ./public
COPY synapse-admin/index.html synapse-admin/vite.config.ts ./
COPY synapse-admin/tsconfig.json synapse-admin/tsconfig.vite.json synapse-admin/tsconfig.eslint.json ./
# `yarn lint` uses .gitignore as its ignore file and errors without it.
COPY synapse-admin/.gitignore ./
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
