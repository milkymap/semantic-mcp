import json
from typing import List

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


def _minimize_server_response(servers: List[dict]) -> List[dict]:
    """Keep only essential fields to reduce context size"""
    essential_fields = {"name", "title", "nbTools", "score"}
    return [
        {k: v for k, v in server.items() if k in essential_fields}
        for server in servers
    ]


class SearchServersTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.3
    ) -> ToolResult:
        try:
            result = await self.engine.discovery_client.search_servers(
                query=query,
                limit=limit,
                min_score=min_score
            )

            if "servers" in result:
                result["servers"] = _minimize_server_response(result["servers"])

            result_text = f"Found {len(result.get('servers', []))} servers for query: '{query}'"

            guidance = "Next steps:\n"
            guidance += "- Use get_server_info to see detailed capabilities\n"
            guidance += "- Use get_server_tools to list all tools on a server\n"
            guidance += "- Use search_tools to find specific tools across servers"

            return ToolResult(
                content=[
                    TextContent(type="text", text=result_text),
                    TextContent(type="text", text=json.dumps(result, indent=2)),
                    TextContent(type="text", text=guidance)
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Search failed: {str(e)}")]
            )
