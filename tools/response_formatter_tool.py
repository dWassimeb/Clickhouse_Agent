"""
Response formatter tool with embedded helper functions.
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseFormatterTool(BaseTool):
    """Tool for formatting query results and responses for user presentation."""

    name: str = "format_response"
    description: str = """
    Format query results into clear, structured responses for users.
    Takes query results and creates readable tables, insights, and summaries.
    """

    def _run(self, query_result: Dict[str, Any], user_question: str = "", response_type: str = "query", csv_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format the response based on type and content."""
        try:
            if response_type == "schema":
                formatted_response = self._format_schema_response(query_result)
            elif response_type == "error":
                formatted_response = self._format_error_response(query_result)
            else:
                formatted_response = self._format_query_response(query_result, user_question, csv_result)

            return {
                'success': True,
                'formatted_response': formatted_response,
                'message': "Response formatted successfully"
            }

        except Exception as e:
            logger.error(f"Response formatting error: {e}")
            return {
                'success': False,
                'error': str(e),
                'formatted_response': f"Error formatting response: {str(e)}"
            }

    def _format_query_response(self, result: Dict[str, Any], user_question: str, csv_result: Dict[str, Any] = None) -> str:
        """Format query results into a structured response."""
        if not result.get('success', True):
            return self._format_error_response(result)

        query_result = result.get('result', {})

        if not query_result.get('data'):
            return "📭 **No Data Found**\n\nThe query executed successfully but returned no results."

        # Build formatted response
        response_parts = []

        # Add summary
        summary = query_result.get('summary', '')
        response_parts.append(f"📊 **Query Results Summary**\n{summary}")

        # Add data table
        formatted_table = self._format_data_table(query_result)
        if formatted_table:
            response_parts.append(f"📋 **Data Table**\n{formatted_table}")

        # Add insights if data is suitable for analysis
        insights = self._generate_insights(query_result)
        if insights:
            response_parts.append(f"💡 **Key Insights**\n{insights}")

        # Add CSV download information
        if csv_result and csv_result.get('success', False):
            csv_info = self._format_csv_download_info(csv_result)
            response_parts.append(csv_info)

        # Add query information
        if result.get('executed_query'):
            response_parts.append(f"🔍 **Executed Query**\n```sql\n{result['executed_query']}\n```")

        return "\n\n".join(response_parts)

    def _format_data_table(self, query_result: Dict[str, Any]) -> str:
        """Format data into a readable table."""
        try:
            columns = query_result.get('columns', [])
            data = query_result.get('data', [])

            if not columns or not data:
                return ""

            # Limit display to first 20 rows for readability
            display_data = data[:20]

            # Calculate column widths
            col_widths = {}
            for i, col in enumerate(columns):
                col_widths[i] = max(len(str(col)), 10)  # Minimum width of 10

                for row in display_data:
                    if i < len(row):
                        col_widths[i] = max(col_widths[i], len(str(row[i])))

                # Cap maximum width at 30 characters
                col_widths[i] = min(col_widths[i], 30)

            # Build table
            table_lines = []

            # Header
            header = " | ".join(f"{col:<{col_widths[i]}}" for i, col in enumerate(columns))
            table_lines.append(header)

            # Separator
            separator = " | ".join("-" * col_widths[i] for i in range(len(columns)))
            table_lines.append(separator)

            # Data rows
            for row in display_data:
                formatted_row = []
                for i, col in enumerate(columns):
                    value = row[i] if i < len(row) else ""
                    formatted_value = self._format_cell_value(value)

                    # Truncate if too long
                    if len(formatted_value) > 30:
                        formatted_value = formatted_value[:27] + "..."

                    formatted_row.append(f"{formatted_value:<{col_widths[i]}}")

                table_lines.append(" | ".join(formatted_row))

            table_str = "```\n" + "\n".join(table_lines) + "\n```"

            # Add note if data was truncated
            if len(data) > 20:
                table_str += f"\n*Showing first 20 of {len(data)} rows*"

            return table_str

        except Exception as e:
            logger.error(f"Table formatting error: {e}")
            return "Error formatting table data"

    def _format_cell_value(self, value: Any) -> str:
        """Format individual cell values for display."""
        if value is None:
            return "NULL"
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            elif isinstance(value, float):
                return f"{value:.2f}"
            else:
                return str(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(value)

    def _generate_insights(self, query_result: Dict[str, Any]) -> str:
        """Generate basic insights from query results."""
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])

            if not data or not columns:
                return ""

            insights = []

            # Row count insight
            insights.append(f"• Found {len(data)} records")

            # Analyze numeric columns
            for i, col in enumerate(columns):
                numeric_values = []
                for row in data:
                    if i < len(row) and isinstance(row[i], (int, float)):
                        numeric_values.append(row[i])

                if numeric_values and len(numeric_values) > 1:
                    avg_val = sum(numeric_values) / len(numeric_values)
                    max_val = max(numeric_values)
                    min_val = min(numeric_values)

                    insights.append(f"• {col}: Average {avg_val:.2f}, Range {min_val} - {max_val}")

            # Unique values for categorical columns
            for i, col in enumerate(columns):
                unique_values = set()
                for row in data:
                    if i < len(row) and row[i] is not None:
                        unique_values.add(row[i])

                if len(unique_values) <= 10 and len(unique_values) > 1:
                    insights.append(f"• {col}: {len(unique_values)} unique values")

            return "\n".join(insights[:5])  # Limit to 5 insights

        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            return ""

    def _format_schema_response(self, schema_result: Dict[str, Any]) -> str:
        """Format schema information for display."""
        if not schema_result.get('success', True):
            return f"❌ **Schema Error:** {schema_result.get('error', 'Unknown error')}"

        if 'tables' in schema_result:
            # List of tables
            response_parts = ["📚 **Available Tables**\n"]

            for table_name, table_description in schema_result['tables'].items():
                response_parts.append(f"**{table_name}**")
                response_parts.append(f"  - {table_description}")
                response_parts.append("")

            return "\n".join(response_parts)

        elif 'schema' in schema_result:
            # Single table schema
            table_name = schema_result.get('table_name', 'Unknown')
            schema = schema_result['schema']

            response_parts = [f"📋 **Table Schema: {table_name}**\n"]

            if schema.get('description'):
                response_parts.append(f"**Description:** {schema['description']}\n")

            response_parts.append("**Columns:**")

            for col_name, col_info in schema.get('columns', {}).items():
                response_parts.append(f"• **{col_name}** ({col_info['type']})")
                response_parts.append(f"  {col_info['description']}")
                response_parts.append("")

            return "\n".join(response_parts)

        return "No schema information available"

    def _format_error_response(self, error_result: Dict[str, Any]) -> str:
        """Format error responses with helpful suggestions."""
        error_msg = error_result.get('error', 'Unknown error')
        suggestion = error_result.get('suggestion', '')

        response = f"❌ **Error:** {error_msg}"

        if suggestion:
            response += f"\n\n💡 **Suggestion:** {suggestion}"

        return response

    def _format_csv_download_info(self, csv_result: Dict[str, Any]) -> str:
        """Format CSV download information."""
        if not csv_result.get('success', False):
            return ""

        filename = csv_result.get('filename', 'Unknown')
        file_path = csv_result.get('file_path', '')
        file_stats = csv_result.get('file_stats', {})

        info_parts = [
            "📥 **CSV Export Available**",
            f"• **File:** {filename}",
            f"• **Location:** {file_path}"
        ]

        if file_stats.get('size_human'):
            info_parts.append(f"• **Size:** {file_stats['size_human']}")

        if file_stats.get('absolute_path'):
            info_parts.append(f"• **Full Path:** {file_stats['absolute_path']}")

        info_parts.append("• **Note:** You can open this file in Excel, Google Sheets, or any CSV viewer")

        return "\n".join(info_parts)

    def format_help_response(self) -> str:
        """Format help information."""
        return """
🆘 **Help - How to use the ClickHouse Agent:**

**Basic Commands:**
- "list tables" or "show tables" - Show all available tables
- "schema TABLE_NAME" - Show schema for a specific table
- "schema" - Show all table schemas

**Example Questions:**
- "How many customers do we have?"
- "Show top 10 customers by data usage"
- "What's the average session duration?"
- "Show data usage by operator"
- "Which devices use the most data?"
- "Show session data for customer ID 12345"

**Tips:**
- Be specific about what data you want to see
- Mention time periods if relevant
- Ask for limits (e.g., "top 10", "last 100 records")
- Use natural language - the agent will convert it to SQL
        """