# MCP Runtime

MCP execution runtime with lifecycle management for MCP servers.

## Overview

`mcp_runtime` is a fastmcp-based MCP server that provides execution and lifecycle management for other MCP servers. It uses `mcp_index` for discovery and manages server runtime locally via ZMQ-based IPC.

```
LLM Client (Claude/Cline)
    │ MCP Protocol
    ▼
┌─────────────────────────────┐
│       mcp_runtime           │
│    (fastmcp MCP Server)     │
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

Required settings:
- `DISCOVERY_URL`: mcp_index API URL (default: `http://localhost:8000`)

## Usage

### Start server (stdio)

```bash
mcp-runtime serve
```

### Start server (SSE)

```bash
mcp-runtime serve --transport sse --port 8001
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "mcp-runtime": {
      "command": "uvx",
      "args": ["--from", "/path/to/mcp_runtime", "mcp-runtime", "serve"],
      "env": {
        "DISCOVERY_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `search_tools` | Search for tools using natural language |
| `search_servers` | Search for servers using natural language |
| `get_server_info` | Get detailed server information |
| `get_server_tools` | List tools on a server |
| `get_tool_details` | Get tool schema and description |
| `list_servers` | List all registered servers |
| `manage_server` | Start or shutdown a server |
| `list_running_servers` | List currently running servers |
| `execute_tool` | Execute a tool on a running server |
| `poll_task_result` | Check background task status |
| `get_content` | Retrieve offloaded content |
| `get_statistics` | Get server/tool counts |

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v
```

## Architecture

- **RuntimeEngine**: Core runtime managing ZMQ communication and server lifecycle
- **DiscoveryClient**: HTTP client for mcp_index API
- **ContentManager**: Large result offloading (text chunking, images)
- **fastmcp**: MCP server framework exposing tools to LLMs

## License

MIT
