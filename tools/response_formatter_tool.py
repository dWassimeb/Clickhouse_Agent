"""
Enhanced Response Formatter for Streamlit Interface
Optimized for modern chat interface with better formatting
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
import logging
from datetime import datetime
import os
import re

logger = logging.getLogger(__name__)

class ResponseFormatterTool(BaseTool):
    """Enhanced response formatter optimized for Streamlit chat interface."""

    name: str = "format_response"
    description: str = """
    Format query results into modern chat-friendly responses optimized for Streamlit.
    Creates clean, interactive responses with embedded downloads and visualizations.
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
                formatted_response = self._format_streamlit_query_response(
                    query_result, user_question, csv_result, visualization_result
                )

            return {
                'success': True,
                'formatted_response': formatted_response,
                'attachments': self._prepare_streamlit_attachments(csv_result, visualization_result),
                'message': "Response formatted successfully"
            }

        except Exception as e:
            logger.error(f"Response formatting error: {e}")
            return {
                'success': False,
                'error': str(e),
                'formatted_response': f"❌ **Error formatting response:** {str(e)}"
            }

    def _format_streamlit_query_response(self, result: Dict[str, Any], user_question: str,
                                       csv_result: Dict[str, Any] = None,
                                       visualization_result: Dict[str, Any] = None) -> str:
        """Format query results for Streamlit chat interface."""
        if not result.get('success', True):
            return self._format_error_response(result)

        query_result = result.get('result', {})

        if not query_result.get('data'):
            return "**No Data Found** 📭\n\nThe query executed successfully but returned no results."

        # Build modern chat response
        response_parts = []

        # 1. Quick Summary First
        summary = self._generate_quick_summary(query_result, user_question)
        if summary:
            response_parts.append(f"**✨ Quick Answer:**\n{summary}")

        # 2. Data Preview Table (limited rows)
        data_preview = self._format_data_preview_table(query_result)
        if data_preview:
            response_parts.append(f"**📊 Data Preview:**\n{data_preview}")

        # 3. Key Insights
        insights = self._generate_key_insights(query_result)
        if insights:
            response_parts.append(f"**🔍 Key Insights:**\n{insights}")

        # 4. Files Section
        files_section = self._format_files_section(csv_result, visualization_result)
        if files_section:
            response_parts.append(files_section)

        # 5. SQL Query (collapsible)
        if result.get('executed_query'):
            clean_query = self._clean_sql_for_streamlit(result['executed_query'])
            response_parts.append(f"**⚡ Executed Query:**\n```sql\n{clean_query}\n```")

        return "\n\n".join(response_parts)

    def _generate_quick_summary(self, query_result: Dict[str, Any], user_question: str) -> str:
        """Generate a quick one-line summary of the results."""
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])

            if not data or not columns:
                return ""

            row_count = len(data)

            # Analyze question intent for summary
            question_lower = user_question.lower()

            if any(word in question_lower for word in ['top', 'highest', 'best', 'most']):
                if row_count > 0:
                    first_row = data[0]
                    if len(first_row) >= 2:
                        name = self._format_cell_value_clean(first_row[0])
                        value = self._format_cell_value_clean(first_row[1])
                        return f"Top result: **{name}** with **{value}**. Found {row_count:,} total records."

            elif any(word in question_lower for word in ['count', 'number', 'how many']):
                if row_count == 1 and len(data[0]) >= 1:
                    count_value = self._format_cell_value_clean(data[0][0])
                    return f"Total count: **{count_value}**"

            elif any(word in question_lower for word in ['total', 'sum', 'volume']):
                if row_count > 0 and len(columns) >= 2:
                    # Find numeric column for sum
                    numeric_totals = []
                    for i, col in enumerate(columns[1:], 1):  # Skip first column (usually name/category)
                        total = 0
                        count = 0
                        for row in data:
                            if i < len(row) and isinstance(row[i], (int, float)):
                                total += row[i]
                                count += 1
                        if count > 0:
                            numeric_totals.append(self._format_cell_value_clean(total))

                    if numeric_totals:
                        return f"Total across {row_count:,} records: **{numeric_totals[0]}**"

            # Default summary
            return f"Found **{row_count:,} records** with **{len(columns)}** columns."

        except Exception as e:
            logger.debug(f"Summary generation failed: {e}")
            return ""

    def _format_data_preview_table(self, query_result: Dict[str, Any]) -> str:
        """Format data into a clean preview table for Streamlit."""
        try:
            columns = query_result.get('columns', [])
            data = query_result.get('data', [])

            if not columns or not data:
                return ""

            # Limit preview to first 10 rows
            preview_data = data[:10]
            total_rows = len(data)

            # Create markdown table
            table_lines = []

            # Header row
            header = " | ".join(f"**{col}**" for col in columns[:6])  # Limit columns too
            table_lines.append(f"| {header} |")

            # Separator
            separator = " | ".join("---" for _ in columns[:6])
            table_lines.append(f"| {separator} |")

            # Data rows
            for row in preview_data:
                formatted_row = []
                for i, col in enumerate(columns[:6]):  # Limit to 6 columns for readability
                    value = row[i] if i < len(row) else ""
                    formatted_value = self._format_cell_value_clean(value)

                    # Truncate long values
                    if len(str(formatted_value)) > 25:
                        formatted_value = str(formatted_value)[:22] + "..."

                    formatted_row.append(str(formatted_value))

                table_lines.append(f"| {' | '.join(formatted_row)} |")

            table_str = "\n".join(table_lines)

            # Add summary info
            if total_rows > 10:
                table_str += f"\n\n*Showing first 10 of {total_rows:,} total rows*"
            else:
                table_str += f"\n\n*{total_rows:,} rows total*"

            if len(columns) > 6:
                table_str += f" • *{len(columns)} columns (showing first 6)*"

            return table_str

        except Exception as e:
            logger.error(f"Table formatting error: {e}")
            return "Error displaying data preview"

    def _generate_key_insights(self, query_result: Dict[str, Any]) -> str:
        """Generate key insights from the data."""
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])

            if not data or len(data) < 2:
                return ""

            insights = []

            # Dataset size insight
            insights.append(f"• **Dataset Size:** {len(data):,} records across {len(columns)} columns")

            # Analyze numeric columns for insights
            for i, col in enumerate(columns):
                if i >= 4:  # Limit analysis to first 4 columns
                    break

                numeric_values = []
                text_values = []

                for row in data:
                    if i < len(row) and row[i] is not None:
                        if isinstance(row[i], (int, float)):
                            numeric_values.append(row[i])
                        else:
                            text_values.append(str(row[i]))

                if numeric_values and len(numeric_values) >= 2:
                    avg_val = sum(numeric_values) / len(numeric_values)
                    max_val = max(numeric_values)
                    min_val = min(numeric_values)

                    insights.append(f"• **{col}:** Range {self._format_number_clean(min_val)} - {self._format_number_clean(max_val)}, Avg {self._format_number_clean(avg_val)}")

                elif text_values:
                    unique_count = len(set(text_values))
                    insights.append(f"• **{col}:** {unique_count} unique values")

            # Top/Bottom insights for ranked data
            if len(data) >= 3 and len(columns) >= 2:
                first_item = self._format_cell_value_clean(data[0][0])
                last_item = self._format_cell_value_clean(data[-1][0])
                insights.append(f"• **Range:** From {first_item} to {last_item}")

            return "\n".join(insights[:4])  # Limit to 4 insights

        except Exception as e:
            logger.debug(f"Insights generation failed: {e}")
            return ""

    def _format_files_section(self, csv_result: Dict[str, Any] = None,
                            visualization_result: Dict[str, Any] = None) -> str:
        """Format the files section for Streamlit."""
        files_info = []

        if csv_result and csv_result.get('success', False):
            filename = csv_result.get('filename', 'data.csv')
            file_size = csv_result.get('file_stats', {}).get('size_human', 'Unknown')
            files_info.append(f"📊 **CSV Export:** `{filename}` ({file_size})")

        if visualization_result and visualization_result.get('success', False):
            file_stats = visualization_result.get('file_stats', {})
            filename = file_stats.get('filename', 'chart.html')
            file_size = file_stats.get('size_human', 'Unknown')
            viz_type = visualization_result.get('visualization_type', 'chart')
            files_info.append(f"📈 **Interactive {viz_type.title()} Chart:** `{filename}` ({file_size})")

        if files_info:
            return "**📁 Generated Files:**\n" + "\n".join(files_info) + "\n\n*Use the download buttons above to save these files*"

        return ""

    def _clean_sql_for_streamlit(self, sql_query: str) -> str:
        """Clean SQL query for Streamlit display."""
        # Remove artifacts and clean up
        clean_query = sql_query.replace('[object Object]', '')
        clean_query = re.sub(r',\s*,', ',', clean_query)
        clean_query = re.sub(r'\s+', ' ', clean_query)

        # Basic formatting
        keywords = ['SELECT', 'FROM', 'JOIN', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT', 'HAVING']
        for keyword in keywords:
            clean_query = clean_query.replace(f' {keyword} ', f'\n{keyword} ')

        return clean_query.strip()

    def _format_cell_value_clean(self, value: Any) -> str:
        """Format individual cell values for clean display."""
        if value is None:
            return "—"
        elif isinstance(value, (int, float)):
            # Don't format years (4-digit numbers between 1900-2100)
            if isinstance(value, (int, float)) and 1900 <= value <= 2100:
                return str(int(value))
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

    def _prepare_streamlit_attachments(self, csv_result: Dict[str, Any] = None,
                                     visualization_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare file attachments optimized for Streamlit."""
        attachments = {}

        if csv_result and csv_result.get('success', False):
            attachments['csv'] = {
                'type': 'csv',
                'filename': csv_result.get('filename'),
                'path': csv_result.get('file_path'),
                'size': csv_result.get('file_stats', {}).get('size_human'),
                'label': f"📊 CSV Data ({csv_result.get('file_stats', {}).get('size_human', 'Unknown')})"
            }

        if visualization_result and visualization_result.get('success', False):
            file_stats = visualization_result.get('file_stats', {})
            viz_type = visualization_result.get('visualization_type', 'chart')
            attachments['chart'] = {
                'type': 'html_chart',
                'filename': file_stats.get('filename'),
                'path': visualization_result.get('html_file'),
                'size': file_stats.get('size_human'),
                'label': f"📈 {viz_type.title()} Chart ({file_stats.get('size_human', 'Unknown')})"
            }

        return attachments

    def _format_schema_response(self, schema_result: Dict[str, Any]) -> str:
        """Format schema information for Streamlit display."""
        if not schema_result.get('success', True):
            return f"❌ **Schema Error:** {schema_result.get('error', 'Unknown error')}"

        if 'tables' in schema_result:
            response_parts = ["**📋 Available Tables**\n"]

            for table_name, table_description in schema_result['tables'].items():
                response_parts.append(f"**{table_name}**")
                response_parts.append(f"  {table_description}")
                response_parts.append("")

            return "\n".join(response_parts)

        elif 'schema' in schema_result:
            table_name = schema_result.get('table_name', 'Unknown')
            schema = schema_result['schema']

            response_parts = [f"**📋 Table Schema: {table_name}**\n"]

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

    def format_help_response(self) -> str:
        """Format help information for Streamlit."""
        return """
**🔮 Telmi - Your Telecom Analytics Assistant**

**What can I help you with?**

• **📊 Data Analysis:** Ask questions about your telecom data in natural language
• **🏆 Top Rankings:** "Show me the top 10 customers by data usage"
• **🌍 Geographic Analysis:** "What's the distribution of users by country?"
• **⏰ Time-based Queries:** "How much data was used last month?"
• **📈 Custom Reports:** "Generate a summary of device activity"

**✨ Features:**
• **Automatic CSV exports** for all query results
• **Interactive visualizations** with professional charts
• **Smart SQL generation** from your questions
• **Mobile-friendly** interface and charts

**💡 Example Questions:**
• "Who are our top 20 customers by ticket count?"
• "Show data usage by country this week"
• "What devices are most active?"
• "List all available tables"

**🚀 Just ask your question in natural language, and I'll analyze your data!**
        """