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

# === optional language toolchains — uncomment what your task needs ===
# Python is already installed above; Node.js ships in the base image.

# --- C / C++ (GCC toolchain) ---
# RUN apt-get update \
#  && apt-get install -y --no-install-recommends \
#         build-essential gcc g++ make pkg-config \
#  && rm -rf /var/lib/apt/lists/*

# --- Go ---
# COPY --from=golang:1.26-bookworm /usr/local/go /usr/local/go
# ENV PATH=/usr/local/go/bin:${PATH}

# --- Rust ---
# ENV CARGO_HOME=/usr/local/cargo \
#     RUSTUP_HOME=/usr/local/rustup \
#     PATH=/usr/local/cargo/bin:${PATH}
# RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
#       | sh -s -- -y --default-toolchain 1.95.0 --profile minimal

# --- C# / .NET SDK ---
# RUN apt-get update \
#  && apt-get install -y --no-install-recommends libicu72 \
#  && rm -rf /var/lib/apt/lists/*
# ENV DOTNET_ROOT=/usr/local/dotnet \
#     PATH=/usr/local/dotnet:${PATH} \
#     DOTNET_CLI_TELEMETRY_OPTOUT=true \
#     DOTNET_NOLOGO=true
# RUN curl -fsSL https://dot.net/v1/dotnet-install.sh | bash -s -- \
#       --channel 8.0 --install-dir /usr/local/dotnet

# === task dependencies (edit me) ===
# Install anything the repo + your verifier need (no network at verify time),
# e.g. `uv sync --all-extras --all-groups`, `uv tool install pytest`.
