import yaml
from typing import Optional, List, Dict, Any, Literal, Annotated
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from .settings import RuntimeSettings
from .runtime_engine import RuntimeEngine
from .log import logger
from .tools import (
    SearchToolsTool,
    SearchServersTool,
    GetServerInfoTool,
    GetServerToolsTool,
    GetToolDetailsTool,
    ListServersTool,
    ManageServerTool,
    ListRunningServersTool,
    ExecuteToolTool,
    PollTaskResultTool,
    GetContentTool,
    GetStatisticsTool,
)


class MCPServer:
    def __init__(self, settings: RuntimeSettings):
        self.settings = settings
        self.runtime_engine: Optional[RuntimeEngine] = None
        self.mcp = FastMCP(
            name="mcp-runtime",
            instructions="""
            MCP Runtime: Execution and lifecycle management for MCP servers.
            I help you discover, start, and execute tools across multiple MCP servers through a central discovery service.
            Discovery: Search for tools and servers using natural language semantic search
            Exploration: Browse servers and tools with detailed schemas and capabilities
            Management: Start/stop servers dynamically based on your needs
            Execution: Run tools with proper schema validation and background execution support
            Progressive: Minimal results first, detailed schemas only when needed for efficient token usage
            Start with search_tools() to find relevant tools, then follow the guided workflow to execution.
            For background tasks, use execute_tool() with in_background=True, then poll_task_result() to check status.
            """,
            lifespan=self.lifespan
        )

    @asynccontextmanager
    async def lifespan(self, app: FastMCP):
        self.runtime_engine = RuntimeEngine(self.settings)
        async with self.runtime_engine:
            self.register_tools()

            # Fetch indexed servers for the router description
            stats = await self.runtime_engine.discovery_client.get_statistics()
            total_servers = stats.get("total_servers", 0)

            servers_info = await self.runtime_engine.discovery_client.list_servers(
                limit=total_servers if total_servers > 0 else 50,
                offset=0
            )

            indexed_servers = []
            for server in servers_info.get("servers", []):
                item = {
                    "server_name": server.get("name"),
                    "title": server.get("title"),
                    "nb_tools": server.get("nbTools", 0)
                }
                indexed_servers.append(yaml.dump(item, sort_keys=False))

            servers_list_msg = "\n###\n".join(indexed_servers) if indexed_servers else "No servers indexed yet"

            self.define_semantic_router(servers_list_msg)
            logger.info(f"MCP Runtime ready with {total_servers} indexed servers")
            yield
        logger.info("MCP Runtime stopped")

    def register_tools(self):
        self.search_tools = SearchToolsTool(self.runtime_engine)
        self.search_servers = SearchServersTool(self.runtime_engine)
        self.get_server_info = GetServerInfoTool(self.runtime_engine)
        self.get_server_tools = GetServerToolsTool(self.runtime_engine)
        self.get_tool_details = GetToolDetailsTool(self.runtime_engine)
        self.list_servers = ListServersTool(self.runtime_engine)
        self.manage_server = ManageServerTool(self.runtime_engine)
        self.list_running_servers = ListRunningServersTool(self.runtime_engine)
        self.execute_tool = ExecuteToolTool(self.runtime_engine)
        self.poll_task_result = PollTaskResultTool(self.runtime_engine)
        self.get_content = GetContentTool(self.runtime_engine.content_manager)
        self.get_statistics = GetStatisticsTool(self.runtime_engine)

    def define_semantic_router(self, indexed_servers_msg: str):
        @self.mcp.tool(
            name="semantic_router",
            description=f"""
Universal gateway to the MCP Runtime ecosystem. Execute any MCP operation through a single unified interface.

OPERATIONS & PARAMETERS:

- search_tools
  Required: query
  Optional: limit, min_score, server_names, tool_type, enabled
  Discover tools using natural language queries with semantic ranking

- search_servers
  Required: query
  Optional: limit, min_score
  Search for servers using natural language queries

- get_server_info
  Required: server_name
  View detailed server capabilities, limitations, and tool count

- get_server_tools
  Required: server_name
  Optional: limit, offset
  List all tools available on a specific server (lightweight, no schemas)

- get_tool_details
  Required: server_name, tool_name
  Get complete tool schema and description before execution

- list_servers
  Optional: limit, offset
  List all registered servers with pagination

- manage_server
  Required: server_name, action
  Start or shutdown MCP server sessions (action: 'start' or 'shutdown')

- list_running_servers
  No parameters required
  Show currently active server sessions ready for tool execution

- execute_tool
  Required: server_name, tool_name
  Optional: arguments, timeout, in_background, priority
  Run tools on active servers with optional background execution support

- poll_task_result
  Required: task_id
  Check status and retrieve results of background tasks

- get_content
  Required: ref_id
  Optional: chunk_index
  Retrieve offloaded content (large text chunks, images) by reference ID

- get_statistics
  No parameters required
  Get total counts of servers and tools from the discovery service

WORKFLOW:
1. DISCOVER: search_tools(query) → find relevant tools
2. EXPLORE: get_server_info(server) → understand capabilities
3. UNDERSTAND: get_tool_details(server, tool) → get full schema
4. START: manage_server(server, 'start') → start the server
5. EXECUTE: execute_tool(server, tool, args) → run the tool
6. CLEANUP: manage_server(server, 'shutdown') → stop when done

BEST PRACTICES:
1. ALWAYS use get_tool_details before execute_tool - never execute without checking the schema first!
2. PREFER search_tools over list_servers for discovery - it's more efficient and finds relevant tools faster
3. START with search_tools to discover what you need - don't browse blindly through all tools
4. VERIFY server is running with list_running_servers before execute_tool, or start it with manage_server
5. FOR background tasks: always save the task_id and poll with poll_task_result to get results
6. CHECK server capabilities with get_server_info to understand limitations before heavy usage
7. FOR search: write clear, descriptive queries with full context (e.g., "tools for reading PDF documents")
8. ONLY 'operation' parameter is required. Other parameters depend on the chosen operation.
9. WHEN tool results show [Reference: ref_id], use get_content to retrieve full content. For chunked text, use chunk_index.

CONTENT RULES:
- Large tool results are automatically offloaded and replaced with references
- When you see [Reference: uuid], use get_content(ref_id="uuid") to retrieve
- For chunked text, use chunk_index parameter to retrieve specific chunks
- Images are stored as base64, retrievable via get_content

-----------------------
LIST OF INDEXED SERVERS
-----------------------
{indexed_servers_msg}
"""
        )
        async def semantic_router(
            operation: Annotated[
                Literal[
                    "search_tools",
                    "search_servers",
                    "get_server_info",
                    "get_server_tools",
                    "get_tool_details",
                    "list_servers",
                    "manage_server",
                    "list_running_servers",
                    "execute_tool",
                    "poll_task_result",
                    "get_content",
                    "get_statistics"
                ],
                "The operation to perform in the MCP ecosystem"
            ],
            # Search parameters
            query: Annotated[str, "Natural language search query for finding servers or tools"] = None,
            limit: Annotated[int, "Maximum number of results to return (default: 10 for search, 50 for list)"] = 10,
            min_score: Annotated[float, "Minimum similarity score 0.0-1.0 (default: 0.3)"] = 0.3,
            # Server/tool identification parameters
            server_name: Annotated[str, "Name of the MCP server to operate on"] = None,
            server_names: Annotated[List[str], "List of server names to filter tool search results"] = None,
            tool_name: Annotated[str, "Name of the tool to retrieve details or execute"] = None,
            tool_type: Annotated[str, "Filter by type: 'app', 'mcp', 'custom', 'base'"] = None,
            enabled: Annotated[bool, "Filter by enabled status (default: True, only enabled tools)"] = True,
            # Pagination parameters
            offset: Annotated[int, "Pagination offset for retrieving next page of results"] = 0,
            # Server management parameters
            action: Annotated[Literal["start", "shutdown"], "Server lifecycle action: 'start' to launch, 'shutdown' to terminate"] = "start",
            # Tool execution parameters
            arguments: Annotated[Dict[str, Any], "Tool-specific arguments as a dictionary matching the tool's schema"] = None,
            timeout: Annotated[float, "Maximum execution time in seconds (default: 60)"] = 60.0,
            in_background: Annotated[bool, "Execute tool asynchronously and return task ID immediately (default: False)"] = False,
            priority: Annotated[int, "Background task priority, lower numbers run first (default: 1)"] = 1,
            # Background task parameters
            task_id: Annotated[str, "Task identifier for polling background execution status"] = None,
            # Content retrieval parameters
            ref_id: Annotated[str, "Reference ID for retrieving offloaded content"] = None,
            chunk_index: Annotated[int, "Specific chunk index to retrieve (for large text content)"] = None,
        ) -> ToolResult:
            try:
                match operation:
                    case "search_tools":
                        if query is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'query' is required for search_tools")]
                            )
                        return await self.search_tools(
                            query=query,
                            limit=limit,
                            min_score=min_score,
                            server_names=server_names,
                            tool_type=tool_type,
                            enabled=enabled
                        )

                    case "search_servers":
                        if query is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'query' is required for search_servers")]
                            )
                        return await self.search_servers(
                            query=query,
                            limit=limit,
                            min_score=min_score
                        )

                    case "get_server_info":
                        if server_name is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'server_name' is required for get_server_info")]
                            )
                        return await self.get_server_info(server_name=server_name)

                    case "get_server_tools":
                        if server_name is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'server_name' is required for get_server_tools")]
                            )
                        return await self.get_server_tools(
                            server_name=server_name,
                            limit=limit if limit != 10 else 50,
                            offset=offset
                        )

                    case "get_tool_details":
                        if server_name is None or tool_name is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'server_name' and 'tool_name' are required for get_tool_details")]
                            )
                        return await self.get_tool_details(
                            server_name=server_name,
                            tool_name=tool_name
                        )

                    case "list_servers":
                        return await self.list_servers(
                            limit=limit if limit != 10 else 50,
                            offset=offset
                        )

                    case "manage_server":
                        if server_name is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'server_name' is required for manage_server")]
                            )
                        return await self.manage_server(
                            server_name=server_name,
                            action=action
                        )

                    case "list_running_servers":
                        return await self.list_running_servers()

                    case "execute_tool":
                        if server_name is None or tool_name is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'server_name' and 'tool_name' are required for execute_tool")]
                            )
                        return await self.execute_tool(
                            server_name=server_name,
                            tool_name=tool_name,
                            arguments=arguments,
                            timeout=timeout,
                            in_background=in_background,
                            priority=priority
                        )

                    case "poll_task_result":
                        if task_id is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'task_id' is required for poll_task_result")]
                            )
                        return await self.poll_task_result(task_id=task_id)

                    case "get_content":
                        if ref_id is None:
                            return ToolResult(
                                content=[TextContent(type="text", text="Error: 'ref_id' is required for get_content")]
                            )
                        return await self.get_content(ref_id=ref_id, chunk_index=chunk_index)

                    case "get_statistics":
                        return await self.get_statistics()

                    case _:
                        return ToolResult(
                            content=[TextContent(type="text", text=f"Unknown operation: {operation}")]
                        )

            except Exception as e:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Router failed: {str(e)}")]
                )

    def run(self, transport: str = "stdio", host: str = "0.0.0.0", port: int = 8001):
        if transport == "stdio":
            self.mcp.run()
        else:
            self.mcp.run(transport=transport, host=host, port=port)

    async def run_async(self, transport: str = "stdio", host: str = "0.0.0.0", port: int = 8001):
        if transport == "stdio":
            await self.mcp.run_async(transport="stdio")
        else:
            await self.mcp.run_async(transport=transport, host=host, port=port)
