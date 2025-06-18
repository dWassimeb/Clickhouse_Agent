"""
LangGraph State Definition - Central state management for the ClickHouse Agent
"""

from typing import Dict, Any, List, Literal, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

class ClickHouseAgentState(TypedDict):
    """
    Central state for the ClickHouse LangGraph Agent workflow.

    This state is passed between all nodes in the graph and contains
    all the information needed for the agent to make decisions and
    execute tools.
    """

    # Core workflow data
    messages: Annotated[List[HumanMessage | AIMessage | SystemMessage], add_messages]
    user_question: str
    query_type: Literal["data_query", "schema_request", "help_request"]

    # Agent reasoning results
    intent_analysis: Dict[str, Any]     # Results from intent analyzer
    sql_generation: Dict[str, Any]      # Results from SQL generator

    # Tool execution results
    query_execution: Dict[str, Any]     # Results from query executor
    csv_export: Dict[str, Any]          # Results from CSV exporter

    # Final output
    final_response: str

    # Workflow control
    next_action: str                    # What the agent should do next
    verbose: bool                       # Control detailed logging

    # Error handling
    error_occurred: bool
    error_message: str