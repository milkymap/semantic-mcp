import pytest
import respx
from httpx import Response

from mcpruntime.services.discovery_client import DiscoveryClient


@pytest.mark.asyncio
async def test_search_tools():
    with respx.mock:
        respx.post("http://test:8000/api/mcp/tools/search").mock(
            return_value=Response(200, json={
                "tools": [{"tool_name": "test", "server_name": "test_server", "score": 0.9}],
                "total_results": 1
            })
        )

        async with DiscoveryClient("http://test:8000") as client:
            result = await client.search_tools("test query")
            assert result["total_results"] == 1
            assert result["tools"][0]["tool_name"] == "test"


@pytest.mark.asyncio
async def test_get_startup_config():
    with respx.mock:
        respx.get("http://test:8000/api/mcp/servers/filesystem/command").mock(
            return_value=Response(200, json={
                "server_name": "filesystem",
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@mcp/filesystem"],
                "env": {},
                "url": None,
                "headers": {}
            })
        )

        async with DiscoveryClient("http://test:8000") as client:
            config = await client.get_startup_config("filesystem")
            assert config.server_name == "filesystem"
            assert config.command == "npx"
            assert config.transport == "stdio"


@pytest.mark.asyncio
async def test_get_statistics():
    with respx.mock:
        respx.get("http://test:8000/api/mcp/statistics").mock(
            return_value=Response(200, json={"total_servers": 10, "total_tools": 100})
        )

        async with DiscoveryClient("http://test:8000") as client:
            stats = await client.get_statistics()
            assert stats["total_servers"] == 10
            assert stats["total_tools"] == 100


@pytest.mark.asyncio
async def test_auth_headers():
    with respx.mock:
        route = respx.get("http://test:8000/api/mcp/statistics").mock(
            return_value=Response(200, json={"total_servers": 0, "total_tools": 0})
        )

        async with DiscoveryClient("http://test:8000", api_key="test-key") as client:
            await client.get_statistics()
            assert route.calls[0].request.headers["Authorization"] == "Bearer test-key"


@pytest.mark.asyncio
async def test_encryption_header_on_command():
    with respx.mock:
        route = respx.get("http://test:8000/api/mcp/servers/test/command").mock(
            return_value=Response(200, json={
                "server_name": "test",
                "transport": "stdio",
                "command": "test",
                "args": [],
                "env": {},
                "url": None,
                "headers": {}
            })
        )

        async with DiscoveryClient(
            "http://test:8000",
            api_key="test-key",
            encryption_key="enc-key"
        ) as client:
            await client.get_startup_config("test")
            headers = route.calls[0].request.headers
            assert headers["Authorization"] == "Bearer test-key"
            assert headers["X-Encryption-Key"] == "enc-key"
