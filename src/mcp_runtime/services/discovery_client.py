from typing import Optional, List, Self, Dict
import httpx

from ..log import logger
from ..models import McpStartupConfig, ServerInfo, ToolInfo


class DiscoveryClient:

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        encryption_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.encryption_key = encryption_key
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    def _auth_headers(self) -> Dict[str, str]:
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _auth_headers_with_encryption(self) -> Dict[str, str]:
        headers = self._auth_headers()
        if self.encryption_key:
            headers["X-Encryption-Key"] = self.encryption_key
        return headers

    async def __aenter__(self) -> Self:
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def search_tools(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.7,
        server_names: Optional[List[str]] = None
    ) -> dict:
        payload = {"query": query, "limit": limit, "min_score": min_score}
        if server_names:
            payload["server_names"] = server_names

        response = await self.client.post(
            f"{self.base_url}/api/mcp/tools/search",
            json=payload,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return response.json()

    async def search_servers(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.7
    ) -> dict:
        response = await self.client.post(
            f"{self.base_url}/api/mcp/servers/search",
            json={"query": query, "limit": limit, "min_score": min_score},
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return response.json()

    async def get_server_info(self, server_name: str) -> ServerInfo:
        response = await self.client.get(
            f"{self.base_url}/api/mcp/servers/{server_name}",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        data = response.json()
        return ServerInfo(**data.get("server", data))

    async def get_startup_config(self, server_name: str) -> McpStartupConfig:
        response = await self.client.get(
            f"{self.base_url}/api/mcp/servers/{server_name}/command",
            headers=self._auth_headers_with_encryption()
        )
        response.raise_for_status()
        return McpStartupConfig(**response.json())

    async def get_server_tools(
        self,
        server_name: str,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        response = await self.client.get(
            f"{self.base_url}/api/mcp/servers/{server_name}/tools",
            params={"limit": limit, "offset": offset},
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return response.json()

    async def get_tool_details(self, server_name: str, tool_name: str) -> ToolInfo:
        response = await self.client.get(
            f"{self.base_url}/api/mcp/servers/{server_name}/tools/{tool_name}",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        data = response.json()
        return ToolInfo(
            tool_name=data["tool_name"],
            tool_description=data["tool_description"],
            tool_schema=data.get("tool_schema", {}),
            server_name=data["server_name"]
        )

    async def list_servers(self, limit: int = 50, offset: int = 0) -> dict:
        response = await self.client.get(
            f"{self.base_url}/api/mcp/servers",
            params={"limit": limit, "offset": offset},
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return response.json()

    async def get_statistics(self) -> dict:
        response = await self.client.get(
            f"{self.base_url}/api/mcp/statistics",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return response.json()
