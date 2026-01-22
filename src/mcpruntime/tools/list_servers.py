import json
from typing import List

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


def _minimize_server_response(servers: List[dict]) -> List[dict]:
    """Keep only essential fields to reduce context size"""
    essential_fields = {"name", "title", "nbTools"}
    return [
        {k: v for k, v in server.items() if k in essential_fields}
        for server in servers
    ]


class ListServersTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self, limit: int = 50, offset: int = 0) -> ToolResult:
        try:
            result = await self.engine.discovery_client.list_servers(
                limit=limit,
                offset=offset
            )

            if "servers" in result:
                result["servers"] = _minimize_server_response(result["servers"])

            servers_count = len(result.get("servers", []))
            result_text = f"Listed {servers_count} servers"

            guidance = "Next steps:\n"
            guidance += "- Use get_server_info to see detailed capabilities\n"
            guidance += "- Use get_server_tools to list tools on a specific server\n"
            guidance += "- Use search_tools for semantic search across all servers"

            return ToolResult(
                content=[
                    TextContent(type="text", text=result_text),
                    TextContent(type="text", text=json.dumps(result, indent=2)),
                    TextContent(type="text", text=guidance)
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to list servers: {str(e)}")]
            )
