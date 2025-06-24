"""
UTF-8 Fixed Professional Visualization Tool - FIXED INDENTATION ISSUE
"""

from typing import Dict, Any, List, Optional, ClassVar
from langchain.tools import BaseTool
from pydantic import Field
import json
import os
import logging
from datetime import datetime
from llm.custom_gpt import CustomGPT
import unicodedata
import re

logger = logging.getLogger(__name__)

class ModernVisualizationTool(BaseTool):
    """Create professional, minimalistic visualizations with proper UTF-8 handling."""

    name: str = "create_visualization"
    description: str = """
    Generate clean, professional charts and dashboards from query results.
    Creates HTML files with Chart.js visualizations that are minimalistic and finance-appropriate.
    """

    export_dir: str = Field(default="visualizations")
    llm: CustomGPT = Field(default_factory=CustomGPT)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create visualizations directory if it doesn't exist
        os.makedirs(self.export_dir, exist_ok=True)

    def _run(self, query_result: Dict[str, Any], user_question: str = "", csv_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create professional visualization from query results."""
        try:
            # Check if we have visualizable data
            if not self._is_visualizable(query_result):
                return {
                    'success': False,
                    'message': 'Data is not suitable for visualization',
                    'reason': 'No numeric data or insufficient rows'
                }

            # Debug: Log the incoming data structure
            result_data = query_result.get('result', {})
            columns = result_data.get('columns', [])
            data = result_data.get('data', [])

            if self._should_log_debug():
                logger.info(f"Visualization Input - Columns: {columns}")
                logger.info(f"Visualization Input - Sample data: {data[:3] if data else 'No data'}")

            # Clean data to handle UTF-8 issues
            cleaned_data = self._clean_data_utf8(data)

            # Analyze data structure and determine best visualization type
            viz_analysis = self._analyze_data_for_visualization_safe(columns, cleaned_data, user_question)

            if self._should_log_debug():
                logger.info(f"LLM Analysis Result: {viz_analysis}")

            # Generate the visualization
            html_file = self._create_professional_visualization_safe(columns, cleaned_data, viz_analysis, user_question)

            # Get file stats
            file_stats = self._get_file_stats(html_file)

            return {
                'success': True,
                'html_file': html_file,
                'visualization_type': viz_analysis.get('chart_type'),
                'file_stats': file_stats,
                'message': f"Professional visualization created: {os.path.basename(html_file)}"
            }

        except Exception as e:
            logger.error(f"Visualization creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to create visualization: {str(e)}"
            }

    def _clean_data_utf8(self, data: List[List]) -> List[List]:
        """Clean data to handle UTF-8 encoding issues."""
        cleaned_data = []

        for row in data:
            cleaned_row = []
            for value in row:
                if isinstance(value, str):
                    # Clean the string to remove problematic characters
                    cleaned_value = self._clean_string_utf8(value)
                    cleaned_row.append(cleaned_value)
                else:
                    cleaned_row.append(value)
            cleaned_data.append(cleaned_row)

        return cleaned_data

    def _clean_string_utf8(self, text: str) -> str:
        """Clean a string to ensure it's UTF-8 compatible."""
        if not text:
            return text

        # Remove surrogate characters and other problematic Unicode
        try:
            # Normalize the string
            normalized = unicodedata.normalize('NFKD', text)
            # Remove non-ASCII characters that might cause issues
            cleaned = re.sub(r'[^\x00-\x7F]+', '', normalized)
            # If the cleaned string is empty, try a different approach
            if not cleaned.strip():
                # Keep only alphanumeric and common punctuation
                cleaned = re.sub(r'[^\w\s\-\.\/\(\)&]+', '', text)
            return cleaned.strip()
        except:
            # Last resort: convert to ASCII
            return text.encode('ascii', 'ignore').decode('ascii')

    def _is_visualizable(self, query_result: Dict[str, Any]) -> bool:
        """Check if query results are suitable for visualization."""
        if not query_result.get('success', True):
            return False

        result_data = query_result.get('result', {})
        data = result_data.get('data', [])
        columns = result_data.get('columns', [])

        # Need at least 1 row and 2 columns for meaningful visualization
        if len(data) < 1 or len(columns) < 2:
            return False

        # Check if we have at least one numeric column
        has_numeric = False
        for row in data[:5]:  # Check first 5 rows
            for value in row:
                if isinstance(value, (int, float)) and not (isinstance(value, float) and (value != value)):  # Check for NaN
                    has_numeric = True
                    break
            if has_numeric:
                break

        return has_numeric

    def _analyze_data_for_visualization_safe(self, columns: List[str], data: List[List], user_question: str) -> Dict[str, Any]:
        """Enhanced analysis with better time series detection and column mapping."""

        # Detect time series first
        time_info = self._detect_time_series_columns(columns, data)

        # Prepare comprehensive data analysis
        sample_data = []
        for i, row in enumerate(data[:5]):
            row_dict = {}
            for j, col in enumerate(columns):
                if j < len(row):
                    value = row[j]
                    if isinstance(value, str):
                        value = self._clean_string_utf8(value)
                    row_dict[col] = value
            sample_data.append(row_dict)

        # Enhanced data type analysis
        data_analysis = self._perform_comprehensive_data_analysis(columns, data)
        question_context = self._analyze_question_context(user_question)

        data_structure = {
            'columns': columns,
            'sample_data': sample_data,
            'total_rows': len(data),
            'data_analysis': data_analysis,
            'question_context': question_context,
            'time_series_info': time_info
        }

        # Enhanced prompt with time series awareness
        prompt = f"""Analyze this query result and determine the BEST visualization approach.

    User Question: "{user_question}"
    Data Structure: {json.dumps(data_structure, indent=2, default=str, ensure_ascii=True)}

    **TIME SERIES DETECTION:**
    Is Time Series: {time_info['is_time_series']}
    Time Columns: {[col['name'] for col in [time_info.get('year_column'), time_info.get('month_column'), time_info.get('date_column')] if col]}

    **CRITICAL RULES FOR TIME SERIES:**
    - If data has YEAR/MONTH/DATE columns → ALWAYS use "line" or "area" chart
    - For time series: X-axis = Time (months/dates), Y-axis = Values (counts/amounts)  
    - Time should ALWAYS be on X-axis, values on Y-axis
    - For evolution/trend questions → "line" chart is mandatory

    **AVAILABLE CHART TYPES:**
    - **line** - Time series, trends, evolution over time (BEST for temporal data)
    - **area** - Time series with filled area
    - **bar** - Categorical comparisons (NOT for time series)
    - **horizontal_bar** - Rankings/top N lists
    - **pie/doughnut** - Distributions (≤8 categories)
    - **scatter** - Correlations between variables

    **COLUMN MAPPING FOR TIME SERIES:**
    - **label_column** = Time column (YEAR, MONTH, DATE) → X-axis
    - **value_column** = Metric column (COUNT, AMOUNT, VOLUME) → Y-axis

    **QUESTION ANALYSIS:**
    - "évolution" = evolution → line chart mandatory
    - "par mois" = by month → line chart with months on X-axis
    - "trend/tendance" → line chart
    - "over time/au fil du temps" → line chart

    Respond ONLY with valid JSON:
    {{
        "chart_type": "line|area|bar|horizontal_bar|pie|doughnut|scatter",
        "title": "Clean descriptive title",
        "label_column": "time_column_for_x_axis",
        "value_column": "metric_column_for_y_axis",
        "color_scheme": "professional_blue",
        "show_legend": false,
        "reasoning": "Why this chart type and column mapping was chosen"
    }}

    **REMEMBER:** For time/date data, ALWAYS use line charts with time on X-axis!

    JSON Response:"""

        try:
            response = self.llm._call(prompt)
            clean_response = response.strip()

            # Clean JSON response
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]

            json_end = clean_response.rfind('}')
            if json_end != -1:
                clean_response = clean_response[:json_end + 1]

            parsed = json.loads(clean_response.strip())

            # OVERRIDE: Force correct mapping for time series
            if time_info['is_time_series']:
                # Force line chart for time series
                if parsed.get('chart_type') not in ['line', 'area']:
                    parsed['chart_type'] = 'line'
                    parsed['reasoning'] = "Forced to line chart for time series data"

                # Force correct column mapping
                if time_info['month_column']:
                    parsed['label_column'] = time_info['month_column']['name']
                elif time_info['year_column']:
                    parsed['label_column'] = time_info['year_column']['name']
                elif time_info['date_column']:
                    parsed['label_column'] = time_info['date_column']['name']

                if time_info['value_column']:
                    parsed['value_column'] = time_info['value_column']['name']

            # Enhanced validation
            validated_analysis = self._validate_and_enhance_chart_analysis(parsed, columns, data, user_question)
            return validated_analysis

        except Exception as e:
            logger.warning(f"LLM visualization analysis failed: {e}")
            # Enhanced intelligent fallback with time series support
            return self._create_time_series_aware_fallback(columns, data, user_question, time_info)

    def _create_time_series_aware_fallback(self, columns: List[str], data: List[List], user_question: str, time_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent fallback with time series awareness."""

        # If it's time series data, force line chart
        if time_info['is_time_series']:
            chart_type = 'line'
            reasoning = "Time series data detected - using line chart"

            # Determine columns
            if time_info['month_column']:
                label_column = time_info['month_column']['name']
            elif time_info['year_column']:
                label_column = time_info['year_column']['name']
            elif time_info['date_column']:
                label_column = time_info['date_column']['name']
            else:
                label_column = columns[0]

            if time_info['value_column']:
                value_column = time_info['value_column']['name']
            else:
                # Find first numeric column that's not a time column
                value_column = None
                time_columns = [
                    time_info.get('year_column', {}).get('name'),
                    time_info.get('month_column', {}).get('name'),
                    time_info.get('date_column', {}).get('name')
                ]

                for col in columns:
                    if col not in time_columns and self._column_is_numeric(col, columns, data):
                        value_column = col
                        break

                if not value_column:
                    value_column = columns[-1] if columns else 'Value'

        else:
            # Use standard fallback logic
            column_types = self._analyze_column_types(columns, data)
            question_context = self._analyze_question_context(user_question)

            text_columns = [col for col, type_ in column_types.items() if type_ == 'text']
            numeric_columns = [col for col, type_ in column_types.items() if type_ == 'numeric']

            # Chart type selection
            if question_context['asks_for_ranking'] or 'top' in user_question.lower():
                chart_type = 'horizontal_bar'
                reasoning = "Horizontal bar chart for ranking analysis"
            elif question_context['asks_for_distribution'] and len(text_columns) == 1 and len(data) <= 8:
                chart_type = 'pie'
                reasoning = "Pie chart for small distribution"
            elif len(data) > 15:
                chart_type = 'horizontal_bar'
                reasoning = "Horizontal bar chart for many categories"
            else:
                chart_type = 'bar'
                reasoning = "Default bar chart"

            label_column = text_columns[0] if text_columns else columns[0]
            value_column = numeric_columns[0] if numeric_columns else columns[-1]

        return {
            "chart_type": chart_type,
            "title": "Data Analysis",
            "label_column": label_column,
            "value_column": value_column,
            "color_scheme": "professional_blue",
            "show_legend": chart_type in ['pie', 'doughnut', 'line'],
            "reasoning": f"Intelligent fallback: {reasoning}"
        }

    def _perform_comprehensive_data_analysis(self, columns: List[str], data: List[List]) -> Dict[str, Any]:
        """Perform comprehensive analysis of data patterns."""

        analysis = {
            'column_types': {},
            'data_patterns': {},
            'relationships': {},
            'distributions': {}
        }

        for i, col in enumerate(columns):
            sample_values = [row[i] for row in data[:20] if i < len(row) and row[i] is not None]

            if not sample_values:
                analysis['column_types'][col] = 'empty'
                continue

            # Determine column type
            if all(isinstance(val, (int, float)) for val in sample_values):
                analysis['column_types'][col] = 'numeric'
                # Analyze numeric patterns
                values = [float(val) for val in sample_values]
                analysis['data_patterns'][col] = {
                    'min': min(values),
                    'max': max(values),
                    'range': max(values) - min(values),
                    'avg': sum(values) / len(values),
                    'has_large_range': (max(values) - min(values)) > 1000
                }
            elif all(isinstance(val, str) for val in sample_values):
                analysis['column_types'][col] = 'text'
                # Analyze categorical patterns
                unique_values = list(set(sample_values))
                analysis['distributions'][col] = {
                    'unique_count': len(unique_values),
                    'total_count': len(sample_values),
                    'uniqueness_ratio': len(unique_values) / len(sample_values),
                    'sample_values': unique_values[:5]
                }
                # Check if it might be dates
                if any(self._might_be_date(val) for val in sample_values[:3]):
                    analysis['column_types'][col] = 'datetime'
            else:
                analysis['column_types'][col] = 'mixed'

        # Detect relationships between numeric columns
        numeric_columns = [col for col, type_ in analysis['column_types'].items() if type_ == 'numeric']
        if len(numeric_columns) >= 2:
            analysis['relationships']['has_multiple_numeric'] = True
            analysis['relationships']['numeric_columns'] = numeric_columns

        return analysis

    def _analyze_question_context(self, user_question: str) -> Dict[str, Any]:
        """Analyze question for visualization hints."""

        question_lower = user_question.lower()

        context = {
            'asks_for_distribution': any(word in question_lower for word in ['distribution', 'breakdown', 'percentage', 'proportion', 'share']),
            'asks_for_ranking': any(word in question_lower for word in ['top', 'bottom', 'ranking', 'highest', 'lowest', 'best', 'worst']),
            'asks_for_trend': any(word in question_lower for word in ['trend', 'over time', 'timeline', 'progression', 'evolution']),
            'asks_for_comparison': any(word in question_lower for word in ['compare', 'comparison', 'versus', 'vs', 'between']),
            'asks_for_correlation': any(word in question_lower for word in ['correlation', 'relationship', 'related', 'depends on']),
            'mentions_time': any(word in question_lower for word in ['time', 'date', 'month', 'year', 'day', 'hour', 'period']),
            'has_specific_count': any(word in question_lower for word in ['top 5', 'top 10', 'first 20', 'last 15'])
        }

        return context

    def _validate_and_enhance_chart_analysis(self, parsed: Dict[str, Any], columns: List[str], data: List[List], user_question: str) -> Dict[str, Any]:
        """Validate and enhance the LLM's chart analysis."""

        chart_type = parsed.get('chart_type', 'bar')

        # Validate chart type
        valid_types = ['bar', 'horizontal_bar', 'line', 'area', 'pie', 'doughnut', 'scatter', 'bubble', 'radar', 'polar']
        if chart_type not in valid_types:
            chart_type = 'bar'
            parsed['chart_type'] = chart_type

        # Validate column assignments
        label_col = parsed.get('label_column', '')
        value_col = parsed.get('value_column', '')

        # Ensure columns exist
        if label_col not in columns:
            # Find first text column or use first column
            text_cols = [col for col in columns if self._column_is_text(col, columns, data)]
            parsed['label_column'] = text_cols[0] if text_cols else columns[0]

        if value_col not in columns:
            # Find first numeric column or use last column
            numeric_cols = [col for col in columns if self._column_is_numeric(col, columns, data)]
            parsed['value_column'] = numeric_cols[0] if numeric_cols else columns[-1]

        # Add intelligent defaults based on chart type
        if chart_type in ['pie', 'doughnut']:
            parsed['show_legend'] = True
            parsed['chart_specific_options'] = parsed.get('chart_specific_options', {})
            parsed['chart_specific_options']['show_data_labels'] = True

        elif chart_type in ['line', 'area']:
            parsed['chart_specific_options'] = parsed.get('chart_specific_options', {})
            parsed['chart_specific_options']['enable_zoom'] = True

        elif chart_type in ['scatter', 'bubble']:
            parsed['chart_specific_options'] = parsed.get('chart_specific_options', {})
            parsed['chart_specific_options']['show_correlation'] = True

        # Ensure we have a reasoning
        if not parsed.get('reasoning'):
            parsed['reasoning'] = f"Selected {chart_type} chart based on data structure and question context"

        return parsed

    def _create_intelligent_fallback_analysis(self, columns: List[str], data: List[List], user_question: str) -> Dict[str, Any]:
        """Create intelligent fallback when LLM fails - considers ALL chart types."""

        # Analyze data characteristics
        column_types = self._analyze_column_types(columns, data)
        question_context = self._analyze_question_context(user_question)

        # Find appropriate columns
        text_columns = [col for col, type_ in column_types.items() if type_ == 'text']
        numeric_columns = [col for col, type_ in column_types.items() if type_ == 'numeric']
        datetime_columns = [col for col, type_ in column_types.items() if type_ == 'datetime']

        # Intelligent chart type selection
        chart_type = 'bar'  # default
        reasoning = "Default bar chart"

        # Check for specific patterns
        if question_context['asks_for_distribution'] and len(text_columns) == 1 and len(data) <= 8:
            chart_type = 'pie'
            reasoning = "Pie chart for distribution with ≤8 categories"

        elif question_context['asks_for_ranking'] or 'top' in user_question.lower():
            chart_type = 'horizontal_bar'
            reasoning = "Horizontal bar chart for ranking/top N analysis"

        elif question_context['asks_for_trend'] or datetime_columns:
            chart_type = 'line'
            reasoning = "Line chart for trend analysis or time series data"

        elif len(numeric_columns) >= 2:
            chart_type = 'scatter'
            reasoning = "Scatter plot for correlation between multiple numeric variables"

        elif len(data) > 15:
            chart_type = 'horizontal_bar'
            reasoning = "Horizontal bar chart for large number of categories"

        elif len(text_columns) == 1 and len(numeric_columns) == 1 and len(data) <= 8:
            chart_type = 'doughnut'
            reasoning = "Doughnut chart for clean categorical distribution"

        # Column assignments
        label_column = text_columns[0] if text_columns else columns[0]
        value_column = numeric_columns[0] if numeric_columns else columns[-1]

        return {
            "chart_type": chart_type,
            "title": "Data Analysis",
            "label_column": label_column,
            "value_column": value_column,
            "color_scheme": "professional_blue",
            "show_legend": chart_type in ['pie', 'doughnut', 'line'],
            "chart_specific_options": {
                "show_data_labels": chart_type in ['pie', 'doughnut'],
                "enable_zoom": chart_type in ['line', 'area', 'scatter']
            },
            "reasoning": f"Intelligent fallback: {reasoning}"
        }

    def _column_is_text(self, column_name: str, columns: List[str], data: List[List]) -> bool:
        """Check if a column contains primarily text data."""
        try:
            col_index = columns.index(column_name)
        except ValueError:
            return False

        sample_values = [row[col_index] for row in data[:5] if col_index < len(row) and row[col_index] is not None]
        return sample_values and all(isinstance(val, str) for val in sample_values)

    def _column_is_numeric(self, column_name: str, columns: List[str], data: List[List]) -> bool:
        """Check if a column contains primarily numeric data."""
        try:
            col_index = columns.index(column_name)
        except ValueError:
            return False

        sample_values = [row[col_index] for row in data[:5] if col_index < len(row) and row[col_index] is not None]
        return sample_values and all(isinstance(val, (int, float)) for val in sample_values)

    def _might_be_date(self, value: str) -> bool:
        """Check if a string value might be a date."""
        if not isinstance(value, str):
            return False

        # Simple date pattern detection
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        ]

        return any(re.search(pattern, value) for pattern in date_patterns)

    def _analyze_column_types(self, columns: List[str], data: List[List]) -> Dict[str, str]:
        """Analyze what type of data each column contains."""
        column_types = {}

        for i, col in enumerate(columns):
            sample_values = [row[i] for row in data[:5] if i < len(row) and row[i] is not None]

            if not sample_values:
                column_types[col] = 'empty'
            elif all(isinstance(val, (int, float)) for val in sample_values):
                column_types[col] = 'numeric'
            elif all(isinstance(val, str) for val in sample_values):
                column_types[col] = 'text'
            else:
                column_types[col] = 'mixed'

        return column_types

    def _find_first_numeric_column(self, columns: List[str], data: List[List]) -> Optional[str]:
        """Find the first column that contains numeric data."""
        for i, col in enumerate(columns):
            sample_values = [row[i] for row in data[:5] if i < len(row) and row[i] is not None]
            if sample_values and all(isinstance(val, (int, float)) for val in sample_values):
                return col
        return None

    def _create_professional_visualization_safe(self, columns: List[str], data: List[List], viz_analysis: Dict[str, Any], user_question: str) -> str:
        """Create the professional HTML visualization file with safe UTF-8 handling."""

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chart_{timestamp}.html"
        filepath = os.path.join(self.export_dir, filename)

        # Prepare data for Chart.js with FIXED mapping
        chart_data = self._prepare_chart_data_fixed(columns, data, viz_analysis)

        if self._should_log_debug():
            logger.info(f"Chart data prepared: {chart_data}")

        # Generate HTML content with safe encoding
        html_content = self._generate_professional_html_template_safe(chart_data, viz_analysis, user_question)

        # Write to file with proper encoding
        try:
            with open(filepath, 'w', encoding='utf-8', errors='replace') as f:
                f.write(html_content)
        except UnicodeEncodeError:
            # Fallback to ASCII if UTF-8 fails
            with open(filepath, 'w', encoding='ascii', errors='replace') as f:
                f.write(html_content)

        logger.info(f"Professional visualization created: {filepath}")
        return filepath

    def _prepare_chart_data_fixed(self, columns: List[str], data: List[List], viz_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data with ENHANCED support for time series and proper column mapping."""

        chart_type = viz_analysis.get('chart_type', 'bar')

        # Enhanced logic to detect time series data
        time_info = self._detect_time_series_columns(columns, data)

        if time_info['is_time_series']:
            # Handle time series data specially
            return self._prepare_time_series_data(columns, data, viz_analysis, time_info)
        else:
            # Use the corrected column names from the analysis
            label_col = viz_analysis.get('label_column', columns[0] if columns else 'Category')
            value_col = viz_analysis.get('value_column', columns[1] if len(columns) > 1 else 'Value')

            return self._prepare_standard_data(columns, data, viz_analysis, label_col, value_col)

    def _detect_time_series_columns(self, columns: List[str], data: List[List]) -> Dict[str, Any]:
        """Detect if this is time series data and identify relevant columns."""

        time_info = {
            'is_time_series': False,
            'year_column': None,
            'month_column': None,
            'date_column': None,
            'value_column': None,
            'other_columns': []
        }

        # Look for time-related column names
        for i, col in enumerate(columns):
            col_lower = col.lower()

            if col_lower in ['year', 'annee', 'année']:
                time_info['year_column'] = {'name': col, 'index': i}
            elif col_lower in ['month', 'mois', 'month_number']:
                time_info['month_column'] = {'name': col, 'index': i}
            elif 'date' in col_lower or 'time' in col_lower:
                time_info['date_column'] = {'name': col, 'index': i}
            elif any(val_word in col_lower for val_word in ['count', 'amount', 'volume', 'total', 'sum', 'ticket']):
                time_info['value_column'] = {'name': col, 'index': i}
            else:
                time_info['other_columns'].append({'name': col, 'index': i})

        # Determine if this is time series
        has_time_component = (time_info['year_column'] or time_info['month_column'] or time_info['date_column'])
        has_value_component = time_info['value_column'] or any(
            self._column_is_numeric(col, columns, data) for col in columns
        )

        time_info['is_time_series'] = has_time_component and has_value_component

        return time_info

    def _prepare_time_series_data(self, columns: List[str], data: List[List], viz_analysis: Dict[str, Any], time_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare time series data with proper month names and formatting."""

        chart_type = viz_analysis.get('chart_type', 'line')

        # Build time series labels and values
        labels = []
        values = []

        # Month names mapping
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }

        # French month names (if French is detected)
        month_names_fr = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }

        # Detect language (simple check)
        user_question = viz_analysis.get('title', '').lower()
        is_french = any(word in user_question for word in ['mois', 'année', 'évolution', 'par'])
        month_map = month_names_fr if is_french else month_names

        # Sort data by time (year, then month if available)
        sorted_data = sorted(data, key=lambda row: (
            row[time_info['year_column']['index']] if time_info['year_column'] else 0,
            row[time_info['month_column']['index']] if time_info['month_column'] else 0
        ))

        for row in sorted_data:
            # Build time label
            label_parts = []

            if time_info['month_column']:
                month_num = row[time_info['month_column']['index']]
                if isinstance(month_num, (int, float)):
                    month_name = month_map.get(int(month_num), f"Month {month_num}")
                    label_parts.append(month_name)

            if time_info['year_column']:
                year = row[time_info['year_column']['index']]
                if isinstance(year, (int, float)):
                    # Don't format year as "2.02K" - keep it as full year
                    label_parts.append(str(int(year)))

            # Combine label parts
            if label_parts:
                if len(label_parts) == 2:  # Month and Year
                    label = f"{label_parts[0]} {label_parts[1]}"
                else:
                    label = " ".join(label_parts)
            else:
                label = f"Period {len(labels) + 1}"

            labels.append(label)

            # Get value
            if time_info['value_column']:
                value = row[time_info['value_column']['index']]
                values.append(float(value) if isinstance(value, (int, float)) else 0)
            else:
                # Find first numeric column
                for i, cell in enumerate(row):
                    if isinstance(cell, (int, float)) and i not in [
                        time_info.get('year_column', {}).get('index', -1),
                        time_info.get('month_column', {}).get('index', -1)
                    ]:
                        values.append(float(cell))
                        break
                else:
                    values.append(0)

        return {
            'labels': labels,
            'values': values,
            'x_axis': 'Time Period',
            'y_axis': time_info['value_column']['name'] if time_info['value_column'] else 'Value',
            'chart_type': chart_type,
            'is_time_series': True
        }

    def _prepare_standard_data(self, columns: List[str], data: List[List], viz_analysis: Dict[str, Any], label_col: str, value_col: str) -> Dict[str, Any]:
        """Prepare standard (non-time-series) data with proper column mapping."""

        chart_type = viz_analysis.get('chart_type', 'bar')

        if self._should_log_debug():
            logger.info(f"Standard data preparation:")
            logger.info(f"  Chart type: {chart_type}")
            logger.info(f"  Columns available: {columns}")
            logger.info(f"  Label column (categories): {label_col}")
            logger.info(f"  Value column (numbers): {value_col}")

        # Find column indices
        try:
            label_index = columns.index(label_col)
        except ValueError:
            label_index = 0
            label_col = columns[0] if columns else 'Category'

        try:
            value_index = columns.index(value_col)
        except ValueError:
            # Find first numeric column
            value_index = -1
            for i, col in enumerate(columns):
                if self._column_is_numeric(col, columns, data):
                    value_index = i
                    value_col = col
                    break
            if value_index == -1:
                value_index = 1 if len(columns) > 1 else 0
                value_col = columns[value_index] if columns else 'Value'

        if self._should_log_debug():
            logger.info(f"  Final mapping: Label='{label_col}'[{label_index}], Value='{value_col}'[{value_index}]")

        labels = []
        values = []

        for row_idx, row in enumerate(data):
            if len(row) > max(label_index, value_index):
                # Get label (category) with UTF-8 cleaning
                raw_label = row[label_index] if label_index < len(row) else f"Item {row_idx + 1}"
                if raw_label is None:
                    raw_label = f"Item {row_idx + 1}"
                label = self._clean_string_utf8(str(raw_label))

                # Get value (number)
                raw_value = row[value_index] if value_index < len(row) else 0

                # Convert value to number if possible
                if isinstance(raw_value, str):
                    try:
                        value = float(raw_value.replace(',', ''))
                    except:
                        value = 0
                elif raw_value is None:
                    value = 0
                else:
                    value = float(raw_value)

                labels.append(label)
                values.append(value)

                # Debug first few mappings
                if self._should_log_debug() and row_idx < 3:
                    logger.info(f"  Row {row_idx}: '{raw_label}' -> '{label}', {raw_value} -> {value}")

        # Limit data points for better visualization
        if len(labels) > 50:
            labels = labels[:50]
            values = values[:50]

        if self._should_log_debug():
            logger.info(f"  Final data - Labels: {labels[:3]}, Values: {values[:3]}")

        return {
            'labels': labels,
            'values': values,
            'x_axis': label_col,
            'y_axis': value_col,
            'chart_type': chart_type,
            'is_time_series': False
        }

    def _format_professional_cell_value(self, value: Any) -> str:
        """Enhanced cell value formatting that preserves years correctly."""
        if value is None:
            return "—"
        elif isinstance(value, (int, float)):
            # Special handling for years (4-digit numbers between 1900-2100)
            if isinstance(value, (int, float)) and 1900 <= value <= 2100:
                return str(int(value))  # Keep years as full numbers
            elif isinstance(value, float) and value.is_integer():
                return self._format_number_smart(int(value))
            elif isinstance(value, float):
                return self._format_number_smart(value)
            else:
                return self._format_number_smart(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
        else:
            return str(value)

    def _format_number_smart(self, value: float) -> str:
        """Smart number formatting that preserves years and formats large numbers."""
        # Don't format years
        if isinstance(value, (int, float)) and 1900 <= value <= 2100:
            return str(int(value))

        # Format large numbers with K/M suffixes
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.2f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.2f}K"
        else:
            return f"{value:.2f}" if isinstance(value, float) else str(value)


    def _generate_professional_html_template_safe(self, chart_data: Dict[str, Any], viz_analysis: Dict[str, Any], user_question: str) -> str:
        """Generate clean, professional HTML template with safe UTF-8 encoding."""

        chart_type = viz_analysis.get('chart_type', 'bar')
        title = self._clean_string_utf8(viz_analysis.get('title', 'Data Analysis'))
        clean_user_question = self._clean_string_utf8(user_question)

        # Professional color schemes
        colors = ['#4299e1', '#63b3ed', '#90cdf4', '#bee3f8', '#ebf8ff']

        # Generate Chart.js configuration
        chart_config = self._generate_professional_chart_config_safe(chart_data, viz_analysis, colors)

        # Clean data for JSON serialization
        clean_labels = [self._clean_string_utf8(str(label)) for label in chart_data['labels']]
        clean_values = chart_data['values']

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #2d3748;
            line-height: 1.5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 24px auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: #ffffff;
            border-bottom: 1px solid #e2e8f0;
            padding: 24px 32px;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            color: #1a1d29;
            margin-bottom: 8px;
        }}
        
        .header p {{
            font-size: 14px;
            color: #718096;
            font-weight: 400;
        }}
        
        .chart-container {{
            padding: 32px;
            background: #ffffff;
        }}
        
        .chart-wrapper {{
            position: relative;
            width: 100%;
            height: 480px;
        }}
        
        .stats-panel {{
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            padding: 24px 32px;
        }}
        
        .stats-title {{
            font-size: 16px;
            font-weight: 500;
            color: #2d3748;
            margin-bottom: 16px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
        }}
        
        .stat-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 16px;
            text-align: left;
        }}
        
        .stat-value {{
            font-size: 20px;
            font-weight: 600;
            color: #1a1d29;
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #718096;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .footer {{
            text-align: center;
            padding: 16px 32px;
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
            color: #a0aec0;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                margin: 16px;
                border-radius: 6px;
            }}
            
            .header {{
                padding: 20px;
            }}
            
            .header h1 {{
                font-size: 20px;
            }}
            
            .chart-container {{
                padding: 20px;
            }}
            
            .chart-wrapper {{
                height: 360px;
            }}
            
            .stats-panel {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{clean_user_question}</p>
        </div>
        
        <div class="chart-container">
            <div class="chart-wrapper">
                <canvas id="mainChart"></canvas>
            </div>
        </div>
        
        <div class="stats-panel">
            <div class="stats-title">Analysis Summary</div>
            <div class="stats-grid" id="statsContainer">
                <!-- Stats will be populated by JavaScript -->
            </div>
        </div>
        
        <div class="footer">
            Powered by Castor • {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
        </div>
    </div>

    <script>
        // Chart configuration
        const chartConfig = {chart_config};
        
        // Create the chart
        const ctx = document.getElementById('mainChart').getContext('2d');
        const mainChart = new Chart(ctx, chartConfig);
        
        // Generate statistics
        const data = {json.dumps(clean_values, ensure_ascii=True)};
        const labels = {json.dumps(clean_labels, ensure_ascii=True)};
        
        function formatNumber(num) {{
            if (Math.abs(num) >= 1000000) {{
                return (num / 1000000).toFixed(2) + 'M';
            }} else if (Math.abs(num) >= 1000) {{
                return (num / 1000).toFixed(2) + 'K';
            }} else {{
                return num.toFixed(2);
            }}
        }}
        
        function generateStats() {{
            const total = data.reduce((sum, val) => sum + val, 0);
            const average = total / data.length;
            const max = Math.max(...data);
            const min = Math.min(...data);
            
            const stats = [
                {{ label: 'Total Records', value: data.length.toString() }},
                {{ label: 'Sum', value: formatNumber(total) }},
                {{ label: 'Average', value: formatNumber(average) }},
                {{ label: 'Maximum', value: formatNumber(max) }},
                {{ label: 'Minimum', value: formatNumber(min) }}
            ];
            
            const container = document.getElementById('statsContainer');
            container.innerHTML = stats.map(stat => `
                <div class="stat-card">
                    <div class="stat-value">${{stat.value}}</div>
                    <div class="stat-label">${{stat.label}}</div>
                </div>
            `).join('');
        }}
        
        // Initialize stats
        generateStats();
    </script>
</body>
</html>"""

        return html_template

    def _generate_professional_chart_config_safe(self, chart_data: Dict[str, Any], viz_analysis: Dict[str, Any], colors: List[str]) -> str:
        """Generate Chart.js configuration supporting ALL chart types."""

        chart_type = viz_analysis.get('chart_type', 'bar')
        chart_options = viz_analysis.get('chart_specific_options', {})

        # Extended color schemes
        color_schemes = {
            'professional_blue': ['#4299e1', '#63b3ed', '#90cdf4', '#bee3f8', '#ebf8ff'],
            'professional_green': ['#48bb78', '#68d391', '#9ae6b4', '#c6f6d5', '#f0fff4'],
            'professional_purple': ['#9f7aea', '#b794f6', '#d6bcfa', '#e9d8fd', '#faf5ff'],
            'warm': ['#f56565', '#fc8181', '#feb2b2', '#fed7d7', '#fff5f5'],
            'cool': ['#4fd1c7', '#81e6d9', '#b2f5ea', '#c6f7f4', '#f0fdfa']
        }

        selected_colors = color_schemes.get(viz_analysis.get('color_scheme', 'professional_blue'), colors)

        # Base configuration
        config = {
            'type': self._get_chartjs_type(chart_type),
            'data': self._build_chart_data(chart_data, viz_analysis, selected_colors),
            'options': self._build_chart_options(chart_type, chart_data, viz_analysis, chart_options)
        }

        # Convert to JSON and inject JavaScript functions
        config_json = json.dumps(config, indent=2, ensure_ascii=True)

        # Inject callback functions for different chart types
        config_json = self._inject_callback_functions(config_json, chart_type)

        return config_json

    def _get_chartjs_type(self, chart_type: str) -> str:
        """Map our chart types to Chart.js types."""
        type_mapping = {
            'bar': 'bar',
            'horizontal_bar': 'bar',
            'line': 'line',
            'area': 'line',
            'pie': 'pie',
            'doughnut': 'doughnut',
            'scatter': 'scatter',
            'bubble': 'bubble',
            'radar': 'radar',
            'polar': 'polarArea'
        }
        return type_mapping.get(chart_type, 'bar')

    def _build_chart_data(self, chart_data: Dict[str, Any], viz_analysis: Dict[str, Any], colors: List[str]) -> Dict[str, Any]:
        """Enhanced chart data building with proper time series support."""

        chart_type = viz_analysis.get('chart_type', 'bar')
        clean_labels = [self._clean_string_utf8(str(label)) for label in chart_data['labels']]
        is_time_series = chart_data.get('is_time_series', False)

        if chart_type in ['pie', 'doughnut', 'polar']:
            # For pie charts, use multiple colors
            return {
                'labels': clean_labels,
                'datasets': [{
                    'label': chart_data.get('y_axis', 'Value'),
                    'data': chart_data['values'],
                    'backgroundColor': colors[:len(clean_labels)] if len(colors) >= len(clean_labels) else colors * (len(clean_labels) // len(colors) + 1),
                    'borderColor': '#ffffff',
                    'borderWidth': 2,
                    'hoverBorderWidth': 3
                }]
            }

        elif chart_type == 'scatter':
            # For scatter plots, create x,y coordinate pairs
            scatter_data = []
            for i, (label, value) in enumerate(zip(clean_labels, chart_data['values'])):
                scatter_data.append({'x': i, 'y': value, 'label': label})

            return {
                'datasets': [{
                    'label': chart_data.get('y_axis', 'Value'),
                    'data': scatter_data,
                    'backgroundColor': colors[0],
                    'borderColor': colors[0],
                    'pointRadius': 6,
                    'pointHoverRadius': 8
                }]
            }

        elif chart_type == 'bubble':
            # For bubble charts, add size dimension
            bubble_data = []
            max_value = max(chart_data['values']) if chart_data['values'] else 1
            for i, (label, value) in enumerate(zip(clean_labels, chart_data['values'])):
                bubble_data.append({
                    'x': i,
                    'y': value,
                    'r': max(5, min(30, (value / max_value) * 30)),  # Scale bubble size
                    'label': label
                })

            return {
                'datasets': [{
                    'label': chart_data.get('y_axis', 'Value'),
                    'data': bubble_data,
                    'backgroundColor': colors[0] + '80',  # Add transparency
                    'borderColor': colors[0],
                    'borderWidth': 2
                }]
            }

        elif chart_type == 'radar':
            # For radar charts
            return {
                'labels': clean_labels,
                'datasets': [{
                    'label': chart_data.get('y_axis', 'Value'),
                    'data': chart_data['values'],
                    'backgroundColor': colors[0] + '40',  # Add transparency
                    'borderColor': colors[0],
                    'borderWidth': 2,
                    'pointBackgroundColor': colors[0],
                    'pointBorderColor': '#ffffff',
                    'pointRadius': 4
                }]
            }

        else:
            # For bar, line, area charts
            dataset_config = {
                'label': chart_data.get('y_axis', 'Value'),
                'data': chart_data['values'],
                'backgroundColor': colors[0],
                'borderColor': colors[0],
                'borderWidth': 2,
                'hoverBackgroundColor': colors[1] if len(colors) > 1 else colors[0],
                'hoverBorderColor': colors[0],
                'hoverBorderWidth': 3
            }

            # Chart-specific properties
            if chart_type == 'line':
                dataset_config.update({
                    'fill': False,
                    'tension': 0.3,
                    'pointRadius': 5,
                    'pointHoverRadius': 8,
                    'pointBackgroundColor': colors[0],
                    'pointBorderColor': '#ffffff',
                    'pointBorderWidth': 2
                })
                # For time series, make points more visible
                if is_time_series:
                    dataset_config.update({
                        'pointRadius': 6,
                        'pointHoverRadius': 10,
                        'borderWidth': 3
                    })

            elif chart_type == 'area':
                dataset_config.update({
                    'fill': True,
                    'tension': 0.3,
                    'pointRadius': 4,
                    'pointHoverRadius': 6,
                    'backgroundColor': colors[0] + '40'  # Add transparency for area
                })
            elif chart_type in ['bar', 'horizontal_bar']:
                dataset_config.update({
                    'borderRadius': 4,
                    'borderSkipped': False
                })

            return {
                'labels': clean_labels,
                'datasets': [dataset_config]
            }

    def _build_chart_options(self, chart_type: str, chart_data: Dict[str, Any], viz_analysis: Dict[str, Any], chart_options: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive options for all chart types."""

        base_options = {
            'responsive': True,
            'maintainAspectRatio': False,
            'plugins': {
                'legend': {
                    'display': viz_analysis.get('show_legend', False),
                    'position': 'top',
                    'labels': {
                        'usePointStyle': True,
                        'padding': 20,
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '400'
                        },
                        'color': '#718096'
                    }
                },
                'tooltip': self._build_tooltip_config(chart_type)
            },
            'animation': {
                'duration': 800,
                'easing': 'easeOutQuart'
            }
        }

        # Chart-type specific options
        if chart_type in ['pie', 'doughnut']:
            base_options['plugins']['legend']['display'] = True
            base_options['plugins']['legend']['position'] = 'right'

            if chart_options.get('show_data_labels', False):
                base_options['plugins']['datalabels'] = {
                    'display': True,
                    'color': '#ffffff',
                    'font': {'weight': 'bold'}
                }

        elif chart_type in ['bar', 'horizontal_bar']:
            base_options['interaction'] = {
                'intersect': True,
                'mode': 'nearest'
            }
            base_options['scales'] = self._build_scales_config(chart_type, chart_data)

            if chart_type == 'horizontal_bar':
                base_options['indexAxis'] = 'y'

        elif chart_type in ['line', 'area']:
            base_options['interaction'] = {
                'intersect': False,
                'mode': 'index'
            }
            base_options['scales'] = self._build_scales_config(chart_type, chart_data)

            if chart_options.get('enable_zoom', False):
                base_options['plugins']['zoom'] = {
                    'pan': {'enabled': True, 'mode': 'x'},
                    'zoom': {'wheel': {'enabled': True}, 'mode': 'x'}
                }

        elif chart_type == 'scatter':
            base_options['scales'] = {
                'x': {
                    'type': 'linear',
                    'position': 'bottom',
                    'title': {'display': True, 'text': chart_data.get('x_axis', 'Category')}
                },
                'y': {
                    'title': {'display': True, 'text': chart_data.get('y_axis', 'Value')}
                }
            }

        elif chart_type == 'radar':
            base_options['scales'] = {
                'r': {
                    'beginAtZero': True,
                    'grid': {'color': '#f1f5f9'},
                    'pointLabels': {
                        'font': {'size': 11, 'family': 'Inter'},
                        'color': '#718096'
                    }
                }
            }

        return base_options

    def _build_scales_config(self, chart_type: str, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build scales configuration for charts that need them."""

        if chart_type == 'horizontal_bar':
            return {
                'x': {
                    'beginAtZero': True,
                    'grid': {'color': '#f1f5f9', 'lineWidth': 1},
                    'ticks': {'color': '#718096', 'font': {'size': 11, 'family': 'Inter'}},
                    'title': {
                        'display': True,
                        'text': chart_data.get('y_axis', 'Value'),
                        'font': {'size': 12, 'family': 'Inter', 'weight': '500'},
                        'color': '#4a5568'
                    }
                },
                'y': {
                    'grid': {'color': '#f8fafc', 'lineWidth': 1},
                    'ticks': {'color': '#718096', 'font': {'size': 11, 'family': 'Inter'}, 'maxRotation': 0},
                    'title': {
                        'display': True,
                        'text': chart_data.get('x_axis', 'Category'),
                        'font': {'size': 12, 'family': 'Inter', 'weight': '500'},
                        'color': '#4a5568'
                    }
                }
            }
        else:
            # For bar, line, area charts
            return {
                'x': {
                    'grid': {'color': '#f8fafc', 'lineWidth': 1},
                    'ticks': {'color': '#718096', 'font': {'size': 11, 'family': 'Inter'}, 'maxRotation': 45},
                    'title': {
                        'display': True,
                        'text': chart_data.get('x_axis', 'Category'),
                        'font': {'size': 12, 'family': 'Inter', 'weight': '500'},
                        'color': '#4a5568'
                    }
                },
                'y': {
                    'beginAtZero': True,
                    'grid': {'color': '#f1f5f9', 'lineWidth': 1},
                    'ticks': {'color': '#718096', 'font': {'size': 11, 'family': 'Inter'}},
                    'title': {
                        'display': True,
                        'text': chart_data.get('y_axis', 'Value'),
                        'font': {'size': 12, 'family': 'Inter', 'weight': '500'},
                        'color': '#4a5568'
                    }
                }
            }

    def _build_tooltip_config(self, chart_type: str) -> Dict[str, Any]:
        """Build tooltip configuration for different chart types."""

        base_tooltip = {
            'enabled': True,
            'backgroundColor': '#ffffff',
            'titleColor': '#2d3748',
            'bodyColor': '#4a5568',
            'borderColor': '#e2e8f0',
            'borderWidth': 1,
            'cornerRadius': 6,
            'displayColors': True,
            'titleFont': {'size': 13, 'family': 'Inter', 'weight': '500'},
            'bodyFont': {'size': 12, 'family': 'Inter', 'weight': '400'},
            'padding': 12
        }

        # Chart-specific tooltip customizations
        if chart_type in ['pie', 'doughnut']:
            base_tooltip['displayColors'] = False
            base_tooltip['callbacks'] = {
                'label': 'PLACEHOLDER_PIE_CALLBACK'
            }
        elif chart_type in ['scatter', 'bubble']:
            base_tooltip['callbacks'] = {
                'label': 'PLACEHOLDER_SCATTER_CALLBACK'
            }
        else:
            base_tooltip['callbacks'] = {
                'label': 'PLACEHOLDER_DEFAULT_CALLBACK'
            }

        return base_tooltip

    def _inject_callback_functions(self, config_json: str, chart_type: str) -> str:
        """Inject JavaScript callback functions into the JSON configuration."""

        # Inject number formatting callback for tick labels (only for charts with scales)
        if chart_type in ['bar', 'horizontal_bar', 'line', 'area']:
            if chart_type == 'horizontal_bar':
                # X-axis gets the number formatting for horizontal bars
                config_json = config_json.replace(
                    '"x": {\n        "beginAtZero": true,\n        "grid": {\n          "color": "#f1f5f9",\n          "lineWidth": 1\n        },\n        "ticks": {\n          "color": "#718096",\n          "font": {\n            "size": 11,\n            "family": "Inter"\n          }\n        }',
                    '''      "x": {
            "beginAtZero": true,
            "grid": {
              "color": "#f1f5f9",
              "lineWidth": 1
            },
            "ticks": {
              "color": "#718096",
              "font": {
                "size": 11,
                "family": "Inter"
              },
              "callback": function(value) {
                if (Math.abs(value) >= 1000000) {
                  return (value / 1000000).toFixed(1) + "M";
                } else if (Math.abs(value) >= 1000) {
                  return (value / 1000).toFixed(1) + "K";
                } else {
                  return value.toLocaleString();
                }
              }
            }'''
                )
            else:
                # Y-axis gets the number formatting for vertical charts
                config_json = config_json.replace(
                    '"y": {\n        "beginAtZero": true,\n        "grid": {\n          "color": "#f1f5f9",\n          "lineWidth": 1\n        },\n        "ticks": {\n          "color": "#718096",\n          "font": {\n            "size": 11,\n            "family": "Inter"\n          }\n        }',
                    '''      "y": {
            "beginAtZero": true,
            "grid": {
              "color": "#f1f5f9",
              "lineWidth": 1
            },
            "ticks": {
              "color": "#718096",
              "font": {
                "size": 11,
                "family": "Inter"
              },
              "callback": function(value) {
                if (Math.abs(value) >= 1000000) {
                  return (value / 1000000).toFixed(1) + "M";
                } else if (Math.abs(value) >= 1000) {
                  return (value / 1000).toFixed(1) + "K";
                } else {
                  return value.toLocaleString();
                }
              }
            }'''
                )

        # Inject tooltip callbacks based on chart type
        if chart_type in ['pie', 'doughnut']:
            config_json = config_json.replace(
                '"label": "PLACEHOLDER_PIE_CALLBACK"',
                '''        "label": function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.parsed / total) * 100).toFixed(1);
                return context.label + ": " + context.parsed.toLocaleString() + " (" + percentage + "%)";
              }'''
            )
        elif chart_type in ['scatter', 'bubble']:
            config_json = config_json.replace(
                '"label": "PLACEHOLDER_SCATTER_CALLBACK"',
                '''        "label": function(context) {
                return context.dataset.label + ": (" + context.parsed.x + ", " + context.parsed.y + ")";
              }'''
            )
        else:
            config_json = config_json.replace(
                '"label": "PLACEHOLDER_DEFAULT_CALLBACK"',
                '''        "label": function(context) {
                const value = context.parsed.y || context.parsed.x;
                let formatted;
                if (Math.abs(value) >= 1000000) {
                  formatted = (value / 1000000).toFixed(2) + "M";
                } else if (Math.abs(value) >= 1000) {
                  formatted = (value / 1000).toFixed(2) + "K";
                } else {
                  formatted = value.toLocaleString();
                }
                return context.dataset.label + ": " + formatted;
              }'''
            )

        return config_json

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _should_log_debug(self) -> bool:
        """Check if debug logging should be enabled."""
        return logger.isEnabledFor(logging.DEBUG) or True  # Enable for debugging