"""
Chat-friendly response formatter - Clean, ChatGPT-like formatting
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ResponseFormatterTool(BaseTool):
    """Tool for formatting query results into chat-friendly responses."""

    name: str = "format_response"
    description: str = """
    Format query results into clean, chat-friendly responses for users.
    Creates ChatGPT-like responses with embedded downloads and visualizations.
    """

    def _run(self, query_result: Dict[str, Any], user_question: str = "", response_type: str = "query",
             csv_result: Dict[str, Any] = None, visualization_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format the response based on type and content."""
        try:
            if response_type == "schema":
                formatted_response = self._format_schema_response(query_result)
            elif response_type == "error":
                formatted_response = self._format_error_response(query_result)
            else:
                formatted_response = self._format_chat_query_response(
                    query_result, user_question, csv_result, visualization_result
                )

            return {
                'success': True,
                'formatted_response': formatted_response,
                'attachments': self._prepare_attachments(csv_result, visualization_result),
                'message': "Response formatted successfully"
            }

        except Exception as e:
            logger.error(f"Response formatting error: {e}")
            return {
                'success': False,
                'error': str(e),
                'formatted_response': f"Error formatting response: {str(e)}"
            }

    def _format_chat_query_response(self, result: Dict[str, Any], user_question: str,
                                  csv_result: Dict[str, Any] = None,
                                  visualization_result: Dict[str, Any] = None) -> str:
        """Format query results into a clean, chat-friendly response."""
        if not result.get('success', True):
            return self._format_error_response(result)

        query_result = result.get('result', {})

        if not query_result.get('data'):
            return "**No Data Found**\n\nThe query executed successfully but returned no results."

        # Build chat-friendly response
        response_parts = []

        # 1. Executed Query (with copy functionality)
        if result.get('executed_query'):
            clean_query = self._clean_sql_for_display(result['executed_query'])
            response_parts.append(f"**Executed Query:**\n```sql\n{clean_query}\n```")

        # 2. Data Results Table
        formatted_table = self._format_data_table_clean(query_result)
        if formatted_table:
            response_parts.append(f"**Results:**\n{formatted_table}")

        # 3. CSV Download (ChatGPT-style)
        if csv_result and csv_result.get('success', False):
            csv_download = self._format_csv_download_chat_style(csv_result)
            response_parts.append(csv_download)

        # 4. Analysis Summary
        insights = self._generate_analysis_summary(query_result)
        if insights:
            response_parts.append(f"**Analysis:**\n{insights}")

        # 5. Interactive Visualization (embedded)
        if visualization_result and visualization_result.get('success', False):
            viz_section = self._format_visualization_chat_style(visualization_result)
            response_parts.append(viz_section)

        return "\n\n".join(response_parts)

    def _clean_sql_for_display(self, sql_query: str) -> str:
        """Clean SQL query for better display"""
        # Remove [object Object] artifacts
        clean_query = sql_query.replace('[object Object]', '')
        clean_query = clean_query.replace(',  ,', ',')
        clean_query = clean_query.replace('  ', ' ')

        # Format for better readability
        lines = clean_query.split(',')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line:
                if any(keyword in line.upper() for keyword in ['SELECT', 'FROM', 'JOIN', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT']):
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(f"    {line}")

        return '\n'.join(formatted_lines)

    def _format_data_table_clean(self, query_result: Dict[str, Any]) -> str:
        """Format data into a clean, chat-friendly table."""
        try:
            columns = query_result.get('columns', [])
            data = query_result.get('data', [])

            if not columns or not data:
                return ""

            # Limit display to first 20 rows for readability
            display_data = data[:20]
            row_count = len(data)

            # Calculate column widths for better formatting
            col_widths = {}
            for i, col in enumerate(columns):
                col_widths[i] = max(len(str(col)), 8)  # Minimum width of 8

                for row in display_data:
                    if i < len(row):
                        formatted_value = self._format_cell_value_clean(row[i])
                        col_widths[i] = max(col_widths[i], len(str(formatted_value)))

                # Cap maximum width at 20 characters for better display
                col_widths[i] = min(col_widths[i], 20)

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
                    formatted_value = self._format_cell_value_clean(value)

                    # Truncate if too long
                    if len(str(formatted_value)) > 20:
                        formatted_value = str(formatted_value)[:17] + "..."

                    formatted_row.append(f"{formatted_value:<{col_widths[i]}}")

                table_lines.append(" | ".join(formatted_row))

            table_str = "```\n" + "\n".join(table_lines) + "\n```"

            # Add summary info
            if row_count > 20:
                table_str += f"\n*Showing first 20 of {row_count:,} total rows*"
            else:
                table_str += f"\n*{row_count:,} rows total*"

            return table_str

        except Exception as e:
            logger.error(f"Table formatting error: {e}")
            return "Error formatting table data"

    def _format_cell_value_clean(self, value: Any) -> str:
        """Format individual cell values for clean display."""
        if value is None:
            return "—"
        elif isinstance(value, (int, float)):
            # Don't format years (4-digit numbers between 1900-2100)
            if isinstance(value, (int, float)) and 1900 <= value <= 2100:
                return str(int(value))
            elif isinstance(value, float) and value.is_integer():
                return self._format_number_clean(int(value))
            elif isinstance(value, float):
                return self._format_number_clean(value)
            else:
                return self._format_number_clean(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        else:
            return str(value)

    def _format_number_clean(self, value: float) -> str:
        """Format numbers with K/M suffixes for better readability."""
        if isinstance(value, (int, float)) and 1900 <= value <= 2100:
            return str(int(value))

        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:,.0f}" if isinstance(value, (int, float)) else str(value)

    def _format_csv_download_chat_style(self, csv_result: Dict[str, Any]) -> str:
        """Format CSV download in ChatGPT style."""
        if not csv_result.get('success', False):
            return ""

        filename = csv_result.get('filename', 'data.csv')
        file_size = csv_result.get('file_stats', {}).get('size_human', 'Unknown')

        return f"📊 **[Download CSV file]({filename})** ({file_size})\n*Click to download the complete dataset as CSV*"

    def _generate_analysis_summary(self, query_result: Dict[str, Any]) -> str:
        """Generate clean analysis summary."""
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])

            if not data or not columns:
                return ""

            insights = []

            # Row count
            record_count = len(data)
            insights.append(f"• **Records:** {record_count:,}")

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

                    insights.append(f"• **{col}:** Avg {self._format_number_clean(avg_val)}, Range {self._format_number_clean(min_val)} - {self._format_number_clean(max_val)}")

            return "\n".join(insights[:3])  # Limit to 3 insights

        except Exception as e:
            logger.error(f"Analysis generation error: {e}")
            return ""

    def _format_visualization_chat_style(self, visualization_result: Dict[str, Any]) -> str:
        """Format visualization in chat style with embedded chart."""
        viz_type = visualization_result.get('visualization_type', 'chart')
        file_stats = visualization_result.get('file_stats', {})
        filename = file_stats.get('filename', 'chart.html')
        file_size = file_stats.get('size_human', 'Unknown')

        # Return placeholder for chart embedding (handled by chat interface)
        return f"📈 **Interactive {viz_type.replace('_', ' ').title()} Chart**\n\n[CHART_PLACEHOLDER]\n\n📁 **[Download Chart]({filename})** ({file_size})\n*Download as interactive HTML file*"

    def _prepare_attachments(self, csv_result: Dict[str, Any] = None,
                           visualization_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare file attachments for the chat interface."""
        attachments = {}

        if csv_result and csv_result.get('success', False):
            attachments['csv'] = {
                'type': 'csv',
                'filename': csv_result.get('filename'),
                'path': csv_result.get('file_path'),
                'size': csv_result.get('file_stats', {}).get('size_human')
            }

        if visualization_result and visualization_result.get('success', False):
            attachments['chart'] = {
                'type': 'html_chart',
                'filename': visualization_result.get('file_stats', {}).get('filename'),
                'path': visualization_result.get('html_file'),
                'size': visualization_result.get('file_stats', {}).get('size_human')
            }

        return attachments

    def _format_schema_response(self, schema_result: Dict[str, Any]) -> str:
        """Format schema information for display."""
        if not schema_result.get('success', True):
            return f"**Schema Error:** {schema_result.get('error', 'Unknown error')}"

        if 'tables' in schema_result:
            response_parts = ["**Available Tables**\n"]

            for table_name, table_description in schema_result['tables'].items():
                response_parts.append(f"**{table_name}**")
                response_parts.append(f"  {table_description}")
                response_parts.append("")

            return "\n".join(response_parts)

        elif 'schema' in schema_result:
            table_name = schema_result.get('table_name', 'Unknown')
            schema = schema_result['schema']

            response_parts = [f"**Table Schema: {table_name}**\n"]

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

        response = f"**Error:** {error_msg}"

        if suggestion:
            response += f"\n\n**Suggestion:** {suggestion}"

        return response

    def format_help_response(self) -> str:
        """Format help information."""
        return """
**Telmi - Your ClickHouse Analytics Assistant**

**What can I help you with?**

• **Data Analysis:** Ask questions about your telecom data in natural language
• **Top Rankings:** "Show me the top 10 customers by data usage"
• **Geographic Analysis:** "What's the distribution of users by country?"
• **Time-based Queries:** "How much data was used last month?"
• **Custom Reports:** "Generate a summary of device activity"

**Features:**
• 📊 **Automatic CSV exports** for all query results
• 📈 **Interactive visualizations** with professional charts
• 🔍 **Smart SQL generation** from your questions
• 📱 **Mobile-friendly** charts and data tables

**Example Questions:**
• "Who are our top 20 customers by ticket count?"
• "Show data usage by country this week"
• "What devices are most active?"
• "List all available tables"

Just ask your question in natural language, and I'll analyze your data!
        """