"""
Main entry point for the ClickHouse Agent using LangGraph.
"""

import logging
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

# Import tools
from tools.schema_analyzer_tool import SchemaAnalyzerTool
from tools.sql_generator_tool import SqlGeneratorTool
from tools.query_execution_tool import QueryExecutionTool
from tools.response_formatter_tool import ResponseFormatterTool
from tools.csv_export_tool import CsvExportTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state for our graph
class AgentState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], add_messages]
    user_question: str
    analysis_result: Dict[str, Any]
    sql_result: Dict[str, Any]
    execution_result: Dict[str, Any]
    csv_export_result: Dict[str, Any]
    final_response: str

class ClickHouseAgent:
    """Main ClickHouse Agent orchestrating the workflow with tools."""

    def __init__(self):
        # Initialize all tools
        self.schema_analyzer = SchemaAnalyzerTool()
        self.sql_generator = SqlGeneratorTool()
        self.query_executor = QueryExecutionTool()
        self.response_formatter = ResponseFormatterTool()
        self.csv_exporter = CsvExportTool()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with conditional routing."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("route_question", self._route_question)
        workflow.add_node("analyze_schema", self._analyze_schema)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("export_csv", self._export_csv)
        workflow.add_node("format_response", self._format_response)
        workflow.add_node("handle_schema_request", self._handle_schema_request)
        workflow.add_node("handle_help_request", self._handle_help_request)

        # Define conditional routing
        workflow.set_entry_point("route_question")

        # Conditional edges from routing
        workflow.add_conditional_edges(
            "route_question",
            self._decide_route,
            {
                "data_query": "analyze_schema",
                "schema_request": "handle_schema_request",
                "help_request": "handle_help_request"
            }
        )

        # Data query flow
        workflow.add_edge("analyze_schema", "generate_sql")
        workflow.add_edge("generate_sql", "execute_query")
        workflow.add_edge("execute_query", "export_csv")
        workflow.add_edge("export_csv", "format_response")

        # Direct response flows
        workflow.add_edge("handle_schema_request", "format_response")
        workflow.add_edge("handle_help_request", "format_response")
        workflow.add_edge("format_response", END)

        return workflow.compile()

    def _route_question(self, state: AgentState) -> AgentState:
        """Initial routing of the user question."""
        logger.info("Routing user question...")
        # Just pass through - routing decision is made in _decide_route
        return state

    def _handle_help_request(self, state: AgentState) -> AgentState:
        """Handle help requests."""
        logger.info("Handling help request...")

        help_response = self.response_formatter.format_help_response()
        state["execution_result"] = {
            "success": True,
            "help_content": help_response,
            "message": "Help information"
        }

        # No CSV export for help
        state["csv_export_result"] = {"success": False, "message": "No data to export"}

        return state

    def _decide_route(self, state: AgentState) -> str:
        """Decide which route to take based on the question."""
        question = state["user_question"].lower().strip()

        # Schema requests
        if any(cmd in question for cmd in ["list tables", "show tables", "schema"]):
            return "schema_request"

        # Help requests
        if question in ["help", "?"]:
            return "help_request"

        # Default to data query
        return "data_query"

    def _analyze_schema(self, state: AgentState) -> AgentState:
        """Analyze the user question for relevant schema elements."""
        logger.info("Analyzing schema...")

        user_question = state["user_question"]
        analysis_result = self.schema_analyzer._run(user_question)
        state["analysis_result"] = analysis_result

        logger.info(f"Schema analysis complete: {analysis_result.get('message', '')}")
        return state

    def _generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL query based on analysis."""
        logger.info("Generating SQL...")

        user_question = state["user_question"]
        analysis_result = state["analysis_result"]

        if not analysis_result.get("success", False):
            state["sql_result"] = {
                "success": False,
                "error": "Schema analysis failed",
                "message": "Cannot generate SQL without schema analysis"
            }
            return state

        sql_result = self.sql_generator._run(user_question, analysis_result)
        state["sql_result"] = sql_result

        logger.info(f"SQL generation complete: {sql_result.get('message', '')}")
        return state

    def _execute_query(self, state: AgentState) -> AgentState:
        """Execute the generated SQL query."""
        logger.info("Executing query...")

        sql_result = state["sql_result"]

        if not sql_result.get("success", False):
            state["execution_result"] = {
                "success": False,
                "error": "SQL generation failed",
                "message": "Cannot execute query - SQL generation failed"
            }
            return state

        sql_query = sql_result.get("sql_query", "")
        execution_result = self.query_executor._run(sql_query)
        state["execution_result"] = execution_result

        logger.info(f"Query execution complete: {execution_result.get('message', '')}")
        return state

    def _handle_schema_request(self, state: AgentState) -> AgentState:
        """Handle schema-related requests."""
        logger.info("Handling schema request...")

        question = state["user_question"].lower()

        if "list tables" in question or "show tables" in question:
            # Get all tables
            tables = self.schema_analyzer.get_all_tables()
            state["execution_result"] = {
                "success": True,
                "tables": tables,
                "message": f"Found {len(tables)} tables"
            }

        elif question.startswith("schema"):
            # Get specific table schema
            parts = state["user_question"].split()
            table_name = parts[1] if len(parts) > 1 else ""

            if table_name:
                schema = self.schema_analyzer.get_table_schema(table_name)
                if schema:
                    state["execution_result"] = {
                        "success": True,
                        "schema": schema,
                        "table_name": table_name,
                        "message": f"Schema for table {table_name}"
                    }
                else:
                    state["execution_result"] = {
                        "success": False,
                        "error": f"Table '{table_name}' not found",
                        "available_tables": list(self.schema_analyzer.get_all_tables().keys())
                    }
            else:
                # Show all schemas
                tables = self.schema_analyzer.get_all_tables()
                state["execution_result"] = {
                    "success": True,
                    "tables": tables,
                    "message": "All available table schemas"
                }

        return state

    def _export_csv(self, state: AgentState) -> AgentState:
        """Export query results to CSV if successful."""
        logger.info("Exporting to CSV...")

        execution_result = state["execution_result"]
        user_question = state["user_question"]

        # Only export if we have successful query results with data
        if (execution_result.get("success", False) and
            execution_result.get("result", {}).get("data", [])):

            csv_result = self.csv_exporter._run(execution_result, user_question)
            state["csv_export_result"] = csv_result

            if csv_result.get("success", False):
                logger.info(f"CSV export complete: {csv_result.get('message', '')}")
            else:
                logger.warning(f"CSV export failed: {csv_result.get('error', '')}")
        else:
            # No data to export or query failed
            state["csv_export_result"] = {
                "success": False,
                "message": "No data available for CSV export"
            }
            logger.info("Skipping CSV export - no data available")

        return state
        """Handle help requests."""
        logger.info("Handling help request...")

        help_response = self.response_formatter.format_help_response()
        state["execution_result"] = {
            "success": True,
            "help_content": help_response,
            "message": "Help information"
        }

        return state

    def _format_response(self, state: AgentState) -> AgentState:
        """Format the final response for the user."""
        logger.info("Formatting response...")

        execution_result = state.get("execution_result", {})
        csv_export_result = state.get("csv_export_result", {})
        user_question = state["user_question"]

        # Determine response type
        if "tables" in execution_result or "schema" in execution_result:
            response_type = "schema"
        elif "help_content" in execution_result:
            state["final_response"] = execution_result["help_content"]
            return state
        elif not execution_result.get("success", True):
            response_type = "error"
        else:
            response_type = "query"

        format_result = self.response_formatter._run(
            execution_result,
            user_question,
            response_type,
            csv_export_result
        )

        state["final_response"] = format_result.get("formatted_response", "No response generated.")

        logger.info("Response formatting complete")
        return state

    def process_question(self, user_question: str) -> str:
        """Process a user question and return the formatted response."""
        logger.info(f"Processing question: {user_question}")

        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=user_question)],
            user_question=user_question,
            analysis_result={},
            sql_result={},
            execution_result={},
            csv_export_result={},
            final_response=""
        )

        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            response = final_state.get("final_response", "No response generated.")

            logger.info("Question processed successfully")
            return response

        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return f"❌ **Error:** An error occurred while processing your question: {str(e)}\n\n💡 **Suggestion:** Please try again with a different question."

def main():
    """Main function to run the ClickHouse Agent."""
    print("🚀 ClickHouse Agent Starting...")

    # Test database connection
    print("🔌 Testing database connection...")
    from database.connection import clickhouse_connection

    try:
        if clickhouse_connection.test_connection():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
            print("💡 Please check if ClickHouse server is running and accessible.")
            return
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("💡 The agent will still start, but database queries will fail.")
        print("   Please check your ClickHouse server and network connectivity.")

    print("Type 'exit' to quit, 'help' for assistance\n")

    agent = ClickHouseAgent()

    while True:
        try:
            user_input = input("📝 Your question: ").strip()

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break

            if not user_input:
                print("❌ Please enter a question.")
                continue

            print("\n🔄 Processing your question...")
            response = agent.process_question(user_input)
            print(f"\n{response}\n")
            print("-" * 80)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again.\n")

if __name__ == "__main__":
    main()