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
from tools.smart_intent_analyzer_tool import SmartIntentAnalyzerTool
from tools.smart_sql_generator_tool import SmartSqlGeneratorTool
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
    analysis_result: Dict[str, Any]  # Intent analysis from SmartIntentAnalyzer
    sql_result: Dict[str, Any]       # SQL generation from SmartSqlGenerator
    execution_result: Dict[str, Any] # Query execution results
    csv_export_result: Dict[str, Any] # CSV export results
    final_response: str

class ClickHouseAgent:
    """Main ClickHouse Agent orchestrating the workflow with tools."""

    def __init__(self, verbose: bool = True):
        # Initialize all tools
        self.intent_analyzer = SmartIntentAnalyzerTool()
        self.sql_generator = SmartSqlGeneratorTool()
        self.query_executor = QueryExecutionTool()
        self.response_formatter = ResponseFormatterTool()
        self.csv_exporter = CsvExportTool()
        self.verbose = verbose  # Control verbose logging
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with conditional routing."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("route_question", self._route_question)
        workflow.add_node("analyze_intent", self._analyze_intent)
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
                "data_query": "analyze_intent",
                "schema_request": "handle_schema_request",
                "help_request": "handle_help_request"
            }
        )

        # Data query flow - clean pipeline
        workflow.add_edge("analyze_intent", "generate_sql")
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

    def _analyze_intent(self, state: AgentState) -> AgentState:
        """Analyze user intent using smart LLM-powered analysis."""
        logger.info("🧠 Analyzing intent with AI...")

        user_question = state["user_question"]
        intent_result = self.intent_analyzer._run(user_question)
        state["analysis_result"] = intent_result

        if intent_result.get("success", False):
            confidence = intent_result.get("overall_confidence", 0.5)

            # Extract and display the AI's analysis conclusions
            if self.verbose:
                self._log_intent_analysis_thoughts(intent_result, user_question)

            logger.info(f"✅ Intent analysis complete (confidence: {confidence:.2f})")
        else:
            logger.warning(f"❌ Intent analysis failed: {intent_result.get('error', 'Unknown error')}")

        return state

    def _log_intent_analysis_thoughts(self, intent_result: Dict[str, Any], user_question: str):
        """Log the AI's reasoning process in a verbose, ReAct-style format."""
        print("\n" + "="*80)
        print("🤖 SMART INTENT ANALYZER - AI REASONING PROCESS")
        print("="*80)

        # Language Detection Thoughts
        language = intent_result.get('language', 'unknown')
        lang_confidence = intent_result.get('language_confidence', 0.0)
        print(f"🌍 LANGUAGE DETECTION:")
        print(f"   Thought: Analyzing linguistic patterns in '{user_question[:50]}...'")
        print(f"   Conclusion: {language.upper()} detected (confidence: {lang_confidence:.2f})")

        # Business Intent Analysis
        intent_analysis = intent_result.get('intent_analysis', {})
        if intent_analysis:
            print(f"\n🎯 BUSINESS INTENT ANALYSIS:")
            print(f"   Thought: What is the user trying to achieve?")
            print(f"   Primary Intent: {intent_analysis.get('primary_intent', 'unknown')}")
            print(f"   Confidence: {intent_analysis.get('intent_confidence', 0.0):.2f}")
            print(f"   Reasoning: {intent_analysis.get('intent_description', 'No description')}")

            if intent_analysis.get('business_scenario'):
                print(f"   Business Scenario: {intent_analysis['business_scenario']}")

        # Table Selection Strategy
        table_analysis = intent_result.get('table_analysis', {})
        if table_analysis:
            print(f"\n📊 TABLE SELECTION STRATEGY:")
            required_tables = table_analysis.get('required_tables', [])
            primary_table = table_analysis.get('primary_table', 'unknown')
            print(f"   Thought: Which tables contain the data needed for this question?")
            print(f"   Required Tables: {', '.join(required_tables)}")
            print(f"   Primary Table: {primary_table}")

            table_reasoning = table_analysis.get('table_reasoning', {})
            if table_reasoning:
                print(f"   Reasoning:")
                for table, reason in table_reasoning.items():
                    print(f"     • {table}: {reason}")

        # Join Strategy
        join_analysis = intent_result.get('join_analysis', {})
        if join_analysis and join_analysis.get('required_joins'):
            print(f"\n🔗 JOIN STRATEGY:")
            print(f"   Thought: How should these tables be connected?")
            for join in join_analysis['required_joins']:
                print(f"   Join: {join['from_table']} → {join['to_table']}")
                print(f"     Condition: {join['join_condition']}")
                print(f"     Purpose: {join['purpose']}")
                print(f"     Type: {join['join_type']}")

            join_reasoning = join_analysis.get('join_reasoning', '')
            if join_reasoning:
                print(f"   Overall Strategy: {join_reasoning}")

        # Column Analysis
        column_analysis = intent_result.get('column_analysis', {})
        if column_analysis:
            print(f"\n📋 COLUMN ANALYSIS:")
            print(f"   Thought: Which columns are needed to answer this question?")

            select_columns = column_analysis.get('select_columns', [])
            if select_columns:
                print(f"   Select Columns:")
                for col in select_columns:
                    alias = f" AS {col['alias']}" if col.get('alias') else ""
                    print(f"     • {col['column']}{alias} - {col['purpose']}")

            if column_analysis.get('aggregation_needed'):
                agg_functions = column_analysis.get('aggregation_functions', [])
                print(f"   Aggregations: {', '.join(agg_functions)}")

            grouping_cols = column_analysis.get('grouping_columns', [])
            if grouping_cols:
                print(f"   Group By: {', '.join(grouping_cols)}")

        # Temporal Analysis
        temporal_analysis = intent_result.get('temporal_analysis', {})
        if temporal_analysis and temporal_analysis.get('needs_time_filter'):
            print(f"\n⏰ TEMPORAL ANALYSIS:")
            print(f"   Thought: Does this question involve time constraints?")
            print(f"   Time Filter Needed: Yes")
            print(f"   Time Column: {temporal_analysis.get('time_column', 'unknown')}")
            print(f"   Time Period: {temporal_analysis.get('time_period', 'unknown')}")
            print(f"   Filter SQL: {temporal_analysis.get('time_filter_sql', 'unknown')}")

        # Output Requirements
        output_req = intent_result.get('output_requirements', {})
        if output_req:
            print(f"\n📤 OUTPUT REQUIREMENTS:")
            print(f"   Thought: How should the results be formatted and limited?")
            if output_req.get('needs_percentage'):
                print(f"   Percentage Calculation: Required")
            if output_req.get('needs_ranking'):
                print(f"   Ranking: Required")
            if output_req.get('suggested_limit'):
                print(f"   Suggested Limit: {output_req['suggested_limit']}")
            if output_req.get('sort_order'):
                print(f"   Sort Order: {output_req['sort_order']} by {output_req.get('sort_column', 'unknown')}")

        # SQL Guidance Generated
        sql_guidance = intent_result.get('sql_guidance', {})
        if sql_guidance:
            print(f"\n🔧 SQL GENERATION GUIDANCE:")
            print(f"   Complexity Level: {sql_guidance.get('complexity_level', 'unknown')}")

            challenges = sql_guidance.get('key_challenges', [])
            if challenges:
                print(f"   Key Challenges:")
                for challenge in challenges:
                    print(f"     • {challenge}")

            considerations = sql_guidance.get('critical_considerations', [])
            if considerations:
                print(f"   Critical Considerations:")
                for consideration in considerations:
                    print(f"     • {consideration}")

            approach = sql_guidance.get('recommended_approach', '')
            if approach:
                print(f"   Recommended Approach: {approach}")

        # Semantic Keywords Extracted
        semantic_keywords = intent_result.get('semantic_keywords', [])
        if semantic_keywords:
            print(f"\n🏷️  SEMANTIC KEYWORDS EXTRACTED:")
            print(f"   Keywords: {', '.join(semantic_keywords)}")

        print("="*80)
        print("🎯 CONCLUSION: Analysis complete - passing structured intent to SQL Generator")
        print("="*80 + "\n")

    def _generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL using smart generator with intent analysis."""
        logger.info("🔧 Generating SQL with AI guidance...")

        user_question = state["user_question"]
        analysis_result = state["analysis_result"]

        if not analysis_result.get("success", False):
            state["sql_result"] = {
                "success": False,
                "error": "Intent analysis failed",
                "message": "Cannot generate SQL without intent analysis"
            }
            return state

        # Extract the parsed intent analysis for SQL generation
        intent_data = {
            key: analysis_result[key] for key in analysis_result
            if key not in ['success', 'message', 'llm_raw_analysis', 'user_question']
        }

        # Show what we're passing to the SQL generator
        if self.verbose:
            self._log_sql_generation_input(intent_data, user_question)

        sql_result = self.sql_generator._run(user_question, intent_data)
        state["sql_result"] = sql_result

        if sql_result.get("success", False):
            # Show the SQL generation results
            if self.verbose:
                self._log_sql_generation_output(sql_result, user_question)
            logger.info(f"✅ SQL generation complete")
        else:
            logger.warning(f"❌ SQL generation failed: {sql_result.get('error', 'Unknown error')}")

        return state

    def _log_sql_generation_input(self, intent_data: Dict[str, Any], user_question: str):
        """Log what data is being passed to the SQL generator."""
        print("\n" + "="*80)
        print("⚡ SQL GENERATOR - RECEIVING INTENT ANALYSIS")
        print("="*80)
        print(f"📝 Original Question: '{user_question}'")

        # Show key intent analysis being passed
        table_analysis = intent_data.get('table_analysis', {})
        if table_analysis:
            print(f"📊 Tables to Use: {', '.join(table_analysis.get('required_tables', []))}")
            print(f"🎯 Primary Table: {table_analysis.get('primary_table', 'unknown')}")

        join_analysis = intent_data.get('join_analysis', {})
        if join_analysis and join_analysis.get('required_joins'):
            print(f"🔗 Joins Required: {len(join_analysis['required_joins'])} joins identified")

        output_req = intent_data.get('output_requirements', {})
        if output_req:
            if output_req.get('needs_percentage'):
                print(f"📊 Special Requirements: Percentage calculation needed")
            if output_req.get('suggested_limit'):
                print(f"🔢 Limit: {output_req['suggested_limit']} rows")

        print("="*80 + "\n")

    def _log_sql_generation_output(self, sql_result: Dict[str, Any], user_question: str):
        """Log the SQL generation results in ReAct style."""
        print("\n" + "="*80)
        print("🔧 SQL GENERATOR - AI REASONING & OUTPUT")
        print("="*80)

        sql_query = sql_result.get('sql_query', '')
        sql_metadata = sql_result.get('sql_metadata', {})
        intent_confidence = sql_result.get('intent_confidence', 0.0)

        print(f"🤖 Thought: Based on the intent analysis, I need to generate SQL that:")
        print(f"   • Answers: '{user_question}'")
        print(f"   • Uses optimal table joins and relationships")
        print(f"   • Follows ClickHouse best practices")
        print(f"   • Implements the analyzed requirements precisely")

        print(f"\n🎯 Action: Generate SQL Query")
        print(f"   Intent Confidence: {intent_confidence:.2f}")

        if sql_metadata:
            print(f"\n📊 Generated Query Metadata:")
            print(f"   Query Type: {sql_metadata.get('query_type', 'unknown')}")
            print(f"   Complexity: {sql_metadata.get('estimated_complexity', 'unknown')}")
            print(f"   Tables Used: {', '.join(sql_metadata.get('tables_used', []))}")

            if sql_metadata.get('joins_detected'):
                print(f"   Joins: {len(sql_metadata['joins_detected'])} detected")

            if sql_metadata.get('aggregations_used'):
                print(f"   Aggregations: {', '.join(sql_metadata['aggregations_used'])}")

            print(f"   Has Limit: {sql_metadata.get('has_limit', False)}")
            print(f"   Has Time Filter: {sql_metadata.get('has_time_filter', False)}")

        print(f"\n🔍 Generated SQL Query:")
        print("   " + "-"*76)
        # Format SQL for better readability
        formatted_sql = self._format_sql_for_display(sql_query)
        for line in formatted_sql.split('\n'):
            print(f"   {line}")
        print("   " + "-"*76)

        print(f"\n✅ Observation: SQL query successfully generated and validated")
        print(f"   Next Action: Execute query against ClickHouse database")

        print("="*80 + "\n")

    def _format_sql_for_display(self, sql_query: str) -> str:
        """Format SQL query for better display in logs."""
        # Simple SQL formatting for readability
        sql = sql_query.strip()

        # Add line breaks after major keywords
        keywords = ['SELECT', 'FROM', 'JOIN', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT']
        for keyword in keywords:
            if keyword in sql.upper():
                sql = sql.replace(keyword, f'\n{keyword}')
                sql = sql.replace(keyword.lower(), f'\n{keyword}')

        # Clean up extra newlines and spaces
        lines = [line.strip() for line in sql.split('\n') if line.strip()]
        return '\n'.join(lines)

    def _execute_query(self, state: AgentState) -> AgentState:
        """Execute the generated SQL query."""
        logger.info("⚡ Executing SQL query...")

        sql_result = state["sql_result"]

        if not sql_result.get("success", False):
            state["execution_result"] = {
                "success": False,
                "error": "SQL generation failed",
                "message": "Cannot execute query - SQL generation failed"
            }
            return state

        sql_query = sql_result.get("sql_query", "")

        # Show query execution thoughts
        if self.verbose:
            self._log_query_execution_thoughts(sql_query)

        execution_result = self.query_executor._run(sql_query)
        state["execution_result"] = execution_result

        # Show execution results
        if self.verbose:
            self._log_query_execution_results(execution_result, sql_query)

        if execution_result.get("success", False):
            logger.info(f"✅ Query execution complete")
        else:
            logger.warning(f"❌ Query execution failed: {execution_result.get('error', 'Unknown error')}")

        return state

    def _log_query_execution_thoughts(self, sql_query: str):
        """Log query execution reasoning."""
        print("\n" + "="*80)
        print("⚡ QUERY EXECUTOR - PREPARING FOR EXECUTION")
        print("="*80)
        print(f"🤖 Thought: About to execute the generated SQL query against ClickHouse")
        print(f"🔒 Action: Validate query safety and execute")
        print(f"   • Checking for dangerous operations (DROP, DELETE, etc.)")
        print(f"   • Ensuring SELECT-only query")
        print(f"   • Adding safety limits if needed")
        print(f"   • Connecting to ClickHouse database")
        print("="*80 + "\n")

    def _log_query_execution_results(self, execution_result: Dict[str, Any], sql_query: str):
        """Log query execution results."""
        print("\n" + "="*80)
        print("📊 QUERY EXECUTOR - EXECUTION RESULTS")
        print("="*80)

        if execution_result.get("success", False):
            result_data = execution_result.get("result", {})
            row_count = result_data.get("row_count", 0)
            columns = result_data.get("columns", [])

            print(f"✅ Observation: Query executed successfully!")
            print(f"📈 Results Summary:")
            print(f"   • Rows returned: {row_count}")
            print(f"   • Columns: {len(columns)} ({', '.join(columns[:5])}{'...' if len(columns) > 5 else ''})")
            print(f"   • Data available: {'Yes' if row_count > 0 else 'No'}")

            if row_count > 0:
                print(f"🎯 Next Action: Export results to CSV and format response")
            else:
                print(f"🤔 Observation: No data returned - query conditions may be too restrictive")
        else:
            error = execution_result.get("error", "Unknown error")
            suggestion = execution_result.get("suggestion", "")

            print(f"❌ Observation: Query execution failed")
            print(f"💥 Error: {error}")
            if suggestion:
                print(f"💡 Suggestion: {suggestion}")
            print(f"🔄 Next Action: Format error response for user")

        print("="*80 + "\n")

    def _handle_schema_request(self, state: AgentState) -> AgentState:
        """Handle schema-related requests."""
        logger.info("Handling schema request...")

        question = state["user_question"].lower()

        if "list tables" in question or "show tables" in question:
            # Get all tables from schema metadata
            from config.schemas import TABLE_SCHEMAS
            tables = {
                table_name: schema.get('description', 'No description')
                for table_name, schema in TABLE_SCHEMAS.items()
            }
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
                from config.schemas import TABLE_SCHEMAS
                schema = TABLE_SCHEMAS.get(table_name.upper(), {})
                if schema:
                    state["execution_result"] = {
                        "success": True,
                        "schema": schema,
                        "table_name": table_name.upper(),
                        "message": f"Schema for table {table_name.upper()}"
                    }
                else:
                    available_tables = list(TABLE_SCHEMAS.keys())
                    state["execution_result"] = {
                        "success": False,
                        "error": f"Table '{table_name}' not found",
                        "available_tables": available_tables
                    }
            else:
                # Show all schemas
                from config.schemas import TABLE_SCHEMAS
                tables = {
                    table_name: schema.get('description', 'No description')
                    for table_name, schema in TABLE_SCHEMAS.items()
                }
                state["execution_result"] = {
                    "success": True,
                    "tables": tables,
                    "message": "All available table schemas"
                }

        # No CSV export for schema requests
        state["csv_export_result"] = {"success": False, "message": "No data to export"}

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
    import sys

    # ===== VERBOSE MODE CONFIGURATION =====
    # Set this to True to always enable verbose mode, False to disable
    VERBOSE_MODE = True  # Change this to False for clean output
    # =====================================

    # Check for command-line flags (these override the config above)
    if "--verbose" in sys.argv or "-v" in sys.argv:
        verbose = True
    elif "--quiet" in sys.argv or "-q" in sys.argv:
        verbose = False
    else:
        verbose = VERBOSE_MODE  # Use the configuration setting

    print("🚀 ClickHouse Agent Starting...")
    if verbose:
        print("🔍 Verbose mode enabled - showing AI reasoning process")
    else:
        print("🤫 Quiet mode - clean output only")

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

    print("Type 'exit' to quit, 'help' for assistance")
    if verbose:
        print("💡 Tip: You're in verbose mode - you'll see the AI's reasoning process")
        print("💡 Use 'python3 main.py --quiet' to disable verbose mode")
    else:
        print("💡 Use 'python3 main.py --verbose' to see AI reasoning process")
    print()

    agent = ClickHouseAgent(verbose=verbose)

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