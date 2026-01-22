import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class GetStatisticsTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self) -> ToolResult:
        try:
            stats = await self.engine.discovery_client.get_statistics()

            guidance = "Next steps:\n"
            guidance += "- Use search_tools to find relevant tools\n"
            guidance += "- Use list_servers to browse all registered servers"

            return ToolResult(
                content=[
                    TextContent(type="text", text="MCP Runtime Statistics:"),
                    TextContent(type="text", text=json.dumps(stats, indent=2)),
                    TextContent(type="text", text=guidance)
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to get statistics: {str(e)}")]
            )
