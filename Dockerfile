# Base image with UV
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# System dependencies + Node.js for npx-based MCP servers
RUN apt update --fix-missing && \
    apt install --yes --no-install-recommends \
        gcc pkg-config git curl build-essential ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt update \
    && apt install --yes nodejs \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Install dependencies
RUN uv venv && uv sync --frozen

EXPOSE 8001

ENTRYPOINT ["uv", "run", "semantic-mcp"]

CMD ["--help"]
