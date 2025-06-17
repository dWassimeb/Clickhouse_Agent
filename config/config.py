"""
Configuration module for the ClickHouse Agent.
Loads environment variables and provides configuration settings.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class ClickHouseConfig(BaseModel):
    """ClickHouse database connection configuration."""
    host: str = os.getenv("CLICKHOUSE_HOST", "172.20.157.162")
    port: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    database: str = os.getenv("CLICKHOUSE_DB", "Default")
    user: str = os.getenv("CLICKHOUSE_USER", "default")
    password: str = os.getenv("CLICKHOUSE_PASSWORD", "")

class LLMConfig(BaseModel):
    """LLM API configuration."""
    api_key: str = os.getenv("GPT_API_KEY", "2b24fef721d14c94a333ab2e4f686f40")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o")
    model_version: str = os.getenv("MODEL_VERSION", "2024-02-01")

# Create config instances
clickhouse_config = ClickHouseConfig()
llm_config = LLMConfig()