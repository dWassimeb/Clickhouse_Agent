"""
Core ClickHouse Agent - AI reasoning and decision making
"""

from typing import Dict, Any
import logging
from langchain_core.messages import HumanMessage

from core.state import ClickHouseAgentState
# Removed router import - it's handled by graph_builder
from core.graph_builder import create_clickhouse_graph

logger = logging.getLogger(__name__)

class ClickHouseAgent:
    """
    Core AI Agent responsible for reasoning and decision making.

    This agent doesn't execute tools directly - it analyzes situations,
    makes decisions, and delegates execution to tool nodes.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.tools_map = self._initialize_tools()

    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize tools that the agent can reason about and use."""
        from tools.smart_intent_analyzer_tool import SmartIntentAnalyzerTool
        from tools.smart_sql_generator_tool import SmartSqlGeneratorTool
        from tools.query_execution_tool import QueryExecutionTool
        from tools.response_formatter_tool import ResponseFormatterTool
        from tools.csv_export_tool import CsvExportTool

        return {
            "intent_analyzer": SmartIntentAnalyzerTool(),
            "sql_generator": SmartSqlGeneratorTool(),
            "query_executor": QueryExecutionTool(),
            "response_formatter": ResponseFormatterTool(),
            "csv_exporter": CsvExportTool()
        }

    def analyze_intent(self, state: ClickHouseAgentState) -> ClickHouseAgentState:
        """
        Agent's reasoning process for understanding user intent.

        This is where the agent thinks about what the user wants and
        determines the best approach to answer their question.
        """
        if self.verbose:
            print(f"\n🤖 AGENT: Starting intent analysis")
            print(f"   💭 Thinking: What does the user really want?")
            print(f"   🎯 Goal: Understand intent and map to database concepts")

        try:
            # Agent uses the intent analyzer tool
            tool = self.tools_map["intent_analyzer"]
            result = tool._run(state["user_question"])

            # Agent reasoning about the results
            state["intent_analysis"] = result

            if result.get("success"):
                state["next_action"] = "generate_sql"
                state["error_occurred"] = False

                if self.verbose:
                    self._log_intent_success(result)
            else:
                state["next_action"] = "error"
                state["error_occurred"] = True
                state["error_message"] = result.get("error", "Intent analysis failed")

                if self.verbose:
                    print(f"   ❌ AGENT: Intent analysis failed - {state['error_message']}")

        except Exception as e:
            state["error_occurred"] = True
            state["error_message"] = str(e)
            state["next_action"] = "error"
            logger.error(f"Agent intent analysis error: {e}")

        return state

    def generate_sql(self, state: ClickHouseAgentState) -> ClickHouseAgentState:
        """
        Agent's reasoning process for SQL generation.

        The agent takes the analyzed intent and reasons about how to
        convert it into optimal SQL for the ClickHouse database.
        """
        if self.verbose:
            print(f"\n🤖 AGENT: Starting SQL generation")
            print(f"   💭 Thinking: How to convert intent into optimal SQL?")
            print(f"   🎯 Goal: Generate accurate, efficient ClickHouse query")

        try:
            # Agent extracts relevant intent data
            intent_data = self._extract_intent_for_sql(state["intent_analysis"])

            if self.verbose:
                self._log_sql_input_reasoning(intent_data)

            # Agent uses the SQL generator tool
            tool = self.tools_map["sql_generator"]
            result = tool._run(state["user_question"], intent_data)

            # Agent reasoning about the generated SQL
            state["sql_generation"] = result

            if result.get("success"):
                state["next_action"] = "execute_query"
                state["error_occurred"] = False

                if self.verbose:
                    self._log_sql_success(result)
            else:
                state["next_action"] = "error"
                state["error_occurred"] = True
                state["error_message"] = result.get("error", "SQL generation failed")

                if self.verbose:
                    print(f"   ❌ AGENT: SQL generation failed - {state['error_message']}")

        except Exception as e:
            state["error_occurred"] = True
            state["error_message"] = str(e)
            state["next_action"] = "error"
            logger.error(f"Agent SQL generation error: {e}")

        return state

    def _extract_intent_for_sql(self, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and clean intent data for SQL generation."""
        return {
            key: value for key, value in intent_analysis.items()
            if key not in ['success', 'message', 'llm_raw_analysis', 'user_question']
        }

    def _log_intent_success(self, result: Dict[str, Any]):
        """Log agent's reasoning about successful intent analysis."""
        print(f"   ✅ AGENT: Intent analysis successful")

        intent_info = result.get('intent_analysis', {})
        if intent_info:
            intent_type = intent_info.get('primary_intent', 'unknown')
            confidence = intent_info.get('intent_confidence', 0)
            print(f"   💡 INSIGHT: Detected '{intent_type}' with {confidence:.2f} confidence")

        table_analysis = result.get('table_analysis', {})
        if table_analysis:
            tables = table_analysis.get('required_tables', [])
            print(f"   📊 STRATEGY: Will use {len(tables)} tables: {', '.join(tables)}")

        print(f"   ➡️  NEXT: Generate SQL based on this analysis")

    def _log_sql_input_reasoning(self, intent_data: Dict[str, Any]):
        """Log agent's reasoning about SQL input preparation."""
        print(f"   📋 AGENT: Preparing SQL generation context")

        table_analysis = intent_data.get('table_analysis', {})
        if table_analysis:
            tables = table_analysis.get('required_tables', [])
            primary = table_analysis.get('primary_table', 'unknown')
            print(f"   🎯 FOCUS: Primary table '{primary}', supporting tables: {tables}")

        join_analysis = intent_data.get('join_analysis', {})
        if join_analysis and join_analysis.get('required_joins'):
            join_count = len(join_analysis['required_joins'])
            print(f"   🔗 COMPLEXITY: {join_count} joins required")

    def _log_sql_success(self, result: Dict[str, Any]):
        """Log agent's reasoning about successful SQL generation."""
        print(f"   ✅ AGENT: SQL generation successful")

        sql_metadata = result.get('sql_metadata', {})
        if sql_metadata:
            complexity = sql_metadata.get('estimated_complexity', 'unknown')
            tables_used = sql_metadata.get('tables_used', [])
            print(f"   💡 INSIGHT: Generated {complexity} query using {len(tables_used)} tables")

            if sql_metadata.get('has_time_filter'):
                print(f"   ⏰ FEATURE: Time filtering applied")
            if sql_metadata.get('aggregations_used'):
                aggs = sql_metadata['aggregations_used']
                print(f"   📊 FEATURE: Aggregations used: {', '.join(aggs)}")

        print(f"   ➡️  NEXT: Execute the generated SQL")

class ClickHouseGraphAgent:
    """
    Main interface for the ClickHouse LangGraph Agent.

    This class provides a clean interface to the LangGraph workflow
    and handles the overall execution flow.
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.graph = create_clickhouse_graph(verbose=verbose)

    def process_question(self, user_question: str) -> str:
        """
        Process a user question through the complete LangGraph workflow.

        Args:
            user_question: The user's natural language question

        Returns:
            Formatted response string
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"🚀 LANGGRAPH WORKFLOW: Starting execution")
            print(f"   📝 Question: '{user_question}'")
            print(f"   🎯 Flow: Smart Router → Agent → Tools → Response")
            print(f"{'='*80}")

        # Initialize state
        initial_state = ClickHouseAgentState(
            messages=[HumanMessage(content=user_question)],
            user_question=user_question,
            query_type="data_query",  # Will be overridden by smart router
            intent_analysis={},
            sql_generation={},
            query_execution={},
            csv_export={},
            final_response="",
            next_action="",
            verbose=self.verbose,
            error_occurred=False,
            error_message=""
        )

        try:
            # Execute the LangGraph workflow
            final_state = self.graph.invoke(initial_state)
            response = final_state.get("final_response", "No response generated")

            if self.verbose:
                print(f"\n🎯 LANGGRAPH WORKFLOW: Execution complete")
                if final_state.get("error_occurred"):
                    print(f"   ⚠️  Completed with errors: {final_state.get('error_message', 'Unknown error')}")
                else:
                    print(f"   ✅ Completed successfully")
                print(f"{'='*80}")

            return response

        except Exception as e:
            logger.error(f"LangGraph execution failed: {e}")
            return f"❌ **Error:** An error occurred while processing your question: {str(e)}"