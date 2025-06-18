"""
Router Node - Decision making logic for the ClickHouse Agent
"""

from typing import Literal
from core.state import ClickHouseAgentState

def router_node(state: ClickHouseAgentState) -> Literal["data_query", "schema_request", "help_request"]:
    """
    Router node that analyzes the user question and decides which workflow path to take.

    This is the entry point of the LangGraph workflow that determines:
    - Data queries: Questions that need SQL generation and execution
    - Schema requests: Questions about database structure
    - Help requests: Questions asking for usage help

    Args:
        state: Current agent state containing the user question

    Returns:
        Literal route decision for conditional edges
    """

    question = state["user_question"].lower().strip()

    # Router reasoning (verbose logging)
    if state.get("verbose", False):
        print(f"\n🧭 ROUTER NODE: Analyzing question type")
        print(f"   📝 Question: '{state['user_question']}'")
        print(f"   🤔 Analyzing routing patterns...")

    # Schema requests - questions about database structure
    schema_keywords = ["list tables", "show tables", "schema", "table structure", "describe table"]
    if any(keyword in question for keyword in schema_keywords):
        state["query_type"] = "schema_request"
        if state.get("verbose", False):
            print(f"   🧭 DECISION: Schema request detected")
            print(f"   ➡️  ROUTE: Direct to response formatter (no SQL needed)")
        return "schema_request"

    # Help requests - questions asking for assistance
    help_keywords = ["help", "?", "aide", "assistant", "how to use", "usage"]
    if any(keyword in question for keyword in help_keywords):
        state["query_type"] = "help_request"
        if state.get("verbose", False):
            print(f"   🧭 DECISION: Help request detected")
            print(f"   ➡️  ROUTE: Direct to response formatter (no SQL needed)")
        return "help_request"

    # Default to data query - questions requiring SQL generation and execution
    state["query_type"] = "data_query"
    if state.get("verbose", False):
        print(f"   🧭 DECISION: Data query detected")
        print(f"   ➡️  ROUTE: Through AI analysis pipeline (Intent → SQL → Execute)")
        print(f"   🎯 This will trigger the full AI reasoning workflow")

    return "data_query"