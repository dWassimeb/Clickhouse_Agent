# Create test_connection.py
from database.connection import clickhouse_connection

try:
    if clickhouse_connection.test_connection():
        print("✅ ClickHouse connection successful!")
    else:
        print("❌ ClickHouse connection failed!")
except Exception as e:
    print(f"❌ Connection error: {e}")