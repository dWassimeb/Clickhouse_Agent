"""
Configuration settings for the ClickHouse Agent.
"""

from pydantic import BaseModel
from typing import Optional

class ClickHouseConfig(BaseModel):
    host: str = "172.20.157.162"
    port: int = 8123
    database: str = "default"
    username: str = "default"
    password: Optional[str] = "default123!"  # Empty string instead of None

    @property
    def connection_params(self) -> dict:
        """For backward compatibility, though we're using clickhouse-connect now."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password or ""
        }

# Global configuration instance
CLICKHOUSE_CONFIG = ClickHouseConfig()