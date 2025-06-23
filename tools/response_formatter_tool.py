"""
Professional response formatter - clean, minimalistic, finance-grade formatting
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseFormatterTool(BaseTool):
    """Tool for formatting query results into professional, clean responses."""

    name: str = "format_response"
    description: str = """
    Format query results into clean, professional responses for users.
    Creates readable tables, insights, summaries, and visualization links without excessive styling.
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
                formatted_response = self._format_query_response(query_result, user_question, csv_result, visualization_result)

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

    def _format_query_response(self, result: Dict[str, Any], user_question: str,
                              csv_result: Dict[str, Any] = None, visualization_result: Dict[str, Any] = None) -> str:
        """Format query results into a clean, professional response."""
        if not result.get('success', True):
            return self._format_error_response(result)

        query_result = result.get('result', {})

        if not query_result.get('data'):
            return "**No Data Found**\n\nThe query executed successfully but returned no results."

        # Build formatted response
        response_parts = []

        # Add clean summary
        summary = query_result.get('summary', '')
        response_parts.append(f"**Query Results**\n{summary}")

        # Add visualization information first (most prominent)
        if visualization_result and visualization_result.get('success', False):
            viz_info = self._format_visualization_info(visualization_result)
            response_parts.append(viz_info)

        # Add data table
        formatted_table = self._format_data_table(query_result)
        if formatted_table:
            response_parts.append(f"**Data Overview**\n{formatted_table}")

        # Add professional insights
        insights = self._generate_professional_insights(query_result)
        if insights:
            response_parts.append(f"**Analysis**\n{insights}")

        # Add CSV download information
        if csv_result and csv_result.get('success', False):
            csv_info = self._format_csv_download_info(csv_result)
            response_parts.append(csv_info)

        # Add query information
        if result.get('executed_query'):
            response_parts.append(f"**Executed Query**\n```sql\n{result['executed_query']}\n```")

        return "\n\n".join(response_parts)

    def _format_visualization_info(self, visualization_result: Dict[str, Any]) -> str:
        """Format visualization information in a clean, professional manner."""
        viz_type = visualization_result.get('visualization_type', 'chart')
        file_stats = visualization_result.get('file_stats', {})
        filename = file_stats.get('filename', 'chart.html')
        file_path = file_stats.get('absolute_path', '')
        file_size = file_stats.get('size_human', 'Unknown')

        viz_info_parts = [
            "**Data Visualization**",
            f"• Type: {viz_type.replace('_', ' ').title()} Chart",
            f"• File: {filename}",
            f"• Size: {file_size}",
            f"• Location: {file_path}",
            "",
            "**Chart Details:**",
            "• Professional design optimized for business use",
            "• Interactive features with clean tooltips",
            "• Responsive layout for all screen sizes",
            "• Finance-grade color scheme and typography",
            "",
            "**Instructions:** Open the HTML file in any web browser to view the interactive chart.",
        ]

        return "\n".join(viz_info_parts)

    def _format_data_table(self, query_result: Dict[str, Any]) -> str:
        """Format data into a clean, readable table."""
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
                        formatted_value = self._format_professional_cell_value(row[i])
                        col_widths[i] = max(col_widths[i], len(str(formatted_value)))

                # Cap maximum width at 25 characters for cleaner display
                col_widths[i] = min(col_widths[i], 25)

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
                    formatted_value = self._format_professional_cell_value(value)

                    # Truncate if too long
                    if len(str(formatted_value)) > 25:
                        formatted_value = str(formatted_value)[:22] + "..."

                    formatted_row.append(f"{formatted_value:<{col_widths[i]}}")

                table_lines.append(" | ".join(formatted_row))

            table_str = "```\n" + "\n".join(table_lines) + "\n```"

            # Add note if data was truncated
            if len(data) > 20:
                table_str += f"\n*Showing first 20 of {len(data):,} rows*"

            return table_str

        except Exception as e:
            logger.error(f"Table formatting error: {e}")
            return "Error formatting table data"

    def _format_professional_cell_value(self, value: Any) -> str:
        """Format individual cell values for professional display."""
        if value is None:
            return "—"
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return self._format_number(int(value))
            elif isinstance(value, float):
                return self._format_number(value)
            else:
                return self._format_number(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        else:
            return str(value)

    def _format_number(self, value: float) -> str:
        """Format numbers with K/M suffixes for better readability."""
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.2f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.2f}K"
        else:
            return f"{value:.2f}"

    def _generate_professional_insights(self, query_result: Dict[str, Any]) -> str:
        """Generate clean, professional insights from query results."""
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])

            if not data or not columns:
                return ""

            insights = []

            # Row count insight
            record_count = len(data)
            insights.append(f"• Records: {self._format_number(record_count)}")

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

                    insights.append(f"• {col}: Avg {self._format_number(avg_val)}, Range {self._format_number(min_val)} - {self._format_number(max_val)}")

            # Unique values for categorical columns (limit to relevant ones)
            for i, col in enumerate(columns):
                unique_values = set()
                total_values = 0
                for row in data:
                    if i < len(row) and row[i] is not None:
                        unique_values.add(row[i])
                        total_values += 1

                if len(unique_values) <= 20 and len(unique_values) > 1 and total_values > 0:
                    percentage = (len(unique_values) / total_values) * 100
                    insights.append(f"• {col}: {len(unique_values)} unique values ({percentage:.1f}% distinct)")

            return "\n".join(insights[:4])  # Limit to 4 insights for cleanliness

        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            return ""

    def _format_schema_response(self, schema_result: Dict[str, Any]) -> str:
        """Format schema information for display."""
        if not schema_result.get('success', True):
            return f"**Schema Error:** {schema_result.get('error', 'Unknown error')}"

        if 'tables' in schema_result:
            # List of tables
            response_parts = ["**Available Tables**\n"]

            for table_name, table_description in schema_result['tables'].items():
                response_parts.append(f"**{table_name}**")
                response_parts.append(f"  {table_description}")
                response_parts.append("")

            return "\n".join(response_parts)

        elif 'schema' in schema_result:
            # Single table schema
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

    def _format_csv_download_info(self, csv_result: Dict[str, Any]) -> str:
        """Format CSV download information."""
        if not csv_result.get('success', False):
            return ""

        filename = csv_result.get('filename', 'Unknown')
        file_path = csv_result.get('file_path', '')
        file_stats = csv_result.get('file_stats', {})

        info_parts = [
            "**CSV Export**",
            f"• File: {filename}",
            f"• Location: {file_path}"
        ]

        if file_stats.get('size_human'):
            info_parts.append(f"• Size: {file_stats['size_human']}")

        if file_stats.get('absolute_path'):
            info_parts.append(f"• Full Path: {file_stats['absolute_path']}")

        info_parts.append("• Compatible with Excel, Google Sheets, and CSV viewers")

        return "\n".join(info_parts)

    def format_help_response(self) -> str:
        """Format help information."""
        return """
**ClickHouse Analytics Agent - User Guide**

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

**Features:**
- **Interactive Visualizations** - Automatic chart generation for your data
- **Professional Dashboards** - Clean, responsive charts optimized for business use
- **Mobile Support** - Visualizations work on all devices
- **Multiple Chart Types** - Bar, line, area, scatter, and more

**Tips:**
- Be specific about what data you want to see
- Mention time periods if relevant
- Ask for limits (e.g., "top 10", "last 100 records")
- Use natural language - the agent will convert it to SQL
- Results include interactive visualizations and CSV exports automatically
        """