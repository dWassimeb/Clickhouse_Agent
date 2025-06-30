"""
Telmi - Modern ClickHouse Analytics Chat Interface
FIXED VERSION - Proper thinking indicator + improved chat history + better sidebar
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
    """Main Telmi application class with FIXED thinking indicator and improved chat history."""

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
            'processing_message': False,  # FIXED: Single processing flag
            'show_thinking': False,       # FIXED: Separate flag for thinking indicator
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

        # FIXED: Add thinking indicator CSS
        self._add_thinking_indicator_css()

        # Check if integration is available
        if not INTEGRATION_AVAILABLE:
            self._show_integration_error()
            return

        # Check authentication
        if not st.session_state.authenticated:
            self._show_login_screen()
        else:
            self._show_main_interface()

    def _add_thinking_indicator_css(self):
        """FIXED: Add CSS for thinking indicator without causing layout issues."""
        st.markdown("""
        <style>
        .thinking-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(5px);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease-in;
        }
        
        .thinking-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px 32px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 16px;
            min-width: 280px;
        }
        
        .thinking-icon {
            font-size: 24px;
            animation: pulse 2s infinite;
        }
        
        .thinking-content h3 {
            margin: 0 0 8px 0;
            font-size: 18px;
            font-weight: 600;
            color: #1a202c;
        }
        
        .thinking-content p {
            margin: 0;
            font-size: 14px;
            color: #718096;
        }
        
        .thinking-dots {
            display: flex;
            gap: 4px;
            margin-top: 8px;
        }
        
        .thinking-dots span {
            width: 8px;
            height: 8px;
            background: #4299e1;
            border-radius: 50%;
            animation: bounce 1.4s infinite;
        }
        
        .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        </style>
        """, unsafe_allow_html=True)

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
        """Display the improved login screen with separate username and email fields."""
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

            # Login/Register tabs using streamlit's native tabs
            login_tab, register_tab = st.tabs(["🔑 Sign In", "📝 Create Account"])

            # LOGIN TAB
            with login_tab:
                with st.form("login_form", clear_on_submit=False):
                    st.markdown("### Welcome Back")
                    st.markdown("Please sign in to your account")

                    # Add some spacing
                    st.markdown("<br>", unsafe_allow_html=True)

                    username = st.text_input(
                        "Username",
                        placeholder="Enter your username",
                        key="login_username"
                    )

                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
                        key="login_password"
                    )

                    # Add some spacing
                    st.markdown("<br>", unsafe_allow_html=True)

                    login_submitted = st.form_submit_button(
                        "🔑 Sign In",
                        use_container_width=True,
                        type="primary"
                    )

                    if login_submitted:
                        if not username or not password:
                            st.error("⚠️ Please fill in all fields")
                        elif self.auth_manager.authenticate_user(username, password):
                            st.session_state.authenticated = True
                            st.session_state.user_info = self.auth_manager.get_user_info(username)
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")

            # REGISTER TAB
            with register_tab:
                with st.form("register_form", clear_on_submit=True):
                    st.markdown("### Create Your Account")
                    st.markdown("Join Telmi and start analyzing your telecom data")

                    # Add some spacing
                    st.markdown("<br>", unsafe_allow_html=True)

                    # Two columns for better layout
                    col_reg1, col_reg2 = st.columns(2)

                    with col_reg1:
                        reg_username = st.text_input(
                            "Username *",
                            placeholder="Choose a username",
                            key="reg_username",
                            help="This will be your unique identifier"
                        )

                    with col_reg2:
                        reg_email = st.text_input(
                            "Email Address *",
                            placeholder="your.email@company.com",
                            key="reg_email",
                            help="We'll use this for account recovery"
                        )

                    reg_password = st.text_input(
                        "Password *",
                        type="password",
                        placeholder="Create a secure password",
                        key="reg_password",
                        help="Choose a strong password for your account"
                    )

                    reg_password_confirm = st.text_input(
                        "Confirm Password *",
                        type="password",
                        placeholder="Confirm your password",
                        key="reg_password_confirm"
                    )

                    # Add some spacing
                    st.markdown("<br>", unsafe_allow_html=True)

                    register_submitted = st.form_submit_button(
                        "📝 Create Account",
                        use_container_width=True,
                        type="primary"
                    )

                    if register_submitted:
                        # Validation
                        if not all([reg_username, reg_email, reg_password, reg_password_confirm]):
                            st.error("⚠️ Please fill in all required fields")
                        elif reg_password != reg_password_confirm:
                            st.error("❌ Passwords do not match")
                        elif len(reg_password) < 6:
                            st.error("⚠️ Password must be at least 6 characters long")
                        else:
                            # Attempt to create user
                            result = self.auth_manager.create_user(reg_username, reg_email, reg_password)

                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                st.info("💡 You can now sign in using the Sign In tab")
                                # Clear form fields
                                for key in ['reg_username', 'reg_email', 'reg_password', 'reg_password_confirm']:
                                    if key in st.session_state:
                                        st.session_state[key] = ""
                            else:
                                st.error(f"❌ {result['message']}")

            # Footer with additional info
            st.markdown("---")
            st.markdown("""
                <div style="text-align: center; color: #718096; font-size: 0.9rem; margin-top: 1rem;">
                    <p>🔒 Your data is secure and encrypted</p>
                    <p>Need help? Contact your system administrator</p>
                </div>
            """, unsafe_allow_html=True)

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

        # FIXED: Show thinking overlay if processing
        if st.session_state.show_thinking:
            self._render_thinking_overlay()

        # Sidebar (with improvements)
        self.sidebar_manager.render_sidebar()

        # Main chat interface
        self._render_main_chat()

        # FIXED: Handle message processing without infinite loops
        if st.session_state.processing_message:
            self._process_queued_message()

    def _render_thinking_overlay(self):
        """FIXED: Render thinking overlay that doesn't interfere with layout."""
        st.markdown("""
            <div class="thinking-overlay">
                <div class="thinking-card">
                    <div class="thinking-icon">🔮</div>
                    <div class="thinking-content">
                        <h3>Analyzing your question</h3>
                        <p>Telmi is working on your request...</p>
                        <div class="thinking-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    def _process_queued_message(self):
        """FIXED: Process queued message without state conflicts."""
        if 'queued_message' not in st.session_state:
            st.session_state.processing_message = False
            st.session_state.show_thinking = False
            return

        user_input = st.session_state.queued_message
        logger.info(f"🔄 Processing queued message: {user_input[:50]}...")

        try:
            # Call the bridge
            result = telmi_bridge.process_question(user_input)

            if result['success']:
                response = result['response']
                processing_time = result.get('processing_time', 0)

                # Add processing time info
                if processing_time > 0:
                    response += f"\n\n*⏱️ Processed in {processing_time:.2f} seconds*"

                # Parse response for attachments
                attachments = self._extract_attachments(response)

                # Add agent response
                self._add_message('agent', response, attachments)
            else:
                # Add error response
                error_response = result.get('response', 'Unknown error occurred')
                self._add_message('agent', error_response)

        except Exception as e:
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

        finally:
            # FIXED: Clear processing states properly
            if 'queued_message' in st.session_state:
                del st.session_state.queued_message
            st.session_state.processing_message = False
            st.session_state.show_thinking = False
            logger.info("🔄 Message processing completed")
            st.rerun()

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

        # Input area at bottom (only if not processing)
        if not st.session_state.processing_message:
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
        """Clean rendering of agent messages."""
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
            self._render_content_cleanly(content, attachments)

    def _render_content_cleanly(self, content: str, attachments: Dict[str, Any]):
        """Render content cleanly with proper viewers for each element type."""
        # Split content by lines and process each section
        lines = content.split('\n\n')

        for section in lines:
            section = section.strip()
            if not section:
                continue

            # Handle each type of placeholder
            if '[TABLE_DATA_PLACEHOLDER]' in section:
                section_title = section.replace('[TABLE_DATA_PLACEHOLDER]', '').strip()
                if section_title:
                    st.markdown(section_title)
                if 'table_data' in attachments:
                    self._render_table_clean(attachments['table_data'])

            elif '[CHART_DISPLAY_PLACEHOLDER]' in section:
                section_title = section.replace('[CHART_DISPLAY_PLACEHOLDER]', '').strip()
                if section_title:
                    st.markdown(section_title)
                if 'chart' in attachments:
                    self._render_chart_complete(attachments['chart'])

            elif '[DOWNLOAD_BUTTONS_PLACEHOLDER]' in section:
                section_title = section.replace('[DOWNLOAD_BUTTONS_PLACEHOLDER]', '').strip()
                if section_title:
                    st.markdown(section_title)
                if attachments:
                    self._render_downloads_clean(attachments)

            elif '```sql' in section or (section.startswith('```') and 'sql' in section.lower()):
                self._render_sql_block_from_section(section)
            else:
                self._render_regular_section(section)

        # Always render chart and downloads if they exist
        if 'chart' in attachments and '[CHART_DISPLAY_PLACEHOLDER]' not in content:
            st.markdown("### **📈 Chart Generated:**")
            self._render_chart_complete(attachments['chart'])

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
                    break
                else:
                    in_sql = True
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
                if '📊' in line:
                    line = line.replace('📊', '📉')
                st.markdown(f"### {line}")
            elif line.startswith('•'):
                st.markdown(line)
            elif line.startswith('*⏱️'):
                time_text = line.replace('*', '').replace('⏱️', '⏱️').strip()
                st.markdown(f"*{time_text}*")
            else:
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

            df = pd.DataFrame(data, columns=columns)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown(f"<small style='color: #666; font-style: italic;'>📉 {len(data):,} rows × {len(columns)} columns</small>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error displaying table: {e}")

    def _render_chart_complete(self, chart_info: Dict[str, str]):
        """Render chart with complete content."""
        if os.path.exists(chart_info['path']):
            try:
                with open(chart_info['path'], 'r', encoding='utf-8') as file:
                    html_content = file.read()
                st.components.v1.html(html_content, height=600, scrolling=True)
                st.markdown(f"<small style='color: #666; font-style: italic;'>📈 Interactive chart • {chart_info.get('size', 'Unknown size')}</small>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error displaying chart: {e}")
        else:
            st.warning("Chart file not found")

    def _render_downloads_clean(self, attachments: Dict[str, Any]):
        """Render download buttons with clean styling."""
        download_items = []

        if 'csv' in attachments:
            download_items.append(('csv', attachments['csv']))
        if 'chart' in attachments:
            download_items.append(('chart', attachments['chart']))

        if not download_items:
            st.warning("No downloads available")
            return

        cols = st.columns(len(download_items))

        # Green download buttons styling
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
        """FIXED: Process user input without infinite loops."""
        # Add user message immediately
        self._add_message('user', user_input)

        # FIXED: Set up processing states properly
        st.session_state.queued_message = user_input
        st.session_state.processing_message = True
        st.session_state.show_thinking = True

        logger.info(f"🔄 Queued message for processing: {user_input[:50]}...")
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

            # Extract table data from CSV for display
            if 'csv' in attachments:
                try:
                    import pandas as pd
                    df = pd.read_csv(attachments['csv']['path'])
                    attachments['table_data'] = {
                        'columns': df.columns.tolist(),
                        'data': df.values.tolist()
                    }
                except Exception as e:
                    logger.error(f"❌ Could not extract table data from CSV: {e}")

        except Exception as e:
            logger.error(f"❌ Error extracting attachments: {e}")

        return attachments

    def _save_session_to_history(self):
        """Save current session to chat history."""
        if not st.session_state.user_info or not st.session_state.current_messages:
            return

        try:
            self._ensure_session_exists()

            # IMPROVED: Generate intelligent session title
            session_data = {
                'title': self._generate_intelligent_session_title(),
                'messages': st.session_state.current_messages.copy(),
                'timestamp': datetime.now().isoformat(),
                'user': st.session_state.user_info['username']
            }

            st.session_state.chat_sessions[st.session_state.current_session_id] = session_data
            self._save_sessions_to_file()

        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")

    def _generate_intelligent_session_title(self) -> str:
        """IMPROVED: Generate intelligent session titles as summaries."""
        if not st.session_state.current_messages:
            return "New Chat"

        # Get first user message
        first_user_message = next(
            (msg['content'] for msg in st.session_state.current_messages if msg['role'] == 'user'),
            "New Chat"
        )

        # Intelligent title generation based on common patterns
        message_lower = first_user_message.lower()

        # Common telecom analytics patterns
        if any(word in message_lower for word in ['top', 'ranking', 'best', 'highest']):
            if 'client' in message_lower or 'customer' in message_lower:
                return "🏆 Top Clients Analysis"
            elif 'usage' in message_lower or 'data' in message_lower:
                return "📊 Top Data Usage"
            else:
                return "🥇 Ranking Analysis"

        elif any(word in message_lower for word in ['evolution', 'trend', 'time', 'journalière', 'daily']):
            return "📈 Time Trend Analysis"

        elif any(word in message_lower for word in ['ticket', 'tickets']):
            if 'between' in message_lower or 'entre' in message_lower:
                return "🎫 Ticket Time Analysis"
            else:
                return "🎫 Ticket Analysis"

        elif any(word in message_lower for word in ['country', 'pays', 'geographic']):
            return "🌍 Geographic Analysis"

        elif any(word in message_lower for word in ['distribution', 'répartition', 'breakdown']):
            return "📊 Distribution Analysis"

        elif any(word in message_lower for word in ['chart', 'pie', 'graph', 'graphique']):
            return "📈 Chart Request"

        elif any(word in message_lower for word in ['table', 'schema', 'structure']):
            return "🗂️ Schema Query"

        # Fallback: Use first few words with smart truncation
        words = first_user_message.split()
        if len(words) <= 6:
            return first_user_message
        else:
            # Take first 4-5 meaningful words
            meaningful_words = [w for w in words[:8] if len(w) > 2 and w.lower() not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']]
            title = ' '.join(meaningful_words[:5])
            return title + "..." if len(title) > 40 else title

    def _save_sessions_to_file(self):
        """Save current chat sessions to file - IMPROVED ERROR HANDLING."""
        if not st.session_state.user_info:
            return

        sessions_file = "data/chat_sessions.json"

        try:
            os.makedirs("data", exist_ok=True)

            # Load existing sessions from file
            all_sessions = {}
            if os.path.exists(sessions_file):
                try:
                    with open(sessions_file, 'r') as f:
                        content = f.read().strip()
                        if content:
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


def main():
    """Main entry point."""
    app = TelmiApp()
    app.run()


if __name__ == "__main__":
    main()