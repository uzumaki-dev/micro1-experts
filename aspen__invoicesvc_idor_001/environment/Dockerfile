FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
 && apt-get update \
 && apt-get install -y --no-install-recommends git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh \
 && chmod 755 /usr/local/bin/uv /usr/local/bin/uvx

# Pre-install Python 3.13 during build (internet available); runtime has no internet
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

# Copy the buggy substrate and smoke test
COPY invoicesvc/ /repo/invoicesvc/
COPY tests/ /repo/tests/
COPY pytest.ini /repo/pytest.ini

# Anti-cheating: fresh git init, single commit, no remote
RUN git init -q \
 && git config user.email build@aspen.local \
 && git config user.name build \
 && git add -A \
 && git commit -q -m "buggy starter (idor v1)"

RUN chown -R user:user /repo
USER user

# Pre-warm harbor-rewardkit while build has internet; runtime is offline
RUN uvx --python 3.13 --from 'harbor-rewardkit[all]' rewardkit --help 2>&1 || true

ENV PYTHONPATH=/repo
ENV UV_OFFLINE=1

CMD ["bash"]
