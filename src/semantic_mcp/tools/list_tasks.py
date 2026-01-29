import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class ListTasksTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self) -> ToolResult:
        try:
            tasks = self.engine.list_tasks()

            if not tasks:
                return ToolResult(
                    content=[
                        TextContent(type="text", text="No background tasks"),
                        TextContent(type="text", text=json.dumps({"tasks": []}, indent=2))
                    ]
                )

            return ToolResult(
                content=[
                    TextContent(type="text", text=f"Found {len(tasks)} background task(s)"),
                    TextContent(type="text", text=json.dumps({"tasks": tasks}, indent=2))
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to list tasks: {str(e)}")]
            )
