"""
Modern Visualization Tool - Creates fancy interactive charts and dashboards
"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import Field
import json
import os
import logging
from datetime import datetime
from llm.custom_gpt import CustomGPT

logger = logging.getLogger(__name__)

class ModernVisualizationTool(BaseTool):
    """Create modern, interactive visualizations from query results."""

    name: str = "create_visualization"
    description: str = """
    Generate modern, interactive charts and dashboards from query results.
    Creates HTML files with Chart.js visualizations that are fancy and lightweight.
    """

    export_dir: str = Field(default="visualizations")
    llm: CustomGPT = Field(default_factory=CustomGPT)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create visualizations directory if it doesn't exist
        os.makedirs(self.export_dir, exist_ok=True)

    def _run(self, query_result: Dict[str, Any], user_question: str = "", csv_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create interactive visualization from query results."""
        try:
            # Check if we have visualizable data
            if not self._is_visualizable(query_result):
                return {
                    'success': False,
                    'message': 'Data is not suitable for visualization',
                    'reason': 'No numeric data or insufficient rows'
                }

            # Analyze data structure and determine best visualization type
            viz_analysis = self._analyze_data_for_visualization(query_result, user_question)

            # Generate the visualization
            html_file = self._create_interactive_visualization(query_result, viz_analysis, user_question)

            # Get file stats
            file_stats = self._get_file_stats(html_file)

            return {
                'success': True,
                'html_file': html_file,
                'visualization_type': viz_analysis.get('chart_type'),
                'file_stats': file_stats,
                'message': f"Interactive visualization created: {os.path.basename(html_file)}"
            }

        except Exception as e:
            logger.error(f"Visualization creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to create visualization: {str(e)}"
            }

    def _is_visualizable(self, query_result: Dict[str, Any]) -> bool:
        """Check if query results are suitable for visualization."""
        if not query_result.get('success', True):
            return False

        result_data = query_result.get('result', {})
        data = result_data.get('data', [])
        columns = result_data.get('columns', [])

        # Need at least 2 rows and 2 columns for meaningful visualization
        if len(data) < 2 or len(columns) < 2:
            return False

        # Check if we have at least one numeric column
        has_numeric = False
        for row in data[:5]:  # Check first 5 rows
            for value in row:
                if isinstance(value, (int, float)) and value != 0:
                    has_numeric = True
                    break
            if has_numeric:
                break

        return has_numeric

    def _analyze_data_for_visualization(self, query_result: Dict[str, Any], user_question: str) -> Dict[str, Any]:
        """Use LLM to analyze data and determine best visualization approach."""

        result_data = query_result.get('result', {})
        columns = result_data.get('columns', [])
        data = result_data.get('data', [])

        # Prepare data sample for LLM analysis
        data_sample = {
            'columns': columns,
            'sample_rows': data[:5],  # First 5 rows
            'total_rows': len(data),
            'row_count': len(data)
        }

        prompt = f"""Analyze this query result data and determine the best modern visualization approach.

User Question: "{user_question}"
Data Structure: {json.dumps(data_sample, indent=2, default=str)}

Determine the best chart type and configuration:

Available chart types:
- bar: For categorical comparisons (counts, sums by category)
- line: For trends over time or sequential data
- pie: For parts of a whole (percentages, distributions)
- scatter: For correlations between two numeric variables
- area: For cumulative trends or stacked data
- doughnut: Modern alternative to pie charts
- radar: For multi-dimensional comparisons

Respond with JSON:
{{
    "chart_type": "bar|line|pie|scatter|area|doughnut|radar",
    "title": "Engaging chart title",
    "x_axis": "column_name_for_x_axis",
    "y_axis": "column_name_for_y_axis", 
    "color_scheme": "modern_blue|vibrant|pastel|dark|gradient",
    "show_legend": true,
    "interactive_features": ["zoom", "hover", "animation"],
    "reasoning": "Why this visualization works best"
}}

Focus on making it visually appealing and informative.

JSON Response:"""

        try:
            response = self.llm._call(prompt)
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:-3]

            parsed = json.loads(clean_response)
            return parsed

        except Exception as e:
            logger.warning(f"LLM visualization analysis failed: {e}")
            # Intelligent fallback based on data structure
            return self._create_fallback_analysis(columns, data)

    def _create_fallback_analysis(self, columns: List[str], data: List[List]) -> Dict[str, Any]:
        """Create fallback visualization analysis when LLM fails."""

        # Simple heuristics for chart type selection
        if len(columns) == 2:
            # Check if first column could be categories/labels
            first_col_sample = [row[0] for row in data[:5] if len(row) > 0]
            if all(isinstance(val, str) for val in first_col_sample):
                chart_type = "bar"
            else:
                chart_type = "line"
        elif len(data) <= 10:  # Small dataset
            chart_type = "pie"
        else:
            chart_type = "bar"

        return {
            "chart_type": chart_type,
            "title": "Query Results Visualization",
            "x_axis": columns[0] if columns else "Category",
            "y_axis": columns[1] if len(columns) > 1 else "Value",
            "color_scheme": "modern_blue",
            "show_legend": True,
            "interactive_features": ["hover", "animation"],
            "reasoning": "Fallback analysis based on data structure"
        }

    def _create_interactive_visualization(self, query_result: Dict[str, Any], viz_analysis: Dict[str, Any], user_question: str) -> str:
        """Create the interactive HTML visualization file."""

        result_data = query_result.get('result', {})
        columns = result_data.get('columns', [])
        data = result_data.get('data', [])

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"visualization_{timestamp}.html"
        filepath = os.path.join(self.export_dir, filename)

        # Prepare data for Chart.js
        chart_data = self._prepare_chart_data(columns, data, viz_analysis)

        # Generate HTML content
        html_content = self._generate_html_template(chart_data, viz_analysis, user_question)

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Visualization created: {filepath}")
        return filepath

    def _prepare_chart_data(self, columns: List[str], data: List[List], viz_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data in Chart.js format."""

        chart_type = viz_analysis.get('chart_type', 'bar')
        x_axis = viz_analysis.get('x_axis', columns[0] if columns else 'Category')
        y_axis = viz_analysis.get('y_axis', columns[1] if len(columns) > 1 else 'Value')

        # Find column indices
        x_index = columns.index(x_axis) if x_axis in columns else 0
        y_index = columns.index(y_axis) if y_axis in columns else 1

        labels = []
        values = []

        for row in data:
            if len(row) > max(x_index, y_index):
                label = str(row[x_index]) if x_index < len(row) else f"Row {len(labels) + 1}"
                value = row[y_index] if y_index < len(row) else 0

                # Convert value to number if possible
                if isinstance(value, str):
                    try:
                        value = float(value)
                    except:
                        value = 0

                labels.append(label)
                values.append(value)

        # Limit data points for better visualization
        if len(labels) > 50:
            labels = labels[:50]
            values = values[:50]

        return {
            'labels': labels,
            'values': values,
            'x_axis': x_axis,
            'y_axis': y_axis,
            'chart_type': chart_type
        }

    def _generate_html_template(self, chart_data: Dict[str, Any], viz_analysis: Dict[str, Any], user_question: str) -> str:
        """Generate modern HTML template with Chart.js."""

        chart_type = viz_analysis.get('chart_type', 'bar')
        title = viz_analysis.get('title', 'Query Results')
        color_scheme = viz_analysis.get('color_scheme', 'modern_blue')

        # Color schemes
        color_schemes = {
            'modern_blue': ['#3B82F6', '#1E40AF', '#2563EB', '#60A5FA', '#93C5FD'],
            'vibrant': ['#EF4444', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6'],
            'pastel': ['#FCA5A5', '#FDE68A', '#A7F3D0', '#BFDBFE', '#C4B5FD'],
            'dark': ['#374151', '#4B5563', '#6B7280', '#9CA3AF', '#D1D5DB'],
            'gradient': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        }

        colors = color_schemes.get(color_scheme, color_schemes['modern_blue'])

        # Generate Chart.js configuration
        chart_config = self._generate_chart_config(chart_data, viz_analysis, colors)

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #3B82F6, #1E40AF);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .chart-container {{
            padding: 40px;
            position: relative;
            min-height: 500px;
        }}

        .chart-wrapper {{
            position: relative;
            width: 100%;
            height: 500px;
        }}

        .info-panel {{
            background: #F8FAFC;
            padding: 30px;
            border-top: 1px solid #E2E8F0;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #3B82F6;
        }}

        .stat-label {{
            font-size: 0.9rem;
            color: #6B7280;
            margin-top: 5px;
        }}

        .powered-by {{
            text-align: center;
            padding: 20px;
            color: #6B7280;
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}

            .chart-container {{
                padding: 20px;
            }}

            .chart-wrapper {{
                height: 400px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {title}</h1>
            <p>Query : {user_question}</p>
        </div>

        <div class="chart-container">
            <div class="chart-wrapper">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <div class="info-panel">
            <h3>📈 Data Insights</h3>
            <div class="stats" id="statsContainer">
                <!-- Stats will be populated by JavaScript -->
            </div>
        </div>

        <div class="powered-by">
            🚀 Powered by Castor • Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
        </div>
    </div>

    <script>
        // Chart configuration
        const chartConfig = {chart_config};

        // Create the chart
        const ctx = document.getElementById('mainChart').getContext('2d');
        const mainChart = new Chart(ctx, chartConfig);

        // Generate statistics
        const data = {json.dumps(chart_data['values'])};
        const labels = {json.dumps(chart_data['labels'])};

        function generateStats() {{
            const total = data.reduce((sum, val) => sum + val, 0);
            const average = total / data.length;
            const max = Math.max(...data);
            const min = Math.min(...data);

            const stats = [
                {{ label: 'Total Records', value: data.length }},
                {{ label: 'Sum', value: total.toLocaleString() }},
                {{ label: 'Average', value: average.toFixed(2) }},
                {{ label: 'Maximum', value: max.toLocaleString() }},
                {{ label: 'Minimum', value: min.toLocaleString() }}
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

        // Add smooth animations
        mainChart.options.animation = {{
            duration: 2000,
            easing: 'easeInOutQuart'
        }};
    </script>
</body>
</html>"""

        return html_template

    def _generate_chart_config(self, chart_data: Dict[str, Any], viz_analysis: Dict[str, Any], colors: List[str]) -> str:
        """Generate Chart.js configuration as JSON string."""

        chart_type = viz_analysis.get('chart_type', 'bar')

        # Base configuration
        config = {
            'type': chart_type,
            'data': {
                'labels': chart_data['labels'],
                'datasets': [{
                    'label': chart_data['y_axis'],
                    'data': chart_data['values'],
                    'backgroundColor': colors[0] if chart_type in ['pie', 'doughnut'] else colors,
                    'borderColor': colors[0],
                    'borderWidth': 2,
                    'borderRadius': 8 if chart_type == 'bar' else 0,
                    'tension': 0.4 if chart_type == 'line' else 0
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {
                        'display': viz_analysis.get('show_legend', True),
                        'position': 'top',
                        'labels': {
                            'usePointStyle': True,
                            'padding': 20,
                            'font': {
                                'size': 14
                            }
                        }
                    },
                    'tooltip': {
                        'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                        'titleColor': 'white',
                        'bodyColor': 'white',
                        'borderColor': colors[0],
                        'borderWidth': 1,
                        'cornerRadius': 8,
                        'displayColors': True
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'grid': {
                            'color': 'rgba(0, 0, 0, 0.1)'
                        },
                        'title': {
                            'display': True,
                            'text': chart_data['y_axis'],
                            'font': {
                                'size': 14,
                                'weight': 'bold'
                            }
                        }
                    },
                    'x': {
                        'grid': {
                            'color': 'rgba(0, 0, 0, 0.1)'
                        },
                        'title': {
                            'display': True,
                            'text': chart_data['x_axis'],
                            'font': {
                                'size': 14,
                                'weight': 'bold'
                            }
                        }
                    }
                } if chart_type not in ['pie', 'doughnut'] else {}
            }
        }

        # Special configurations for different chart types
        if chart_type == 'pie':
            config['data']['datasets'][0]['backgroundColor'] = colors[:len(chart_data['labels'])]
        elif chart_type == 'doughnut':
            config['data']['datasets'][0]['backgroundColor'] = colors[:len(chart_data['labels'])]
            config['options']['cutout'] = '60%'

        return json.dumps(config, indent=2)

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

    def cleanup_old_files(self, max_files: int = 20) -> Dict[str, Any]:
        """Clean up old visualization files."""
        try:
            files = []
            for filename in os.listdir(self.export_dir):
                if filename.endswith('.html'):
                    file_path = os.path.join(self.export_dir, filename)
                    stats = self._get_file_stats(file_path)
                    files.append({
                        'filename': filename,
                        'path': file_path,
                        **stats
                    })

            if len(files) <= max_files:
                return {
                    'success': True,
                    'message': f"No cleanup needed. {len(files)} files present.",
                    'deleted_count': 0
                }

            # Sort by creation time and delete oldest
            files.sort(key=lambda x: x.get('created', ''), reverse=False)
            files_to_delete = files[:-max_files]
            deleted_count = 0

            for file_info in files_to_delete:
                try:
                    os.remove(file_info['path'])
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {file_info['filename']}: {e}")

            return {
                'success': True,
                'message': f"Cleanup completed. Deleted {deleted_count} old files.",
                'deleted_count': deleted_count,
                'remaining_files': len(files) - deleted_count
            }

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Cleanup failed: {str(e)}"
            }