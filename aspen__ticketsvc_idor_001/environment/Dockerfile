FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV M1_RL_ENVS_TEMPLATE_REV=v2-public

RUN id -u user >/dev/null 2>&1 || useradd -m -u 1000 -s /bin/bash user \
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

COPY ticketsvc/ /repo/ticketsvc/
COPY tests/ /repo/tests/
COPY pytest.ini /repo/pytest.ini

RUN git init -q \
 && git config user.email build@aspen.local \
 && git config user.name build \
 && git config --system --add safe.directory /repo \
 && git add -A \
 && git commit -q -m "buggy starter (idor v1)"

RUN mkdir -p /logs/verifier /logs/artifacts \
 && chown -R user:user /repo /logs

USER user

RUN uvx --python 3.13 --from 'harbor-rewardkit[all]' rewardkit --version

ENV PYTHONPATH=/repo
ENV UV_OFFLINE=1

CMD ["sleep", "infinity"]
