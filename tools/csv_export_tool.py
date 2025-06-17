"""
CSV export tool for saving query results.
"""

import csv
import os
from typing import Dict, Any, List
from langchain.tools import BaseTool
from pydantic import Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CsvExportTool(BaseTool):
    """Tool for exporting query results to CSV files."""

    name: str = "export_csv"
    description: str = """
    Export query results to CSV files for download.
    Creates CSV files with proper formatting and provides file path.
    """

    # Properly declare the export_dir field for Pydantic v2
    export_dir: str = Field(default="exports")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create exports directory if it doesn't exist
        os.makedirs(self.export_dir, exist_ok=True)

    def _run(self, query_result: Dict[str, Any], user_question: str = "", filename: str = None) -> Dict[str, Any]:
        """Export query results to CSV file."""
        try:
            # Check if we have valid data to export
            if not self._has_exportable_data(query_result):
                return {
                    'success': False,
                    'error': 'No data available for export',
                    'message': 'Query returned no results or data is not exportable'
                }

            # Generate filename if not provided
            if not filename:
                filename = self._generate_filename(user_question)

            # Get data from query result
            export_data = self._extract_export_data(query_result)

            # Create CSV file
            file_path = self._create_csv_file(export_data, filename)

            # Get file stats
            file_stats = self._get_file_stats(file_path)

            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'file_stats': file_stats,
                'message': f"CSV file created successfully: {filename}"
            }

        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to export CSV: {str(e)}"
            }

    def _has_exportable_data(self, query_result: Dict[str, Any]) -> bool:
        """Check if query result has data that can be exported."""
        if not query_result.get('success', True):
            return False

        result_data = query_result.get('result', {})
        data = result_data.get('data', [])
        columns = result_data.get('columns', [])

        return len(data) > 0 and len(columns) > 0

    def _generate_filename(self, user_question: str = "") -> str:
        """Generate a filename based on timestamp and question."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if user_question:
            # Clean question for filename
            clean_question = self._clean_filename(user_question)
            if len(clean_question) > 30:
                clean_question = clean_question[:30]
            filename = f"query_{clean_question}_{timestamp}.csv"
        else:
            filename = f"query_results_{timestamp}.csv"

        return filename

    def _clean_filename(self, text: str) -> str:
        """Clean text to be safe for filename."""
        # Keep only alphanumeric, spaces, hyphens, underscores
        import re
        clean_text = re.sub(r'[^\w\s\-_]', '', text)
        # Replace spaces with underscores
        clean_text = re.sub(r'\s+', '_', clean_text)
        # Remove multiple underscores
        clean_text = re.sub(r'_+', '_', clean_text)
        return clean_text.lower()

    def _extract_export_data(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for CSV export."""
        result_data = query_result.get('result', {})

        return {
            'columns': result_data.get('columns', []),
            'data': result_data.get('data', []),
            'row_count': result_data.get('row_count', 0),
            'query': query_result.get('executed_query', ''),
            'timestamp': datetime.now().isoformat()
        }

    def _create_csv_file(self, export_data: Dict[str, Any], filename: str) -> str:
        """Create the actual CSV file."""
        file_path = os.path.join(self.export_dir, filename)

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write headers
            columns = export_data['columns']
            writer.writerow(columns)

            # Write data rows
            for row in export_data['data']:
                # Convert each value to string and handle None values
                csv_row = [self._format_csv_value(value) for value in row]
                writer.writerow(csv_row)

            # Write metadata as comments (optional)
            if export_data.get('query'):
                csvfile.write(f"\n# Query: {export_data['query']}")
            if export_data.get('timestamp'):
                csvfile.write(f"\n# Generated: {export_data['timestamp']}")
            csvfile.write(f"\n# Total rows: {export_data['row_count']}")

        logger.info(f"CSV file created: {file_path}")
        return file_path

    def _format_csv_value(self, value: Any) -> str:
        """Format a value for CSV output."""
        if value is None:
            return ""
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(value)

    def _get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics."""
        try:
            stat = os.stat(file_path)
            return {
                'size_bytes': stat.st_size,
                'size_human': self._format_file_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'absolute_path': os.path.abspath(file_path)
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

    def list_exported_files(self) -> List[Dict[str, Any]]:
        """List all exported CSV files."""
        try:
            files = []
            for filename in os.listdir(self.export_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(self.export_dir, filename)
                    stats = self._get_file_stats(file_path)
                    files.append({
                        'filename': filename,
                        'path': file_path,
                        **stats
                    })

            # Sort by creation time (newest first)
            files.sort(key=lambda x: x.get('created', ''), reverse=True)
            return files

        except Exception as e:
            logger.error(f"Failed to list exported files: {e}")
            return []

    def cleanup_old_files(self, max_files: int = 50) -> Dict[str, Any]:
        """Clean up old CSV files, keeping only the most recent ones."""
        try:
            files = self.list_exported_files()

            if len(files) <= max_files:
                return {
                    'success': True,
                    'message': f"No cleanup needed. {len(files)} files present.",
                    'deleted_count': 0
                }

            # Delete oldest files
            files_to_delete = files[max_files:]
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