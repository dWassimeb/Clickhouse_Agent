"""
Query execution tool with embedded helper functions.
"""

from typing import Dict, Any
from langchain.tools import BaseTool
import re
import logging
from database.clickhouse.connection import clickhouse_connection

logger = logging.getLogger(__name__)

class QueryExecutionTool(BaseTool):
    """Tool for executing SQL queries safely on ClickHouse."""

    name: str = "execute_query"
    description: str = """
    Execute SQL queries on ClickHouse database safely.
    Validates queries, adds safety limits, and returns structured results.
    """

    def _run(self, sql_query: str) -> Dict[str, Any]:
        """Execute the SQL query safely."""
        try:
            # Validate query safety
            if not self._validate_query(sql_query):
                return {
                    'success': False,
                    'error': 'Query validation failed - potentially unsafe query',
                    'details': 'Only SELECT statements are allowed'
                }

            # Add safety limits
            safe_query = self._add_safety_limits(sql_query)

            # Execute the query
            result = clickhouse_connection.execute_query_with_names(safe_query)

            # Process results
            processed_result = self._process_results(result)

            return {
                'success': True,
                'result': processed_result,
                'executed_query': safe_query,
                'message': f"Query executed successfully"
            }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            error_info = self._parse_clickhouse_error(str(e))
            return {
                'success': False,
                'error': error_info['user_message'],
                'suggestion': error_info['suggestion'],
                'details': str(e)
            }

    def _validate_query(self, query: str) -> bool:
        """Validate SQL query for security and safety."""
        # Remove comments and normalize whitespace
        clean_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        clean_query = ' '.join(clean_query.split())
        clean_query = clean_query.upper()

        # Check for dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'EXEC', 'EXECUTE', 'SYSTEM'
        ]

        for keyword in dangerous_keywords:
            if keyword in clean_query:
                logger.warning(f"Dangerous keyword '{keyword}' found in query")
                return False

        # Ensure query starts with SELECT
        if not clean_query.strip().startswith('SELECT'):
            logger.warning("Query does not start with SELECT")
            return False

        return True

    def _add_safety_limits(self, query: str, default_limit: int = 1000) -> str:
        """Add LIMIT clause if not present."""
        query_upper = query.upper()
        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {default_limit}"
        return query

    def _process_results(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw query results into structured format."""
        if not raw_result['data']:
            return {
                'columns': raw_result['columns'],
                'data': [],
                'formatted_data': [],
                'row_count': 0,
                'summary': "No data found"
            }

        # Format data for better readability
        formatted_data = []
        for row in raw_result['data']:
            formatted_row = {}
            for i, col in enumerate(raw_result['columns']):
                value = row[i] if i < len(row) else None
                formatted_row[col] = self._format_value(value, raw_result['types'][i])
            formatted_data.append(formatted_row)

        return {
            'columns': raw_result['columns'],
            'data': raw_result['data'],
            'formatted_data': formatted_data,
            'types': raw_result['types'],
            'row_count': len(raw_result['data']),
            'summary': f"Found {len(raw_result['data'])} rows with {len(raw_result['columns'])} columns"
        }

    def _format_value(self, value: Any, data_type: str) -> Any:
        """Format individual values based on their type."""
        if value is None:
            return None

        if 'Int' in data_type or 'UInt' in data_type:
            return int(value)
        elif 'Float' in data_type or 'Decimal' in data_type:
            return float(value)
        elif 'DateTime' in data_type:
            return str(value)
        else:
            return value

    def _parse_clickhouse_error(self, error_msg: str) -> Dict[str, str]:
        """Parse ClickHouse error messages for user-friendly explanations."""
        error_info = {
            'type': 'unknown',
            'user_message': error_msg,
            'suggestion': None
        }

        error_lower = error_msg.lower()

        if "table doesn't exist" in error_lower or 'unknown table' in error_lower:
            error_info['type'] = 'table_not_found'
            error_info['user_message'] = "The specified table was not found"
            error_info['suggestion'] = "Use 'list tables' to see available tables"

        elif 'no such column' in error_lower or 'unknown identifier' in error_lower:
            error_info['type'] = 'column_not_found'
            error_info['user_message'] = "One or more columns don't exist"
            error_info['suggestion'] = "Check column names using 'schema TABLE_NAME'"

        elif 'syntax error' in error_lower:
            error_info['type'] = 'syntax_error'
            error_info['user_message'] = "SQL syntax error"
            error_info['suggestion'] = "Try rephrasing your question"

        elif 'timeout' in error_lower:
            error_info['type'] = 'timeout'
            error_info['user_message'] = "Query took too long to execute"
            error_info['suggestion'] = "Add more specific filters or reduce date range"

        return error_info