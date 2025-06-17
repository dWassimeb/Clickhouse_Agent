"""
Smart intent analyzer that uses LLM for semantic understanding.
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
from pydantic import Field
import json
import logging
from llm.custom_gpt import CustomGPT
from config.schemas import TABLE_SCHEMAS, TABLE_RELATIONSHIPS, BUSINESS_SCENARIOS

logger = logging.getLogger(__name__)

class SmartIntentAnalyzerTool(BaseTool):
    """LLM-powered intent analyzer for semantic understanding of user queries."""

    name: str = "analyze_intent"
    description: str = """
    Use LLM to understand user intent, detect language, identify relevant tables,
    suggest optimal joins, and provide schema guidance for SQL generation.
    """

    # Declare LLM field for Pydantic v2
    llm: CustomGPT = Field(default_factory=CustomGPT)

    def _run(self, user_question: str) -> Dict[str, Any]:
        """Perform LLM-powered semantic analysis of user question."""
        try:
            # Build comprehensive schema context for LLM
            schema_context = self._build_comprehensive_schema_context()

            # Get LLM analysis
            llm_analysis = self._get_llm_semantic_analysis(user_question, schema_context)

            # Parse LLM response
            parsed_analysis = self._parse_llm_analysis(llm_analysis)

            # Validate and enhance the analysis
            validated_analysis = self._validate_and_enhance_analysis(parsed_analysis, user_question)

            return {
                'success': True,
                'user_question': user_question,
                'llm_raw_analysis': llm_analysis,
                **validated_analysis,
                'message': "Smart intent analysis completed successfully"
            }

        except Exception as e:
            logger.error(f"Smart intent analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Smart intent analysis failed: {str(e)}"
            }

    def _build_comprehensive_schema_context(self) -> str:
        """Build comprehensive schema context for LLM understanding."""
        context = """# ClickHouse Database Schema - Complete Reference

## Database Overview
This is a telecommunications database containing mobile communication session data, with geographic and customer information.

## Tables and Relationships

