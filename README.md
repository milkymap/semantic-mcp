# Semantic MCP

[![PyPI version](https://badge.fury.io/py/semantic-mcp.svg)](https://pypi.org/project/semantic-mcp/)
[![Docker](https://img.shields.io/docker/v/milkymap/semantic-mcp?label=docker)](https://hub.docker.com/r/milkymap/semantic-mcp)

Semantic router for MCP ecosystems - Discover, manage, and execute tools across multiple MCP servers with progressive disclosure.

## Overview

`semantic-mcp` is a FastMCP-based MCP server that provides semantic discovery and lifecycle management for other MCP servers. It connects to a discovery service for semantic search and manages server lifecycles locally via ZMQ-based IPC.

```
LLM Client (Claude/Cline)
    │ MCP Protocol
    ▼
┌─────────────────────────────┐
│       semantic-mcp          │
│    (FastMCP MCP Server)     │
├─────────────────────────────┤
│  Discovery → mcp-index API  │
│  Execution → ZMQ + Sessions │
└─────────────────────────────┘
    │               │
    ▼               ▼
mcp-index       MCP Servers
(Elasticsearch) (stdio/http)
```

## Related Projects

- **[mcp-index](https://github.com/milkymap/mcp-index)** - Elasticsearch-based semantic discovery service for MCP servers. Required backend for `semantic-mcp` to enable semantic search and server registry.

## Installation

### Option 1: uvx (Recommended)

```bash
uvx semantic-mcp serve --transport stdio
```

### Option 2: pip/uv

```bash
# Install from PyPI
pip install semantic-mcp

# Or with uv
uv pip install semantic-mcp

# Run
semantic-mcp serve --transport stdio
```

### Option 3: Docker

```bash
docker pull milkymap/semantic-mcp:0.2

docker run -d \
  -p 8001:8001 \
  -e DISCOVERY_URL=http://your-discovery-service \
  -e DISCOVERY_API_KEY=your-key \
  milkymap/semantic-mcp:0.2 serve --transport streamable-http --port 8001
```

### Option 4: From source

```bash
git clone https://github.com/milkymap/semantic-mcp
cd semantic-mcp
uv sync
uv run semantic-mcp serve
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCOVERY_URL` | Discovery service API URL | `http://localhost:8000` |
| `DISCOVERY_API_KEY` | API key for discovery authentication | None |
| `DISCOVERY_ENCRYPTION_KEY` | Key to decrypt sensitive env vars in server configs | None |
| `TOOL_OFFLOADED_DATA_PATH` | Path for large result offloading | `/tmp/mcp_offloaded` |
| `MAX_RESULT_TOKENS` | Max tokens before content offloading | `4096` |
| `BACKGROUND_QUEUE_SIZE` | Max background tasks in queue | `100` |
| `OPENAI_API_KEY` | OpenAI API key (for image descriptions) | None |

## MCP Client Integration

### Claude Code / Cline (uvx)

Add to your `.mcp.json` or MCP config:

```json
{
  "mcpServers": {
    "semantic-mcp": {
      "command": "uvx",
      "args": ["semantic-mcp", "serve", "--transport", "stdio"],
      "env": {
        "DISCOVERY_URL": "https://your-discovery-service",
        "DISCOVERY_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Claude Desktop (Docker)

```json
{
  "mcpServers": {
    "semantic-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DISCOVERY_URL", "-e", "DISCOVERY_API_KEY",
        "--add-host=host.docker.internal:host-gateway",
        "milkymap/semantic-mcp:0.2", "serve", "--transport", "stdio"
      ],
      "env": {
        "DISCOVERY_URL": "http://host.docker.internal:8000",
        "DISCOVERY_API_KEY": "your-key"
      }
    }
  }
}
```

### Remote HTTP Server

Start the server:

```bash
semantic-mcp serve --transport streamable-http --host 0.0.0.0 --port 8001
```

Client configuration:

```json
{
  "mcpServers": {
    "semantic-mcp": {
      "url": "http://your-server:8001/mcp"
    }
  }
}
```

## Available Operations

`semantic-mcp` exposes a single `semantic_router` tool with these operations:

### Discovery (lightweight)
| Operation | Description |
|-----------|-------------|
| `search_tools` | Search for tools using natural language |
| `search_servers` | Search for servers using natural language |
| `list_servers` | List all registered servers |
| `get_server_tools` | List tools on a server |
| `get_statistics` | Get server/tool counts |

### Exploration (full details)
| Operation | Description |
|-----------|-------------|
| `get_server_info` | Get detailed server information |
| `get_tool_details` | Get full tool schema and description |

### Lifecycle
| Operation | Description |
|-----------|-------------|
| `manage_server` | Start or shutdown a server |
| `list_running_servers` | List currently running servers |

### Execution
| Operation | Description |
|-----------|-------------|
| `execute_tool` | Execute a tool on a running server |
| `poll_task_result` | Check background task status |
| `cancel_task` | Cancel a running background task |
| `list_tasks` | List all background tasks |
| `get_content` | Retrieve offloaded content by reference ID |

## Workflow

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
| **DiscoveryClient** | HTTP client for discovery service API |
| **ContentManager** | Large result offloading (text chunking, images) |
| **BackgroundTasks** | Priority queue for async tool execution |
| **FastMCP** | MCP server framework exposing tools to LLMs |

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest tests/ -v
```

## License

MIT
