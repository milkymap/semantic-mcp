import json

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class PollTaskResultTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(self, task_id: str) -> ToolResult:
        try:
            status, result, error = await self.engine.poll_task_result(task_id)

            if status == "not_found":
                return ToolResult(
                    content=[
                        TextContent(type="text", text=f"Task '{task_id}' not found"),
                        TextContent(type="text", text=json.dumps({"status": "not_found", "error": error}, indent=2))
                    ]
                )

            if status == "failed":
                return ToolResult(
                    content=[
                        TextContent(type="text", text=f"Task '{task_id}' failed"),
                        TextContent(type="text", text=json.dumps({"status": "failed", "error": error}, indent=2))
                    ]
                )

            if status == "completed":
                return ToolResult(
                    content=[
                        TextContent(type="text", text=f"Task '{task_id}' completed"),
                        TextContent(type="text", text=json.dumps({"status": "completed", "result": result}, indent=2))
                    ]
                )

            # status == "running"
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
