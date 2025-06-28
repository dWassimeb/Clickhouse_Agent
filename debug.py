#!/usr/bin/env python3
"""
Debug Tool for Telmi LangGraph Agent
Test individual components and workflow steps
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_imports():
    """Test all required imports."""
    print("🧪 Testing Imports...")

    try:
        from core.agent import ClickHouseGraphAgent
        print("✅ Core agent import successful")
    except Exception as e:
        print(f"❌ Core agent import failed: {e}")
        return False

    try:
        from database.connection import clickhouse_connection
        print("✅ Database connection import successful")
    except Exception as e:
        print(f"❌ Database connection import failed: {e}")
        return False

    try:
        from tools.smart_intent_analyzer_tool import SmartIntentAnalyzerTool
        from tools.smart_sql_generator_tool import SmartSqlGeneratorTool
        from tools.query_execution_tool import QueryExecutionTool
        print("✅ All tools import successful")
    except Exception as e:
        print(f"❌ Tools import failed: {e}")
        return False

    return True

def test_database():
    """Test database connection."""
    print("\n🔌 Testing Database Connection...")

    try:
        from database.connection import clickhouse_connection

        if clickhouse_connection.test_connection():
            print("✅ Database connection successful")

            # Test a simple query
            result = clickhouse_connection.execute_query_with_names("SELECT 1 as test")
            if result and result.get('data'):
                print(f"✅ Simple query test successful: {result['data'][0]}")
                return True
            else:
                print("❌ Simple query failed")
                return False
        else:
            print("❌ Database connection failed")
            return False

    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_individual_tools():
    """Test each tool individually."""
    print("\n🛠️ Testing Individual Tools...")

    # Test Intent Analyzer
    try:
        from tools.smart_intent_analyzer_tool import SmartIntentAnalyzerTool
        intent_tool = SmartIntentAnalyzerTool()

        print("Testing Intent Analyzer...")
        result = intent_tool._run("Show me top 5 customers")

        if result.get('success'):
            print("✅ Intent Analyzer working")
        else:
            print(f"❌ Intent Analyzer failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Intent Analyzer test failed: {e}")
        return False

    # Test SQL Generator
    try:
        from tools.smart_sql_generator_tool import SmartSqlGeneratorTool
        sql_tool = SmartSqlGeneratorTool()

        print("Testing SQL Generator...")
        # Simple intent data for testing
        intent_data = {
            'table_analysis': {'required_tables': ['RM_AGGREGATED_DATA'], 'primary_table': 'RM_AGGREGATED_DATA'},
            'join_analysis': {'required_joins': []},
            'column_analysis': {'aggregation_needed': True},
            'temporal_analysis': {'needs_time_filter': False},
            'output_requirements': {'suggested_limit': 5}
        }

        result = sql_tool._run("Show me top 5 customers", intent_data)

        if result.get('success'):
            print("✅ SQL Generator working")
            print(f"Generated SQL: {result.get('sql_query', 'No SQL')[:100]}...")
        else:
            print(f"❌ SQL Generator failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ SQL Generator test failed: {e}")
        return False

    # Test Query Execution
    try:
        from tools.query_execution_tool import QueryExecutionTool
        query_tool = QueryExecutionTool()

        print("Testing Query Executor...")
        result = query_tool._run("SELECT 'test' as message LIMIT 1")

        if result.get('success'):
            print("✅ Query Executor working")
        else:
            print(f"❌ Query Executor failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Query Executor test failed: {e}")
        return False

    return True

def test_agent_creation():
    """Test agent creation without running a query."""
    print("\n🤖 Testing Agent Creation...")

    try:
        from core.agent import ClickHouseGraphAgent

        print("Creating agent...")
        agent = ClickHouseGraphAgent(verbose=True)

        if agent:
            print("✅ Agent created successfully")

            # Test if the graph is compiled
            if hasattr(agent, 'graph') and agent.graph:
                print("✅ LangGraph compiled successfully")
                return True
            else:
                print("❌ LangGraph not compiled")
                return False
        else:
            print("❌ Agent creation failed")
            return False

    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_query():
    """Test a very simple query through the agent."""
    print("\n🔍 Testing Simple Query...")

    try:
        from core.agent import ClickHouseGraphAgent

        agent = ClickHouseGraphAgent(verbose=True)

        print("Running simple query: 'List available tables'")
        start_time = time.time()

        response = agent.process_question("List available tables")

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"✅ Query completed in {processing_time:.2f} seconds")
        print(f"Response length: {len(response)} characters")
        print(f"Response preview: {response[:200]}...")

        return True

    except Exception as e:
        print(f"❌ Simple query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests."""
    print("🔮 Telmi Debug Tool")
    print("==================")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    print()

    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("Individual Tools", test_individual_tools),
        ("Agent Creation", test_agent_creation),
        ("Simple Query", test_simple_query)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

        if results[test_name]:
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
            break  # Stop on first failure

    print(f"\n{'='*50}")
    print("📊 Test Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")

    if all(results.values()):
        print("\n🎉 All tests passed! Your agent should work in Streamlit.")
    else:
        print("\n⚠️  Some tests failed. Fix these issues before running Streamlit.")

        # Provide specific guidance
        if not results.get("Imports", True):
            print("\n💡 Import issues: Check if you're in the right directory and all files exist")
        elif not results.get("Database", True):
            print("\n💡 Database issues: Check ClickHouse server and network connectivity")
        elif not results.get("Individual Tools", True):
            print("\n💡 Tools issues: Check LLM configuration and tool implementations")
        elif not results.get("Agent Creation", True):
            print("\n💡 Agent issues: Check LangGraph configuration and dependencies")
        else:
            print("\n💡 Query issues: Check LangGraph workflow and tool integration")

if __name__ == "__main__":
    main()