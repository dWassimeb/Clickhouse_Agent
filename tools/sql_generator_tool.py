"""
SQL generator tool with embedded helper functions.
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
from pydantic import Field
import logging
from llm.custom_gpt import CustomGPT
from config.schemas import TABLE_SCHEMAS

logger = logging.getLogger(__name__)

class SqlGeneratorTool(BaseTool):
    """Tool for generating SQL queries from natural language."""

    name: str = "generate_sql"
    description: str = """
    Generate SQL queries from natural language questions.
    Takes user question and schema analysis to produce ClickHouse SQL.
    """

    # Properly declare the llm field for Pydantic v2
    llm: CustomGPT = Field(default_factory=CustomGPT)

    def _run(self, user_question: str, analysis_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate SQL query from natural language question."""
        try:
            # Get relevant tables from analysis or use all tables
            relevant_tables = []
            if analysis_data and analysis_data.get('relevant_tables'):
                relevant_tables = analysis_data['relevant_tables']

            # Build schema context
            schema_context = self._build_schema_context(relevant_tables)

            # Generate SQL
            sql_query = self._generate_sql_with_llm(user_question, schema_context, analysis_data)

            # Clean up the SQL
            cleaned_sql = self._clean_sql_query(sql_query)

            return {
                'success': True,
                'sql_query': cleaned_sql,
                'relevant_tables': relevant_tables,
                'message': f"Generated SQL query successfully"
            }

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to generate SQL: {str(e)}"
            }

    def _build_schema_context(self, table_names: List[str]) -> str:
        """Build schema context for LLM."""
        if not table_names:
            # Use all tables if none specified
            table_names = list(TABLE_SCHEMAS.keys())

        context = "# ClickHouse Database Schema\n\n"

        for table_name in table_names:
            if table_name in TABLE_SCHEMAS:
                schema = TABLE_SCHEMAS[table_name]
                context += f"## Table: {table_name}\n"
                context += f"Description: {schema.get('description', 'No description')}\n\n"
                context += "### Columns:\n"

                for col_name, col_info in schema.get('columns', {}).items():
                    context += f"- **{col_name}** ({col_info['type']}): {col_info['description']}\n"

                context += "\n"

        return context

    def _generate_sql_with_llm(self, user_question: str, schema_context: str, analysis_data: Dict[str, Any] = None) -> str:
        """Generate SQL using LLM."""

        # Build additional context from analysis
        analysis_context = ""
        if analysis_data:
            intent = analysis_data.get('query_intent', {})
            if intent.get('aggregation_needed'):
                analysis_context += "- This query needs aggregation (COUNT, SUM, AVG, etc.)\n"
            if intent.get('sorting_needed'):
                analysis_context += "- This query needs sorting (ORDER BY)\n"
            if intent.get('grouping_needed'):
                analysis_context += "- This query needs grouping (GROUP BY)\n"
            if intent.get('suggested_limit'):
                analysis_context += f"- Suggested LIMIT: {intent['suggested_limit']}\n"

        prompt = f"""You are an expert SQL developer working with a ClickHouse database. 
Your task is to generate a precise SQL query based on the user's natural language question.

{schema_context}

## Query Analysis:
{analysis_context}

## Important Guidelines:
1. Use ONLY SELECT statements - no INSERT, UPDATE, DELETE, or DDL operations
2. Always include appropriate LIMIT clauses (default 100 unless user specifies otherwise)
3. Use proper JOIN syntax when combining tables
4. Format dates using ClickHouse functions like toDate(), formatDateTime()
5. Use aggregate functions appropriately (SUM, COUNT, AVG, etc.)
6. Consider using HAVING clause for filtering aggregated results
7. Use ORDER BY for meaningful result ordering
8. Be careful with data types - use appropriate casting when needed

## User Question:
{user_question}

Generate ONLY the SQL query without any explanation or markdown formatting. The query should be executable and efficient.

SQL Query:"""

        try:
            sql_query = self.llm._call(prompt)
            return sql_query.strip()

        except Exception as e:
            logger.error(f"LLM SQL generation failed: {e}")
            raise Exception(f"Failed to generate SQL query: {str(e)}")

    def _clean_sql_query(self, query: str) -> str:
        """Clean and normalize SQL query."""
        # Remove markdown code blocks if present
        if query.startswith('```'):
            lines = query.split('\n')
            query = '\n'.join(lines[1:-1]) if len(lines) > 2 else query

        # Remove any trailing semicolon and whitespace
        query = query.rstrip(';').strip()

        # Remove extra whitespace
        query = ' '.join(query.split())

        return query

    def refine_sql(self, original_sql: str, user_feedback: str, schema_context: str) -> str:
        """Refine SQL query based on user feedback."""

        prompt = f"""You are refining a ClickHouse SQL query based on user feedback.

Original SQL Query:
{original_sql}

User Feedback:
{user_feedback}

Database Schema Context:
{schema_context}

Please generate an improved SQL query that addresses the user's feedback while maintaining the original intent.

Generate ONLY the refined SQL query without explanation:"""

        try:
            refined_sql = self.llm._call(prompt)
            return self._clean_sql_query(refined_sql)

        except Exception as e:
            logger.error(f"SQL refinement failed: {e}")
            raise Exception(f"Failed to refine SQL query: {str(e)}")

    def explain_query(self, sql_query: str, schema_context: str) -> str:
        """Generate a natural language explanation of the SQL query."""

        prompt = f"""Explain this ClickHouse SQL query in simple, non-technical language.
Focus on what data it retrieves and what business question it answers.

SQL Query:
{sql_query}

Database Schema Context:
{schema_context}

Provide a clear, concise explanation of what this query does:"""

        try:
            explanation = self.llm._call(prompt)
            return explanation.strip()

        except Exception as e:
            logger.error(f"Query explanation failed: {e}")
            return f"Unable to explain query: {str(e)}"