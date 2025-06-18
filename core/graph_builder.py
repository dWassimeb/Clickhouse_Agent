"""
Graph Builder - Constructs the LangGraph workflow
"""

from langgraph.graph import StateGraph, END
from core.state import ClickHouseAgentState
from core.router import router_node
from core.tool_nodes import execute_query_node, export_csv_node, format_response_node

def create_clickhouse_graph(verbose: bool = True) -> StateGraph:
    """
    Create the complete LangGraph workflow for the ClickHouse Agent.

    This function builds the entire graph structure with:
    - Router for decision making
    - Agent nodes for reasoning
    - Tool nodes for execution
    - Proper conditional edges and flow control

    Args:
        verbose: Whether to enable verbose logging

    Returns:
        Compiled StateGraph ready for execution
    """

    if verbose:
        print(f"🔧 GRAPH BUILDER: Constructing LangGraph workflow")
        print(f"   📋 Components: Router + Agent + Tools")
        print(f"   🔀 Flow: Conditional routing with linear tool execution")

    # Initialize the agent for reasoning nodes
    from core.agent import ClickHouseAgent
    agent = ClickHouseAgent(verbose=verbose)

    # Create the StateGraph
    workflow = StateGraph(ClickHouseAgentState)

    # ===== ADD NODES =====

    # Router node (entry point with decision making)
    workflow.add_node("router", router_node)

    # Agent nodes (AI reasoning and decision making)
    workflow.add_node("agent_intent_analysis", agent.analyze_intent)
    workflow.add_node("agent_sql_generation", agent.generate_sql)

    # Tool nodes (execution and processing)
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("export_csv", export_csv_node)
    workflow.add_node("format_response", format_response_node)

    if verbose:
        print(f"   ✅ Added 6 nodes: 1 router + 2 agent + 3 tools")

    # ===== DEFINE WORKFLOW EDGES =====

    # Entry point
    workflow.set_entry_point("router")

    # Conditional routing from router
    workflow.add_conditional_edges(
        "router",
        lambda state: state["query_type"],  # Use the router's decision
        {
            "data_query": "agent_intent_analysis",     # Full AI pipeline
            "schema_request": "format_response",        # Direct to formatter
            "help_request": "format_response"           # Direct to formatter
        }
    )

    # Data query workflow (full AI pipeline)
    workflow.add_edge("agent_intent_analysis", "agent_sql_generation")
    workflow.add_edge("agent_sql_generation", "execute_query")
    workflow.add_edge("execute_query", "export_csv")
    workflow.add_edge("export_csv", "format_response")

    # All paths end at format_response
    workflow.add_edge("format_response", END)

    if verbose:
        print(f"   ✅ Added conditional routing and linear execution flow")
        print(f"   🎯 Workflow paths:")
        print(f"      • Data queries: Router → Intent → SQL → Execute → CSV → Format → END")
        print(f"      • Schema/Help:  Router → Format → END")

    # Compile the graph
    compiled_graph = workflow.compile()

    if verbose:
        print(f"   ✅ Graph compiled successfully - ready for execution!")

    return compiled_graph