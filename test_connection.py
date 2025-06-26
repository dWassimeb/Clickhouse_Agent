"""
Test ClickHouse connection with the updated configuration
"""

try:
    from database.clickhouse.connection import clickhouse_connection

    if clickhouse_connection.test_connection():
        print("✅ ClickHouse connection successful!")
    else:
        print("❌ ClickHouse connection failed!")
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("\nTrying alternative import...")

try:
    # Alternative test without existing connection module
    import clickhouse_connect
    from config.settings import CLICKHOUSE_CONFIG

    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_CONFIG.host,
        port=CLICKHOUSE_CONFIG.port,
        username=CLICKHOUSE_CONFIG.username,
        password=CLICKHOUSE_CONFIG.password or '',
        database=CLICKHOUSE_CONFIG.database
    )

    # Test connection
    result = client.query("SELECT 1")
    print("✅ ClickHouse connection successful (direct test)!")
    print(f"Connected to: {CLICKHOUSE_CONFIG.host}:{CLICKHOUSE_CONFIG.port}")

except Exception as e2:
    print(f"❌ Direct connection also failed: {e2}")
    print("Please check:")
    print("1. ClickHouse server is running")
    print("2. Network connectivity")
    print("3. clickhouse-connect is installed: pip install clickhouse-connect")

