from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .settings import RuntimeSettings
from .runtime_engine import RuntimeEngine
from .log import logger

settings = RuntimeSettings()
runtime_engine: Optional[RuntimeEngine] = None


@asynccontextmanager
async def lifespan(app: FastMCP):
    global runtime_engine
    runtime_engine = RuntimeEngine(settings)
    async with runtime_engine:
        logger.info("MCP Runtime ready")
        yield
    logger.info("MCP Runtime stopped")


mcp = FastMCP("mcp-runtime", lifespan=lifespan)


MCP_RUNTIME_README = """
<overview>
MCP Runtime is an execution and lifecycle management layer for MCP servers.
It connects to a central discovery service (mcp_index) to search, explore, start, and execute tools across multiple MCP servers dynamically.
You do not need local configuration files - everything is fetched from the discovery service.
</overview>

<available_tools>
Discovery:
- search_tools: Search for tools using natural language (lightweight results, no schemas)
- search_servers: Search for servers using natural language
- get_server_info: Get detailed information about a specific server
- get_server_tools: List all tools on a server (lightweight results, no schemas)
- get_tool_details: Get full tool schema and description (required before execution)
- list_servers: List all registered servers
- get_statistics: Get total counts of servers and tools

Lifecycle:
- manage_server: Start or shutdown an MCP server (action: 'start' or 'shutdown')
- list_running_servers: List currently running servers

Execution:
- execute_tool: Execute a tool on a running server
- poll_task_result: Check status of background tasks

Content:
- get_content: Retrieve offloaded content by reference ID
</available_tools>

<workflow>
Follow this workflow for optimal usage:

1. DISCOVER: Start by searching for relevant tools or servers
   search_tools(query="your need") → returns lightweight list

2. EXPLORE: Deep dive into interesting results
   get_server_info(server_name) → server capabilities and limitations
   get_server_tools(server_name) → list tools on that server

3. UNDERSTAND: Always read the full schema before execution
   get_tool_details(server_name, tool_name) → full schema with parameters

4. START: Start the server before executing any tool
   manage_server(server_name, action="start") → starts the server

5. EXECUTE: Now you can execute the tool
   execute_tool(server_name, tool_name, arguments={...})

6. CLEANUP: Shutdown servers when done (optional but recommended)
   manage_server(server_name, action="shutdown")
</workflow>

<execution_rules>
- NEVER execute a tool without first reading its schema via get_tool_details
- NEVER execute a tool on a server that is not running
- ALWAYS call manage_server(action="start") before execute_tool
- Use list_running_servers to verify server status before execution
- For long-running tools, use in_background=True and poll with poll_task_result
</execution_rules>

<discovery_rules>
- search_tools and get_server_tools return lightweight results WITHOUT schemas
- This is intentional to save context window space
- You MUST call get_tool_details to see the full parameter schema
- Use min_score parameter to adjust search sensitivity (default: 0.3)
- Use server_names parameter to filter search to specific servers
</discovery_rules>

<content_rules>
- Large tool results are automatically offloaded and replaced with references
- When you see [Reference: uuid], use get_content(ref_id="uuid") to retrieve
- For chunked text, use chunk_index parameter to retrieve specific chunks
- Images and audio are stored as base64, retrievable via get_content
</content_rules>

<best_practices>
- Start with broad searches, then narrow down
- Read server capabilities before exploring its tools
- Always verify tool parameters match the schema
- Use background execution for tools that may take long
- Shutdown unused servers to free resources
- When a tool returns truncated content, use get_content to retrieve full data
</best_practices>
""".strip()


@mcp.tool()
async def readme() -> str:
    """Get usage instructions for MCP Runtime. Call this first to understand how to use the available tools."""
    return MCP_RUNTIME_README


def _strip_tool_schema(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove tool_schema from tool list to reduce context size"""
    return [
        {k: v for k, v in tool.items() if k != "tool_schema"}
        for tool in tools
    ]


@mcp.tool()
async def search_tools(
    query: str,
    limit: int = 10,
    min_score: float = 0.3,
    server_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Search for tools using natural language query. Returns lightweight results without schemas. Use get_tool_details for full schema."""
    result = await runtime_engine.discovery_client.search_tools(
        query=query,
        limit=limit,
        min_score=min_score,
        server_names=server_names
    )
    if "tools" in result:
        result["tools"] = _strip_tool_schema(result["tools"])
    return result


@mcp.tool()
async def search_servers(
    query: str,
    limit: int = 10,
    min_score: float = 0.3
) -> Dict[str, Any]:
    """Search for servers using natural language query"""
    return await runtime_engine.discovery_client.search_servers(
        query=query,
        limit=limit,
        min_score=min_score
    )


@mcp.tool()
async def get_server_info(server_name: str) -> Dict[str, Any]:
    """Get detailed information about a server"""
    info = await runtime_engine.discovery_client.get_server_info(server_name)
    return info.model_dump()


@mcp.tool()
async def get_server_tools(
    server_name: str,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List all tools available on a server. Returns lightweight results without schemas. Use get_tool_details for full schema."""
    result = await runtime_engine.discovery_client.get_server_tools(
        server_name=server_name,
        limit=limit,
        offset=offset
    )
    if "tools" in result:
        result["tools"] = _strip_tool_schema(result["tools"])
    return result


@mcp.tool()
async def get_tool_details(server_name: str, tool_name: str) -> Dict[str, Any]:
    """Get detailed schema and description of a specific tool"""
    info = await runtime_engine.discovery_client.get_tool_details(server_name, tool_name)
    return info.model_dump()


@mcp.tool()
async def list_servers(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List all registered servers"""
    return await runtime_engine.discovery_client.list_servers(limit=limit, offset=offset)


@mcp.tool()
async def manage_server(server_name: str, action: str) -> Dict[str, Any]:
    """Start or shutdown an MCP server. action: 'start' or 'shutdown'"""
    if action == "start":
        success, message = await runtime_engine.start_mcp_server(server_name)
    elif action == "shutdown":
        success, message = await runtime_engine.shutdown_mcp_server(server_name)
    else:
        return {"success": False, "message": f"Invalid action: {action}. Use 'start' or 'shutdown'"}
    return {"success": success, "message": message}


@mcp.tool()
async def list_running_servers() -> List[str]:
    """List all currently running MCP servers"""
    return runtime_engine.list_running_servers()


@mcp.tool()
async def execute_tool(
    server_name: str,
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    timeout: float = 60,
    in_background: bool = False,
    priority: int = 1
) -> Dict[str, Any]:
    """Execute a tool on a running MCP server"""
    try:
        result = await runtime_engine.execute_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=arguments,
            timeout=timeout,
            in_background=in_background,
            priority=priority
        )
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def poll_task_result(task_id: str) -> Dict[str, Any]:
    """Check status and retrieve result of a background task"""
    is_done, result, error = await runtime_engine.poll_task_result(task_id)
    if error:
        return {"status": "error", "error": error}
    if is_done:
        return {"status": "completed", "result": result}
    return {"status": "running"}


@mcp.tool()
async def get_content(ref_id: str, chunk_index: Optional[int] = None) -> Dict[str, Any]:
    """Retrieve offloaded content by reference ID"""
    try:
        content = runtime_engine.content_manager.get_content(ref_id, chunk_index)
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_statistics() -> Dict[str, Any]:
    """Get statistics about registered servers and tools"""
    return await runtime_engine.discovery_client.get_statistics()
