import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class GetServerInfoTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self, server_name: str) -> ToolResult:
        try:
            info = await self.engine.discovery_client.get_server_info(server_name)
            result = info.model_dump()

            guidance = "Next steps:\n"
            guidance += f"- Use get_server_tools('{server_name}') to see available tools\n"
            guidance += f"- Use manage_server('{server_name}', 'start') to start the server\n"
            guidance += "- Use search_tools to find specific tools on this server"

            return ToolResult(
                content=[
                    TextContent(type="text", text=f"Server info for '{server_name}':"),
                    TextContent(type="text", text=json.dumps(result, indent=2)),
                    TextContent(type="text", text=guidance)
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to get server info: {str(e)}")]
            )
