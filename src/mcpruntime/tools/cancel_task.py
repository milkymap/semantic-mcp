import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class CancelTaskTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self, task_id: str) -> ToolResult:
        try:
            success, message = await self.engine.cancel_task(task_id)

            if success:
                return ToolResult(
                    content=[
                        TextContent(type="text", text=message),
                        TextContent(type="text", text=json.dumps({"status": "cancelled", "task_id": task_id}, indent=2))
                    ]
                )

            return ToolResult(
                content=[TextContent(type="text", text=f"Cancel failed: {message}")]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to cancel task: {str(e)}")]
            )
