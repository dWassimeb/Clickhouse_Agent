"""
Telmi - Modern ClickHouse Analytics Chat Interface
FIXED VERSION - Unified agent response box for all elements
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
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TelmiApp:
    """Main Telmi application class with unified response rendering."""

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
            'sessions_loaded': False,
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
                        <h1>Telmi</h1>
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
                <h1>Telmi</h1>
                <p>Ask me anything about your telecom data</p>
            </div>
        """, unsafe_allow_html=True)

        # Chat container
        chat_container = st.container()

        with chat_container:
            # Display chat messages
            self._display_chat_messages()

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
                        <li>📉 Data usage and traffic analysis</li>
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
                self._render_agent_message_unified(message)

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

    def _render_agent_message_unified(self, message: Dict[str, Any]):
        """SIMPLIFIED: Clean rendering without bubbles - just parse everything in order."""
        content = message['content']
        attachments = message.get('attachments', {})

        # Simple container with avatar and clean content
        col1, col2 = st.columns([0.08, 0.92])

        with col1:
            st.markdown("""
                <div style="
                    width: 2.5rem; 
                    height: 2.5rem; 
                    border-radius: 50%; 
                    background: #f1f5f9; 
                    border: 1px solid #e2e8f0; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    font-size: 1.2rem;
                    flex-shrink: 0;
                ">🔮</div>
            """, unsafe_allow_html=True)

        with col2:
            # Just render everything cleanly in order
            self._render_content_cleanly(content, attachments)

    def _render_content_cleanly(self, content: str, attachments: Dict[str, Any]):
        """Render content cleanly with proper viewers for each element type."""

        # Split content by lines and process each section
        lines = content.split('\n\n')  # Split by double newlines to preserve sections

        for section in lines:
            section = section.strip()
            if not section:
                continue

            # Handle each type of placeholder with appropriate rendering
            if '[TABLE_DATA_PLACEHOLDER]' in section:
                # Render section title
                section_title = section.replace('[TABLE_DATA_PLACEHOLDER]', '').strip()
                if section_title:
                    st.markdown(section_title)

                # Render table with clean viewer
                if 'table_data' in attachments:
                    self._render_table_clean(attachments['table_data'])

            elif '[CHART_DISPLAY_PLACEHOLDER]' in section:
                # Render section title
                section_title = section.replace('[CHART_DISPLAY_PLACEHOLDER]', '').strip()
                if section_title:
                    st.markdown(section_title)

                # Render chart with clean viewer
                if 'chart' in attachments:
                    self._render_chart_clean(attachments['chart'])

            elif '[DOWNLOAD_BUTTONS_PLACEHOLDER]' in section:
                # Render section title
                section_title = section.replace('[DOWNLOAD_BUTTONS_PLACEHOLDER]', '').strip()
                if section_title:
                    st.markdown(section_title)

                # Render downloads with clean viewer
                if attachments:
                    self._render_downloads_clean(attachments)

            elif '```sql' in section or (section.startswith('```') and 'sql' in section.lower()):
                # Handle SQL code block
                self._render_sql_block_from_section(section)

            else:
                # Regular content section
                self._render_regular_section(section)

        # IMPORTANT: Always render chart and downloads if they exist, even if placeholders are missing
        if 'chart' in attachments and '[CHART_DISPLAY_PLACEHOLDER]' not in content:
            st.markdown("### **📈 Chart Generated:**")
            self._render_chart_clean(attachments['chart'])

        if ('csv' in attachments or 'chart' in attachments) and '[DOWNLOAD_BUTTONS_PLACEHOLDER]' not in content:
            st.markdown("### **📁 Downloads:**")
            self._render_downloads_clean(attachments)

    def _render_sql_block_from_section(self, section: str):
        """Render SQL code block from a section."""
        lines = section.split('\n')
        sql_lines = []
        in_sql = False

        for line in lines:
            if line.strip().startswith('```') and ('sql' in line.lower() or in_sql):
                if in_sql:
                    break  # End of SQL block
                else:
                    in_sql = True  # Start of SQL block
                    continue
            elif in_sql:
                sql_lines.append(line)

        if sql_lines:
            sql_content = '\n'.join(sql_lines)
            st.code(sql_content, language='sql')

    def _render_regular_section(self, section: str):
        """Render regular content section."""
        lines = section.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('**') and line.endswith(':**'):
                # Section headers - make them bigger and more prominent
                # Replace 📊 with 📉 for data results
                if '📊' in line:
                    line = line.replace('📊', '📉')
                st.markdown(f"### {line}")
            elif line.startswith('•'):
                # Bullet points
                st.markdown(line)
            elif line.startswith('*⏱️'):
                # Processing time - render as styled caption like other info messages
                time_text = line.replace('*', '').replace('⏱️', '⏱️').strip()
                st.markdown(f"*{time_text}*")
            else:
                # Regular markdown
                st.markdown(line)


    def _render_table_clean(self, table_data: Dict[str, Any]):
        """Render data table with clean styling."""
        try:
            import pandas as pd

            columns = table_data.get('columns', [])
            data = table_data.get('data', [])

            if not columns or not data:
                st.warning("No data to display")
                return

            # Create DataFrame
            df = pd.DataFrame(data, columns=columns)

            # Render with clean styling
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            # Add summary info with consistent styling (no asterisks)
            st.markdown(f"<small style='color: #666; font-style: italic;'>📉 {len(data):,} rows × {len(columns)} columns</small>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error displaying table: {e}")

    def _render_chart_clean(self, chart_info: Dict[str, str]):
        """Render chart with clean styling."""
        if os.path.exists(chart_info['path']):
            try:
                with open(chart_info['path'], 'r', encoding='utf-8') as file:
                    html_content = file.read()

                # Render chart with clean container
                st.components.v1.html(html_content, height=500, scrolling=True)

                # Add chart info with consistent styling (no asterisks)
                st.markdown(f"<small style='color: #666; font-style: italic;'>📈 Interactive chart • {chart_info.get('size', 'Unknown size')}</small>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error displaying chart: {e}")
        else:
            st.warning("Chart file not found")

    def _render_downloads_clean(self, attachments: Dict[str, Any]):
        """Render download buttons with clean styling and attractive green colors."""
        # Create columns for downloads
        download_items = []

        if 'csv' in attachments:
            download_items.append(('csv', attachments['csv']))
        if 'chart' in attachments:
            download_items.append(('chart', attachments['chart']))

        if not download_items:
            st.warning("No downloads available")
            return

        # Create columns based on number of items
        cols = st.columns(len(download_items))

        # Add custom CSS for green download buttons
        st.markdown("""
            <style>
            .stDownloadButton > button {
                background-color: #22c55e !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                transition: all 0.2s ease !important;
            }
            .stDownloadButton > button:hover {
                background-color: #16a34a !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 8px rgba(34, 197, 94, 0.3) !important;
            }
            .stDownloadButton > button:active {
                transform: translateY(0px) !important;
            }
            </style>
        """, unsafe_allow_html=True)

        for i, (item_type, item_info) in enumerate(download_items):
            with cols[i]:
                if item_type == 'csv' and os.path.exists(item_info['path']):
                    with open(item_info['path'], 'rb') as file:
                        st.download_button(
                            label=f"📉 CSV Data ({item_info.get('size', 'Unknown')})",
                            data=file.read(),
                            file_name=item_info['filename'],
                            mime='text/csv',
                            use_container_width=True,
                            help="Download the complete dataset as CSV file"
                        )
                elif item_type == 'chart' and os.path.exists(item_info['path']):
                    with open(item_info['path'], 'rb') as file:
                        st.download_button(
                            label=f"📈 Chart ({item_info.get('size', 'Unknown')})",
                            data=file.read(),
                            file_name=item_info['filename'],
                            mime='text/html',
                            use_container_width=True,
                            help="Download the interactive chart as HTML file"
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
        """Process user input and get agent response."""

        # Add user message
        self._add_message('user', user_input)

        # Show a thinking indicator
        thinking_container = st.container()
        with thinking_container:
            st.markdown("""
                <div class="message-container agent-message">
                    <div class="message-avatar agent-avatar">🔮</div>
                    <div class="message-bubble agent-bubble">
                        <div class="typing-indicator">
                            <div class="typing-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                            <span class="typing-text">Telmi is analyzing your question...</span>
                        </div>
                    </div>
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
• Verify the backend agent is working: `python3 debug.py`
• Try a simpler question: "List available tables"

**Debug Info:** {str(e)}"""

            self._add_message('agent', error_response)
            logger.error(f"❌ Unexpected error in message processing: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

        finally:
            logger.info("🔄 Question processing completed")
            # Now rerun to show the complete conversation
            st.rerun()

    def _add_message(self, role: str, content: str, attachments: Dict[str, Any] = None):
        """Add a message to the current session."""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'attachments': attachments or {}
        }

        st.session_state.current_messages.append(message)

        # Save to session history
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

        try:
            # Find the most recent CSV and chart files
            csv_dir = "exports"
            if os.path.exists(csv_dir):
                csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
                if csv_files:
                    csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(csv_dir, x)), reverse=True)
                    latest_csv = csv_files[0]
                    csv_path = os.path.join(csv_dir, latest_csv)

                    stat = os.stat(csv_path)
                    attachments['csv'] = {
                        'filename': latest_csv,
                        'path': csv_path,
                        'size': f"{stat.st_size/1024:.1f} KB"
                    }

                    logger.info(f"📊 Found CSV file: {latest_csv}")

            # Find the most recent chart file
            chart_dir = "visualizations"
            if os.path.exists(chart_dir):
                chart_files = [f for f in os.listdir(chart_dir) if f.endswith('.html')]
                if chart_files:
                    chart_files.sort(key=lambda x: os.path.getmtime(os.path.join(chart_dir, x)), reverse=True)
                    latest_chart = chart_files[0]
                    chart_path = os.path.join(chart_dir, latest_chart)

                    stat = os.stat(chart_path)
                    attachments['chart'] = {
                        'filename': latest_chart,
                        'path': chart_path,
                        'size': f"{stat.st_size/1024:.1f} KB"
                    }

                    logger.info(f"📈 Found chart file: {latest_chart}")

            # Extract table data from CSV for display
            if 'csv' in attachments:
                try:
                    import pandas as pd
                    df = pd.read_csv(attachments['csv']['path'])
                    attachments['table_data'] = {
                        'columns': df.columns.tolist(),
                        'data': df.values.tolist()
                    }
                    logger.info(f"📋 Extracted table data: {len(df)} rows, {len(df.columns)} columns")
                except Exception as e:
                    logger.error(f"❌ Could not extract table data from CSV: {e}")

            logger.info(f"🔗 Total attachments found: CSV={('csv' in attachments)}, Chart={('chart' in attachments)}, Table={('table_data' in attachments)}")

        except Exception as e:
            logger.error(f"❌ Error extracting attachments: {e}")

        return attachments

    def _save_session_to_history(self):
        """Save current session to chat history."""
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


def main():
    """Main entry point."""
    app = TelmiApp()
    app.run()


if __name__ == "__main__":
    main()