import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class PollTaskResultTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self, task_id: str) -> ToolResult:
        try:
            is_done, result, error = await self.engine.poll_task_result(task_id)

            if error:
                return ToolResult(
                    content=[TextContent(type="text", text=f"Task error: {error}")]
                )

            if is_done:
                return ToolResult(
                    content=[
                        TextContent(type="text", text=f"Task '{task_id}' completed"),
                        TextContent(type="text", text=json.dumps({"status": "completed", "result": result}, indent=2))
                    ]
                )

            return ToolResult(
                content=[
                    TextContent(type="text", text=f"Task '{task_id}' still running"),
                    TextContent(type="text", text=json.dumps({"status": "running"}, indent=2)),
                    TextContent(type="text", text="Next: Poll again after a short delay")
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Failed to poll task: {str(e)}")]
            )
