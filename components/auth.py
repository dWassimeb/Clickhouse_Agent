"""
Updated Authentication Manager with Separate Username and Email Fields
Clean, professional design with proper distinction between username and email
"""

import json
import os
import hashlib
import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

class AuthManager:
    """Manages user authentication and account settings with separate username and email."""

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
                    content = f.read().strip()
                    if content:
                        self.users = json.loads(content)
                    else:
                        self.users = {}
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

    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        Create a new user account with separate username and email.

        Returns:
            Dict with 'success' boolean and 'message' string
        """
        # Validate inputs
        if not username or not email or not password:
            return {
                'success': False,
                'message': 'All fields are required'
            }

        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            return {
                'success': False,
                'message': 'Please enter a valid email address'
            }

        # Check if username already exists
        if username in self.users:
            return {
                'success': False,
                'message': 'Username already exists'
            }

        # Check if email already exists
        for existing_user, user_data in self.users.items():
            if user_data.get('email') == email:
                return {
                    'success': False,
                    'message': 'Email address already registered'
                }

        # Create new user
        self.users[username] = {
            'password': self._hash_password(password),
            'email': email,  # Store actual email, not generated one
            'username': username,  # Store username separately for clarity
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
        return {
            'success': True,
            'message': 'Account created successfully!'
        }

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

        # Update email (with validation)
        if 'email' in settings:
            new_email = settings['email']
            # Check if email is already used by another user
            for existing_user, user_data in self.users.items():
                if existing_user != username and user_data.get('email') == new_email:
                    return False  # Email already in use
            self.users[username]['email'] = new_email

        self._save_users()
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        if not self.authenticate_user(username, old_password):
            return False

        self.users[username]['password'] = self._hash_password(new_password)
        self._save_users()
        return True

    def delete_user(self, username: str) -> bool:
        """Delete a user account completely."""
        if username not in self.users:
            return False

        try:
            # Remove user from users dictionary
            del self.users[username]

            # Save updated users file
            self._save_users()

            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def render_account_settings(self):
        """Render account settings interface with improved email handling."""
        if not st.session_state.user_info:
            st.warning("⚠️ Please log in to access account settings")
            return

        username = st.session_state.user_info['username']
        user_data = self.users[username]

        st.markdown("### 👤 Account Settings")

        # Profile Settings
        st.markdown("#### Profile Information")
        st.markdown(f"**Username:** {username}")
        st.markdown(f"**Email:** {user_data.get('email', 'No email set')}")
        st.markdown(f"**Account Created:** {user_data.get('created_at', 'Unknown')[:10]}")

        # Email Update Section
        st.markdown("#### Update Email")
        new_email = st.text_input(
            "New Email Address",
            value=user_data.get('email', ''),
            key="main_settings_email",
            help="Enter your new email address"
        )

        # Theme Settings
        theme = st.selectbox(
            "Theme",
            options=['light', 'dark'],
            index=0 if user_data['preferences'].get('theme', 'light') == 'light' else 1,
            key="main_settings_theme"
        )

        # Database Settings
        st.markdown("#### Database Connection")
        db_settings = user_data.get('database_settings', {})

        col1, col2 = st.columns(2)

        with col1:
            db_host = st.text_input(
                "ClickHouse Host",
                value=db_settings.get('host', '172.20.157.162'),
                key="main_settings_db_host"
            )

            db_database = st.text_input(
                "Database",
                value=db_settings.get('database', 'default'),
                key="main_settings_db_database"
            )

        with col2:
            db_port = st.number_input(
                "Port",
                value=db_settings.get('port', 8123),
                min_value=1,
                max_value=65535,
                key="main_settings_db_port"
            )

            db_username = st.text_input(
                "Username",
                value=db_settings.get('username', 'default'),
                key="main_settings_db_username"
            )

        db_password = st.text_input(
            "Password",
            value=db_settings.get('password', ''),
            type="password",
            key="main_settings_db_password"
        )

        # Password Change
        st.markdown("#### Change Password")
        col1, col2 = st.columns(2)

        with col1:
            old_password = st.text_input(
                "Current Password",
                type="password",
                key="main_old_password"
            )

        with col2:
            new_password = st.text_input(
                "New Password",
                type="password",
                key="main_new_password"
            )

        if st.button("🔒 Change Password", key="main_change_password_btn"):
            if old_password and new_password:
                if self.change_password(username, old_password, new_password):
                    st.success("✅ Password changed successfully!")
                    # Clear password fields
                    st.session_state.main_old_password = ""
                    st.session_state.main_new_password = ""
                    st.rerun()
                else:
                    st.error("❌ Current password is incorrect")
            else:
                st.error("⚠️ Please fill in both password fields")

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
                st.success("✅ Settings saved successfully!")
                # Update session state
                st.session_state.user_info = self.get_user_info(username)
                st.rerun()
            else:
                st.error("❌ Failed to save settings (email might already be in use)")

        # Account Actions
        st.markdown("---")
        st.markdown("#### Account Actions")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.session_state.current_messages = []
                st.session_state.current_session_id = None
                st.rerun()

        with col2:
            if st.button("🗑️ Delete Account", use_container_width=True, type="secondary"):
                st.session_state.show_main_delete_confirmation = True
                st.rerun()

        # Delete confirmation
        if getattr(st.session_state, 'show_main_delete_confirmation', False):
            st.markdown("---")
            st.error("⚠️ **DELETE ACCOUNT CONFIRMATION**")
            st.markdown("""
            **This action is irreversible!**
            
            All your data will be permanently deleted including:
            • Your user account and profile
            • All chat history and conversations  
            • All saved preferences and settings
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Cancel", key="main_cancel_delete", use_container_width=True):
                    st.session_state.show_main_delete_confirmation = False
                    st.rerun()

            with col2:
                if st.button("🗑️ Confirm Delete", key="main_confirm_delete", use_container_width=True, type="primary"):
                    if self.delete_user(username):
                        st.session_state.authenticated = False
                        st.session_state.user_info = None
                        st.session_state.current_messages = []
                        st.session_state.current_session_id = None
                        st.session_state.show_main_delete_confirmation = False
                        st.success("✅ Account deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete account")