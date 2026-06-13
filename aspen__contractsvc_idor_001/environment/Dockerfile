# === BEGIN realm base (do not edit) ===
FROM --platform=linux/amd64 node:24-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Core tooling present in every task image. Node.js comes from the base image.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates curl wget \
        git patch \
        ripgrep fd-find jq less file unzip \
        vim sudo procps \
 && rm -rf /var/lib/apt/lists/* \
 && ln -sf /usr/bin/fdfind /usr/local/bin/fd

# Python (default language, uv-managed; uv also drives dependency installs).
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN curl -LsSf https://astral.sh/uv/0.11.13/install.sh | UV_INSTALL_DIR=/usr/local/bin sh \
 && uv python install 3.13 \
 && ln -sf "$(uv python find 3.13)" /usr/local/bin/python3 \
 && ln -sf /usr/local/bin/python3 /usr/local/bin/python

RUN mkdir -p /app
# === END realm base ===

# === uv tool directory (REQUIRED for harbor-rewardkit) ===
# The verifier runs `uvx harbor-rewardkit` as the `node` user (UID 1000).
# Without this, uv can't write to its cache and the verifier exits rc=1.
RUN mkdir -p /opt/uv-tools/bin \
 && chown -R node:node /opt/uv-tools

ENV UV_TOOL_DIR=/opt/uv-tools \
    UV_TOOL_BIN_DIR=/opt/uv-tools/bin \
    PATH=/opt/uv-tools/bin:${PATH}

# === Harbor runtime mount points ===
RUN mkdir -p /solution /tests /logs/verifier /logs/artifacts \
 && chown -R node:node /solution /tests /logs

WORKDIR /repo

# === substrate setup ===
COPY requirements.txt /repo/requirements.txt
COPY contractsvc/     /repo/contractsvc/
COPY tests/           /repo/tests/
COPY pytest.ini       /repo/pytest.ini

# Install Python dependencies into a venv owned by the node user.
RUN uv venv /opt/venv \
 && uv pip install -p /opt/venv -r /repo/requirements.txt \
 && chown -R node:node /opt/venv

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:${PATH}

# Squash into one reproducible commit (anti-cheating).
# Fixed identity + dates → identical SHA on every build.
RUN find /repo -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true; \
    find /repo -name '*.pyc' -delete 2>/dev/null || true; \
    git init -q \
 && git config user.email "task@local" \
 && git config user.name "task" \
 && git add -A \
 && GIT_AUTHOR_NAME=task GIT_AUTHOR_EMAIL=task@local \
    GIT_COMMITTER_NAME=task GIT_COMMITTER_EMAIL=task@local \
    GIT_AUTHOR_DATE="2025-01-01T00:00:00Z" GIT_COMMITTER_DATE="2025-01-01T00:00:00Z" \
    git commit -qm "buggy starter (idor v1)" \
 && chown -R node:node /repo

USER node
WORKDIR /repo

ENV PYTHONPATH=/repo

CMD ["sleep", "infinity"]
