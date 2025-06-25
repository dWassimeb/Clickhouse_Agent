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
        state["next_action"] = "create_visualization"

        if state.get("verbose", False):
            print(f"   ➡️  NEXT: Create interactive visualization")

    except Exception as e:
        logger.error(f"CSV export tool error: {e}")
        state["csv_export"] = {
            "success": False,
            "error": str(e),
            "message": "CSV export failed"
        }
        state["next_action"] = "create_visualization"

    return state

def create_visualization_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Tool Node: Create modern interactive visualizations from query results.
    Now supports user chart type preferences from intent analysis.
    """
    if state.get("verbose", False):
        print(f"\n📈 TOOL NODE: Modern Visualization Creator")
        print(f"   🎯 Task: Generate interactive charts and dashboards")
        print(f"   🎨 Style: Modern, fancy, lightweight with Chart.js")

    try:
        from tools.modern_visualization_tool import ModernVisualizationTool
        tool = ModernVisualizationTool()

        query_result = state["query_execution"]
        user_question = state["user_question"]
        csv_result = state.get("csv_export", {})
        intent_analysis = state.get("intent_analysis", {})  # ✅ Pass intent analysis

        # Only create visualization if we have successful query results
        if (query_result.get("success") and
                query_result.get("result", {}).get("data")):

            if state.get("verbose", False):
                print(f"   🧠 ANALYZING: Determining best visualization type with LLM")

                # Log user chart preference if detected
                viz_prefs = intent_analysis.get('visualization_preferences', {})
                user_requested = viz_prefs.get('user_requested_chart_type')
                if user_requested and user_requested != 'auto':
                    print(f"   🎯 USER PREFERENCE: {user_requested} chart requested")

            # ✅ Pass intent_analysis to the tool
            result = tool._run(query_result, user_question, csv_result, intent_analysis)

            if result.get("success"):
                if state.get("verbose", False):
                    viz_type = result.get("visualization_type", "unknown")
                    filename = result.get("file_stats", {}).get("filename", "unknown")
                    file_size = result.get("file_stats", {}).get("size_human", "unknown")
                    print(f"   ✅ SUCCESS: Created {viz_type} chart → '{filename}' ({file_size})")
            else:
                if state.get("verbose", False):
                    reason = result.get("reason", result.get("error", "Unknown reason"))
                    print(f"   ⏩ SKIPPED: {reason}")
        else:
            # No data to visualize
            result = {
                "success": False,
                "message": "No data available for visualization",
                "reason": "Query returned no results or failed"
            }
            if state.get("verbose", False):
                print(f"   ⏩ SKIPPED: No data available for visualization")

        state["visualization"] = result
        state["next_action"] = "format_response"

        if state.get("verbose", False):
            print(f"   ➡️  NEXT: Format final response with visualization links")

    except Exception as e:
        logger.error(f"Visualization creation tool error: {e}")
        state["visualization"] = {
            "success": False,
            "error": str(e),
            "message": "Visualization creation failed"
        }
        state["next_action"] = "format_response"

    return state

def smart_schema_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Tool Node: Handle schema requests using LLM-powered Smart Schema Tool.

    This node processes any schema-related question with intelligent analysis
    and uses ClickHouse SDK when possible, falling back to hardcoded schemas.
    """
    if state.get("verbose", False):
        print(f"\n🧠 TOOL NODE: Smart Schema Handler")
        print(f"   🎯 Task: Process schema question with LLM reasoning")
        print(f"   🔗 Method: ClickHouse SDK + LLM analysis + Hardcoded fallback")

    try:
        from tools.smart_schema_tool import SmartSchemaTool
        tool = SmartSchemaTool()

        user_question = state["user_question"]

        if state.get("verbose", False):
            print(f"   🧠 ANALYZING: Understanding schema requirements")

        result = tool._run(user_question)

        if result.get("success"):
            state["final_response"] = result.get("formatted_response", "Schema information processed")

            if state.get("verbose", False):
                schema_intent = result.get("schema_intent", {})
                operation = schema_intent.get("operation", "unknown")
                source = result.get("schema_data", {}).get("source", "unknown")
                print(f"   ✅ SUCCESS: {operation} completed using {source}")
        else:
            state["final_response"] = result.get("formatted_response", f"❌ Schema error: {result.get('error', 'Unknown error')}")
            state["error_occurred"] = True
            state["error_message"] = result.get("error", "Schema processing failed")

            if state.get("verbose", False):
                print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Smart schema tool error: {e}")
        state["final_response"] = f"❌ **Error:** Schema processing failed: {str(e)}"
        state["error_occurred"] = True
        state["error_message"] = str(e)

    return state

def format_response_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Tool Node: Format the final response for the user.

    This node takes all the workflow results and creates a well-formatted,
    user-friendly response with tables, insights, CSV downloads, and visualization links.
    """
    if state.get("verbose", False):
        print(f"\n📝 TOOL NODE: Response Formatter")
        print(f"   🎯 Task: Create user-friendly formatted response")
        print(f"   📋 Input: Query results, CSV info, visualization info, user question")

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
            # This should not happen anymore since schema requests go to smart_schema_node
            # But keeping as fallback
            if state.get("verbose", False):
                print(f"   🗂️  TYPE: Schema request - unexpected fallback route")
            state["final_response"] = "❌ **Error:** Schema request should be handled by Smart Schema Tool"

        else:
            # Handle data query results with visualization
            if state.get("verbose", False):
                print(f"   📊 TYPE: Data query - formatting results with insights + visualization")
            query_result = state["query_execution"]
            csv_result = state.get("csv_export", {})
            visualization_result = state.get("visualization", {})

            # Enhanced formatting with visualization info
            format_result = tool._run(query_result, state["user_question"], "query", csv_result, visualization_result)
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