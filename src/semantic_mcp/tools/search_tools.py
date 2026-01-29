import json
from typing import List, Optional

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


def _minimize_tool_response(tools: List[dict]) -> List[dict]:
    """Keep only essential fields to reduce context size"""
    essential_fields = {"name", "serverName", "description", "title", "score"}
    return [
        {k: v for k, v in tool.items() if k in essential_fields}
        for tool in tools
    ]


class SearchToolsTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.3,
        server_names: Optional[List[str]] = None,
        tool_type: Optional[str] = None,
        enabled: Optional[bool] = True
    ) -> ToolResult:
        try:
            result = await self.engine.discovery_client.search_tools(
                query=query,
                limit=limit,
                min_score=min_score,
                server_names=server_names,
                tool_type=tool_type,
                enabled=enabled
            )
            if "tools" in result:
                result["tools"] = _minimize_tool_response(result["tools"])

            result_text = f"Found {len(result.get('tools', []))} tools for query: '{query}'"
            if tool_type:
                result_text += f" (type: {tool_type})"

            guidance = "Next steps:\n"
            guidance += "- Use get_tool_details to see full schema before execution\n"
            guidance += "- Use get_server_info to see server capabilities\n"
            guidance += "- Use manage_server to start a server before executing tools"

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
