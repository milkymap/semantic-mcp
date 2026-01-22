import json
from typing import List

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


def _minimize_tool_response(tools: List[dict]) -> List[dict]:
    """Keep only essential fields to reduce context size"""
    essential_fields = {"name", "serverName", "description", "title"}
    return [
        {k: v for k, v in tool.items() if k in essential_fields}
        for tool in tools
    ]


class GetServerToolsTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(
        self,
        server_name: str,
        limit: int = 50,
        offset: int = 0
    ) -> ToolResult:
        try:
            result = await self.engine.discovery_client.get_server_tools(
                server_name=server_name,
                limit=limit,
                offset=offset
            )
            if "tools" in result:
                result["tools"] = _minimize_tool_response(result["tools"])

            tools_count = len(result.get("tools", []))
            result_text = f"Found {tools_count} tools on server '{server_name}'"

            guidance = "Next steps:\n"
            guidance += "- Use get_tool_details to see full schema before execution\n"
            guidance += f"- Use manage_server('{server_name}', 'start') to start the server\n"
            guidance += "- Use execute_tool to run a tool after starting the server"

            return ToolResult(
                content=[
                    TextContent(type="text", text=result_text),
                    TextContent(type="text", text=json.dumps(result, indent=2)),
                    TextContent(type="text", text=guidance)
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to get server tools: {str(e)}")]
            )