"""

        # Add detailed table information
        for table_name, schema in TABLE_SCHEMAS.items():
            context += f"### {table_name}\n"
            context += f"**Purpose:** {schema.get('description', 'No description')}\n"
            context += f"**Business Context:** {schema.get('business_context', 'General table')}\n"
            context += f"**Primary Key:** {schema.get('primary_key', 'Unknown')}\n"
            context += f"**Common Use Cases:** {', '.join(schema.get('common_queries', []))}\n\n"

            context += "**Columns:**\n"
            for col_name, col_info in schema.get('columns', {}).items():
                context += f"- **{col_name}** ({col_info['type']}): {col_info['description']}\n"

                # Add business meaning if available
                if col_info.get('business_meaning'):
                    context += f"  - Business meaning: {col_info['business_meaning']}\n"

                # Add foreign key information
                if col_info.get('foreign_key'):
                    context += f"  - Links to: {col_info['foreign_key']}\n"

                # Add special attributes
                if col_info.get('is_geographic'):
                    context += f"  - Geographic data: Use for location analysis\n"
                if col_info.get('aggregatable'):
                    context += f"  - Can be aggregated: {col_info.get('unit', '')}\n"
                if col_info.get('is_temporal'):
                    context += f"  - Time field: Use for date filtering\n"
                if col_info.get('enum_values'):
                    context += f"  - Values: {col_info['enum_values']}\n"

            context += "\n"

        # Add relationship information
        context += "## Table Relationships and Join Patterns\n\n"
        for main_table, relationships in TABLE_RELATIONSHIPS.items():
            if 'joins_to' in relationships:
                context += f"### {main_table} Joins:\n"
                for target_table, join_info in relationships['joins_to'].items():
                    context += f"**To {target_table}:**\n"
                    context += f"- SQL: `{join_info['join_sql']}`\n"
                    context += f"- Purpose: {join_info['purpose']}\n"
                    context += f"- Relationship: {join_info['relationship']}\n"
                    context += f"- When to use: {join_info['purpose']}\n\n"

        # Add business scenarios
        context += "## Common Business Scenarios\n\n"
        for scenario_name, scenario_info in BUSINESS_SCENARIOS.items():
            context += f"### {scenario_name.replace('_', ' ').title()}\n"
            context += f"**Description:** {scenario_info['description']}\n"
            context += f"**Keywords:** {', '.join(scenario_info['keywords'])}\n"
            context += f"**Required Tables:** {', '.join(scenario_info['required_tables'])}\n"
            context += f"**SQL Template:**\n```sql\n{scenario_info['sql_template']}\n```\n\n"

        return context

    def _get_llm_semantic_analysis(self, user_question: str, schema_context: str) -> str:
        """Get LLM's semantic analysis of the user question."""

        prompt = f"""You are an expert database analyst and SQL architect. Analyze the user's question in the context of the provided database schema and provide a comprehensive semantic analysis.

{schema_context}

## User Question
"{user_question}"

## Task
Provide a detailed JSON analysis with the following structure:

```json
{{
    "language": "english|french|other",
    "language_confidence": 0.95,
    "intent_analysis": {{
        "primary_intent": "geographic_distribution|data_usage|customer_analysis|temporal_analysis|general_query",
        "intent_confidence": 0.9,
        "intent_description": "Clear description of what user wants to achieve",
        "business_scenario": "matching scenario from the provided scenarios"
    }},
    "table_analysis": {{
        "required_tables": ["table1", "table2"],
        "table_reasoning": {{
            "table1": "Why this table is needed",
            "table2": "Why this table is needed"
        }},
        "primary_table": "main table for the query"
    }},
    "join_analysis": {{
        "required_joins": [
            {{
                "from_table": "table1",
                "to_table": "table2", 
                "join_condition": "table1.col = table2.col",
                "purpose": "why this join is needed",
                "join_type": "INNER|LEFT|RIGHT"
            }}
        ],
        "join_reasoning": "Overall explanation of join strategy"
    }},
    "column_analysis": {{
        "select_columns": [
            {{
                "column": "table.column_name",
                "purpose": "for grouping|aggregation|display",
                "alias": "suggested alias"
            }}
        ],
        "aggregation_needed": true,
        "aggregation_functions": ["COUNT", "SUM", "AVG"],
        "grouping_columns": ["table.column"],
        "filtering_columns": ["table.column"]
    }},
    "temporal_analysis": {{
        "needs_time_filter": true,
        "time_column": "table.time_column",
        "time_period": "2 days|1 week|1 month",
        "time_filter_sql": "WHERE column >= now() - INTERVAL X DAY"
    }},
    "output_requirements": {{
        "needs_percentage": true,
        "needs_ranking": true,
        "suggested_limit": 10,
        "sort_order": "DESC|ASC",
        "sort_column": "suggested sort column"
    }},
    "sql_guidance": {{
        "complexity_level": "simple|medium|complex",
        "key_challenges": ["challenge1", "challenge2"],
        "critical_considerations": ["consideration1", "consideration2"],
        "recommended_approach": "step by step approach"
    }},
    "semantic_keywords": ["key", "concepts", "extracted", "from", "question"]
}}
```

## Important Guidelines:
1. **Language Detection**: Use semantic clues, not just keyword matching
2. **Intent Understanding**: Focus on business meaning, not just technical requirements  
3. **Table Selection**: Choose tables based on actual data needs, not just keyword matches
4. **Join Strategy**: Think about data flow and relationships logically
5. **Geographic Queries**: For country/geographic analysis, ALWAYS use PLMN table for country data (COUNTRY_ISO3)
6. **Percentage Calculations**: Structure for proper percentage calculation with subqueries
7. **Time Filters**: Extract time periods intelligently from natural language

Analyze the question semantically and provide the most accurate technical implementation guidance.

Response (JSON only):"""

        try:
            response = self.llm._call(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"LLM semantic analysis failed: {e}")
            raise

    def _parse_llm_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM JSON response safely."""
        try:
            # Clean the response - remove markdown if present
            clean_response = llm_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]

            # Parse JSON
            parsed = json.loads(clean_response.strip())
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {llm_response}")

            # Fallback parsing - extract key information manually
            return self._fallback_parse(llm_response)

    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """Fallback parsing if JSON parsing fails."""
        # Basic fallback structure
        fallback = {
            "language": "english",
            "language_confidence": 0.5,
            "intent_analysis": {
                "primary_intent": "general_query",
                "intent_confidence": 0.5,
                "intent_description": "Could not parse intent clearly"
            },
            "table_analysis": {
                "required_tables": ["RM_AGGREGATED_DATA"],
                "primary_table": "RM_AGGREGATED_DATA"
            },
            "sql_guidance": {
                "complexity_level": "medium",
                "recommended_approach": "Use fallback analysis"
            }
        }

        # Try to extract some basic information
        if any(word in response.lower() for word in ['french', 'français', 'pays', 'répartition']):
            fallback["language"] = "french"

        if any(word in response.lower() for word in ['geographic', 'country', 'pays']):
            fallback["intent_analysis"]["primary_intent"] = "geographic_distribution"
            fallback["table_analysis"]["required_tables"] = ["RM_AGGREGATED_DATA", "PLMN"]

        return fallback

    def _validate_and_enhance_analysis(self, parsed_analysis: Dict[str, Any], user_question: str) -> Dict[str, Any]:
        """Validate LLM analysis and add enhancements."""

        # Ensure required tables exist
        table_analysis = parsed_analysis.get('table_analysis', {})
        required_tables = table_analysis.get('required_tables', [])

        valid_tables = []
        for table in required_tables:
            if table in TABLE_SCHEMAS:
                valid_tables.append(table)
            else:
                logger.warning(f"LLM suggested invalid table: {table}")

        if not valid_tables:
            valid_tables = ["RM_AGGREGATED_DATA"]  # Fallback

        parsed_analysis['table_analysis']['required_tables'] = valid_tables

        # Validate join analysis
        join_analysis = parsed_analysis.get('join_analysis', {})
        if join_analysis.get('required_joins'):
            validated_joins = []
            for join in join_analysis['required_joins']:
                from_table = join.get('from_table')
                to_table = join.get('to_table')
                if from_table in TABLE_SCHEMAS and to_table in TABLE_SCHEMAS:
                    validated_joins.append(join)
            parsed_analysis['join_analysis']['required_joins'] = validated_joins

        # Add confidence scoring
        parsed_analysis['overall_confidence'] = self._calculate_confidence(parsed_analysis, user_question)

        return parsed_analysis

    def _calculate_confidence(self, analysis: Dict[str, Any], user_question: str) -> float:
        """Calculate overall confidence in the analysis."""
        confidence_factors = []

        # Language confidence
        lang_conf = analysis.get('language_confidence', 0.5)
        confidence_factors.append(lang_conf)

        # Intent confidence
        intent_conf = analysis.get('intent_analysis', {}).get('intent_confidence', 0.5)
        confidence_factors.append(intent_conf)

        # Table validation
        required_tables = analysis.get('table_analysis', {}).get('required_tables', [])
        valid_table_ratio = len([t for t in required_tables if t in TABLE_SCHEMAS]) / max(len(required_tables), 1)
        confidence_factors.append(valid_table_ratio)

        return sum(confidence_factors) / len(confidence_factors)