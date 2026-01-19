# Base image with UV
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# System dependencies
RUN apt update --fix-missing && \
    apt install --yes --no-install-recommends \
        gcc pkg-config git curl build-essential \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install dependencies
RUN uv venv && uv sync --frozen

EXPOSE 8001

CMD ["uv", "run", "mcp-runtime", "serve", "--transport", "streamable-http", "--port", "8001"]
