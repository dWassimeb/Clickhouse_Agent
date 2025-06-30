"""
Enhanced Response Formatter for Streamlit Interface
Fixed version - keeping original structure, just improving formatting as requested
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
        """Format query results for Streamlit chat interface with YOUR REQUESTED STRUCTURE."""
        if not result.get('success', True):
            return self._format_error_response(result)

        query_result = result.get('result', {})

        if not query_result.get('data'):
            return "**No Data Found** 📭\n\nThe query executed successfully but returned no results."

        # Build response with YOUR EXACT REQUESTED STRUCTURE
        response_parts = []

        # 1. Data Results Section (placeholder for Streamlit dataframe)
        response_parts.append("**📊 Data Results:**")
        response_parts.append("[TABLE_DATA_PLACEHOLDER]")

        # 2. Key Insights Section (with proper line breaks as you requested)
        insights = self._generate_key_insights_formatted(query_result)
        if insights:
            response_parts.append("**🔍 Key Insights:**")
            response_parts.append(insights)

        # 3. Executed Query Section
        if result.get('executed_query'):
            clean_query = self._clean_sql_for_streamlit(result['executed_query'])
            response_parts.append("**⚡ Executed Query:**")
            response_parts.append(f"```sql\n{clean_query}\n```")

        # 4. Chart Generated Section
        if visualization_result and visualization_result.get('success', False):
            response_parts.append("**📈 Chart Generated:**")
            response_parts.append("[CHART_DISPLAY_PLACEHOLDER]")

        # 5. Download Buttons Section
        if csv_result or visualization_result:
            response_parts.append("**📁 Downloads:**")
            response_parts.append("[DOWNLOAD_BUTTONS_PLACEHOLDER]")

        return "\n\n".join(response_parts)

    def _generate_key_insights_formatted(self, query_result: Dict[str, Any]) -> str:
        """Generate key insights with proper line breaks as you requested (NOT one single line)."""
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])

            if not data or len(data) < 1:
                return ""

            insights = []

            # Dataset size insight
            insights.append(f"• **Dataset Size:** {len(data):,} records across {len(columns)} columns")

            # Analyze columns for insights (limit to first 4 columns for readability)
            for i, col in enumerate(columns[:4]):
                if i >= 4:  # Safety check
                    break

                # Get column values
                column_values = []
                for row in data:
                    if i < len(row) and row[i] is not None:
                        column_values.append(row[i])

                if not column_values:
                    continue

                # Analyze based on data type
                if all(isinstance(val, (int, float)) for val in column_values):
                    # Numeric column analysis
                    if len(column_values) >= 2:
                        avg_val = sum(column_values) / len(column_values)
                        max_val = max(column_values)
                        min_val = min(column_values)
                        insights.append(f"• **{col}:** Range {self._format_number_clean(min_val)} - {self._format_number_clean(max_val)}, Avg {self._format_number_clean(avg_val)}")
                else:
                    # Text column analysis
                    unique_count = len(set(str(val) for val in column_values))
                    insights.append(f"• **{col}:** {unique_count} unique values")

            # Top/Bottom range insight for ranked data
            if len(data) >= 2 and len(columns) >= 2:
                first_item = self._format_cell_value_clean(data[0][0])
                last_item = self._format_cell_value_clean(data[-1][0])
                insights.append(f"• **Range:** From {first_item} to {last_item}")

            # Join with proper line breaks (THIS IS KEY - separate lines, not one line)
            # Make sure each insight is on its own line with proper spacing
            formatted_insights = []
            for insight in insights[:5]:  # Limit to 5 insights for readability
                formatted_insights.append(insight)

            return "\n\n".join(formatted_insights)  # Double line breaks for better spacing

        except Exception as e:
            logger.debug(f"Insights generation failed: {e}")
            return ""

    def _clean_sql_for_streamlit(self, sql_query: str) -> str:
        """Clean SQL query for Streamlit display."""
        # Remove artifacts and clean up
        clean_query = sql_query.replace('[object Object]', '')
        clean_query = re.sub(r',\s*,', ',', clean_query)
        clean_query = re.sub(r'\s+', ' ', clean_query)

        # Basic formatting with proper line breaks
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