"""
Smart SQL generator that uses LLM with comprehensive schema context.
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
from pydantic import Field
import logging
from llm.custom_gpt import CustomGPT
from config.schemas import TABLE_SCHEMAS, TABLE_RELATIONSHIPS, BUSINESS_SCENARIOS

logger = logging.getLogger(__name__)

class SmartSqlGeneratorTool(BaseTool):
    """LLM-powered SQL generator with comprehensive schema understanding."""

    name: str = "generate_smart_sql"
    description: str = """
    Generate optimal SQL queries using LLM with full schema context and intent analysis.
    Produces highly accurate, business-relevant SQL based on semantic understanding.
    """

    # Declare LLM field for Pydantic v2
    llm: CustomGPT = Field(default_factory=CustomGPT)

    def _run(self, user_question: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query using pre-analyzed intent data."""
        try:
            # Validate intent analysis input
            if not intent_analysis:
                raise ValueError("Intent analysis is required for smart SQL generation")

            # Build focused SQL context based on intent analysis
            sql_context = self._build_focused_sql_context(intent_analysis)

            # Generate SQL with precise guidance
            sql_query = self._generate_targeted_sql(user_question, sql_context, intent_analysis)

            # Clean and validate SQL
            cleaned_sql = self._clean_and_validate_sql(sql_query)

            # Extract metadata from generated SQL
            sql_metadata = self._extract_sql_metadata(cleaned_sql, intent_analysis)

            return {
                'success': True,
                'sql_query': cleaned_sql,
                'sql_metadata': sql_metadata,
                'intent_confidence': intent_analysis.get('overall_confidence', 0.8),
                'message': "Smart SQL generation completed successfully"
            }

        except Exception as e:
            logger.error(f"Smart SQL generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Smart SQL generation failed: {str(e)}"
            }

    def _build_focused_sql_context(self, intent_analysis: Dict[str, Any]) -> str:
        """Build focused SQL context based on intent analysis results."""

        # Get required tables from intent analysis
        table_analysis = intent_analysis.get('table_analysis', {})
        required_tables = table_analysis.get('required_tables', ['RM_AGGREGATED_DATA'])

        # Build minimal, focused context for only the needed tables
        context = "# ClickHouse SQL Generation Context\n\n"

        # Add only relevant table schemas
        context += "## Required Tables:\n\n"
        for table_name in required_tables:
            if table_name in TABLE_SCHEMAS:
                schema = TABLE_SCHEMAS[table_name]
                context += f"### {table_name}\n"
                context += f"**Purpose:** {schema.get('description')}\n"

                # Only show columns that are likely to be used
                context += "**Key Columns:**\n"
                for col_name, col_info in schema.get('columns', {}).items():
                    context += f"- `{col_name}` ({col_info['type']}): {col_info['description']}\n"
                    if col_info.get('foreign_key'):
                        context += f"  → Links to: {col_info['foreign_key']}\n"
                context += "\n"

        # Add specific join patterns from intent analysis
        join_analysis = intent_analysis.get('join_analysis', {})
        required_joins = join_analysis.get('required_joins', [])
        if required_joins:
            context += "## Required Join Patterns:\n"
            for join in required_joins:
                context += f"**{join['from_table']} → {join['to_table']}:**\n"
                context += f"```sql\n{join['from_table']} {join['join_type']} {join['to_table']} ON {join['join_condition']}\n```\n"
                context += f"Purpose: {join['purpose']}\n\n"

        # Add business scenario template if detected
        intent_info = intent_analysis.get('intent_analysis', {})
        business_scenario = intent_info.get('business_scenario')
        if business_scenario and business_scenario in BUSINESS_SCENARIOS:
            scenario_info = BUSINESS_SCENARIOS[business_scenario]
            context += f"## Recommended SQL Pattern:\n"
            context += f"**Scenario:** {scenario_info['description']}\n"
            context += f"```sql\n{scenario_info['sql_template']}\n```\n\n"

        return context

    def _generate_targeted_sql(self, user_question: str, sql_context: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate SQL with highly targeted context - no redundant analysis."""

        # Build execution instructions based on intent analysis
        execution_instructions = self._build_execution_instructions(intent_analysis)

        prompt = f"""You are a ClickHouse SQL expert. Generate the precise SQL query based on the pre-analyzed intent and focused schema context.

{sql_context}

## Pre-Analyzed Intent Requirements:
{execution_instructions}

## User Question:
"{user_question}"

## Task:
Generate ONLY the SQL query that implements the analyzed requirements. Do not re-analyze the question - use the provided intent analysis.

Requirements:
- Use SELECT statements only
- Follow the exact join patterns provided
- Implement the specific aggregations and filters identified
- Use the recommended table aliases
- Include proper LIMIT clauses

SQL Query:"""

        try:
            response = self.llm._call(prompt)
            return response.strip()

        except Exception as e:
            logger.error(f"Targeted SQL generation failed: {e}")
            raise

    def _build_execution_instructions(self, intent_analysis: Dict[str, Any]) -> str:
        """Build precise execution instructions from intent analysis."""
        instructions = ""

        # Table instructions
        table_analysis = intent_analysis.get('table_analysis', {})
        if table_analysis.get('required_tables'):
            instructions += f"**Tables to use:** {', '.join(table_analysis['required_tables'])}\n"
            instructions += f"**Primary table:** {table_analysis.get('primary_table', 'RM_AGGREGATED_DATA')}\n"

        # Column instructions
        column_analysis = intent_analysis.get('column_analysis', {})
        if column_analysis.get('select_columns'):
            instructions += "**Select columns:**\n"
            for col in column_analysis['select_columns']:
                alias = f" AS {col['alias']}" if col.get('alias') else ""
                instructions += f"- {col['column']}{alias} ({col['purpose']})\n"

        if column_analysis.get('grouping_columns'):
            instructions += f"**Group by:** {', '.join(column_analysis['grouping_columns'])}\n"

        # Aggregation instructions
        if column_analysis.get('aggregation_needed'):
            agg_functions = column_analysis.get('aggregation_functions', ['COUNT'])
            instructions += f"**Aggregations:** {', '.join(agg_functions)}\n"

        # Join instructions
        join_analysis = intent_analysis.get('join_analysis', {})
        if join_analysis.get('required_joins'):
            instructions += "**Joins required:**\n"
            for join in join_analysis['required_joins']:
                instructions += f"- {join['from_table']} {join['join_type']} {join['to_table']} ON {join['join_condition']}\n"

        # Time filter instructions
        temporal_analysis = intent_analysis.get('temporal_analysis', {})
        if temporal_analysis.get('needs_time_filter'):
            instructions += f"**Time filter:** {temporal_analysis.get('time_filter_sql', 'WHERE RECORD_OPENING_TIME >= now() - INTERVAL 2 DAY')}\n"

        # Output requirements
        output_req = intent_analysis.get('output_requirements', {})
        if output_req.get('needs_percentage'):
            instructions += "**Percentage calculation:** COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ... WHERE same_conditions)\n"

        if output_req.get('suggested_limit'):
            instructions += f"**Limit:** LIMIT {output_req['suggested_limit']}\n"

        if output_req.get('sort_order') and output_req.get('sort_column'):
            instructions += f"**Sort:** ORDER BY {output_req['sort_column']} {output_req['sort_order']}\n"

        return instructions

    def _clean_and_validate_sql(self, sql_query: str) -> str:
        """Clean and validate the generated SQL."""
        # Remove markdown code blocks if present
        if sql_query.startswith('```'):
            lines = sql_query.split('\n')
            sql_query = '\n'.join(lines[1:-1]) if len(lines) > 2 else sql_query

        # Remove any trailing semicolon and whitespace
        sql_query = sql_query.rstrip(';').strip()

        # Basic validation
        if not sql_query.upper().strip().startswith('SELECT'):
            raise ValueError("Generated query must be a SELECT statement")

        # Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        sql_upper = sql_query.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"Query contains dangerous keyword: {keyword}")

        return sql_query

    def _extract_sql_metadata(self, sql_query: str, intent_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract metadata from the generated SQL."""
        metadata = {
            'query_type': 'SELECT',
            'estimated_complexity': 'medium',
            'tables_used': [],
            'joins_detected': [],
            'aggregations_used': [],
            'has_limit': False,
            'has_time_filter': False
        }

        sql_upper = sql_query.upper()

        # Detect tables
        for table_name in TABLE_SCHEMAS.keys():
            if table_name in sql_upper:
                metadata['tables_used'].append(table_name)

        # Detect joins
        if 'JOIN' in sql_upper:
            metadata['joins_detected'] = ['JOIN detected']
            metadata['estimated_complexity'] = 'high'

        # Detect aggregations
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']
        for func in agg_functions:
            if func in sql_upper:
                metadata['aggregations_used'].append(func)

        # Detect other patterns
        metadata['has_limit'] = 'LIMIT' in sql_upper
        metadata['has_time_filter'] = 'RECORD_OPENING_TIME' in sql_upper or 'INTERVAL' in sql_upper

        # Calculate complexity
        complexity_score = 0
        complexity_score += len(metadata['tables_used'])
        complexity_score += len(metadata['joins_detected']) * 2
        complexity_score += len(metadata['aggregations_used'])

        if complexity_score <= 2:
            metadata['estimated_complexity'] = 'simple'
        elif complexity_score <= 5:
            metadata['estimated_complexity'] = 'medium'
        else:
            metadata['estimated_complexity'] = 'complex'

        return metadata