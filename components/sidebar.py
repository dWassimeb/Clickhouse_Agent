"""
Sidebar Manager for Telmi
Handles chat history, session management, and account settings
"""

import streamlit as st
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
from components.auth import AuthManager

class SidebarManager:
    """Manages the sidebar interface with chat history and account settings."""

    def __init__(self):
        self.auth_manager = AuthManager()
        self.sessions_file = "data/chat_sessions.json"
        self._ensure_data_directory()

    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs("data", exist_ok=True)

    def render_sidebar(self):
        """Render the complete sidebar interface."""
        with st.sidebar:
            # Header
            self._render_sidebar_header()

            # System Status
            self._render_system_status()

            # Account section
            self._render_account_section()

            # Chat sessions
            self._render_chat_sessions()

            # Footer
            self._render_sidebar_footer()

    def _render_sidebar_header(self):
        """Render the sidebar header."""
        st.markdown("""
            <div class="sidebar-header">
                <h2>🔮 Telmi</h2>
                <p>Analytics Assistant</p>
            </div>
        """, unsafe_allow_html=True)

        # New chat button
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
            self._start_new_chat()

    def _render_account_section(self):
        """Render the account management section."""
        if st.session_state.user_info:
            username = st.session_state.user_info['username']

            # Account header
            st.markdown(f"""
                <div class="account-section">
                    <div class="user-info">
                        <span class="user-avatar">👤</span>
                        <span class="username">{username}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Account settings toggle
            col1, col2 = st.columns([3, 1])

            with col1:
                if st.button("⚙️ Account Settings", use_container_width=True):
                    st.session_state.show_account_settings = not st.session_state.show_account_settings

            with col2:
                if st.button("🚪", help="Logout"):
                    self._logout()

            # Account settings panel
            if st.session_state.show_account_settings:
                with st.expander("Account Settings", expanded=True):
                    self.auth_manager.render_account_settings()

        st.markdown("---")

    def _render_system_status(self):
        """Render system status information."""
        st.markdown("### 🔧 System Status")

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
        if st.button("🔄 Refresh Status", key="refresh_status"):
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

        st.markdown("---")

    def _render_chat_sessions(self):
        """Render the chat sessions history."""
        st.markdown("### 💬 Chat History")

        # Load and display sessions
        sessions = self._load_user_sessions()

        if not sessions:
            st.markdown("*No chat history yet*")
            st.markdown("Start a conversation to see your chat history here!")
        else:
            # Sort sessions by timestamp (newest first)
            sorted_sessions = sorted(
                sessions.items(),
                key=lambda x: x[1].get('timestamp', ''),
                reverse=True
            )

            for session_id, session_data in sorted_sessions:
                self._render_session_item(session_id, session_data)

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
        container_class = "session-item current" if is_current else "session-item"

        col1, col2 = st.columns([4, 1])

        with col1:
            if st.button(
                    f"📝 {title[:30]}{'...' if len(title) > 30 else ''}",
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
            session_title = st.session_state.current_messages[0]['content'][:50] if st.session_state.current_messages else "New Chat"
            st.session_state.chat_sessions[st.session_state.current_session_id] = {
                'title': session_title + "..." if len(session_title) == 50 else session_title,
                'messages': st.session_state.current_messages.copy(),
                'timestamp': datetime.now().isoformat(),
                'user': st.session_state.user_info['username'] if st.session_state.user_info else 'anonymous'
            }

        # Reset for new chat
        st.session_state.current_session_id = None
        st.session_state.current_messages = []
        st.rerun()

    def _render_chat_sessions(self):
        """Render the chat sessions history."""
        st.markdown("### 💬 Chat History")

        # Load and display sessions
        sessions = st.session_state.chat_sessions

        if not sessions:
            st.markdown("*No chat history yet*")
            st.markdown("Start a conversation to see your chat history here!")
        else:
            # Sort sessions by timestamp (newest first)
            sorted_sessions = sorted(
                sessions.items(),
                key=lambda x: x[1].get('timestamp', ''),
                reverse=True
            )

            for session_id, session_data in sorted_sessions:
                self._render_session_item(session_id, session_data)

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
                    f"📝 {title[:30]}{'...' if len(title) > 30 else ''}",
                    key=f"session_{session_id}",
                    help=f"{message_count} messages • {time_str}",
                    use_container_width=True,
                    disabled=is_current
            ):
                self._load_chat_session(session_id)

        with col2:
            if st.button("🗑️", key=f"delete_{session_id}", help="Delete chat"):
                self._delete_chat_session(session_id)

    def _load_chat_session(self, session_id: str):
        """Load a specific chat session."""
        # Save current session first if it has messages
        if st.session_state.current_messages and st.session_state.current_session_id:
            self._save_current_session()

        # Load the selected session
        if session_id in st.session_state.chat_sessions:
            session_data = st.session_state.chat_sessions[session_id]
            st.session_state.current_session_id = session_id
            st.session_state.current_messages = session_data.get('messages', [])
            st.rerun()

    def _delete_chat_session(self, session_id: str):
        """Delete a chat session."""
        if session_id in st.session_state.chat_sessions:
            del st.session_state.chat_sessions[session_id]

            # If deleting current session, start new chat
            if session_id == st.session_state.current_session_id:
                self._start_new_chat()
            else:
                st.rerun()

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

        st.session_state.chat_sessions[st.session_state.current_session_id] = session_data

    def _generate_session_title(self) -> str:
        """Generate a title for the chat session."""
        if st.session_state.current_messages:
            first_user_message = next(
                (msg['content'] for msg in st.session_state.current_messages if msg['role'] == 'user'),
                "New Chat"
            )
            return first_user_message[:50] + "..." if len(first_user_message) > 50 else first_user_message
        return "New Chat"

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

    def _start_new_chat(self):
        """Start a new chat session."""
        # Save current session if it has messages
        if st.session_state.current_messages and st.session_state.current_session_id:
            self._save_current_session()

        # Reset chat state
        st.session_state.current_session_id = None
        st.session_state.current_messages = []
        st.rerun()

    def _load_chat_session(self, session_id: str):
        """Load a specific chat session."""
        # Save current session first
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
        sessions = self._load_user_sessions()
        if session_id in sessions:
            del sessions[session_id]
            self._save_user_sessions(sessions)

            # If deleting current session, start new chat
            if session_id == st.session_state.current_session_id:
                self._start_new_chat()
            else:
                st.rerun()

    def _load_user_sessions(self) -> Dict[str, Any]:
        """Load chat sessions for the current user."""
        if not st.session_state.user_info:
            return {}

        username = st.session_state.user_info['username']

        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    all_sessions = json.load(f)
                    # Return only sessions for current user
                    return {
                        session_id: session_data
                        for session_id, session_data in all_sessions.items()
                        if session_data.get('user') == username
                    }
        except (json.JSONDecodeError, FileNotFoundError):
            pass

        return {}

    def _save_user_sessions(self, user_sessions: Dict[str, Any]):
        """Save chat sessions for the current user."""
        if not st.session_state.user_info:
            return

        username = st.session_state.user_info['username']

        # Load all sessions
        all_sessions = {}
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    all_sessions = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

        # Update sessions for current user
        for session_id, session_data in user_sessions.items():
            session_data['user'] = username
            all_sessions[session_id] = session_data

        # Save back to file
        with open(self.sessions_file, 'w') as f:
            json.dump(all_sessions, f, indent=2)

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

        # Load current sessions and add/update this one
        sessions = self._load_user_sessions()
        sessions[st.session_state.current_session_id] = session_data
        self._save_user_sessions(sessions)

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