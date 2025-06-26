"""
Simplified Smart Schema Tool - Adaptive and user-friendly with LLM intelligence
"""

from typing import Dict, Any
from langchain.tools import BaseTool
from pydantic import Field
import json
import logging
from llm.custom_gpt import CustomGPT
from database.clickhouse.connection import clickhouse_connection
from config.schemas import TABLE_SCHEMAS

logger = logging.getLogger(__name__)

class SmartSchemaTool(BaseTool):
    """Simplified LLM-powered schema tool that adapts to user input and suggests corrections."""

    name: str = "smart_schema"
    description: str = "Handle schema questions with intelligent table name matching and suggestions."

    llm: CustomGPT = Field(default_factory=CustomGPT)

    def _run(self, user_question: str) -> Dict[str, Any]:
        """
        Process schema questions with smart table matching and LLM adaptation.
        """
        try:
            # Step 1: Let LLM extract and correct table names from the question
            extracted_info = self._extract_table_info_with_llm(user_question)

            # Step 2: Get schema data with smart matching
            schema_data = self._get_smart_schema_data(extracted_info)

            # Step 3: Let LLM format the final response
            formatted_response = self._format_response_with_llm(user_question, extracted_info, schema_data)

            return {
                'success': True,
                'formatted_response': formatted_response,
                'message': "Schema analysis completed successfully"
            }

        except Exception as e:
            logger.error(f"Smart schema tool failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'formatted_response': f"❌ **Schema Error:** {str(e)}",
                'message': f"Schema analysis failed: {str(e)}"
            }

    def _extract_table_info_with_llm(self, user_question: str) -> Dict[str, Any]:
        """Use LLM to extract table information and determine what the user wants."""

        available_tables = list(TABLE_SCHEMAS.keys())

        prompt = f"""Analyze this schema question and extract the requested information.

Available tables in the database: {', '.join(available_tables)}

User Question: "{user_question}"

Determine:
1. What type of schema information does the user want?
2. Which table(s) are they asking about (if any)?
3. If they mention a table name that doesn't match exactly, find the closest match

Respond with JSON:
{{
    "request_type": "all_tables|specific_table|table_exists|search",
    "mentioned_table": "exact table name mentioned by user or null",
    "closest_match": "closest matching table from available tables or null",
    "confidence": 0.95,
    "reasoning": "Why you chose this interpretation"
}}

Important: For table names, be flexible - 'customer' should match 'CUSTOMER', 'rm_data' should match 'RM_AGGREGATED_DATA', etc.

JSON Response:"""

        try:
            response = self.llm._call(prompt)
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:-3]

            parsed = json.loads(clean_response)
            return parsed

        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            # Simple fallback
            return {
                "request_type": "all_tables",
                "mentioned_table": None,
                "closest_match": None,
                "confidence": 0.5,
                "reasoning": f"Fallback due to parsing error: {str(e)}"
            }

    def _get_smart_schema_data(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get schema data with smart table matching."""

        request_type = extracted_info.get("request_type", "all_tables")
        closest_match = extracted_info.get("closest_match")
        mentioned_table = extracted_info.get("mentioned_table")

        if request_type == "specific_table" and closest_match:
            # Try to get schema for the closest matching table
            return self._get_table_schema_smart(closest_match, mentioned_table)

        elif request_type == "table_exists":
            # Check if table exists
            return self._check_table_exists_smart(closest_match, mentioned_table)

        else:
            # Default to showing all tables
            return self._get_all_tables_simple()

    def _get_table_schema_smart(self, table_name: str, original_name: str = None) -> Dict[str, Any]:
        """Get table schema with fallback and user-friendly messaging."""

        # Always use hardcoded schema as primary source (more reliable)
        if table_name in TABLE_SCHEMAS:
            schema = TABLE_SCHEMAS[table_name]

            # Try to enhance with ClickHouse data if possible
            try:
                clickhouse_data = self._get_clickhouse_table_info(table_name)
                if clickhouse_data:
                    schema['clickhouse_info'] = clickhouse_data
            except Exception as e:
                logger.warning(f"ClickHouse enhancement failed: {e}")

            return {
                'operation': 'describe_table',
                'table_name': table_name,
                'original_name': original_name,
                'schema': schema,
                'found': True,
                'source': 'hardcoded_schema'
            }

        # Table not found
        return {
            'operation': 'describe_table',
            'table_name': table_name,
            'original_name': original_name,
            'found': False,
            'available_tables': list(TABLE_SCHEMAS.keys()),
            'error': f"Table not found"
        }

    def _check_table_exists_smart(self, table_name: str, original_name: str = None) -> Dict[str, Any]:
        """Check if table exists with smart suggestions."""

        exists = table_name in TABLE_SCHEMAS if table_name else False

        return {
            'operation': 'check_exists',
            'table_name': table_name,
            'original_name': original_name,
            'exists': exists,
            'available_tables': list(TABLE_SCHEMAS.keys()) if not exists else None
        }

    def _get_all_tables_simple(self) -> Dict[str, Any]:
        """Get simple overview of all tables."""

        tables_info = {}

        for table_name, schema in TABLE_SCHEMAS.items():
            tables_info[table_name] = {
                'description': schema.get('description', 'No description'),
                'column_count': len(schema.get('columns', {}))
            }

            # Try to add ClickHouse info if possible
            try:
                clickhouse_info = self._get_clickhouse_table_info(table_name)
                if clickhouse_info:
                    tables_info[table_name].update(clickhouse_info)
            except:
                pass  # Ignore ClickHouse errors for table listing

        return {
            'operation': 'list_tables',
            'tables': tables_info,
            'total_tables': len(tables_info)
        }

    def _get_clickhouse_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get additional info from ClickHouse (non-critical)."""

        try:
            info_query = f"""
            SELECT total_rows, total_bytes
            FROM system.tables 
            WHERE database = currentDatabase() AND name = '{table_name}'
            """

            result = clickhouse_connection.execute_query_with_names(info_query)

            if result.get("data") and len(result["data"]) > 0:
                row = result["data"][0]
                return {
                    'total_rows': row[0] if len(row) > 0 else 0,
                    'total_bytes': row[1] if len(row) > 1 else 0,
                    'size_human': self._format_bytes(row[1]) if len(row) > 1 else "Unknown"
                }
        except Exception as e:
            logger.debug(f"ClickHouse table info failed for {table_name}: {e}")

        return None

    def _format_response_with_llm(self, user_question: str, extracted_info: Dict[str, Any], schema_data: Dict[str, Any]) -> str:
        """Use LLM to create a user-friendly response."""

        prompt = f"""Create a helpful response to this schema question.

User Question: "{user_question}"
Extracted Info: {json.dumps(extracted_info, indent=2)}
Schema Data: {json.dumps(schema_data, indent=2, default=str)}

Guidelines:
1. If the user asked for a specific table but we found a closest match, acknowledge this clearly
2. If table wasn't found, suggest the available tables
3. Format schema information in clear tables
4. Use appropriate emojis and markdown formatting
5. Be conversational and helpful

Create a clear, well-formatted markdown response.

Response:"""

        try:
            response = self.llm._call(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            # Simple fallback
            return self._create_simple_fallback_response(extracted_info, schema_data)

    def _create_simple_fallback_response(self, extracted_info: Dict[str, Any], schema_data: Dict[str, Any]) -> str:
        """Create a simple fallback response without LLM."""

        if schema_data.get('operation') == 'describe_table':
            if schema_data.get('found'):
                table_name = schema_data.get('table_name')
                original_name = schema_data.get('original_name')

                response = f"## 📋 Schema for Table: {table_name}\n\n"

                if original_name and original_name.lower() != table_name.lower():
                    response += f"*(You asked for '{original_name}', showing '{table_name}')*\n\n"

                schema = schema_data.get('schema', {})
                description = schema.get('description', 'No description available')
                response += f"**Description:** {description}\n\n"

                columns = schema.get('columns', {})
                if columns:
                    response += "### Columns:\n\n"
                    for col_name, col_info in columns.items():
                        col_type = col_info.get('type', 'Unknown')
                        col_desc = col_info.get('description', 'No description')
                        response += f"- **{col_name}** ({col_type}): {col_desc}\n"

                return response
            else:
                available = ', '.join(schema_data.get('available_tables', []))
                return f"❌ **Table not found**\n\nAvailable tables: {available}"

        # Default fallback
        return "**Schema Information**\n\nProcessed your request but formatting failed."

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format."""
        if not bytes_value or bytes_value == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"