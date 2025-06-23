"""
Graph Builder - Constructs the LangGraph workflow with Smart Schema Tool and Visualization
"""

from langgraph.graph import StateGraph, END
from core.state import ClickHouseAgentState
from core.router import smart_router_node, route_condition
from core.tool_nodes import execute_query_node, export_csv_node, format_response_node, smart_schema_node, create_visualization_node

def create_clickhouse_graph(verbose: bool = True) -> StateGraph:
    """
    Create the complete LangGraph workflow for the ClickHouse Agent.

    This function builds the entire graph structure with:
    - Smart LLM-powered router for decision making
    - Agent nodes for reasoning
    - Tool nodes for execution including Smart Schema Tool and Modern Visualization
    - Proper conditional edges and flow control

    Args:
        verbose: Whether to enable verbose logging

    Returns:
        Compiled StateGraph ready for execution
    """

    if verbose:
        print(f"🔧 GRAPH BUILDER: Constructing LangGraph workflow")
        print(f"   📋 Components: Smart Router + Agent + Tools + Schema + Visualization")
        print(f"   🤖 Router: LLM-powered intent classification")
        print(f"   🧠 Schema: LLM-powered with ClickHouse SDK integration")
        print(f"   📈 Visualization: Modern interactive charts with Chart.js")
        print(f"   🔀 Flow: Conditional routing with specialized tool execution")

    # Initialize the agent for reasoning nodes
    from core.agent import ClickHouseAgent
    agent = ClickHouseAgent(verbose=verbose)

    # Create the StateGraph
    workflow = StateGraph(ClickHouseAgentState)

    # ===== ADD NODES =====

    # Smart Router node (LLM-powered entry point with decision making)
    workflow.add_node("router", smart_router_node)

    # Agent nodes (AI reasoning and decision making)
    workflow.add_node("agent_intent_analysis", agent.analyze_intent)
    workflow.add_node("agent_sql_generation", agent.generate_sql)

    # Tool nodes (execution and processing)
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("export_csv", export_csv_node)
    workflow.add_node("create_visualization", create_visualization_node)
    workflow.add_node("format_response", format_response_node)
    workflow.add_node("smart_schema", smart_schema_node)

    if verbose:
        print(f"   ✅ Added 8 nodes: 1 smart router + 2 agent + 5 tools")

    # ===== DEFINE WORKFLOW EDGES =====

    # Entry point
    workflow.set_entry_point("router")

    # Conditional routing from smart router
    workflow.add_conditional_edges(
        "router",
        route_condition,  # Uses LLM classification results
        {
            "data_query": "agent_intent_analysis",     # Full AI pipeline with visualization
            "schema_request": "smart_schema",           # Smart schema tool
            "help_request": "format_response"           # Direct to formatter
        }
    )

    # Data query workflow (full AI pipeline with visualization)
    workflow.add_edge("agent_intent_analysis", "agent_sql_generation")
    workflow.add_edge("agent_sql_generation", "execute_query")
    workflow.add_edge("execute_query", "export_csv")
    workflow.add_edge("export_csv", "create_visualization")
    workflow.add_edge("create_visualization", "format_response")

    # Schema workflow (smart schema processing)
    workflow.add_edge("smart_schema", END)

    # Help workflow
    workflow.add_edge("format_response", END)

    if verbose:
        print(f"   ✅ Added conditional routing and specialized execution flows")
        print(f"   🎯 Workflow paths:")
        print(f"      • Data queries: Router → Intent → SQL → Execute → CSV → Visualization → Format → END")
        print(f"      • Schema queries: Router → Smart Schema → END")
        print(f"      • Help requests: Router → Format → END")
        print(f"   🧠 Smart features: LLM routing + ClickHouse SDK schema + Interactive visualizations")

    # Compile the graph
    compiled_graph = workflow.compile()

    if verbose:
        print(f"   ✅ Graph compiled successfully - ready for execution!")

    return compiled_graph