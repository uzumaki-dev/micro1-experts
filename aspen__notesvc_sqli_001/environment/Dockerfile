FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
 && apt-get update \
 && apt-get install -y --no-install-recommends git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh \
 && chmod 755 /usr/local/bin/uv /usr/local/bin/uvx

ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN mkdir -p /opt/uv-python /opt/uv-cache \
 && uv python install --install-dir /opt/uv-python 3.13 \
 && chmod -R a+rX /opt/uv-python /opt/uv-cache

ENV UV_CACHE_DIR=/opt/uv-cache \
    UV_TOOL_DIR=/opt/uv-tools \
    UV_TOOL_BIN_DIR=/opt/uv-tools/bin \
    UV_PYTHON=3.13 \
    UV_PYTHON_PREFERENCE=only-managed
RUN mkdir -p /opt/uv-tools/bin \
 && chown -R user:user /opt/uv-cache /opt/uv-tools

WORKDIR /repo

COPY requirements.txt /repo/requirements.txt
RUN pip install -r /repo/requirements.txt

COPY notesvc/ /repo/notesvc/
COPY tests/ /repo/tests/
COPY pytest.ini /repo/pytest.ini

# Anti-cheating: fresh git init, single commit, no remote.
# Dates pinned so SHA is stable across rebuilds.
# __pycache__ purged before git add to keep SHA clean.
RUN find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; \
    find . -name '*.pyc' -delete 2>/dev/null; \
    git init -q \
 && git config user.email build@aspen.local \
 && git config user.name build \
 && git add -A \
 && GIT_AUTHOR_DATE="2025-01-01T00:00:00Z" GIT_COMMITTER_DATE="2025-01-01T00:00:00Z" \
    git commit -q -m "buggy starter (sqli v1)"

RUN chown -R user:user /repo
USER user

RUN uvx --python 3.13 --from 'harbor-rewardkit[all]' rewardkit --help 2>&1 || true

RUN curl -fsSL https://claude.ai/install.sh | bash

USER root
RUN mv /usr/bin/curl /usr/bin/real_curl \
 && printf '#!/bin/sh\nif echo "$*" | grep -q "claude.ai"; then exit 0; fi\nexec /usr/bin/real_curl "$@"\n' \
      > /usr/bin/curl \
 && chmod +x /usr/bin/curl
USER user

ENV PATH="/home/user/.local/bin:$PATH"
ENV PYTHONPATH=/repo
ENV UV_OFFLINE=1

CMD ["bash"]
