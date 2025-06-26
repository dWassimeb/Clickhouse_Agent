"""
File handling utilities for Telmi Streamlit interface
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib
from datetime import datetime
import mimetypes

def ensure_directory_exists(directory_path: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False

def save_uploaded_file(uploaded_file, upload_dir: str = "uploads") -> Optional[str]:
    """Save uploaded file and return file path"""

    if not uploaded_file:
        return None

    try:
        # Ensure upload directory exists
        ensure_directory_exists(upload_dir)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(uploaded_file.name).suffix
        file_hash = hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8]

        filename = f"{timestamp}_{file_hash}{file_extension}"
        file_path = os.path.join(upload_dir, filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        return file_path

    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        return None

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get file information"""

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    try:
        stat = os.stat(file_path)
        file_size = stat.st_size

        return {
            "filename": os.path.basename(file_path),
            "size_bytes": file_size,
            "size_human": format_file_size(file_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "mime_type": mimetypes.guess_type(file_path)[0],
            "extension": Path(file_path).suffix.lower()
        }

    except Exception as e:
        return {"error": f"Error getting file info: {e}"}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""

    if size_bytes == 0:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"

def cleanup_old_files(directory: str, max_age_days: int = 7) -> int:
    """Clean up files older than specified days"""

    if not os.path.exists(directory):
        return 0

    try:
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)

                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1

        return deleted_count

    except Exception as e:
        print(f"Error cleaning up files: {e}")
        return 0

def get_directory_size(directory: str) -> int:
    """Get total size of directory in bytes"""

    total_size = 0

    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except Exception as e:
        print(f"Error calculating directory size: {e}")

    return total_size

def list_files_in_directory(directory: str, extension_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """List files in directory with optional extension filter"""

    if not os.path.exists(directory):
        return []

    files = []

    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            if os.path.isfile(file_path):
                file_ext = Path(filename).suffix.lower()

                # Apply extension filter if provided
                if extension_filter and file_ext not in extension_filter:
                    continue

                file_info = get_file_info(file_path)
                if "error" not in file_info:
                    file_info["path"] = file_path
                    files.append(file_info)

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)

    except Exception as e:
        print(f"Error listing files: {e}")

    return files

def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe for use"""

    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']

    for char in dangerous_chars:
        if char in filename:
            return False

    # Check filename length
    if len(filename) > 255:
        return False

    # Check for reserved names (Windows)
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]

    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in reserved_names:
        return False

    return True

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe use"""

    # Replace dangerous characters
    safe_filename = filename
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']

    for char in dangerous_chars:
        safe_filename = safe_filename.replace(char, '_')

    # Remove multiple dots except for extension
    parts = safe_filename.split('.')
    if len(parts) > 2:
        safe_filename = '.'.join([parts[0]] + ['_'.join(parts[1:-1])] + [parts[-1]])

    # Limit length
    if len(safe_filename) > 255:
        name, ext = os.path.splitext(safe_filename)
        max_name_length = 255 - len(ext)
        safe_filename = name[:max_name_length] + ext

    return safe_filename

def create_backup(file_path: str, backup_dir: str = "backups") -> Optional[str]:
    """Create backup of file"""

    if not os.path.exists(file_path):
        return None

    try:
        ensure_directory_exists(backup_dir)

        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)

        backup_filename = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)

        shutil.copy2(file_path, backup_path)
        return backup_path

    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def get_disk_usage(path: str = ".") -> Dict[str, Any]:
    """Get disk usage statistics"""

    try:
        if os.name == 'nt':  # Windows
            import psutil
            usage = psutil.disk_usage(path)
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": (usage.used / usage.total) * 100,
                "total_human": format_file_size(usage.total),
                "used_human": format_file_size(usage.used),
                "free_human": format_file_size(usage.free)
            }
        else:  # Unix-like
            statvfs = os.statvfs(path)
            total = statvfs.f_frsize * statvfs.f_blocks
            free = statvfs.f_frsize * statvfs.f_available
            used = total - free

            return {
                "total": total,
                "used": used,
                "free": free,
                "percent": (used / total) * 100 if total > 0 else 0,
                "total_human": format_file_size(total),
                "used_human": format_file_size(used),
                "free_human": format_file_size(free)
            }

    except Exception as e:
        return {"error": f"Error getting disk usage: {e}"}