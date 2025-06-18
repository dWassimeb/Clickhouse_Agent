"""
Streamlined Smart SQL Generator - Focused on efficient SQL generation
"""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import Field
import logging
from llm.custom_gpt import CustomGPT
from config.schemas import TABLE_SCHEMAS

logger = logging.getLogger(__name__)

class SmartSqlGeneratorTool(BaseTool):
    """Streamlined SQL generator focused on accurate ClickHouse queries."""

    name: str = "generate_smart_sql"
    description: str = "Generate optimal SQL queries from intent analysis efficiently."

    llm: CustomGPT = Field(default_factory=CustomGPT)

    def _run(self, user_question: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query from pre-analyzed intent."""
        try:
            # Validate input
            if not intent_analysis:
                raise ValueError("Intent analysis required for SQL generation")

            # Build focused context
            sql_context = self._build_sql_context(intent_analysis)

            # Generate SQL
            sql_query = self._generate_sql(user_question, sql_context, intent_analysis)

            # Validate and clean
            cleaned_sql = self._clean_sql(sql_query)

            # Extract metadata
            metadata = self._extract_metadata(cleaned_sql)

            return {
                'success': True,
                'sql_query': cleaned_sql,
                'sql_metadata': metadata,
                'message': "SQL generated successfully"
            }

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"SQL generation failed: {str(e)}"
            }

    def _build_sql_context(self, intent_analysis: Dict[str, Any]) -> str:
        """Build minimal SQL context based on intent."""

        # Get required tables
        table_analysis = intent_analysis.get('table_analysis', {})
        required_tables = table_analysis.get('required_tables', ['RM_AGGREGATED_DATA'])

        context = "# ClickHouse SQL Context\n\n"

        # Only include relevant table schemas
        for table_name in required_tables:
            if table_name in TABLE_SCHEMAS:
                schema = TABLE_SCHEMAS[table_name]
                context += f"## {table_name}\n"

                # Essential columns only
                for col_name, col_info in schema.get('columns', {}).items():
                    context += f"- {col_name} ({col_info['type']}): {col_info['description']}\n"
                context += "\n"

        # Add specific join patterns if needed
        join_analysis = intent_analysis.get('join_analysis', {})
        required_joins = join_analysis.get('required_joins', [])
        if required_joins:
            context += "# Required Joins:\n"
            for join in required_joins:
                context += f"- {join['from_table']} JOIN {join['to_table']} ON {join['join_condition']}\n"
            context += "\n"

        # Add ClickHouse specifics
        context += """# ClickHouse Functions:
- toDate(column) - Convert to date
- now() - Current timestamp  
- INTERVAL X DAY - Time intervals
- COUNT(*) - Count rows
- Percentage: COUNT(*) * 100.0 / (SELECT COUNT(*) FROM table WHERE conditions)

# Critical Rules:
- Geographic queries: Use PLMN.COUNTRY_ISO3 for countries
- Time filters: Use RECORD_OPENING_TIME for date filtering
- Always include LIMIT clauses
"""

        return context

    def _generate_sql(self, user_question: str, sql_context: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate SQL with focused prompting."""

        # Build execution instructions
        instructions = self._build_instructions(intent_analysis)

        prompt = f"""Generate ClickHouse SQL query based on analyzed intent.

{sql_context}

## Analyzed Requirements:
{instructions}

## User Question: "{user_question}"

Generate ONLY the SQL query - no explanations or markdown.
Requirements:
- Use SELECT statements only
- Follow ClickHouse syntax (toDate, now(), INTERVAL)
- Include appropriate LIMIT
- For geographic analysis: ALWAYS use PLMN.COUNTRY_ISO3

SQL Query:"""

        try:
            response = self.llm._call(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise

    def _build_instructions(self, intent_analysis: Dict[str, Any]) -> str:
        """Build concise execution instructions."""
        instructions = []

        # Tables
        table_analysis = intent_analysis.get('table_analysis', {})
        if table_analysis.get('required_tables'):
            instructions.append(f"Tables: {', '.join(table_analysis['required_tables'])}")

        # Joins
        join_analysis = intent_analysis.get('join_analysis', {})
        if join_analysis.get('required_joins'):
            join_count = len(join_analysis['required_joins'])
            instructions.append(f"Joins: {join_count} required")

        # Columns
        column_analysis = intent_analysis.get('column_analysis', {})
        if column_analysis.get('aggregation_needed'):
            instructions.append("Aggregation: Required")
        if column_analysis.get('grouping_columns'):
            instructions.append(f"Group by: {', '.join(column_analysis['grouping_columns'])}")

        # Time filters
        temporal_analysis = intent_analysis.get('temporal_analysis', {})
        if temporal_analysis.get('needs_time_filter'):
            period = temporal_analysis.get('time_period', '7 days')
            instructions.append(f"Time filter: Last {period}")

        # Output
        output_req = intent_analysis.get('output_requirements', {})
        if output_req.get('needs_percentage'):
            instructions.append("Calculate: Percentages")
        if output_req.get('suggested_limit'):
            instructions.append(f"Limit: {output_req['suggested_limit']}")

        return "\n".join([f"- {inst}" for inst in instructions])

    def _clean_sql(self, sql_query: str) -> str:
        """Clean and validate SQL."""
        # Remove markdown
        if sql_query.startswith('```'):
            lines = sql_query.split('\n')
            sql_query = '\n'.join(lines[1:-1]) if len(lines) > 2 else sql_query

        # Clean up
        sql_query = sql_query.rstrip(';').strip()

        # Basic validation
        sql_upper = sql_query.upper()
        if not sql_upper.startswith('SELECT'):
            raise ValueError("Query must be a SELECT statement")

        # Check for dangerous keywords
        dangerous = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        for keyword in dangerous:
            if keyword in sql_upper:
                raise ValueError(f"Dangerous keyword detected: {keyword}")

        return sql_query

    def _extract_metadata(self, sql_query: str) -> Dict[str, Any]:
        """Extract basic metadata from SQL."""
        sql_upper = sql_query.upper()

        # Find tables
        tables_used = []
        for table_name in TABLE_SCHEMAS.keys():
            if table_name in sql_upper:
                tables_used.append(table_name)

        # Detect features
        has_joins = 'JOIN' in sql_upper
        has_aggregation = any(func in sql_upper for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'])
        has_limit = 'LIMIT' in sql_upper
        has_time_filter = 'RECORD_OPENING_TIME' in sql_upper

        # Estimate complexity
        complexity_score = len(tables_used) + (2 if has_joins else 0) + (1 if has_aggregation else 0)
        if complexity_score <= 2:
            complexity = "simple"
        elif complexity_score <= 4:
            complexity = "medium"
        else:
            complexity = "complex"

        return {
            'query_type': 'SELECT',
            'tables_used': tables_used,
            'estimated_complexity': complexity,
            'has_joins': has_joins,
            'has_aggregation': has_aggregation,
            'has_limit': has_limit,
            'has_time_filter': has_time_filter,
            'aggregations_used': [func for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'] if func in sql_upper]
        }