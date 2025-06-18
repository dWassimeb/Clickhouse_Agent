"""
Streamlined Smart Intent Analyzer - Essential functionality only
"""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import Field
import json
import logging
from llm.custom_gpt import CustomGPT
from config.schemas import TABLE_SCHEMAS, TABLE_RELATIONSHIPS, BUSINESS_SCENARIOS

logger = logging.getLogger(__name__)

class SmartIntentAnalyzerTool(BaseTool):
    """Streamlined LLM-powered intent analyzer for semantic understanding."""

    name: str = "analyze_intent"
    description: str = "Analyze user intent and map to database concepts efficiently."

    llm: CustomGPT = Field(default_factory=CustomGPT)

    def _run(self, user_question: str) -> Dict[str, Any]:
        """Perform streamlined semantic analysis of user question."""
        try:
            # Build focused schema context (only essential info)
            schema_context = self._build_focused_context()

            # Get LLM analysis
            llm_analysis = self._get_semantic_analysis(user_question, schema_context)

            # Parse and validate
            parsed_analysis = self._parse_analysis(llm_analysis)
            validated_analysis = self._validate_analysis(parsed_analysis)

            return {
                'success': True,
                'user_question': user_question,
                **validated_analysis,
                'message': "Intent analysis completed"
            }

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Intent analysis failed: {str(e)}"
            }

    def _build_focused_context(self) -> str:
        """Build minimal but complete schema context."""
        context = "# ClickHouse Database Schema\n\n"

        # Essential table info only
        for table_name, schema in TABLE_SCHEMAS.items():
            context += f"## {table_name}\n"
            context += f"Purpose: {schema.get('description', '')}\n"
            context += f"Key columns: "

            # Only show most important columns
            key_columns = []
            for col_name, col_info in schema.get('columns', {}).items():
                if (col_info.get('is_primary_key') or
                    col_info.get('foreign_key') or
                    col_info.get('is_geographic') or
                    col_info.get('is_temporal') or
                    'NAME' in col_name.upper()):
                    key_columns.append(f"{col_name} ({col_info['type']})")

            context += ", ".join(key_columns[:5]) + "\n\n"

        # Essential relationships
        context += "# Key Relationships\n"
        context += "- RM_AGGREGATED_DATA → CUSTOMER (via PARTY_ID) for customer names\n"
        context += "- RM_AGGREGATED_DATA → PLMN (via PLMN) for country info (COUNTRY_ISO3)\n"
        context += "- RM_AGGREGATED_DATA → CELL (via CELL_ID) for location coordinates\n\n"

        return context

    def _get_semantic_analysis(self, user_question: str, schema_context: str) -> str:
        """Get focused LLM analysis."""

        prompt = f"""Analyze this database query and provide a structured JSON response.

{schema_context}

User Question: "{user_question}"

Provide analysis as JSON:
{{
    "language": "french|english",
    "intent_analysis": {{
        "primary_intent": "geographic_distribution|customer_analysis|data_usage|temporal_analysis|general",
        "intent_confidence": 0.9,
        "business_scenario": "geographic_distribution|customer_ranking|data_analysis"
    }},
    "table_analysis": {{
        "required_tables": ["table1", "table2"],
        "primary_table": "main_table"
    }},
    "join_analysis": {{
        "required_joins": [
            {{
                "from_table": "table1",
                "to_table": "table2",
                "join_condition": "table1.col = table2.col",
                "purpose": "why needed"
            }}
        ]
    }},
    "column_analysis": {{
        "select_columns": [
            {{"column": "table.column", "purpose": "grouping|aggregation", "alias": "name"}}
        ],
        "aggregation_needed": true,
        "grouping_columns": ["table.column"]
    }},
    "temporal_analysis": {{
        "needs_time_filter": true,
        "time_column": "RECORD_OPENING_TIME",
        "time_period": "7 days",
        "time_filter_sql": "WHERE RECORD_OPENING_TIME >= now() - INTERVAL 7 DAY"
    }},
    "output_requirements": {{
        "needs_percentage": false,
        "suggested_limit": 10,
        "sort_order": "DESC"
    }}
}}

Critical: For geographic queries, ALWAYS use PLMN table for country data (COUNTRY_ISO3), never CELL table.

JSON Response:"""

        try:
            response = self.llm._call(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise

    def _parse_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM JSON response safely."""
        try:
            # Clean response
            clean_response = llm_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]

            parsed = json.loads(clean_response.strip())
            return parsed

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            # Fallback to basic analysis
            return self._create_fallback_analysis(llm_response)

    def _create_fallback_analysis(self, response: str) -> Dict[str, Any]:
        """Create fallback analysis if JSON parsing fails."""
        response_lower = response.lower()

        # Detect language
        language = "french" if any(word in response_lower for word in ['français', 'répartition', 'clients', 'données']) else "english"

        # Detect intent
        if any(word in response_lower for word in ['geographic', 'country', 'pays', 'répartition']):
            primary_intent = "geographic_distribution"
            tables = ["RM_AGGREGATED_DATA", "PLMN"]
        elif any(word in response_lower for word in ['customer', 'client', 'top']):
            primary_intent = "customer_analysis"
            tables = ["RM_AGGREGATED_DATA", "CUSTOMER"]
        else:
            primary_intent = "general"
            tables = ["RM_AGGREGATED_DATA"]

        return {
            "language": language,
            "intent_analysis": {
                "primary_intent": primary_intent,
                "intent_confidence": 0.7,
                "business_scenario": primary_intent
            },
            "table_analysis": {
                "required_tables": tables,
                "primary_table": "RM_AGGREGATED_DATA"
            },
            "join_analysis": {"required_joins": []},
            "column_analysis": {"select_columns": [], "aggregation_needed": True},
            "temporal_analysis": {"needs_time_filter": False},
            "output_requirements": {"suggested_limit": 100, "sort_order": "DESC"}
        }

    def _validate_analysis(self, parsed_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance analysis results."""

        # Ensure required tables exist
        table_analysis = parsed_analysis.get('table_analysis', {})
        required_tables = table_analysis.get('required_tables', [])

        valid_tables = [table for table in required_tables if table in TABLE_SCHEMAS]
        if not valid_tables:
            valid_tables = ["RM_AGGREGATED_DATA"]  # Fallback

        parsed_analysis['table_analysis']['required_tables'] = valid_tables

        # Set confidence
        intent_confidence = parsed_analysis.get('intent_analysis', {}).get('intent_confidence', 0.5)
        table_confidence = 1.0 if len(valid_tables) == len(required_tables) else 0.7

        parsed_analysis['overall_confidence'] = (intent_confidence + table_confidence) / 2

        return parsed_analysis