"""
UTF-8 Fixed Professional Visualization Tool - FIXED INDENTATION ISSUE
"""

from typing import Dict, Any, List, Optional
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
        """Safely analyze data for visualization with CORRECTED axis mapping logic."""

        # Prepare safe data sample for LLM analysis
        sample_data = []
        for i, row in enumerate(data[:3]):  # Show first 3 rows
            row_dict = {}
            for j, col in enumerate(columns):
                if j < len(row):
                    value = row[j]
                    # Clean the value for JSON serialization
                    if isinstance(value, str):
                        value = self._clean_string_utf8(value)
                    row_dict[col] = value
            sample_data.append(row_dict)

        data_structure = {
            'columns': columns,
            'sample_data': sample_data,
            'total_rows': len(data),
            'data_types': self._analyze_column_types(columns, data)
        }

        # IMPROVED prompt with clear axis instructions
        prompt = f"""Analyze this query result and determine the best visualization approach.

User Question: "{user_question}"
Data Structure: {json.dumps(data_structure, indent=2, default=str, ensure_ascii=True)}

**CRITICAL AXIS MAPPING RULES:**
1. For horizontal bar charts (which show rankings/top N):
   - CATEGORIES/NAMES go on the Y-axis (vertical labels)
   - VALUES/NUMBERS go on the X-axis (horizontal bars)
   - Example: Company names on Y-axis, ticket counts on X-axis

2. For vertical bar charts:
   - CATEGORIES/NAMES go on the X-axis (bottom labels)  
   - VALUES/NUMBERS go on the Y-axis (vertical bars)

**COLUMN IDENTIFICATION:**
- Text columns (company names, categories) = LABELS/CATEGORIES
- Numeric columns (counts, amounts, values) = VALUES/NUMBERS

Choose the chart type and map columns correctly:

Respond ONLY with valid JSON:
{{
    "chart_type": "horizontal_bar|bar|line|area|scatter",
    "title": "Clean title without emojis",
    "label_column": "column_name_containing_categories_or_names",
    "value_column": "column_name_containing_numeric_values",
    "color_scheme": "professional_blue",
    "show_legend": false,
    "reasoning": "Brief explanation of column mapping"
}}

**REMEMBER:** 
- Label column = text/names (company names, categories)
- Value column = numbers (counts, amounts, measurements)

JSON Response:"""

        try:
            response = self.llm._call(prompt)
            clean_response = response.strip()

            # Clean JSON response
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]

            # Remove any trailing text after the JSON
            json_end = clean_response.rfind('}')
            if json_end != -1:
                clean_response = clean_response[:json_end + 1]

            parsed = json.loads(clean_response.strip())

            # VALIDATION AND CORRECTION: Ensure correct mapping
            label_col = parsed.get('label_column', '')
            value_col = parsed.get('value_column', '')

            # Validate that label column is actually text and value column is numeric
            if label_col in columns and value_col in columns:
                # Check if we have the mapping backwards
                label_index = columns.index(label_col)
                value_index = columns.index(value_col)

                # Sample values to check types
                label_samples = [row[label_index] for row in data[:3] if label_index < len(row)]
                value_samples = [row[value_index] for row in data[:3] if value_index < len(row)]

                label_is_text = all(isinstance(v, str) for v in label_samples if v is not None)
                value_is_numeric = all(isinstance(v, (int, float)) for v in value_samples if v is not None)

                # If mapping is backwards, fix it
                if not label_is_text or not value_is_numeric:
                    if self._should_log_debug():
                        logger.warning(f"LLM mapping seems backwards - fixing automatically")
                        logger.warning(f"  Original: label='{label_col}' (text: {label_is_text}), value='{value_col}' (numeric: {value_is_numeric})")

                    # Swap them
                    parsed['label_column'] = value_col
                    parsed['value_column'] = label_col

                    if self._should_log_debug():
                        logger.warning(f"  Corrected: label='{value_col}', value='{label_col}'")

            # Final validation - ensure columns exist
            if parsed.get('label_column') not in columns:
                parsed['label_column'] = columns[0] if columns else 'Category'
            if parsed.get('value_column') not in columns:
                numeric_col = self._find_first_numeric_column(columns, data)
                parsed['value_column'] = numeric_col if numeric_col else columns[-1] if columns else 'Value'

            return parsed

        except Exception as e:
            logger.warning(f"LLM visualization analysis failed: {e}")
            # Intelligent fallback based on data structure
            return self._create_smart_fallback_analysis(columns, data, user_question)

    def _create_smart_fallback_analysis(self, columns: List[str], data: List[List], user_question: str) -> Dict[str, Any]:
        """Create intelligent fallback when LLM fails - with CORRECT mapping."""

        # Analyze column types
        column_types = self._analyze_column_types(columns, data)

        # Find text and numeric columns CORRECTLY
        text_columns = [col for col, type_ in column_types.items() if type_ == 'text']
        numeric_columns = [col for col, type_ in column_types.items() if type_ == 'numeric']

        # CORRECT assignments
        label_column = text_columns[0] if text_columns else columns[0]      # Text = labels
        value_column = numeric_columns[0] if numeric_columns else columns[-1]  # Numbers = values

        # Choose chart type based on question context
        question_lower = user_question.lower()
        if 'top' in question_lower or 'ranking' in question_lower or 'most' in question_lower:
            chart_type = "horizontal_bar"
        elif len(data) <= 15:
            chart_type = "horizontal_bar"
        else:
            chart_type = "bar"

        return {
            "chart_type": chart_type,
            "title": "Data Analysis",
            "label_column": label_column,  # ✅ CORRECT: text column for labels
            "value_column": value_column,  # ✅ CORRECT: numeric column for values
            "color_scheme": "professional_blue",
            "show_legend": False,
            "reasoning": f"Fallback: Using {label_column} (text) as labels vs {value_column} (numeric) as values"
        }

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
        """Prepare data with CORRECTLY FIXED column mapping."""

        chart_type = viz_analysis.get('chart_type', 'bar')
        # Use the corrected column names from the analysis
        label_col = viz_analysis.get('label_column', columns[0] if columns else 'Category')
        value_col = viz_analysis.get('value_column', columns[1] if len(columns) > 1 else 'Value')

        if self._should_log_debug():
            logger.info(f"Chart type: {chart_type}")
            logger.info(f"Columns available: {columns}")
            logger.info(f"Label column (categories): {label_col}")
            logger.info(f"Value column (numbers): {value_col}")

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
                sample_vals = [row[i] for row in data[:3] if i < len(row)]
                if sample_vals and all(isinstance(v, (int, float)) for v in sample_vals):
                    value_index = i
                    value_col = col
                    break
            if value_index == -1:
                value_index = 1 if len(columns) > 1 else 0
                value_col = columns[value_index] if columns else 'Value'

        if self._should_log_debug():
            logger.info(f"Final mapping: Label='{label_col}'[{label_index}], Value='{value_col}'[{value_index}]")

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
                    logger.info(f"Row {row_idx}: '{raw_label}' -> '{label}', {raw_value} -> {value}")

        # Limit data points for better visualization
        if len(labels) > 50:
            labels = labels[:50]
            values = values[:50]

        if self._should_log_debug():
            logger.info(f"Final data - Labels: {labels[:3]}, Values: {values[:3]}")

        return {
            'labels': labels,
            'values': values,
            'x_axis': label_col,    # For display purposes
            'y_axis': value_col,    # For display purposes
            'chart_type': chart_type
        }

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
        """Generate professional Chart.js configuration with WORKING axis and tooltips."""

        chart_type = viz_analysis.get('chart_type', 'bar')

        # Clean labels for JSON
        clean_labels = [self._clean_string_utf8(str(label)) for label in chart_data['labels']]

        # For horizontal bar charts, we need specific configuration
        is_horizontal = chart_type == 'horizontal_bar'

        # Professional Chart.js configuration
        config = {
            'type': 'bar',  # Always use 'bar', horizontal is controlled by indexAxis
            'data': {
                'labels': clean_labels,
                'datasets': [{
                    'label': chart_data['y_axis'],
                    'data': chart_data['values'],
                    'backgroundColor': colors[0],
                    'borderColor': colors[0],
                    'borderWidth': 2,
                    'borderRadius': 4,
                    'hoverBackgroundColor': '#63b3ed',
                    'hoverBorderColor': '#4299e1',
                    'hoverBorderWidth': 3
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'interaction': {
                    'intersect': True if is_horizontal else False,
                    'mode': 'nearest' if is_horizontal else 'index'
                },
                'plugins': {
                    'legend': {
                        'display': viz_analysis.get('show_legend', False)
                    }
                },
                'scales': {},
                'animation': {
                    'duration': 600,
                    'easing': 'easeOutQuart'
                }
            }
        }

        # Add indexAxis for horizontal bars
        if is_horizontal:
            config['options']['indexAxis'] = 'y'

        # Configure scales based on chart orientation
        if is_horizontal:
            # For horizontal bars: X = values (numbers), Y = labels (categories)
            config['options']['scales'] = {
                'x': {
                    'beginAtZero': True,
                    'grid': {
                        'color': '#f1f5f9',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        }
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['y_axis'],  # The values (ticket_count)
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                },
                'y': {
                    'grid': {
                        'color': '#f8fafc',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        },
                        'maxRotation': 0
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['x_axis'],  # The categories (NAME)
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                }
            }
        else:
            # For vertical bars: X = labels (categories), Y = values (numbers)
            config['options']['scales'] = {
                'x': {
                    'grid': {
                        'color': '#f8fafc',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        },
                        'maxRotation': 45
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['x_axis'],  # The categories
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                },
                'y': {
                    'beginAtZero': True,
                    'grid': {
                        'color': '#f1f5f9',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        }
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['y_axis'],  # The values
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                }
            }

        # Convert to JSON string and then fix the callback functions
        config_json = json.dumps(config, indent=2, ensure_ascii=True)

        # Now we need to add the callback functions as actual JavaScript functions
        # We'll do string replacement to inject the functions

        # Add tick formatting callback for the value axis
        if is_horizontal:
            # For horizontal, X axis has the values
            config_json = config_json.replace(
                '"ticks": {\n          "color": "#718096",\n          "font": {\n            "size": 11,\n            "family": "Inter"\n          }\n        }',
                '''    "ticks": {
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
            # For vertical, Y axis has the values
            config_json = config_json.replace(
                '"y": {\n        "beginAtZero": true,\n        "grid": {\n          "color": "#f1f5f9",\n          "lineWidth": 1\n        },\n        "ticks": {\n          "color": "#718096",\n          "font": {\n            "size": 11,\n            "family": "Inter"\n          }\n        }',
                '''    "y": {
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

        # Add tooltip configuration
        tooltip_config = '''"tooltip": {
            "enabled": true,
            "backgroundColor": "#ffffff",
            "titleColor": "#2d3748",
            "bodyColor": "#4a5568",
            "borderColor": "#e2e8f0",
            "borderWidth": 1,
            "cornerRadius": 6,
            "displayColors": false,
            "titleFont": {
              "size": 13,
              "family": "Inter",
              "weight": "500"
            },
            "bodyFont": {
              "size": 12,
              "family": "Inter",
              "weight": "400"
            },
            "padding": 12,
            "callbacks": {
              "label": function(context) {
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
              }
            }
          }'''

        # Insert tooltip after legend
        config_json = config_json.replace(
            '"legend": {\n          "display": false\n        }',
            f'''    "legend": {{
              "display": false
            }},
            {tooltip_config}'''
        )

        return config_json

    def _get_scales_config(self, chart_type: str, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get proper scales configuration based on chart type."""

        if chart_type in ['pie', 'doughnut']:
            return {}

        if chart_type == 'horizontal_bar':
            # For horizontal bars, X is values, Y is labels
            return {
                'x': {
                    'beginAtZero': True,
                    'grid': {
                        'color': '#f1f5f9',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        },
                        'callback': 'function(value) { if (Math.abs(value) >= 1000000) { return (value / 1000000).toFixed(1) + "M"; } else if (Math.abs(value) >= 1000) { return (value / 1000).toFixed(1) + "K"; } else { return value.toLocaleString(); } }'
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['y_axis'],
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                },
                'y': {
                    'grid': {
                        'color': '#f8fafc',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        },
                        'maxRotation': 0
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['x_axis'],
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                }
            }
        else:
            # For regular vertical bars/lines
            return {
                'y': {
                    'beginAtZero': True,
                    'grid': {
                        'color': '#f1f5f9',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        },
                        'callback': 'function(value) { if (Math.abs(value) >= 1000000) { return (value / 1000000).toFixed(1) + "M"; } else if (Math.abs(value) >= 1000) { return (value / 1000).toFixed(1) + "K" else { return value.toLocaleString(); } }'
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['y_axis'],
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                },
                'x': {
                    'grid': {
                        'color': '#f8fafc',
                        'lineWidth': 1
                    },
                    'ticks': {
                        'color': '#718096',
                        'font': {
                            'size': 11,
                            'family': 'Inter'
                        },
                        'maxRotation': 45
                    },
                    'title': {
                        'display': True,
                        'text': chart_data['x_axis'],
                        'font': {
                            'size': 12,
                            'family': 'Inter',
                            'weight': '500'
                        },
                        'color': '#4a5568'
                    }
                }
            }

    def _should_log_debug(self) -> bool:
        """Check if debug logging should be enabled."""
        return logger.isEnabledFor(logging.DEBUG) or True  # Enable for debugging

    def _get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics."""
        try:
            stat = os.stat(file_path)
            return {
                'size_bytes': stat.st_size,
                'size_human': self._format_file_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'absolute_path': os.path.abspath(file_path),
                'filename': os.path.basename(file_path)
            }
        except Exception as e:
            logger.error(f"Failed to get file stats: {e}")
            return {'error': str(e)}

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"