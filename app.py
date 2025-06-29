"""
Telmi - Modern ClickHouse Analytics Chat Interface
Final Production Version with Full Backend Integration - FIXED VERSION
"""

import streamlit as st
import uuid
import time
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import integration bridge
try:
    from integration.agent_bridge import telmi_bridge
    INTEGRATION_AVAILABLE = True
except ImportError:
    # Fallback: try direct import
    try:
        from core.agent import ClickHouseGraphAgent
        from database.connection import clickhouse_connection
        INTEGRATION_AVAILABLE = "direct"
        print("⚠️  Using direct import fallback")
    except ImportError:
        INTEGRATION_AVAILABLE = False
        print("❌ Neither integration nor direct import available")

# Import core components
from components.auth import AuthManager
from components.chat import ChatInterface
from components.sidebar import SidebarManager
from components.styling import apply_custom_styling

# Configure Streamlit page
st.set_page_config(
    page_title="Telmi - Telecom Analytics Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TelmiApp:
    """Main Telmi application class with full backend integration."""

    def __init__(self):
        self.auth_manager = AuthManager()
        self.chat_interface = ChatInterface()
        self.sidebar_manager = SidebarManager()

        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        default_states = {
            'authenticated': False,
            'user_info': None,
            'chat_sessions': {},
            'current_session_id': None,
            'current_messages': [],
            'agent_thinking': False,
            'typing_response': "",
            'show_account_settings': False,
            'agent_status_checked': False,
            'sessions_loaded': False,  # Add this flag
            'agent_status': {
                'agent_initialized': False,
                'database_connected': False,
                'ready': False,
                'message': 'System not tested yet'
            }
        }

        for key, default_value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def run(self):
        """Main application entry point."""
        # Apply custom styling
        apply_custom_styling()

        # Check if integration is available
        if not INTEGRATION_AVAILABLE:
            self._show_integration_error()
            return

        # Check authentication
        if not st.session_state.authenticated:
            self._show_login_screen()
        else:
            self._show_main_interface()


    def _save_sessions_to_file(self):
        """Save current chat sessions to file - IMPROVED ERROR HANDLING."""
        if not st.session_state.user_info:
            return

        sessions_file = "data/chat_sessions.json"

        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)

            # Load existing sessions from file
            all_sessions = {}
            if os.path.exists(sessions_file):
                try:
                    with open(sessions_file, 'r') as f:
                        content = f.read().strip()
                        if content:  # Only parse if file has content
                            all_sessions = json.loads(content)
                        else:
                            logger.info("📄 Sessions file was empty, starting fresh")
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Corrupted sessions file, creating new one: {e}")
                    all_sessions = {}

            # Update with current user's sessions
            username = st.session_state.user_info['username']
            for session_id, session_data in st.session_state.chat_sessions.items():
                session_data['user'] = username
                all_sessions[session_id] = session_data

            # Save back to file with proper formatting
            with open(sessions_file, 'w') as f:
                json.dump(all_sessions, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Saved {len(st.session_state.chat_sessions)} sessions to file")

        except Exception as e:
            logger.error(f"❌ Error saving sessions to file: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _load_sessions_from_file(self):
        """Load chat sessions from file for the current user - IMPROVED ERROR HANDLING."""
        if not st.session_state.user_info:
            return

        username = st.session_state.user_info['username']
        sessions_file = "data/chat_sessions.json"

        try:
            if os.path.exists(sessions_file):
                with open(sessions_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        logger.info("📄 Sessions file is empty")
                        st.session_state.chat_sessions = {}
                        return

                    all_sessions = json.loads(content)

                # Filter sessions for current user
                user_sessions = {
                    session_id: session_data
                    for session_id, session_data in all_sessions.items()
                    if session_data.get('user') == username
                }

                st.session_state.chat_sessions = user_sessions
                logger.info(f"📂 Loaded {len(user_sessions)} sessions for user {username}")
            else:
                st.session_state.chat_sessions = {}
                logger.info("📄 No sessions file found, starting fresh")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing sessions file: {e}")
            # Create a backup of the corrupted file
            backup_file = f"{sessions_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.rename(sessions_file, backup_file)
                logger.info(f"📄 Corrupted file backed up as: {backup_file}")
            except:
                pass
            st.session_state.chat_sessions = {}
        except Exception as e:
            logger.error(f"❌ Error loading sessions: {e}")
            st.session_state.chat_sessions = {}


    def _show_integration_error(self):
        """Show integration error screen."""
        st.error("🔧 **Setup Required**")
        st.markdown("""
        The Telmi backend integration is not properly configured.

        **Please check the following:**
        1. Make sure you're running from the project root directory
        2. Verify all modules exist:
           - `core/agent.py`
           - `database/connection.py`
           - `tools/` directory
        3. Check if the CLI agent works: `python3 main.py`
        4. Restart the Streamlit application

        **Current Status:**
        - Database server appears to be down (172.20.157.162:8123)
        - Try demo mode when available
        """)

    def _show_login_screen(self):
        """Display the login screen."""
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("""
                <div class="login-container">
                    <div class="login-header">
                        <h1>🔮 Telmi</h1>
                        <p>Your Intelligent Telecom Analytics Assistant</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Login form
            with st.form("login_form", clear_on_submit=False):
                st.markdown("### Sign In")

                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")

                col_login, col_register = st.columns(2)

                with col_login:
                    login_submitted = st.form_submit_button("Sign In", use_container_width=True)

                with col_register:
                    register_submitted = st.form_submit_button("Create Account", use_container_width=True)

                if login_submitted:
                    if self.auth_manager.authenticate_user(username, password):
                        st.session_state.authenticated = True
                        st.session_state.user_info = self.auth_manager.get_user_info(username)
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

                if register_submitted:
                    if username and password:
                        if self.auth_manager.create_user(username, password):
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error("Username already exists")
                    else:
                        st.error("Please fill in all fields")

    def _show_main_interface(self):
        """Display the main chat interface."""
        # Load chat sessions from file on first access
        if not st.session_state.sessions_loaded:
            self._load_sessions_from_file()
            st.session_state.sessions_loaded = True

        # Test agent status on first load
        if not st.session_state.agent_status_checked:
            with st.spinner("🔧 Initializing Telmi agent..."):
                try:
                    status = telmi_bridge.get_agent_status()
                    st.session_state.agent_status = status
                    st.session_state.agent_status_checked = True

                    if not status['ready']:
                        st.warning("⚠️ Agent initialization issue. Check the status panel in the sidebar.")
                except Exception as e:
                    st.session_state.agent_status = {
                        'agent_initialized': False,
                        'database_connected': False,
                        'ready': False,
                        'message': f'Initialization error: {str(e)}'
                    }
                    st.session_state.agent_status_checked = True
                    st.error(f"❌ Agent initialization failed: {e}")

        # Sidebar
        self.sidebar_manager.render_sidebar()

        # Main chat interface
        self._render_main_chat()

    def _render_main_chat(self):
        """Render the main chat interface."""
        # Header
        st.markdown("""
            <div class="chat-header">
                <h1>🔮 Telmi</h1>
                <p>Ask me anything about your telecom data</p>
            </div>
        """, unsafe_allow_html=True)

        # Chat container
        chat_container = st.container()

        with chat_container:
            # Display chat messages
            self._display_chat_messages()

            # Typing indicator
            if st.session_state.agent_thinking:
                st.markdown("""
                    <div class="typing-indicator">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <span class="typing-text">Telmi is analyzing your question...</span>
                    </div>
                """, unsafe_allow_html=True)

        # Input area at bottom
        self._render_input_area()

    def _display_chat_messages(self):
        """Display all chat messages."""
        if not st.session_state.current_messages:
            # Welcome message with system status
            system_ready = st.session_state.agent_status.get('ready', False)

            if system_ready:
                status_message = "🟢 **System Ready** - I'm connected to your ClickHouse database and ready to help!"
            else:
                status_message = "🟡 **System Checking** - Connecting to backend systems..."

            st.markdown(f"""
                <div class="welcome-message">
                    <h3>👋 Welcome to Telmi!</h3>
                    <p>{status_message}</p>
                    <p>I'm your intelligent telecom analytics assistant. Ask me questions about:</p>
                    <ul>
                        <li>📊 Data usage and traffic analysis</li>
                        <li>👥 Customer analytics and rankings</li>
                        <li>🌍 Geographic distribution and roaming</li>
                        <li>📱 Device and technology insights</li>
                        <li>⏰ Time-based analysis and trends</li>
                    </ul>
                    <p><strong>Example:</strong> "Show me the top 10 customers by data usage this month"</p>
                </div>
            """, unsafe_allow_html=True)

        for message in st.session_state.current_messages:
            if message['role'] == 'user':
                self._render_user_message(message['content'])
            else:
                self._render_agent_message(message)

    def _render_user_message(self, content: str):
        """Render a user message."""
        st.markdown(f"""
            <div class="message-container user-message">
                <div class="message-bubble user-bubble">
                    {content}
                </div>
                <div class="message-avatar user-avatar">👤</div>
            </div>
        """, unsafe_allow_html=True)

    def _render_agent_message(self, message: Dict[str, Any]):
        """Render an agent message with attachments and inline charts."""
        content = message['content']
        attachments = message.get('attachments', {})

        # Check if this message contains table data
        has_table_data = '[TABLE_DATA_PLACEHOLDER]' in content

        # Process content for placeholders
        processed_content = self._process_content_placeholders(content, attachments)

        # Agent message bubble
        st.markdown(f"""
            <div class="message-container agent-message">
                <div class="message-avatar agent-avatar">🔮</div>
                <div class="message-bubble agent-bubble">
                    {processed_content}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Display table data if placeholder was found
        if has_table_data and 'table_data' in attachments:
            self._render_data_table(attachments['table_data'])

        # Display inline chart if placeholder was found
        if '[CHART_DISPLAY_PLACEHOLDER]' in content and attachments.get('chart'):
            self._render_inline_chart(attachments['chart'])

        # Display download buttons if placeholder was found
        if '[DOWNLOAD_BUTTONS_PLACEHOLDER]' in content and attachments:
            self._render_download_buttons(attachments)

    def _process_content_placeholders(self, content: str, attachments: Dict[str, Any]) -> str:
        """Process content placeholders for better display."""
        processed_content = content

        # Replace table placeholder
        if '[TABLE_DATA_PLACEHOLDER]' in content:
            processed_content = processed_content.replace('[TABLE_DATA_PLACEHOLDER]', '')

        # Replace chart placeholder
        if '[CHART_DISPLAY_PLACEHOLDER]' in content:
            processed_content = processed_content.replace('[CHART_DISPLAY_PLACEHOLDER]', '')

        # Replace download buttons placeholder
        if '[DOWNLOAD_BUTTONS_PLACEHOLDER]' in content:
            processed_content = processed_content.replace('[DOWNLOAD_BUTTONS_PLACEHOLDER]', '')

        return processed_content

    def _render_data_table(self, table_data: Dict[str, Any]):
        """Render data table using Streamlit's dataframe component."""
        try:
            import pandas as pd

            columns = table_data.get('columns', [])
            data = table_data.get('data', [])

            if not columns or not data:
                return

            # Create DataFrame
            df = pd.DataFrame(data, columns=columns)

            # Display with Streamlit's dataframe
            st.markdown("**📊 Data Results:**")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            # Add summary
            st.caption(f"*{len(data):,} rows total • {len(columns)} columns*")

        except Exception as e:
            st.error(f"Error displaying table: {e}")

    def _render_inline_chart(self, chart_info: Dict[str, str]):
        """Render chart inline in the chat."""
        if os.path.exists(chart_info['path']):
            try:
                with open(chart_info['path'], 'r', encoding='utf-8') as file:
                    html_content = file.read()

                st.markdown("**📈 Chart Generated:**")
                st.components.v1.html(html_content, height=600, scrolling=True)
            except Exception as e:
                st.error(f"Error displaying chart: {e}")

    def _render_download_buttons(self, attachments: Dict[str, Any]):
        """Render modern download buttons that match the interface style."""
        st.markdown("---")  # Add separator

        col1, col2 = st.columns(2)

        with col1:
            if 'csv' in attachments:
                csv_info = attachments['csv']
                if os.path.exists(csv_info['path']):
                    with open(csv_info['path'], 'rb') as file:
                        st.download_button(
                            label="📊 Download CSV Data",
                            data=file.read(),
                            file_name=csv_info['filename'],
                            mime='text/csv',
                            use_container_width=True,
                            type="secondary"
                        )

        with col2:
            if 'chart' in attachments:
                chart_info = attachments['chart']
                if os.path.exists(chart_info['path']):
                    with open(chart_info['path'], 'rb') as file:
                        st.download_button(
                            label="📈 Download Chart",
                            data=file.read(),
                            file_name=chart_info['filename'],
                            mime='text/html',
                            use_container_width=True,
                            type="secondary"
                        )

    def _render_input_area(self):
        """Render the input area at the bottom."""
        # Input form
        with st.form("chat_input_form", clear_on_submit=True):
            col1, col2 = st.columns([6, 1])

            with col1:
                user_input = st.text_input(
                    "message",
                    placeholder="Ask me anything about your telecom data...",
                    label_visibility="collapsed"
                )

            with col2:
                submit_button = st.form_submit_button("Send", use_container_width=True)

            if submit_button and user_input.strip():
                self._process_user_message(user_input.strip())

    def _process_user_message(self, user_input: str):
        """Process user input and get agent response - SIMPLE FIX."""

        # Add user message
        self._add_message('user', user_input)

        # Set thinking state (but don't rerun immediately)
        st.session_state.agent_thinking = True

        # Show a temporary thinking message while processing
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
            <div class="typing-indicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="typing-text">Telmi is analyzing your question...</span>
            </div>
        """, unsafe_allow_html=True)

        try:
            logger.info(f"🔄 Sending question to agent: {user_input[:50]}...")

            # Call the bridge directly
            result = telmi_bridge.process_question(user_input)

            logger.info(f"🔄 Agent response received: success={result.get('success')}")

            if result['success']:
                response = result['response']
                processing_time = result.get('processing_time', 0)

                # Add processing time info for debugging
                if processing_time > 0:
                    response += f"\n\n*⏱️ Processed in {processing_time:.2f} seconds*"

                # Parse response for attachments
                attachments = self._extract_attachments(response)

                # Add agent response
                self._add_message('agent', response, attachments)

                logger.info("✅ Agent response processed successfully")
            else:
                # Add error response
                error_response = result.get('response', 'Unknown error occurred')
                self._add_message('agent', error_response)

                logger.error(f"❌ Agent processing failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            # Add detailed error response
            error_response = f"""❌ **Unexpected Error**

    **Issue:** {str(e)}

    **Type:** {type(e).__name__}

    **Possible Solutions:**
    • Check the terminal console for detailed errors
    • Restart the Streamlit application  
    • Verify the backend agent is working: `python3 debug_telmi.py`
    • Try a simpler question: "List available tables"

    **Debug Info:** {str(e)}"""

            self._add_message('agent', error_response)
            logger.error(f"❌ Unexpected error in message processing: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

        finally:
            # Clear thinking state and placeholder
            st.session_state.agent_thinking = False
            thinking_placeholder.empty()  # Remove the thinking indicator
            logger.info("🔄 Question processing completed")

            # Now rerun to show the complete conversation
            st.rerun()


    def _add_message(self, role: str, content: str, attachments: Dict[str, Any] = None):
        """Add a message to the current session - FIXED to ensure saving."""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'attachments': attachments or {}
        }

        st.session_state.current_messages.append(message)

        # ALWAYS save to session history after adding a message
        self._ensure_session_exists()
        self._save_session_to_history()


    def _ensure_session_exists(self):
        """Ensure we have a session ID for saving."""
        if not st.session_state.current_session_id:
            st.session_state.current_session_id = str(uuid.uuid4())
            logger.info(f"📝 Created new session ID: {st.session_state.current_session_id}")

    def _extract_attachments(self, response: str) -> Dict[str, Any]:
        """Extract file attachments and data from agent response."""
        attachments = {}

        # Look for CSV and chart file patterns
        import re

        csv_pattern = r'\[Download CSV file\]\(([^)]+)\)'
        chart_pattern = r'\[Download Chart\]\(([^)]+)\)'

        csv_match = re.search(csv_pattern, response)
        chart_match = re.search(chart_pattern, response)

        if csv_match:
            csv_filename = csv_match.group(1)
            csv_path = os.path.join('exports', csv_filename)
            if os.path.exists(csv_path):
                stat = os.stat(csv_path)
                attachments['csv'] = {
                    'filename': csv_filename,
                    'path': csv_path,
                    'size': f"{stat.st_size/1024:.1f} KB"
                }

        if chart_match:
            chart_filename = chart_match.group(1)
            chart_path = os.path.join('visualizations', chart_filename)
            if os.path.exists(chart_path):
                stat = os.stat(chart_path)
                attachments['chart'] = {
                    'filename': chart_filename,
                    'path': chart_path,
                    'size': f"{stat.st_size/1024:.1f} KB"
                }

        # Extract table data from the last query execution for display
        if hasattr(st.session_state, 'last_query_result') and st.session_state.last_query_result:
            result = st.session_state.last_query_result
            if result.get('success') and result.get('result', {}).get('data'):
                query_result = result['result']
                attachments['table_data'] = {
                    'columns': query_result.get('columns', []),
                    'data': query_result.get('data', [])
                }

        return attachments

    def _save_session_to_history(self):
        """Save current session to chat history - FIXED VERSION."""
        if not st.session_state.user_info:
            logger.warning("⚠️ No user info - cannot save session")
            return

        if not st.session_state.current_messages:
            logger.warning("⚠️ No messages to save")
            return

        try:
            # Ensure we have a session ID
            self._ensure_session_exists()

            # Create session data
            session_data = {
                'title': self._generate_session_title(),
                'messages': st.session_state.current_messages.copy(),
                'timestamp': datetime.now().isoformat(),
                'user': st.session_state.user_info['username']
            }

            # Update in-memory sessions
            st.session_state.chat_sessions[st.session_state.current_session_id] = session_data

            # Save to file immediately
            self._save_sessions_to_file()

            logger.info(f"💾 Session saved: {st.session_state.current_session_id} with {len(st.session_state.current_messages)} messages")

        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")

    def _generate_session_title(self) -> str:
        """Generate a title for the chat session."""
        if st.session_state.current_messages:
            first_user_message = next(
                (msg['content'] for msg in st.session_state.current_messages if msg['role'] == 'user'),
                "New Chat"
            )
            return first_user_message[:50] + "..." if len(first_user_message) > 50 else first_user_message
        return "New Chat"

    def _parse_query_result_from_response(self, response: str) -> Dict[str, Any]:
        """Try to extract query result data from the agent response."""
        # This is a temporary solution - ideally we'd modify the bridge to return structured data
        try:
            # Look for CSV files that were generated
            import re
            csv_pattern = r'\[Download CSV file\]\(([^)]+)\)'
            csv_match = re.search(csv_pattern, response)

            if csv_match:
                csv_filename = csv_match.group(1)
                csv_path = os.path.join('exports', csv_filename)

                if os.path.exists(csv_path):
                    import pandas as pd
                    df = pd.read_csv(csv_path)

                    return {
                        'success': True,
                        'result': {
                            'columns': df.columns.tolist(),
                            'data': df.values.tolist()
                        }
                    }

            return None

        except Exception as e:
            logger.error(f"Error parsing query result: {e}")
            return None


def main():
    """Main entry point."""
    app = TelmiApp()
    app.run()


if __name__ == "__main__":
    main()