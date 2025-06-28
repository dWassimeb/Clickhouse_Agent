"""
Authentication Manager for Telmi
Handles user registration, login, and account management
"""

import json
import os
import hashlib
import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

class AuthManager:
    """Manages user authentication and account settings."""

    def __init__(self):
        self.users_file = "data/users.json"
        self._ensure_data_directory()
        self._load_users()

    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs("data", exist_ok=True)

    def _load_users(self):
        """Load users from the JSON file."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.users = {}
        else:
            self.users = {}

    def _save_users(self):
        """Save users to the JSON file."""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, password: str, email: str = None) -> bool:
        """Create a new user account."""
        if username in self.users:
            return False

        self.users[username] = {
            'password': self._hash_password(password),
            'email': email or f"{username}@telmi.local",
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'preferences': {
                'theme': 'light',
                'language': 'en',
                'notifications': True
            },
            'database_settings': {
                'host': '172.20.157.162',
                'port': 8123,
                'database': 'default',
                'username': 'default',
                'password': ''
            }
        }

        self._save_users()
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user login."""
        if username not in self.users:
            return False

        stored_password = self.users[username]['password']
        provided_password = self._hash_password(password)

        if stored_password == provided_password:
            # Update last login
            self.users[username]['last_login'] = datetime.now().isoformat()
            self._save_users()
            return True

        return False

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        if username in self.users:
            user_info = self.users[username].copy()
            # Remove password from returned info
            user_info.pop('password', None)
            user_info['username'] = username
            return user_info
        return None

    def update_user_settings(self, username: str, settings: Dict[str, Any]) -> bool:
        """Update user settings."""
        if username not in self.users:
            return False

        # Update preferences
        if 'preferences' in settings:
            self.users[username]['preferences'].update(settings['preferences'])

        # Update database settings
        if 'database_settings' in settings:
            self.users[username]['database_settings'].update(settings['database_settings'])

        # Update email
        if 'email' in settings:
            self.users[username]['email'] = settings['email']

        self._save_users()
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        if not self.authenticate_user(username, old_password):
            return False

        self.users[username]['password'] = self._hash_password(new_password)
        self._save_users()
        return True

    def render_account_settings(self):
        """Render the account settings interface."""
        if not st.session_state.user_info:
            return

        username = st.session_state.user_info['username']
        user_data = self.users[username]

        st.markdown("### 👤 Account Settings")

        # Profile Settings
        with st.expander("Profile Settings", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                new_email = st.text_input(
                    "Email",
                    value=user_data.get('email', ''),
                    key="settings_email"
                )

            with col2:
                theme = st.selectbox(
                    "Theme",
                    options=['light', 'dark'],
                    index=0 if user_data['preferences'].get('theme', 'light') == 'light' else 1,
                    key="settings_theme"
                )

        # Database Settings
        with st.expander("Database Connection", expanded=False):
            db_settings = user_data.get('database_settings', {})

            col1, col2 = st.columns(2)

            with col1:
                db_host = st.text_input(
                    "ClickHouse Host",
                    value=db_settings.get('host', '172.20.157.162'),
                    key="settings_db_host"
                )

                db_database = st.text_input(
                    "Database",
                    value=db_settings.get('database', 'default'),
                    key="settings_db_database"
                )

            with col2:
                db_port = st.number_input(
                    "Port",
                    value=db_settings.get('port', 8123),
                    min_value=1,
                    max_value=65535,
                    key="settings_db_port"
                )

                db_username = st.text_input(
                    "Username",
                    value=db_settings.get('username', 'default'),
                    key="settings_db_username"
                )

            db_password = st.text_input(
                "Password",
                value=db_settings.get('password', ''),
                type="password",
                key="settings_db_password"
            )

        # Password Change
        with st.expander("Change Password", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                old_password = st.text_input(
                    "Current Password",
                    type="password",
                    key="old_password"
                )

            with col2:
                new_password = st.text_input(
                    "New Password",
                    type="password",
                    key="new_password"
                )

            if st.button("Change Password", key="change_password_btn"):
                if old_password and new_password:
                    if self.change_password(username, old_password, new_password):
                        st.success("Password changed successfully!")
                    else:
                        st.error("Current password is incorrect")
                else:
                    st.error("Please fill in both password fields")

        # Save Settings Button
        if st.button("💾 Save Settings", use_container_width=True):
            settings_update = {
                'email': new_email,
                'preferences': {
                    'theme': theme,
                    'language': user_data['preferences'].get('language', 'en'),
                    'notifications': user_data['preferences'].get('notifications', True)
                },
                'database_settings': {
                    'host': db_host,
                    'port': db_port,
                    'database': db_database,
                    'username': db_username,
                    'password': db_password
                }
            }

            if self.update_user_settings(username, settings_update):
                st.success("Settings saved successfully!")
                # Update session state
                st.session_state.user_info = self.get_user_info(username)
                st.rerun()
            else:
                st.error("Failed to save settings")

        # Logout button
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.current_messages = []
            st.session_state.current_session_id = None
            st.rerun()