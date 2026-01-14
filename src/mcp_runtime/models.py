from pydantic import BaseModel, model_validator
from typing import Optional, List, Dict, Any


class McpStartupConfig(BaseModel):
    server_name: str
    transport: str = "stdio"
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = {}
    url: Optional[str] = None
    headers: Dict[str, str] = {}
    timeout: float = 30.0

    @model_validator(mode='after')
    def validate_transport(self):
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio transport requires 'command'")
        if self.transport == "http" and not self.url:
            raise ValueError("http transport requires 'url'")
        return self


class ServerInfo(BaseModel):
    server_name: str
    title: str
    summary: str
    capabilities: List[str] = []
    limitations: List[str] = []
    nb_tools: int = 0


class ToolInfo(BaseModel):
    tool_name: str
    tool_description: str
    tool_schema: Dict[str, Any] = {}
    server_name: str


class SearchResultTool(BaseModel):
    tool_id: str
    tool_name: str
    tool_description: str
    tool_schema: Dict[str, Any] = {}
    server_name: str
    score: float


class SearchResultServer(BaseModel):
    server_id: str
    server_name: str
    title: str
    summary: str
    capabilities: List[str] = []
    limitations: List[str] = []
    nb_tools: int = 0
    score: float
