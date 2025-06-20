"""
Smart Router Node - LLM-powered decision making logic for the ClickHouse Agent
"""

from typing import Literal
import json
import logging
from core.state import ClickHouseAgentState
from llm.custom_gpt import CustomGPT

logger = logging.getLogger(__name__)

def smart_router_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Smart router node that uses LLM to analyze the user question and decide workflow path.

    This router can understand intent across languages (French/English) and make
    intelligent routing decisions based on semantic understanding rather than keywords.

    Args:
        state: Current agent state containing the user question

    Returns:
        Modified state with query_type set based on LLM analysis
    """

    question = state["user_question"].strip()

    # Router reasoning (verbose logging)
    if state.get("verbose", False):
        print(f"\n🧭 SMART ROUTER: Analyzing question with LLM")
        print(f"   📝 Question: '{question}'")
        print(f"   🤖 Using AI to understand intent and language")

    try:
        # Use LLM to classify the question
        llm = CustomGPT()
        classification = _classify_question_with_llm(llm, question)

        # Set the query type based on LLM decision
        state["query_type"] = classification["query_type"]

        if state.get("verbose", False):
            language = classification.get("language", "unknown")
            confidence = classification.get("confidence", 0.0)
            reasoning = classification.get("reasoning", "No reasoning provided")

            print(f"   🧭 LLM ANALYSIS:")
            print(f"      Language: {language}")
            print(f"      Intent: {classification['query_type']}")
            print(f"      Confidence: {confidence:.2f}")
            print(f"      Reasoning: {reasoning}")
            print(f"   ➡️  ROUTE: {_get_route_description(classification['query_type'])}")

    except Exception as e:
        logger.error(f"Smart router LLM analysis failed: {e}")
        # Fallback to data_query for safety
        state["query_type"] = "data_query"
        if state.get("verbose", False):
            print(f"   ❌ LLM analysis failed: {e}")
            print(f"   🔄 FALLBACK: Defaulting to data_query route")

    return state

def route_condition(state: ClickHouseAgentState) -> Literal["data_query", "schema_request", "help_request"]:
    """
    Condition function for conditional edges.
    This function only returns the routing decision based on the state.
    """
    return state["query_type"]

def _classify_question_with_llm(llm: CustomGPT, question: str) -> dict:
    """
    Use LLM to classify the user question into appropriate workflow categories.

    Args:
        llm: The CustomGPT instance
        question: User's question to classify

    Returns:
        Dict with classification results
    """

    prompt = f"""You are a smart router for a ClickHouse database agent. Analyze the user question and classify it into one of three categories.

**Categories:**
1. **data_query**: Questions asking for data from the database (analytics, counts, reports, statistics, etc.)
   - Examples: "How many customers?", "Show top 10...", "What is the total...", "Combien de clients...", "Répartition par..."
   
2. **schema_request**: Questions asking about database structure, tables, or columns
   - Examples: "List tables", "Show schema", "What tables exist?", "Quelles sont les tables?", "Structure de la base"
   
3. **help_request**: Questions asking for help on HOW TO USE THE AGENT itself
   - Examples: "How do I use this?", "Help me", "What can you do?", "Comment utiliser cet agent?", "Aide"

**IMPORTANT**: 
- Most business questions about data should be "data_query"
- Only classify as "help_request" if user is asking about agent usage, not data
- The agent can handle both French and English

**User Question**: "{question}"

Respond with JSON only:
{{
    "query_type": "data_query|schema_request|help_request",
    "language": "french|english|mixed",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why you chose this classification"
}}

JSON Response:"""

    try:
        response = llm._call(prompt)

        # Clean and parse response
        clean_response = response.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]

        parsed = json.loads(clean_response.strip())

        # Validate the response
        valid_types = ["data_query", "schema_request", "help_request"]
        if parsed.get("query_type") not in valid_types:
            raise ValueError(f"Invalid query_type: {parsed.get('query_type')}")

        # Ensure confidence is a float between 0 and 1
        confidence = float(parsed.get("confidence", 0.8))
        parsed["confidence"] = max(0.0, min(1.0, confidence))

        return parsed

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"LLM classification parsing failed: {e}, response: {response}")
        # Return safe fallback
        return {
            "query_type": "data_query",
            "language": "unknown",
            "confidence": 0.5,
            "reasoning": f"Failed to parse LLM response, defaulting to data_query. Error: {str(e)}"
        }

def _get_route_description(query_type: str) -> str:
    """Get human-readable description of the route."""
    descriptions = {
        "data_query": "Through AI analysis pipeline (Intent → SQL → Execute)",
        "schema_request": "Direct to response formatter (database structure)",
        "help_request": "Direct to response formatter (usage instructions)"
    }
    return descriptions.get(query_type, "Unknown route")

# Keep the old router as backup
def simple_router_node(state: ClickHouseAgentState) -> ClickHouseAgentState:
    """
    Fallback simple keyword-based router (backup option).
    """
    question = state["user_question"].lower().strip()

    # Schema requests
    schema_keywords = ["list tables", "show tables", "schema", "table structure", "describe table",
                      "quelles tables", "structure", "liste des tables"]
    if any(keyword in question for keyword in schema_keywords):
        state["query_type"] = "schema_request"
        return state

    # Help requests - ONLY for agent usage questions
    help_keywords = ["how to use", "how do i", "comment utiliser", "aide pour utiliser",
                    "agent help", "usage help", "how does this work"]
    if any(keyword in question for keyword in help_keywords):
        state["query_type"] = "help_request"
        return state

    # Default to data query
    state["query_type"] = "data_query"
    return state