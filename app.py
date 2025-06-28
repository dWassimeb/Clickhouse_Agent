"""
Telmi - Modern ClickHouse Analytics Chat Interface
Main Streamlit Application
"""

import streamlit as st
import uuid
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# Import integration bridge
from integration.agent_bridge import telmi_bridge

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
    """Main Telmi application class."""

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
            'show_account_settings': False
        }

        for key, default_value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def run(self):
        """Main application entry point."""
        # Apply custom styling
        apply_custom_styling()

        # Check authentication
        if not st.session_state.authenticated:
            self._show_login_screen()
        else:
            self._show_main_interface()

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
        # Test agent status on first load
        if 'agent_status_checked' not in st.session_state:
            with st.spinner("🔧 Initializing Telmi agent..."):
                status = telmi_bridge.get_agent_status()
                st.session_state.agent_status = status
                st.session_state.agent_status_checked = True

                if not status['ready']:
                    st.error("⚠️ Agent initialization issue. Check the status panel in the sidebar.")

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
                        <span class="typing-text">Telmi is thinking...</span>
                    </div>
                """, unsafe_allow_html=True)

        # Input area at bottom
        self._render_input_area()

    def _display_chat_messages(self):
        """Display all chat messages."""
        if not st.session_state.current_messages:
            # Welcome message
            st.markdown("""
                <div class="welcome-message">
                    <h3>👋 Welcome to Telmi!</h3>
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
        """Render an agent message with attachments."""
        content = message['content']
        attachments = message.get('attachments', {})

        # Agent message bubble
        st.markdown(f"""
            <div class="message-container agent-message">
                <div class="message-avatar agent-avatar">🔮</div>
                <div class="message-bubble agent-bubble">
                    {content}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Handle attachments
        if attachments:
            col1, col2 = st.columns(2)

            with col1:
                if 'csv' in attachments:
                    csv_info = attachments['csv']
                    if os.path.exists(csv_info['path']):
                        with open(csv_info['path'], 'rb') as file:
                            st.download_button(
                                label=f"📊 Download CSV ({csv_info['size']})",
                                data=file.read(),
                                file_name=csv_info['filename'],
                                mime='text/csv',
                                use_container_width=True
                            )

            with col2:
                if 'chart' in attachments:
                    chart_info = attachments['chart']
                    if os.path.exists(chart_info['path']):
                        with open(chart_info['path'], 'rb') as file:
                            st.download_button(
                                label=f"📈 Download Chart ({chart_info['size']})",
                                data=file.read(),
                                file_name=chart_info['filename'],
                                mime='text/html',
                                use_container_width=True
                            )

            # Display chart inline
            if 'chart' in attachments:
                chart_info = attachments['chart']
                if os.path.exists(chart_info['path']):
                    with open(chart_info['path'], 'r', encoding='utf-8') as file:
                        html_content = file.read()
                        st.components.v1.html(html_content, height=600, scrolling=True)

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

        # Show thinking indicator
        st.session_state.agent_thinking = True

        # Create a placeholder for the response
        response_placeholder = st.empty()

        with response_placeholder.container():
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

        try:
            # Process question through the bridge
            with response_placeholder.container():
                st.markdown("🧠 **Analyzing your question with AI...**")

            result = telmi_bridge.process_question(user_input)

            # Clear the thinking indicator
            response_placeholder.empty()

            if result['success']:
                response = result['response']
                # Parse response for attachments
                attachments = self._extract_attachments(response)
                # Add agent response
                self._add_message('agent', response, attachments)
            else:
                # Add error response
                self._add_message('agent', result['response'])

        except Exception as e:
            # Clear the thinking indicator
            response_placeholder.empty()

            # Add detailed error response
            error_response = f"""❌ **Unexpected Error**

**Issue:** {str(e)}

**Possible Solutions:**
• Restart the Streamlit application
• Check if the backend agent is properly configured
• Verify all dependencies are installed
• Contact your system administrator

**Debug Info:** Make sure you're running from the project root directory with all core modules available."""

            self._add_message('agent', error_response)

        finally:
            # Hide thinking indicator
            st.session_state.agent_thinking = False
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
        if st.session_state.current_session_id:
            self._save_session_to_history()

    def _extract_attachments(self, response: str) -> Dict[str, Any]:
        """Extract file attachments from agent response."""
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

        return attachments

    def _save_session_to_history(self):
        """Save current session to chat history."""
        if not st.session_state.current_session_id:
            st.session_state.current_session_id = str(uuid.uuid4())

        st.session_state.chat_sessions[st.session_state.current_session_id] = {
            'title': self._generate_session_title(),
            'messages': st.session_state.current_messages.copy(),
            'timestamp': datetime.now().isoformat(),
            'user': st.session_state.user_info['username']
        }

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