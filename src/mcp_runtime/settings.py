from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DISCOVERY_URL: str = "http://localhost:8000"
    DISCOVERY_API_KEY: Optional[str] = None
    DISCOVERY_ENCRYPTION_KEY: Optional[str] = None

    TOOL_OFFLOADED_DATA_PATH: str = "/tmp/mcp_offloaded"
    MAX_RESULT_TOKENS: int = 4096
    DESCRIBE_IMAGES: bool = True

    BACKGROUND_QUEUE_SIZE: int = 100
    BACKGROUND_QUEUE_MAX_SUBSCRIBERS: int = 4

    OPENAI_API_KEY: Optional[str] = None
    VISION_MODEL_NAME: str = "gpt-4.1-mini"
    MCP_SERVER_POLLING_INTERVAL_MS: int = 1000
