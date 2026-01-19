# MCP Runtime

MCP execution runtime with lifecycle management for MCP servers.

## Overview

`mcp_runtime` is a FastMCP-based MCP server that provides execution and lifecycle management for other MCP servers. It connects to `mcp_index` for discovery and manages server lifecycles locally via ZMQ-based IPC.

```
LLM Client (Claude/Cline)
    │ MCP Protocol
    ▼
┌─────────────────────────────┐
│       mcp_runtime           │
│    (FastMCP MCP Server)     │
├─────────────────────────────┤
│  Discovery → mcp_index API  │
│  Execution → ZMQ + Sessions │
└─────────────────────────────┘
    │               │
    ▼               ▼
mcp_index       MCP Servers
(FastAPI)       (stdio/http)
```

## Installation

```bash
uv sync
```

## Configuration

Create `.env` from template:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCOVERY_URL` | mcp_index API URL | `http://localhost:8000` |
| `DISCOVERY_API_KEY` | API key for mcp_index authentication | None |
| `DISCOVERY_ENCRYPTION_KEY` | Key to decrypt sensitive env vars in server configs | None |
| `TOOL_OFFLOADED_DATA_PATH` | Path for large result offloading | `/tmp/mcp_offloaded` |
| `MAX_RESULT_TOKENS` | Max tokens before content offloading | `4096` |
| `DESCRIBE_IMAGES` | Enable image description via vision model | `true` |
| `BACKGROUND_QUEUE_SIZE` | Max background tasks in queue | `100` |
| `OPENAI_API_KEY` | OpenAI API key (for image descriptions) | None |

The **encryption key** is required when MCP servers in `mcp_index` have encrypted environment variables (API keys, tokens). Without it, servers with secrets won't start.

## Integration

### Option 1: Streamable HTTP (Remote MCP Server)

MCP now supports [remote servers via Streamable HTTP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports), replacing the older SSE transport. This allows any MCP client to connect over HTTP.

**Start the server:**

```bash
mcp-runtime serve --transport streamable-http --host 0.0.0.0 --port 8001
```

**Client configuration (Claude Desktop, Cline, etc.):**

```json
{
  "mcpServers": {
    "mcp-runtime": {
      "url": "http://your-server:8001/mcp"
    }
  }
}
```

The server exposes a single endpoint at `/mcp` supporting both POST and GET methods for bidirectional messaging.

### Option 2: Docker

Build and run as a container:

```dockerfile
# Dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

RUN apt update --fix-missing && \
    apt install --yes --no-install-recommends \
        gcc pkg-config git curl build-essential \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv venv && uv sync --frozen

EXPOSE 8001

CMD ["uv", "run", "mcp-runtime", "serve", "--transport", "streamable-http", "--port", "8001"]
```

**Build and run:**

```bash
docker build -t mcp-runtime .
docker run -d \
  -p 8001:8001 \
  -e DISCOVERY_URL=http://mcp-index:8000 \
  -e DISCOVERY_ENCRYPTION_KEY=your-key \
  mcp-runtime
```

### Option 3: Local stdio (Claude Desktop via Docker)

For local development with Claude Desktop using Docker in stdio mode:

```json
{
  "mcpServers": {
    "mcp-runtime": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DISCOVERY_URL=http://host.docker.internal:8000",
        "-e", "DISCOVERY_ENCRYPTION_KEY=your-key",
        "--add-host=host.docker.internal:host-gateway",
        "mcp-runtime",
        "uv", "run", "mcp-runtime", "serve"
      ]
    }
  }
}
```

Note: `host.docker.internal` allows the container to reach services on the host machine (like mcp_index running on localhost:8000).

## Available Tools

| Tool | Description |
|------|-------------|
| `search_tools` | Search for tools using natural language |
| `search_servers` | Search for servers using natural language |
| `get_server_info` | Get detailed server information |
| `get_server_tools` | List tools on a server |
| `get_tool_details` | Get full tool schema and description |
| `list_servers` | List all registered servers |
| `get_statistics` | Get server/tool counts |
| `manage_server` | Start or shutdown a server |
| `list_running_servers` | List currently running servers |
| `execute_tool` | Execute a tool on a running server |
| `poll_task_result` | Check background task status |
| `get_content` | Retrieve offloaded content by reference ID |

## Workflow

Follow this workflow for optimal usage:

```
1. DISCOVER    search_tools("your need")         → Find relevant tools
       ↓
2. EXPLORE     get_server_info(server)           → Check capabilities
               get_server_tools(server)          → List available tools
       ↓
3. UNDERSTAND  get_tool_details(server, tool)    → Get full schema (REQUIRED)
       ↓
4. START       manage_server(server, "start")    → Start the MCP server
       ↓
5. EXECUTE     execute_tool(server, tool, args)  → Run the tool
       ↓
6. CLEANUP     manage_server(server, "shutdown") → Stop when done (optional)
```

**Important rules:**
- Always call `get_tool_details` before `execute_tool` to understand the schema
- Always call `manage_server(start)` before executing tools
- Use `in_background=true` for long-running operations, then `poll_task_result`
- Large responses are automatically offloaded; use `get_content(ref_id)` to retrieve

## Architecture

| Component | Description |
|-----------|-------------|
| **RuntimeEngine** | Core runtime managing ZMQ communication and server lifecycle |
| **DiscoveryClient** | HTTP client for mcp_index API |
| **ContentManager** | Large result offloading (text chunking, images) |
| **BackgroundTasks** | Priority queue for async tool execution |
| **FastMCP** | MCP server framework exposing tools to LLMs |

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v
```

## License

MIT
