default: test

# Install dependencies, pre-commit hooks, and the playwright chromium browser.
setup:
    uv sync
    uv run pre-commit install
    uv run playwright install chromium

# Build the container image and serve it locally on http://localhost:8080.
# Credentials persist in ./.local-data, standing in for the OpenHost app data mount.
run: build
    mkdir -p .local-data
    podman run --rm -p 8080:8080 \
        -v ./.local-data:/data/app_data/synapse-admin \
        -e OPENHOST_APP_DATA_DIR=/data/app_data/synapse-admin \
        synapse-admin

# Run the test suite.
test:
    uv run pytest -x

# Lint, format, and typecheck (same checks as the pre-commit hooks).
check:
    uv run ruff check --fix .
    uv run ruff format .
    uv run mypy

# Build the container image.
build:
    podman build -t synapse-admin .
