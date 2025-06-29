"""
Test script to check database connectivity and session saving
"""

import os
import json
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_database_connection():
    """Test database connection in isolation."""
    print("🔌 Testing Database Connection...")

    try:
        from database.connection import clickhouse_connection

        print("  📦 Database module imported successfully")

        # Test connection
        if clickhouse_connection.test_connection():
            print("  ✅ Database connection successful")

            # Test simple query
            result = clickhouse_connection.execute_query_with_names("SELECT 1 as test")
            if result and result.get('data'):
                print(f"  ✅ Simple query successful: {result['data'][0]}")
                return True
            else:
                print("  ❌ Simple query failed")
                return False
        else:
            print("  ❌ Database connection failed")
            return False

    except Exception as e:
        print(f"  ❌ Database test error: {e}")
        import traceback
        print(f"  📄 Full traceback:")
        traceback.print_exc()
        return False

def test_network_connectivity():
    """Test network connectivity to ClickHouse server."""
    print("\n🌐 Testing Network Connectivity...")

    import socket

    try:
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('172.20.157.162', 8123))
        sock.close()

        if result == 0:
            print("  ✅ TCP connection to 172.20.157.162:8123 successful")
            return True
        else:
            print(f"  ❌ TCP connection failed with code: {result}")
            return False

    except Exception as e:
        print(f"  ❌ Network test error: {e}")
        return False

def test_http_connectivity():
    """Test HTTP connectivity to ClickHouse."""
    print("\n🌐 Testing HTTP Connectivity...")

    try:
        import urllib.request
        import urllib.error

        # Test HTTP connection
        url = "http://172.20.157.162:8123/"
        request = urllib.request.Request(url)

        try:
            response = urllib.request.urlopen(request, timeout=5)
            content = response.read()
            print(f"  ✅ HTTP connection successful, status: {response.getcode()}")
            print(f"  📄 Response length: {len(content)} bytes")
            return True
        except urllib.error.URLError as e:
            print(f"  ❌ HTTP connection failed: {e}")
            return False

    except Exception as e:
        print(f"  ❌ HTTP test error: {e}")
        return False

def test_session_saving():
    """Test session file creation and saving."""
    print("\n💾 Testing Session Saving...")

    try:
        # Create data directory
        os.makedirs("data", exist_ok=True)
        print("  📁 Data directory created/verified")

        # Test writing to sessions file
        sessions_file = "data/chat_sessions.json"
        test_data = {
            "test_session": {
                "title": "Test Session",
                "messages": [
                    {"role": "user", "content": "test message", "timestamp": datetime.now().isoformat()}
                ],
                "timestamp": datetime.now().isoformat(),
                "user": "test_user"
            }
        }

        # Write test data
        with open(sessions_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        print("  ✅ Successfully wrote test session data")

        # Read test data back
        with open(sessions_file, 'r') as f:
            loaded_data = json.load(f)

        if loaded_data == test_data:
            print("  ✅ Successfully read session data back")

            # Check file permissions
            stat = os.stat(sessions_file)
            print(f"  📄 File size: {stat.st_size} bytes")
            print(f"  🔒 File permissions: {oct(stat.st_mode)[-3:]}")

            return True
        else:
            print("  ❌ Data mismatch when reading back")
            return False

    except Exception as e:
        print(f"  ❌ Session saving test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all connectivity tests."""
    print("🔮 Telmi Connectivity Test")
    print("=" * 50)

    results = {
        "Network": test_network_connectivity(),
        "HTTP": test_http_connectivity(),
        "Database": test_database_connection(),
        "Session Saving": test_session_saving()
    }

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")

    if all(results.values()):
        print("\n🎉 All tests passed!")
        print("💡 The issue might be in the Streamlit environment or agent configuration.")
    else:
        print("\n⚠️ Some tests failed.")

        if not results["Network"]:
            print("💡 Network issue: Check if ClickHouse server is running and accessible")
            print("   Try: ping 172.20.157.162")
        elif not results["HTTP"]:
            print("💡 HTTP issue: ClickHouse HTTP interface might not be enabled")
            print("   Check ClickHouse configuration")
        elif not results["Database"]:
            print("💡 Database issue: Check ClickHouse connection parameters")
        elif not results["Session Saving"]:
            print("💡 File system issue: Check permissions on data/ directory")

if __name__ == "__main__":
    main()