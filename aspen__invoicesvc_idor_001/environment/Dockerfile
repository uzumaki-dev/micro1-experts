FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
 && apt-get update \
 && apt-get install -y --no-install-recommends git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh \
 && chmod 755 /usr/local/bin/uv /usr/local/bin/uvx

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

ENV PYTHONPATH=/repo

CMD ["bash"]
