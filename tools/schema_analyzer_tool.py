"""
Schema analyzer tool with embedded helper functions.
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
import re
import logging
from config.schemas import TABLE_SCHEMAS, TABLE_RELATIONSHIPS, QUERY_PATTERNS

logger = logging.getLogger(__name__)

class SchemaAnalyzerTool(BaseTool):
    """Tool for analyzing user questions and finding relevant schema elements."""

    name: str = "analyze_schema"
    description: str = """
    Analyze user questions to find relevant database tables and columns.
    Returns suggestions for tables, columns, and query structure.
    """

    def _run(self, user_question: str) -> Dict[str, Any]:
        """Analyze the user question and suggest relevant schema elements."""
        try:
            # Extract keywords
            keywords = self._extract_keywords(user_question)

            # Find relevant tables
            relevant_tables = self._find_relevant_tables(keywords, user_question)

            # Get column suggestions
            column_suggestions = self._get_column_suggestions(user_question)

            # Detect query intent
            intent = self._detect_query_intent(user_question)

            return {
                'success': True,
                'user_question': user_question,
                'keywords': keywords,
                'relevant_tables': relevant_tables,
                'column_suggestions': column_suggestions,
                'query_intent': intent,
                'message': f"Found {len(relevant_tables)} relevant tables"
            }

        except Exception as e:
            logger.error(f"Schema analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Schema analysis failed: {str(e)}"
            }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from user question."""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'what', 'when', 'where', 'why', 'how', 'who', 'which', 'that', 'this',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
            'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our',
            'their', 'can', 'may', 'might', 'must', 'shall', 'show', 'get', 'find'
        }

        # Extract words and filter
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]

        return keywords

    def _find_relevant_tables(self, keywords: List[str], question: str) -> List[str]:
        """Find tables relevant to given keywords and question."""
        relevant_tables = set()
        question_lower = question.lower()

        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Check each table and its columns
            for table_name, schema in TABLE_SCHEMAS.items():
                # Check table description
                if keyword_lower in schema.get("description", "").lower():
                    relevant_tables.add(table_name)

                # Check column names and descriptions
                for col_name, col_info in schema.get("columns", {}).items():
                    if (keyword_lower in col_name.lower() or
                        keyword_lower in col_info.get("description", "").lower()):
                        relevant_tables.add(table_name)

        # Check against query patterns
        for pattern_name, pattern_keywords in QUERY_PATTERNS.items():
            for pattern_keyword in pattern_keywords:
                if pattern_keyword in question_lower:
                    # Find tables with columns related to this pattern
                    for table_name, schema in TABLE_SCHEMAS.items():
                        for col_name, col_info in schema.get("columns", {}).items():
                            if (pattern_keyword in col_name.lower() or
                                pattern_keyword in col_info.get("description", "").lower()):
                                relevant_tables.add(table_name)

        return list(relevant_tables)

    def _get_column_suggestions(self, query_text: str) -> Dict[str, List[str]]:
        """Get column suggestions based on query text."""
        suggestions = {}
        query_lower = query_text.lower()

        for pattern, keywords in QUERY_PATTERNS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    suggestions[pattern] = []

                    # Find relevant columns
                    for table_name, schema in TABLE_SCHEMAS.items():
                        for col_name, col_info in schema.get("columns", {}).items():
                            if (keyword in col_name.lower() or
                                keyword in col_info.get("description", "").lower()):
                                suggestions[pattern].append(f"{table_name}.{col_name}")

        return suggestions

    def _detect_query_intent(self, user_question: str) -> Dict[str, Any]:
        """Detect the intent of the user question."""
        question_lower = user_question.lower()

        intent = {
            'type': 'query',
            'aggregation_needed': False,
            'sorting_needed': False,
            'filtering_needed': False,
            'grouping_needed': False,
            'limit_needed': True,
            'suggested_limit': 100
        }

        # Aggregation indicators
        agg_keywords = ['total', 'sum', 'count', 'average', 'avg', 'max', 'min', 'how many', 'how much']
        if any(keyword in question_lower for keyword in agg_keywords):
            intent['aggregation_needed'] = True
            intent['suggested_limit'] = 50

        # Sorting indicators
        sort_keywords = ['top', 'bottom', 'highest', 'lowest', 'best', 'worst', 'first', 'last']
        if any(keyword in question_lower for keyword in sort_keywords):
            intent['sorting_needed'] = True
            intent['suggested_limit'] = 20

        # Grouping indicators
        group_keywords = ['by', 'per', 'each', 'every', 'breakdown']
        if any(keyword in question_lower for keyword in group_keywords):
            intent['grouping_needed'] = True
            intent['suggested_limit'] = 50

        # Filtering indicators
        filter_keywords = ['where', 'with', 'having', 'only', 'specific', 'particular']
        if any(keyword in question_lower for keyword in filter_keywords):
            intent['filtering_needed'] = True

        # Extract number limits from question
        number_pattern = r'\b(?:top|first|last)\s+(\d+)\b'
        number_match = re.search(number_pattern, question_lower)
        if number_match:
            intent['suggested_limit'] = int(number_match.group(1))

        return intent

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema for a specific table."""
        return TABLE_SCHEMAS.get(table_name.upper(), {})

    def get_all_tables(self) -> Dict[str, str]:
        """Get all available tables with descriptions."""
        return {
            table_name: schema.get('description', 'No description')
            for table_name, schema in TABLE_SCHEMAS.items()
        }