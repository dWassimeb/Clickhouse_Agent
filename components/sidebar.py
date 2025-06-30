"""
Fixed Sidebar Manager for Telmi - Complete Implementation
- Fixed missing methods error
- Updated for new blue theme
"""

import streamlit as st
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
from components.auth import AuthManager

class SidebarManager:
    """Manages the sidebar interface with clean, structured sections."""

    def __init__(self):
        self.auth_manager = AuthManager()
        self.sessions_file = "data/chat_sessions.json"
        self._ensure_data_directory()

    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs("data", exist_ok=True)

    def render_sidebar(self):
        """Render the complete sidebar interface with clean structure."""
        with st.sidebar:
            # Header with clean text only
            self._render_sidebar_header()

            # Section 1: Chat History
            self._render_chat_history_section()

            # Section 2: System Status
            self._render_system_status_section()

            # Section 3: Account Settings
            self._render_account_settings_section()

            # Footer
            self._render_sidebar_footer()

    def _render_sidebar_header(self):
        """Render the sidebar header with clean text only."""
        st.markdown("""
            <div class="sidebar-header">
                <h2>Telmi</h2>
                <p>Analytics Assistant</p>
            </div>
        """, unsafe_allow_html=True)

    def _render_chat_history_section(self):
        """Render the chat history section with dropdown."""
        with st.expander("💬 Chat History", expanded=True):
            # New chat button at the top
            if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
                self._start_new_chat()

            st.markdown("---")

            # Load and display sessions
            sessions = self._load_user_sessions()

            if not sessions:
                st.markdown("*No chat history yet*")
                st.caption("Start a conversation to see your chat history here!")
            else:
                # Sort sessions by timestamp (newest first)
                sorted_sessions = sorted(
                    sessions.items(),
                    key=lambda x: x[1].get('timestamp', ''),
                    reverse=True
                )

                for session_id, session_data in sorted_sessions:
                    self._render_session_item(session_id, session_data)

    def _render_system_status_section(self):
        """Render the system status section with dropdown."""
        with st.expander("🔧 System Status", expanded=False):
            # Get agent status
            if 'agent_status' in st.session_state:
                status = st.session_state.agent_status

                if status.get('ready', False):
                    st.success("🟢 **System Ready**")
                    st.markdown("✅ Agent initialized  \n✅ Database connected")
                else:
                    st.warning("🟡 **System Issues**")

                    if not status.get('agent_initialized', False):
                        st.markdown("❌ Agent not initialized")
                    else:
                        st.markdown("✅ Agent initialized")

                    if not status.get('database_connected', False):
                        st.markdown("❌ Database disconnected")
                        if 'database_message' in status:
                            st.caption(f"Details: {status['database_message']}")
                    else:
                        st.markdown("✅ Database connected")
            else:
                st.info("⏳ **Checking system status...**")

            # Refresh status button
            if st.button("🔄 Refresh Status", key="refresh_status", use_container_width=True):
                try:
                    from integration.agent_bridge import telmi_bridge
                    with st.spinner("Checking system status..."):
                        status = telmi_bridge.get_agent_status()
                        st.session_state.agent_status = status
                        st.rerun()
                except ImportError:
                    st.error("❌ Integration module not found. Please ensure integration/agent_bridge.py exists.")
                except Exception as e:
                    st.error(f"❌ Status check failed: {e}")

    def _render_account_settings_section(self):
        """Render the account settings section."""
        if st.session_state.user_info:
            username = st.session_state.user_info['username']
            email = st.session_state.user_info.get('email', 'No email set')

            with st.expander("👤 Account Settings", expanded=False):
                # Display current user info
                st.markdown("**Current User:**")
                st.markdown(f"👤 **Username:** {username}")
                st.markdown(f"📧 **Email:** {email}")

                st.markdown("---")

                # Change Password Section
                st.markdown("**🔒 Change Password:**")

                col1, col2 = st.columns(2)
                with col1:
                    old_password = st.text_input(
                        "Current Password",
                        type="password",
                        key="sidebar_old_password"
                    )
                with col2:
                    new_password = st.text_input(
                        "New Password",
                        type="password",
                        key="sidebar_new_password"
                    )

                if st.button("🔒 Change Password", key="change_password_sidebar", use_container_width=True):
                    if old_password and new_password:
                        if self.auth_manager.change_password(username, old_password, new_password):
                            st.success("✅ Password changed successfully!")
                            # Clear password fields
                            st.session_state.sidebar_old_password = ""
                            st.session_state.sidebar_new_password = ""
                            st.rerun()
                        else:
                            st.error("❌ Current password is incorrect")
                    else:
                        st.error("⚠️ Please fill in both password fields")

                st.markdown("---")

                # Account Actions Section
                st.markdown("**⚙️ Account Actions:**")

                # Delete Account button FIRST
                if st.button("🗑️ Delete Account", key="delete_account_sidebar", use_container_width=True, type="secondary"):
                    st.session_state.show_delete_confirmation = True
                    st.rerun()

                # Logout button SECOND
                if st.button("🚪 Logout", key="logout_sidebar", use_container_width=True):
                    self._logout()

                # Delete Account Confirmation Dialog
                if getattr(st.session_state, 'show_delete_confirmation', False):
                    st.markdown("---")
                    st.error("⚠️ **DELETE ACCOUNT CONFIRMATION**")
                    st.markdown("""
                    **This action is irreversible!**
                    
                    The following will be **permanently deleted**:
                    • Your user account and profile
                    • All chat history and conversations
                    • All saved preferences and settings
                    • All exported files and data
                    
                    Are you sure you want to proceed?
                    """)

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("❌ Cancel", key="cancel_delete", use_container_width=True):
                            st.session_state.show_delete_confirmation = False
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Yes, Delete Everything", key="confirm_delete", use_container_width=True, type="primary"):
                            self._delete_user_account(username)

        else:
            # No user logged in
            with st.expander("👤 Account Settings", expanded=False):
                st.info("⚠️ Please log in to access account settings")

    def _render_session_item(self, session_id: str, session_data: Dict[str, Any]):
        """Render a single chat session item."""
        title = session_data.get('title', 'Untitled Chat')
        timestamp = session_data.get('timestamp', '')
        message_count = len(session_data.get('messages', []))

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%m/%d %H:%M")
        except:
            time_str = "Unknown"

        # Session container
        is_current = session_id == st.session_state.current_session_id

        col1, col2 = st.columns([4, 1])

        with col1:
            if st.button(
                    f"📝 {title[:25]}{'...' if len(title) > 25 else ''}",
                    key=f"session_{session_id}",
                    help=f"{message_count} messages • {time_str}",
                    use_container_width=True,
                    disabled=is_current
            ):
                self._load_chat_session(session_id)

        with col2:
            if st.button("🗑️", key=f"delete_{session_id}", help="Delete chat"):
                self._delete_chat_session(session_id)

    def _start_new_chat(self):
        """Start a new chat session properly."""
        # Save current session first if it has messages
        if st.session_state.current_messages:
            # Make sure we have a session ID
            if not st.session_state.current_session_id:
                st.session_state.current_session_id = str(uuid.uuid4())

            # Save current session
            self._save_current_session()

        # Reset for new chat
        st.session_state.current_session_id = None
        st.session_state.current_messages = []
        st.rerun()

    def _load_chat_session(self, session_id: str):
        """Load a specific chat session."""
        # Save current session first if it has messages
        if st.session_state.current_messages and st.session_state.current_session_id:
            self._save_current_session()

        # Load the selected session
        sessions = self._load_user_sessions()
        if session_id in sessions:
            session_data = sessions[session_id]
            st.session_state.current_session_id = session_id
            st.session_state.current_messages = session_data.get('messages', [])
            st.rerun()

    def _delete_chat_session(self, session_id: str):
        """Delete a chat session."""
        try:
            # Load all sessions from file
            all_sessions = {}
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        all_sessions = json.loads(content)

            # Remove the specific session
            if session_id in all_sessions:
                del all_sessions[session_id]

                # Save back to file
                with open(self.sessions_file, 'w') as f:
                    json.dump(all_sessions, f, indent=2)

                # Update in-memory sessions for current user
                user_sessions = self._load_user_sessions()
                if session_id in user_sessions:
                    del user_sessions[session_id]

                # If deleting current session, start new chat
                if session_id == st.session_state.current_session_id:
                    st.session_state.current_session_id = None
                    st.session_state.current_messages = []

                st.success(f"✅ Chat deleted successfully!")
                st.rerun()
            else:
                st.error("❌ Session not found")

        except Exception as e:
            st.error(f"❌ Failed to delete session: {e}")

    def _delete_user_account(self, username: str):
        """Delete user account and all associated data."""
        try:
            # 1. Delete user from users.json
            if self.auth_manager.delete_user(username):

                # 2. Delete all user's chat sessions
                self._delete_all_user_sessions(username)

                # 3. Clear session state
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.session_state.current_messages = []
                st.session_state.current_session_id = None
                st.session_state.show_delete_confirmation = False

                # 4. Show success message and redirect
                st.success("✅ Account deleted successfully. You have been logged out.")
                st.rerun()
            else:
                st.error("❌ Failed to delete account")

        except Exception as e:
            st.error(f"❌ Error deleting account: {e}")

    def _delete_all_user_sessions(self, username: str):
        """Delete all chat sessions for a specific user."""
        try:
            # Load all sessions
            all_sessions = {}
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        all_sessions = json.loads(content)

            # Filter out sessions for this user
            remaining_sessions = {
                session_id: session_data
                for session_id, session_data in all_sessions.items()
                if session_data.get('user') != username
            }

            # Save filtered sessions back to file
            with open(self.sessions_file, 'w') as f:
                json.dump(remaining_sessions, f, indent=2)

        except Exception as e:
            print(f"Error deleting user sessions: {e}")

    def _load_user_sessions(self) -> Dict[str, Any]:
        """Load chat sessions for the current user."""
        if not st.session_state.user_info:
            return {}

        username = st.session_state.user_info['username']

        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    all_sessions = json.loads(content)

                    # Return only sessions for current user
                    return {
                        session_id: session_data
                        for session_id, session_data in all_sessions.items()
                        if session_data.get('user') == username
                    }
        except (json.JSONDecodeError, FileNotFoundError):
            pass

        return {}

    def _save_current_session(self):
        """Save the current chat session."""
        if not st.session_state.current_messages or not st.session_state.user_info:
            return

        if not st.session_state.current_session_id:
            st.session_state.current_session_id = str(uuid.uuid4())

        session_data = {
            'title': self._generate_session_title(),
            'messages': st.session_state.current_messages,
            'timestamp': datetime.now().isoformat(),
            'user': st.session_state.user_info['username']
        }

        try:
            # Load all existing sessions
            all_sessions = {}
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        all_sessions = json.loads(content)

            # Add/update this session
            all_sessions[st.session_state.current_session_id] = session_data

            # Save back to file
            with open(self.sessions_file, 'w') as f:
                json.dump(all_sessions, f, indent=2)

        except Exception as e:
            print(f"Error saving session: {e}")

    def _generate_session_title(self) -> str:
        """Generate a title for the chat session."""
        if st.session_state.current_messages:
            first_user_message = next(
                (msg['content'] for msg in st.session_state.current_messages if msg['role'] == 'user'),
                "New Chat"
            )
            return first_user_message[:50] + "..." if len(first_user_message) > 50 else first_user_message
        return "New Chat"

    def _logout(self):
        """Logout the current user."""
        # Save current session before logout
        if st.session_state.current_messages and st.session_state.current_session_id:
            self._save_current_session()

        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.current_messages = []
        st.session_state.current_session_id = None
        st.session_state.show_account_settings = False
        st.rerun()

    def _render_sidebar_footer(self):
        """Render the sidebar footer."""
        st.markdown("---")

        # Statistics
        if st.session_state.user_info:
            sessions = self._load_user_sessions()
            total_sessions = len(sessions)
            total_messages = sum(len(session.get('messages', [])) for session in sessions.values())

            st.markdown(f"""
                <div class="sidebar-stats">
                    <small>
                        📊 {total_sessions} conversations<br>
                        💬 {total_messages} messages
                    </small>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div class="sidebar-footer">
                <small>Powered by Telmi AI</small>
            </div>
        """, unsafe_allow_html=True)