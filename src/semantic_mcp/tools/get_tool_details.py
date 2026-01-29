import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class GetToolDetailsTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self, server_name: str, tool_name: str) -> ToolResult:
        try:
            info = await self.engine.discovery_client.get_tool_details(server_name, tool_name)
            result = info.model_dump()

            guidance = "Next steps:\n"
            guidance += f"- Use manage_server('{server_name}', 'start') to start the server\n"
            guidance += f"- Use execute_tool('{server_name}', '{tool_name}', arguments) to run the tool\n"
            guidance += "- Ensure arguments match the schema above"

            return ToolResult(
                content=[
                    TextContent(type="text", text=f"Tool details for '{tool_name}' on '{server_name}':"),
                    TextContent(type="text", text=json.dumps(result, indent=2)),
                    TextContent(type="text", text=guidance)
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to get tool details: {str(e)}")]
            )
