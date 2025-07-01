"""
FIXED Sidebar Manager for Telmi - Permanent Delete & Optimized Performance
- Fixed caching issues causing deleted conversations to reappear
- Permanent deletion with proper file sync
- Fast performance with smart caching
- No UI blocking or success messages
"""

import streamlit as st
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List
from components.auth import AuthManager

class SidebarManager:
    """Manages the sidebar interface with permanent deletion and optimized performance."""

    def __init__(self):
        self.auth_manager = AuthManager()
        self.sessions_file = "data/chat_sessions.json"
        self._ensure_data_directory()
        # FIXED: Cache conversations to avoid repeated file reads
        self._conversations_cache = None
        self._cache_timestamp = None

    def _ensure_data_directory(self):
        """Ensure the data directory exists."""
        os.makedirs("data", exist_ok=True)

    def render_sidebar(self):
        """Render the complete sidebar interface with optimized performance."""
        with st.sidebar:
            # Header
            self._render_sidebar_header()

            # Section headers styling
            self._add_section_header_styling()

            # Section 1: Chat History (FIXED VERSION)
            self._render_fast_chat_history_section()

            # Section 2: System Status
            self._render_system_status_section()

            # Section 3: Account Settings
            self._render_account_settings_section()

            # Footer with stats
            self._render_sidebar_footer()

    def _add_section_header_styling(self):
        """Add CSS for better section header styling."""
        st.markdown("""
            <style>
            /* FIXED: Make section headers more prominent */
            .streamlit-expanderHeader {
                font-weight: 600 !important;
                font-size: 16px !important;
                color: #2d3748 !important;
                background: #f8fafc !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 8px !important;
                margin: 8px 0 !important;
            }
            
            .streamlit-expanderHeader:hover {
                background: #edf2f7 !important;
                border-color: #cbd5e0 !important;
            }
            
            .streamlit-expanderContent {
                border: 1px solid #e2e8f0 !important;
                border-top: none !important;
                border-radius: 0 0 8px 8px !important;
                background: #ffffff !important;
                margin-bottom: 8px !important;
            }
            
            /* FIXED: Stats container - left aligned */
            .sidebar-stats-improved {
                background: #f8fafc !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 8px !important;
                padding: 12px !important;
                margin: 8px 0 !important;
                text-align: left !important;
            }
            
            .stats-text-improved {
                font-size: 13px !important;
                color: #4a5568 !important;
                line-height: 1.4 !important;
                margin: 0 !important;
            }
            </style>
        """, unsafe_allow_html=True)

    def _render_sidebar_header(self):
        """Render the sidebar header."""
        st.markdown("""
            <div class="sidebar-header">
                <h2>Telmi</h2>
                <p>Analytics Assistant</p>
            </div>
        """, unsafe_allow_html=True)

    def _render_fast_chat_history_section(self):
        """FIXED: Render chat history with fast loading and permanent deletion."""
        with st.expander("💬 Chat History", expanded=False):
            # New chat button at the top
            if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
                self._start_new_chat()

            st.markdown("---")

            # FIXED: Load conversations with proper caching
            conversations = self._load_conversations_cached()

            if not conversations:
                st.markdown("*No chat history yet*")
                st.caption("Start a conversation to see your chat history here!")
            else:
                # Sort conversations by timestamp (newest first)
                sorted_conversations = sorted(
                    conversations.items(),
                    key=lambda x: x[1].get('timestamp', ''),
                    reverse=True
                )

                for conversation_id, conversation_data in sorted_conversations:
                    self._render_fast_conversation_item(conversation_id, conversation_data)

    def _render_fast_conversation_item(self, conversation_id: str, conversation_data: Dict[str, Any]):
        """FIXED: Render conversation item with instant delete."""

        # Get conversation metadata
        title = conversation_data.get('title', 'Untitled Chat')
        timestamp = conversation_data.get('timestamp', '')
        message_count = len(conversation_data.get('messages', []))

        # Simple timestamp formatting
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime("%m/%d %H:%M")
        except:
            time_str = "Unknown"

        # Check if this is the current conversation
        is_current = conversation_id == st.session_state.current_session_id

        # Layout
        col1, col2 = st.columns([4, 1])

        with col1:
            # Simple title truncation
            display_title = self._truncate_title(title, 30)
            button_text = f"{display_title}"

            if st.button(
                button_text,
                key=f"load_conv_{conversation_id}",
                help=f"{message_count} messages • {time_str}",
                use_container_width=True,
                disabled=is_current
            ):
                self._load_conversation_fast(conversation_id)

        with col2:
            # FIXED: Instant permanent delete
            if st.button("🗑️", key=f"delete_conv_{conversation_id}", help="Delete"):
                self._instant_delete_conversation(conversation_id)

        # Show metadata
        st.caption(f"💬 {message_count} • ⏰ {time_str}")

    def _truncate_title(self, title: str, max_length: int) -> str:
        """Truncate title with ellipsis if too long."""
        if len(title) <= max_length:
            return title
        return title[:max_length-3] + "..."

    def _load_conversations_cached(self) -> Dict[str, Any]:
        """FIXED: Load conversations with proper cache invalidation and permanent deletion support."""
        if not st.session_state.user_info:
            return {}

        username = st.session_state.user_info['username']

        try:
            # FIXED: Always check file existence and read fresh data after deletions
            if not os.path.exists(self.sessions_file):
                # File doesn't exist, clear cache and return empty
                self._conversations_cache = None
                self._cache_timestamp = None
                return {}

            file_mtime = os.path.getmtime(self.sessions_file)

            # FIXED: Force reload if cache is None or file is newer
            if (self._conversations_cache is None or
                self._cache_timestamp is None or
                file_mtime > self._cache_timestamp):

                # Read fresh data from file
                with open(self.sessions_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        # Empty file, clear cache
                        self._conversations_cache = {username: {}}
                        self._cache_timestamp = file_mtime
                        return {}

                    all_sessions = json.loads(content)

                # Filter sessions for current user only
                user_conversations = {
                    session_id: session_data
                    for session_id, session_data in all_sessions.items()
                    if session_data.get('user') == username
                }

                # Update cache with fresh data
                self._conversations_cache = {username: user_conversations}
                self._cache_timestamp = file_mtime

                return user_conversations

            # Return cached data if it's still valid
            return self._conversations_cache.get(username, {})

        except (json.JSONDecodeError, FileNotFoundError, OSError):
            # On any error, clear cache and return empty
            self._conversations_cache = None
            self._cache_timestamp = None
            return {}

    def _start_new_chat(self):
        """FIXED: Start new chat with cache refresh."""
        # Save current session first if it has messages
        if st.session_state.current_messages:
            if not st.session_state.current_session_id:
                st.session_state.current_session_id = str(uuid.uuid4())
            self._save_current_session_fast()

        # Reset for new chat
        st.session_state.current_session_id = None
        st.session_state.current_messages = []

        # FIXED: Force cache refresh when starting new chat
        self._conversations_cache = None
        self._cache_timestamp = None

        st.rerun()

    def _load_conversation_fast(self, conversation_id: str):
        """FIXED: Load a conversation quickly."""
        # Save current session first if it has messages
        if st.session_state.current_messages and st.session_state.current_session_id:
            self._save_current_session_fast()

        # Load the conversation data
        conversations = self._load_conversations_cached()
        if conversation_id in conversations:
            conversation_data = conversations[conversation_id]
            st.session_state.current_session_id = conversation_id
            st.session_state.current_messages = conversation_data.get('messages', [])
            st.rerun()

    def _instant_delete_conversation(self, conversation_id: str):
        """FIXED: Permanent delete with proper cache and file handling."""
        try:
            # STEP 1: Immediately clear cache to force fresh read
            self._conversations_cache = None
            self._cache_timestamp = None

            # STEP 2: Update session state if deleting current conversation
            if conversation_id == st.session_state.current_session_id:
                st.session_state.current_session_id = None
                st.session_state.current_messages = []

            # STEP 3: Permanent file deletion
            if os.path.exists(self.sessions_file):
                # Read current file
                with open(self.sessions_file, 'r') as f:
                    content = f.read().strip()

                if content:
                    all_sessions = json.loads(content)

                    # Remove the conversation permanently
                    if conversation_id in all_sessions:
                        del all_sessions[conversation_id]

                        # Write back to file immediately
                        with open(self.sessions_file, 'w') as f:
                            json.dump(all_sessions, f, indent=2)
                            f.flush()
                            # FIXED: Force file system sync
                            if hasattr(os, 'fsync'):
                                os.fsync(f.fileno())

            # STEP 4: Clear any potential session state caches
            if hasattr(st.session_state, 'chat_sessions'):
                if conversation_id in st.session_state.chat_sessions:
                    del st.session_state.chat_sessions[conversation_id]

            # STEP 5: Immediate rerun to refresh UI
            st.rerun()

        except Exception as e:
            # FIXED: Clear cache even on error and rerun
            self._conversations_cache = None
            self._cache_timestamp = None
            st.rerun()

    def _save_current_session_fast(self):
        """FIXED: Save current session with proper cache invalidation."""
        if not st.session_state.current_messages or not st.session_state.user_info:
            return

        if not st.session_state.current_session_id:
            st.session_state.current_session_id = str(uuid.uuid4())

        # Generate simple title
        first_user_message = next(
            (msg['content'] for msg in st.session_state.current_messages if msg['role'] == 'user'),
            'New Chat'
        )

        simple_title = self._create_simple_title(first_user_message)

        session_data = {
            'title': simple_title,
            'messages': st.session_state.current_messages,
            'timestamp': datetime.now().isoformat(),
            'user': st.session_state.user_info['username']
        }

        try:
            # FIXED: Clear cache before file operations
            self._conversations_cache = None
            self._cache_timestamp = None

            # Load existing sessions
            all_sessions = {}
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        all_sessions = json.loads(content)

            # Add/update this session
            all_sessions[st.session_state.current_session_id] = session_data

            # Save to file with forced sync
            with open(self.sessions_file, 'w') as f:
                json.dump(all_sessions, f, indent=2)
                f.flush()
                if hasattr(os, 'fsync'):
                    os.fsync(f.fileno())

            # FIXED: Update app.py session state as well (if it exists)
            if hasattr(st.session_state, 'chat_sessions'):
                st.session_state.chat_sessions[st.session_state.current_session_id] = session_data

        except Exception:
            # On error, ensure cache is cleared
            self._conversations_cache = None
            self._cache_timestamp = None

    def _create_simple_title(self, first_question: str) -> str:
        """FIXED: Create simple title without LLM calls."""
        question_lower = first_question.lower()

        # Fast pattern matching
        if any(word in question_lower for word in ['top', 'ranking', 'best']):
            if 'client' in question_lower or 'customer' in question_lower:
                return "🏆 Top Clients Analysis"
            return "🥇 Ranking Analysis"

        elif any(word in question_lower for word in ['evolution', 'trend', 'daily']):
            return "📈 Trend Analysis"

        elif 'ticket' in question_lower:
            return "🎫 Ticket Analysis"

        elif any(word in question_lower for word in ['country', 'pays', 'geographic']):
            return "🌍 Geographic Analysis"

        elif any(word in question_lower for word in ['distribution', 'répartition']):
            return "📊 Distribution Analysis"

        elif any(word in question_lower for word in ['table', 'schema']):
            return "🗂️ Schema Query"

        else:
            # Simple word extraction
            words = first_question.split()[:4]
            meaningful_words = [w for w in words if len(w) > 2]
            if meaningful_words:
                title = ' '.join(meaningful_words[:3])
                return title.title()
            else:
                return "💬 Chat Session"

    def _render_system_status_section(self):
        """Render the system status section."""
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
                    st.error("❌ Integration module not found.")
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

                if st.button("🗑️ Delete Account", key="delete_account_sidebar", use_container_width=True, type="secondary"):
                    st.session_state.show_delete_confirmation = True
                    st.rerun()

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
            with st.expander("👤 Account Settings", expanded=False):
                st.info("⚠️ Please log in to access account settings")

    def _delete_user_account(self, username: str):
        """Delete user account and all associated data."""
        try:
            if self.auth_manager.delete_user(username):
                self._delete_all_user_sessions(username)

                # Clear session state
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.session_state.current_messages = []
                st.session_state.current_session_id = None
                st.session_state.show_delete_confirmation = False

                # Clear cache
                self._conversations_cache = None
                self._cache_timestamp = None

                st.success("✅ Account deleted successfully.")
                st.rerun()
            else:
                st.error("❌ Failed to delete account")

        except Exception as e:
            st.error(f"❌ Error deleting account: {e}")

    def _delete_all_user_sessions(self, username: str):
        """Delete all chat sessions for a specific user."""
        try:
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

            with open(self.sessions_file, 'w') as f:
                json.dump(remaining_sessions, f, indent=2)
                f.flush()
                if hasattr(os, 'fsync'):
                    os.fsync(f.fileno())

        except Exception:
            pass

    def _logout(self):
        """Logout the current user."""
        # Save current session before logout
        if st.session_state.current_messages and st.session_state.current_session_id:
            self._save_current_session_fast()

        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.current_messages = []
        st.session_state.current_session_id = None
        st.session_state.show_account_settings = False

        # Clear cache
        self._conversations_cache = None
        self._cache_timestamp = None

        st.rerun()

    def _render_sidebar_footer(self):
        """Render the sidebar footer with stats."""
        st.markdown("---")

        # Simple stats without complex calculations
        if st.session_state.user_info:
            conversations = self._load_conversations_cached()
            total_conversations = len(conversations)

            # Simple message count
            total_messages = 0
            for conv in conversations.values():
                total_messages += len(conv.get('messages', []))

            st.markdown(f"""
                <div class="sidebar-stats-improved">
                    <div class="stats-text-improved">
                        💭 {total_conversations} conversations<br>
                        💬 {total_messages} messages
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            <div class="sidebar-footer">
                <small>Powered by Castor</small>
            </div>
        """, unsafe_allow_html=True)