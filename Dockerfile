# syntax=docker/dockerfile:1

# Use the official uv image with Python 3.13 pre-installed
FROM ghcr.io/astral-sh/uv:0.8-python3.13-bookworm-slim

RUN apt-get update && apt-get -y install curl --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Use copy link mode since cache mount and target are on different filesystems
ENV UV_LINK_MODE=copy

# Disable uv cache at runtime — deps are already installed, and the app user
# has no home directory to write a cache to
ENV UV_NO_CACHE=1

RUN mkdir -p /home/app

WORKDIR /home/app

RUN addgroup --system --gid 1000 app && adduser --system --uid 1000 --group app

# Install dependencies first (cached layer — only re-runs when lock/pyproject changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY flask_app.py config.py boot.sh ./
RUN chmod a+x boot.sh && chown -R app:app /home/app

USER app

# This gets synced in the docker compose but not when building the image alone
COPY app app
COPY migrations migrations
