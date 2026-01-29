import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class ListRunningServersTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self) -> ToolResult:
        try:
            running_servers = self.engine.list_running_servers()

            if running_servers:
                result_text = f"Currently running {len(running_servers)} server(s)"
                guidance = "Next steps:\n"
                guidance += "- Use execute_tool to run tools on any running server\n"
                guidance += "- Use manage_server(server_name, 'shutdown') to stop a server\n"
                guidance += "- Use get_server_tools to see available tools on a server"
            else:
                result_text = "No servers currently running"
                guidance = "Next steps:\n"
                guidance += "- Use manage_server(server_name, 'start') to start a server\n"
                guidance += "- Use search_tools to find relevant tools first"

            return ToolResult(
                content=[
                    TextContent(type="text", text=result_text),
                    TextContent(type="text", text=json.dumps({"running_servers": running_servers}, indent=2)),
                    TextContent(type="text", text=guidance)
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to list running servers: {str(e)}")]
            )
