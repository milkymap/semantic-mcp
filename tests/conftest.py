import pytest
from unittest.mock import AsyncMock

from mcpruntime.settings import RuntimeSettings
from mcpruntime.services.discovery_client import DiscoveryClient


@pytest.fixture
def settings():
    return RuntimeSettings(
        DISCOVERY_URL="http://localhost:8000",
        TOOL_OFFLOADED_DATA_PATH="/tmp/test_offloaded"
    )


@pytest.fixture
def mock_discovery_client():
    client = AsyncMock(spec=DiscoveryClient)
    client.search_tools = AsyncMock(return_value={"tools": [], "total_results": 0})
    client.search_servers = AsyncMock(return_value={"servers": [], "total_results": 0})
    client.get_statistics = AsyncMock(return_value={"total_servers": 0, "total_tools": 0})
    return client
