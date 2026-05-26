FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

ENV M1_RL_ENVS_TEMPLATE_REV=v2-public

USER root

RUN apt-get update \
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

RUN id -u user >/dev/null 2>&1 || useradd -m -u 1000 -s /bin/bash user
RUN mkdir -p /opt/uv-tools/bin && chown -R user:user /opt/uv-cache /opt/uv-tools

WORKDIR /repo

COPY requirements.txt /repo/requirements.txt
RUN pip install -r /repo/requirements.txt

COPY docvault/ /repo/docvault/
COPY pytest.ini /repo/pytest.ini
COPY tests/conftest.py /repo/tests/conftest.py
COPY tests/test_smoke.py /repo/tests/test_smoke.py

RUN git init -q \
 && git config user.email build@aspen.local \
 && git config user.name build \
 && git add -A \
 && git commit -q -m "vulnerable starter (docvault idor v1)"

RUN chown -R user:user /repo \
 && mkdir -p /logs/verifier /logs/artifacts \
 && chown -R user:user /logs \
 && git config --system --add safe.directory /repo

ENV PYTHONPATH=/repo

CMD ["sleep", "infinity"]
