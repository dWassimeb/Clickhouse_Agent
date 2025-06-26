"""
Application configuration settings for Telmi Streamlit interface
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ClickHouseConfig:
    host: str = "172.20.157.162"
    port: int = 8123
    database: str = "default"  # Fixed: lowercase 'default' instead of 'Default'
    username: str = "default"
    password: str = "default123!"  # Fixed: empty string instead of "default123!"


CLICKHOUSE_CONFIG = ClickHouseConfig()


# Application configuration
APP_CONFIG = {
    "app_name": "Telmi",
    "app_description": "Your AI-powered Telecom Analytics Assistant",
    "app_version": "1.0.0",
    "company": "Telecom Analytics Inc.",
    "support_email": "support@telmi.ai",
    "app_url": "/clickhouseagent/",  # For reverse proxy
}

# Database configuration
USER_DATABASE_CONFIG = {
    "users_db_path": "data/users.db",
}

# Security configuration
SECURITY_CONFIG = {
    "session_timeout_hours": 24,
    "max_login_attempts": 5,
    "password_min_length": 8,
    "require_password_complexity": True,
    "enable_two_factor": False,  # Future feature
}

# UI configuration
UI_CONFIG = {
    "default_theme": "professional_blue",
    "enable_dark_mode": True,
    "default_language": "english",
    "max_chat_history": 100,
    "auto_save_chat": True,
    "enable_animations": True,
}

# Query configuration
QUERY_CONFIG = {
    "default_query_limit": 1000,
    "max_query_limit": 10000,
    "query_timeout_seconds": 300,
    "enable_auto_visualization": True,
    "enable_auto_csv_export": True,
    "max_csv_size_mb": 50,
}

# File upload configuration
UPLOAD_CONFIG = {
    "max_file_size_mb": 5,
    "allowed_image_types": ["png", "jpg", "jpeg", "gif"],
    "upload_directory": "uploads",
    "export_directory": "exports",
    "visualization_directory": "visualizations",
}

# Notification configuration
NOTIFICATION_CONFIG = {
    "enable_email_notifications": False,  # Disabled for now
    "enable_browser_notifications": True,
    "notification_timeout_seconds": 5,
}

# Performance configuration
PERFORMANCE_CONFIG = {
    "enable_caching": True,
    "cache_ttl_seconds": 3600,
    "max_concurrent_queries": 5,
    "enable_query_optimization": True,
}

# Development configuration
DEV_CONFIG = {
    "debug_mode": False,
    "enable_profiler": False,
    "log_level": "INFO",
    "enable_test_data": False,
}

# Environment-specific overrides
def load_environment_config():
    """Load configuration from environment variables"""

    # Override database configuration from environment
    if os.getenv("CLICKHOUSE_HOST"):
        CLICKHOUSE_CONFIG.host = os.getenv("CLICKHOUSE_HOST")

    if os.getenv("CLICKHOUSE_PORT"):
        CLICKHOUSE_CONFIG.port = int(os.getenv("CLICKHOUSE_PORT"))

    if os.getenv("CLICKHOUSE_DATABASE"):
        CLICKHOUSE_CONFIG.database = os.getenv("CLICKHOUSE_DATABASE")

    if os.getenv("CLICKHOUSE_USERNAME"):
        CLICKHOUSE_CONFIG.username = os.getenv("CLICKHOUSE_USERNAME")

    if os.getenv("CLICKHOUSE_PASSWORD"):
        CLICKHOUSE_CONFIG.password = os.getenv("CLICKHOUSE_PASSWORD")

    # Override app configuration
    if os.getenv("APP_URL"):
        APP_CONFIG["app_url"] = os.getenv("APP_URL")

    if os.getenv("DEBUG"):
        DEV_CONFIG["debug_mode"] = os.getenv("DEBUG").lower() == "true"

# Load environment configuration on import
load_environment_config()

# Create directories if they don't exist
def ensure_directories():
    """Ensure required directories exist"""

    directories = [
        "data",
        UPLOAD_CONFIG["upload_directory"],
        UPLOAD_CONFIG["export_directory"],
        UPLOAD_CONFIG["visualization_directory"],
        "static/css",
        "static/js",
        "static/images",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Color schemes for theming
COLOR_SCHEMES = {
    "professional_blue": {
        "primary": "#667eea",
        "secondary": "#764ba2",
        "accent": "#4f46e5",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "text": "#1e293b",
        "text_secondary": "#64748b",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
    },
    "dark_mode": {
        "primary": "#3b82f6",
        "secondary": "#8b5cf6",
        "accent": "#06b6d4",
        "background": "#0f172a",
        "surface": "#1e293b",
        "text": "#f1f5f9",
        "text_secondary": "#94a3b8",
        "success": "#22c55e",
        "warning": "#eab308",
        "error": "#f87171",
    },
    "light_mode": {
        "primary": "#2563eb",
        "secondary": "#7c3aed",
        "accent": "#0891b2",
        "background": "#ffffff",
        "surface": "#f9fafb",
        "text": "#111827",
        "text_secondary": "#6b7280",
        "success": "#059669",
        "warning": "#d97706",
        "error": "#dc2626",
    }
}

# Feature flags
FEATURE_FLAGS = {
    "enable_user_authentication": True,
    "enable_chat_history": True,
    "enable_file_uploads": True,
    "enable_csv_export": True,
    "enable_data_visualization": True,
    "enable_user_profiles": True,
    "enable_admin_panel": False,  # Future feature
    "enable_api_access": False,   # Future feature
    "enable_collaboration": False,  # Future feature
}

# API configuration (for future use)
API_CONFIG = {
    "api_version": "v1",
    "rate_limit_per_minute": 60,
    "enable_api_keys": False,
    "require_authentication": True,
}

# Monitoring configuration
MONITORING_CONFIG = {
    "enable_analytics": True,
    "enable_error_tracking": True,
    "enable_performance_monitoring": True,
    "log_retention_days": 30,
}

def get_config(section: str) -> Dict[str, Any]:
    """Get configuration section"""

    config_sections = {
        "app": APP_CONFIG,
        "database": CLICKHOUSE_CONFIG,
        "security": SECURITY_CONFIG,
        "ui": UI_CONFIG,
        "query": QUERY_CONFIG,
        "upload": UPLOAD_CONFIG,
        "notification": NOTIFICATION_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "dev": DEV_CONFIG,
        "features": FEATURE_FLAGS,
        "api": API_CONFIG,
        "monitoring": MONITORING_CONFIG,
    }

    return config_sections.get(section, {})

def update_config(section: str, key: str, value: Any) -> bool:
    """Update configuration value"""

    config_sections = {
        "app": APP_CONFIG,
        "database": CLICKHOUSE_CONFIG,
        "security": SECURITY_CONFIG,
        "ui": UI_CONFIG,
        "query": QUERY_CONFIG,
        "upload": UPLOAD_CONFIG,
        "notification": NOTIFICATION_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "dev": DEV_CONFIG,
        "features": FEATURE_FLAGS,
        "api": API_CONFIG,
        "monitoring": MONITORING_CONFIG,
    }

    if section in config_sections and key in config_sections[section]:
        config_sections[section][key] = value
        return True

    return False

# Initialize directories on import
ensure_directories()