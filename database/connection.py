"""
ClickHouse database connection management using clickhouse-connect.
"""

import clickhouse_connect
from typing import Optional, Dict, Any, List
import logging
from config.settings import CLICKHOUSE_CONFIG

logger = logging.getLogger(__name__)

class ClickHouseConnection:
    """Manages ClickHouse database connections using clickhouse-connect."""

    def __init__(self):
        self.client: Optional[clickhouse_connect.driver.Client] = None
        self._is_connected = False

    def _connect(self) -> None:
        """Establish connection to ClickHouse."""
        if self._is_connected and self.client:
            return

        try:
            self.client = clickhouse_connect.get_client(
                host=CLICKHOUSE_CONFIG.host,
                port=CLICKHOUSE_CONFIG.port,
                username=CLICKHOUSE_CONFIG.username,
                password=CLICKHOUSE_CONFIG.password or '',
                database=CLICKHOUSE_CONFIG.database
            )

            # Test connection
            self.client.query("SELECT 1")
            self._is_connected = True
            logger.info("Successfully connected to ClickHouse")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            self._is_connected = False
            raise

    def execute_query_with_names(self, query: str) -> Dict[str, Any]:
        """Execute query and return results with column names."""
        # Ensure connection before executing
        if not self._is_connected:
            self._connect()

        if not self.client:
            raise Exception("No ClickHouse connection available")

        try:
            logger.info(f"Executing query: {query}")

            # Execute query and get result
            result = self.client.query(query)

            # Get column names and data
            columns = result.column_names
            data = result.result_rows

            # Get column types
            types = [str(col_type) for col_type in result.column_types]

            logger.info(f"Query executed successfully, returned {len(data)} rows")

            return {
                "columns": columns,
                "data": data,
                "types": types
            }
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            # Reset connection flag on error
            self._is_connected = False
            raise

    def test_connection(self) -> bool:
        """Test if connection is alive."""
        try:
            if not self._is_connected:
                self._connect()
            if self.client:
                self.client.query("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            self._is_connected = False
        return False

    def close(self) -> None:
        """Close the connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("ClickHouse connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.client = None
                self._is_connected = False

# Global connection instance (lazy initialization)
clickhouse_connection = ClickHouseConnection()