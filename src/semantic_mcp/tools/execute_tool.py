import json
from typing import Optional, Dict, Any

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..runtime_engine import RuntimeEngine


class ExecuteToolTool:
    def __init__(self, runtime_engine: RuntimeEngine):
        self.engine = runtime_engine

    async def __call__(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: float = 60,
        in_background: bool = False,
        priority: int = 1
    ) -> ToolResult:
        try:
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            result = await self.engine.execute_tool(
                server_name=server_name,
                tool_name=tool_name,
                arguments=arguments,
                timeout=timeout,
                in_background=in_background,
                priority=priority
            )

            if in_background:
                return ToolResult(
                    content=[
                        TextContent(type="text", text=f"Tool '{tool_name}' queued for background execution"),
                        TextContent(type="text", text=json.dumps({"result": result}, indent=2)),
                        TextContent(type="text", text="Next: Use poll_task_result with the task_id to check status")
                    ]
                )

            return ToolResult(
                content=[
                    TextContent(type="text", text=f"Tool '{tool_name}' executed successfully"),
                    TextContent(type="text", text=json.dumps({"success": True, "result": result}, indent=2))
                ]
            )
        except Exception as e:
            return ToolResult(
                content=[TextContent(type="text", text=f"Execution failed: {str(e)}")]
            )
