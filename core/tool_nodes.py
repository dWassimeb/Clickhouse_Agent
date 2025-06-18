"""
Tool Nodes - Structured tool execution for the LangGraph workflow
"""

from typing import Dict, Any
import logging
from core.state import ClickHouseAgentState

logger = logging.getLogger(__name__)

def execute_query_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Tool Node: Execute SQL query against ClickHouse database.

    This node takes the generated SQL and executes it safely,
    returning structured results for further processing.
    """
    if state.get("verbose", False):
        print(f"\n⚡ TOOL NODE: Query Executor")
        print(f"   🎯 Task: Execute SQL against ClickHouse database")
        print(f"   🔒 Safety: Validation and limits applied")

    try:
        from tools.query_execution_tool import QueryExecutionTool
        tool = QueryExecutionTool()

        sql_query = state["sql_generation"].get("sql_query", "")

        if not sql_query:
            raise ValueError("No SQL query to execute")

        if state.get("verbose", False):
            print(f"   ⚡ EXECUTING: Running query against database")

        result = tool._run(sql_query)
        state["query_execution"] = result

        # Determine next action based on results
        if result.get("success") and result.get("result", {}).get("data"):
            state["next_action"] = "export_csv"
            if state.get("verbose", False):
                row_count = result.get("result", {}).get("row_count", 0)
                print(f"   ✅ SUCCESS: {row_count} rows returned")
                print(f"   ➡️  NEXT: Export results to CSV")
        else:
            state["next_action"] = "format_response"
            if state.get("verbose", False):
                if result.get("success"):
                    print(f"   ✅ SUCCESS: Query executed but no data returned")
                else:
                    print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                print(f"   ➡️  NEXT: Format response (skip CSV export)")

    except Exception as e:
        logger.error(f"Query execution tool error: {e}")
        state["query_execution"] = {
            "success": False,
            "error": str(e),
            "message": "Query execution failed"
        }
        state["next_action"] = "format_response"
        state["error_occurred"] = True
        state["error_message"] = str(e)

    return state

def export_csv_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Tool Node: Export query results to CSV file.

    This node takes successful query results and creates a downloadable
    CSV file for the user.
    """
    if state.get("verbose", False):
        print(f"\n📊 TOOL NODE: CSV Exporter")
        print(f"   🎯 Task: Export query results to CSV file")
        print(f"   📁 Output: Timestamped file in exports/ directory")

    try:
        from tools.csv_export_tool import CsvExportTool
        tool = CsvExportTool()

        query_result = state["query_execution"]
        user_question = state["user_question"]

        # Only export if we have data
        if (query_result.get("success") and
                query_result.get("result", {}).get("data")):

            if state.get("verbose", False):
                print(f"   📊 PROCESSING: Creating CSV from query results")

            result = tool._run(query_result, user_question)

            if result.get("success"):
                if state.get("verbose", False):
                    filename = result.get("filename", "unknown")
                    size = result.get("file_stats", {}).get("size_human", "unknown")
                    print(f"   ✅ SUCCESS: Created '{filename}' ({size})")
            else:
                if state.get("verbose", False):
                    print(f"   ❌ FAILED: {result.get('error', 'CSV creation failed')}")
        else:
            # No data to export
            result = {
                "success": False,
                "message": "No data available for CSV export"
            }
            if state.get("verbose", False):
                print(f"   ⏩ SKIPPED: No data to export")

        state["csv_export"] = result
        state["next_action"] = "format_response"

        if state.get("verbose", False):
            print(f"   ➡️  NEXT: Format final response for user")

    except Exception as e:
        logger.error(f"CSV export tool error: {e}")
        state["csv_export"] = {
            "success": False,
            "error": str(e),
            "message": "CSV export failed"
        }
        state["next_action"] = "format_response"

    return state

def format_response_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Tool Node: Format the final response for the user.

    This node takes all the workflow results and creates a well-formatted,
    user-friendly response with tables, insights, and download links.
    """
    if state.get("verbose", False):
        print(f"\n📝 TOOL NODE: Response Formatter")
        print(f"   🎯 Task: Create user-friendly formatted response")
        print(f"   📋 Input: Query results, CSV info, user question")

    try:
        from tools.response_formatter_tool import ResponseFormatterTool
        tool = ResponseFormatterTool()

        query_type = state["query_type"]

        if query_type == "help_request":
            # Handle help requests
            if state.get("verbose", False):
                print(f"   📚 TYPE: Help request - showing usage instructions")
            state["final_response"] = tool.format_help_response()

        elif query_type == "schema_request":
            # Handle schema requests
            if state.get("verbose", False):
                print(f"   🗂️  TYPE: Schema request - showing database structure")
            schema_result = _handle_schema_request(state)
            format_result = tool._run(schema_result, state["user_question"], "schema")
            state["final_response"] = format_result.get("formatted_response", "Schema information")

        else:
            # Handle data query results
            if state.get("verbose", False):
                print(f"   📊 TYPE: Data query - formatting results with insights")
            query_result = state["query_execution"]
            csv_result = state.get("csv_export", {})
            format_result = tool._run(query_result, state["user_question"], "query", csv_result)
            state["final_response"] = format_result.get("formatted_response", "No response generated")

        if state.get("verbose", False):
            response_length = len(state["final_response"])
            print(f"   ✅ SUCCESS: Generated {response_length} character response")
            print(f"   🎁 COMPLETE: Response ready for user")

    except Exception as e:
        logger.error(f"Response formatting tool error: {e}")
        state["final_response"] = f"❌ **Error:** Failed to format response: {str(e)}"
        state["error_occurred"] = True
        state["error_message"] = str(e)

    return state

def _handle_schema_request(state: ClickHouseAgentState) -> Dict[str, Any]:
    """
    Helper function to handle schema-related requests.

    Processes schema requests without needing external tools,
    using the metadata directly from config.
    """
    question = state["user_question"].lower()

    try:
        from config.schemas import TABLE_SCHEMAS

        if "list tables" in question or "show tables" in question:
            # Return all tables
            tables = {
                table_name: schema.get('description', 'No description')
                for table_name, schema in TABLE_SCHEMAS.items()
            }
            return {
                "success": True,
                "tables": tables,
                "message": f"Found {len(tables)} tables"
            }

        # Handle specific table schema requests
        parts = state["user_question"].split()
        if len(parts) > 1:
            table_name = parts[1].upper()
            schema = TABLE_SCHEMAS.get(table_name, {})
            if schema:
                return {
                    "success": True,
                    "schema": schema,
                    "table_name": table_name,
                    "message": f"Schema for table {table_name}"
                }
            else:
                available_tables = list(TABLE_SCHEMAS.keys())
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found",
                    "available_tables": available_tables
                }

        # Default: return all tables
        tables = {
            table_name: schema.get('description', 'No description')
            for table_name, schema in TABLE_SCHEMAS.items()
        }
        return {
            "success": True,
            "tables": tables,
            "message": "All available table schemas"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Schema request failed: {str(e)}",
            "message": "Could not process schema request"
        }