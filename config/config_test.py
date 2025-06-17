"""
ClickHouse Database connection configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Database connection parameters
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', '172.20.157.162'),
    'port': int(os.getenv('CLICKHOUSE_PORT', '8123')),
    'database': os.getenv('CLICKHOUSE_DB', 'default'),
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
    'secure': False,  # Set to True if using HTTPS
}