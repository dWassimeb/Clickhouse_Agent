"""
Chat Interface Components for Telmi
Handles message rendering, streaming, and chat interactions
"""

import streamlit as st
import time
import re
import os
from typing import Dict, Any, List
from datetime import datetime

class ChatInterface:
    """Manages the chat interface and message interactions."""

    def __init__(self):
        self.typing_speed = 0.03  # Seconds per character for typing effect

    def render_message_stream(self, message: str, message_type: str = "agent"):
        """Render a message with typing effect."""
        if message_type == "user":
            self._render_user_message(message)
        else:
            self._render_agent_message_stream(message)

    def _render_user_message(self, content: str):
        """Render a user message bubble."""
        st.markdown(f"""
            <div class="message-container user-message">
                <div class="message-bubble user-bubble">
                    {self._format_message_content(content)}
                </div>
                <div class="message-avatar user-avatar">👤</div>
            </div>
        """, unsafe_allow_html=True)

    def _render_agent_message_stream(self, content: str):
        """Render an agent message with streaming effect."""
        # Create container for the message
        message_container = st.empty()

        # Split content into parts (text, code blocks, etc.)
        parts = self._split_message_content(content)

        current_content = ""

        for part in parts:
            if part['type'] == 'text':
                # Stream text character by character
                for i in range(len(part['content'])):
                    current_content += part['content'][i]
                    self._update_agent_message(message_container, current_content)
                    time.sleep(self.typing_speed)
            else:
                # Add non-text content immediately
                current_content += part['content']
                self._update_agent_message(message_container, current_content)
                time.sleep(0.1)

    def _update_agent_message(self, container, content: str):
        """Update the agent message container."""
        container.markdown(f"""
            <div class="message-container agent-message">
                <div class="message-avatar agent-avatar">🔮</div>
                <div class="message-bubble agent-bubble">
                    {self._format_message_content(content)}
                </div>
            </div>
        """, unsafe_allow_html=True)

    def _split_message_content(self, content: str) -> List[Dict[str, str]]:
        """Split message content into streamable parts."""
        parts = []

        # Split by code blocks
        code_pattern = r'```[\s\S]*?```'
        last_end = 0

        for match in re.finditer(code_pattern, content):
            # Add text before code block
            if match.start() > last_end:
                text_content = content[last_end:match.start()]
                if text_content.strip():
                    parts.append({
                        'type': 'text',
                        'content': text_content
                    })

            # Add code block
            parts.append({
                'type': 'code',
                'content': match.group()
            })

            last_end = match.end()

        # Add remaining text
        if last_end < len(content):
            remaining_text = content[last_end:]
            if remaining_text.strip():
                parts.append({
                    'type': 'text',
                    'content': remaining_text
                })

        # If no code blocks found, treat entire content as text
        if not parts:
            parts.append({
                'type': 'text',
                'content': content
            })

        return parts

    def _format_message_content(self, content: str) -> str:
        """Format message content for HTML display."""
        # Convert markdown to HTML
        content = self._convert_markdown_to_html(content)

        # Handle special patterns
        content = self._process_special_patterns(content)

        return content

    def _convert_markdown_to_html(self, content: str) -> str:
        """Convert basic markdown to HTML."""
        # Bold text
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

        # Italic text
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)

        # Code spans
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)

        # Line breaks
        content = content.replace('\n', '<br>')

        # Headers
        content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)

        # Lists
        content = re.sub(r'^• (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)
        content = re.sub(r'^- (.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)

        # Wrap consecutive list items in ul tags
        content = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul>\1</ul>', content, flags=re.DOTALL)

        return content

    def _process_special_patterns(self, content: str) -> str:
        """Process special patterns like file links."""
        # Convert download links to buttons
        download_pattern = r'\[Download (.*?)\]\(([^)]+)\)'

        def replace_download(match):
            label = match.group(1)
            filename = match.group(2)
            return f'<span class="download-link">📁 {label}: {filename}</span>'

        content = re.sub(download_pattern, replace_download, content)

        # Process chart placeholders
        content = content.replace('[CHART_PLACEHOLDER]', '<div class="chart-placeholder">📈 Interactive chart will appear below</div>')

        return content

    def render_typing_indicator(self):
        """Render typing indicator."""
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

    def render_welcome_message(self):
        """Render the welcome message."""
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

    def render_input_area(self, on_submit_callback):
        """Render the input area with proper styling."""
        # Create a container for the input area
        input_container = st.container()

        with input_container:
            # Custom CSS for the input area
            st.markdown("""
                <style>
                .chat-input-container {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: white;
                    border-top: 1px solid var(--border-color);
                    padding: 1rem;
                    z-index: 1000;
                }

                .chat-input-form {
                    max-width: 800px;
                    margin: 0 auto;
                    display: flex;
                    gap: 0.5rem;
                    align-items: end;
                }

                .chat-input-wrapper {
                    flex: 1;
                }

                .chat-send-button {
                    flex-shrink: 0;
                }
                </style>
            """, unsafe_allow_html=True)

            # Input form
            with st.form("chat_input_form", clear_on_submit=True):
                col1, col2 = st.columns([6, 1])

                with col1:
                    user_input = st.text_input(
                        "message",
                        placeholder="Ask me anything about your telecom data...",
                        label_visibility="collapsed",
                        key="chat_input"
                    )

                with col2:
                    submit_button = st.form_submit_button(
                        "Send",
                        use_container_width=True,
                        type="primary"
                    )

                if submit_button and user_input.strip():
                    on_submit_callback(user_input.strip())

    def render_file_attachments(self, attachments: Dict[str, Any]):
        """Render file attachments with download buttons."""
        if not attachments:
            return

        st.markdown("### 📎 Attachments")

        cols = st.columns(len(attachments))

        for i, (attachment_type, attachment_info) in enumerate(attachments.items()):
            with cols[i]:
                if attachment_type == 'csv':
                    self._render_csv_attachment(attachment_info)
                elif attachment_type == 'chart':
                    self._render_chart_attachment(attachment_info)

    def _render_csv_attachment(self, csv_info: Dict[str, str]):
        """Render CSV file attachment."""
        if os.path.exists(csv_info['path']):
            with open(csv_info['path'], 'rb') as file:
                st.download_button(
                    label=f"📊 CSV Data ({csv_info['size']})",
                    data=file.read(),
                    file_name=csv_info['filename'],
                    mime='text/csv',
                    use_container_width=True,
                    help="Download the complete dataset as CSV"
                )

    def _render_chart_attachment(self, chart_info: Dict[str, str]):
        """Render chart file attachment."""
        if os.path.exists(chart_info['path']):
            with open(chart_info['path'], 'rb') as file:
                st.download_button(
                    label=f"📈 Interactive Chart ({chart_info['size']})",
                    data=file.read(),
                    file_name=chart_info['filename'],
                    mime='text/html',
                    use_container_width=True,
                    help="Download the interactive chart as HTML"
                )

    def render_inline_chart(self, chart_path: str, height: int = 600):
        """Render chart inline in the chat."""
        if os.path.exists(chart_path):
            with open(chart_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

                # Modify the HTML to fit better in the chat
                modified_html = self._modify_chart_for_inline_display(html_content)

                st.components.v1.html(modified_html, height=height, scrolling=True)

    def _modify_chart_for_inline_display(self, html_content: str) -> str:
        """Modify chart HTML for better inline display."""
        # Remove any fixed positioning and adjust sizing
        modifications = [
            # Make container responsive
            ('style="width: 100%; height: 500px;"', 'style="width: 100%; height: 400px;"'),
            # Adjust chart container padding
            ('padding: 40px;', 'padding: 20px;'),
            # Reduce header size
            ('font-size: 2.5rem;', 'font-size: 1.8rem;'),
            ('padding: 30px;', 'padding: 20px;'),
        ]

        modified_html = html_content
        for old, new in modifications:
            modified_html = modified_html.replace(old, new)

        return modified_html

    def extract_and_display_table(self, content: str):
        """Extract and display tables from message content."""
        # Look for code blocks that contain tabular data
        code_pattern = r'```\n(.*?)\n```'
        matches = re.findall(code_pattern, content, re.DOTALL)

        for match in matches:
            if self._is_tabular_data(match):
                self._render_data_table(match)

    def _is_tabular_data(self, text: str) -> bool:
        """Check if text contains tabular data."""
        lines = text.strip().split('\n')
        if len(lines) < 3:
            return False

        # Check for table-like structure
        first_line = lines[0]
        second_line = lines[1]

        # Look for pipe separators or consistent spacing
        if '|' in first_line and '|' in second_line:
            return True

        # Look for header separator line
        if all(c in '-| ' for c in second_line):
            return True

        return False

    def _render_data_table(self, table_text: str):
        """Render tabular data as a Streamlit dataframe."""
        try:
            lines = table_text.strip().split('\n')

            # Parse header
            header_line = lines[0]
            headers = [col.strip() for col in header_line.split('|') if col.strip()]

            # Skip separator line if it exists
            data_start = 2 if len(lines) > 1 and all(c in '-| ' for c in lines[1]) else 1

            # Parse data rows
            data_rows = []
            for line in lines[data_start:]:
                if line.strip():
                    row = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if len(row) == len(headers):
                        data_rows.append(row)

            if data_rows:
                import pandas as pd
                df = pd.DataFrame(data_rows, columns=headers)
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            # If parsing fails, just display as code
            st.code(table_text)

    def get_message_timestamp(self) -> str:
        """Get formatted timestamp for messages."""
        return datetime.now().strftime("%H:%M")

    def format_response_for_display(self, response: str, attachments: Dict[str, Any] = None) -> str:
        """Format agent response for optimal display."""
        # Clean up the response
        formatted_response = self._clean_response_text(response)

        # Add attachment information
        if attachments:
            attachment_info = []
            for attachment_type, info in attachments.items():
                if attachment_type == 'csv':
                    attachment_info.append(f"📊 CSV file: {info['filename']}")
                elif attachment_type == 'chart':
                    attachment_info.append(f"📈 Chart: {info['filename']}")

            if attachment_info:
                formatted_response += "\n\n**Files generated:**\n" + "\n".join(attachment_info)

        return formatted_response

    def _clean_response_text(self, text: str) -> str:
        """Clean up response text for better display."""
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Clean up markdown artifacts
        text = text.replace('**Results:**', '**📊 Results:**')
        text = text.replace('**Analysis:**', '**🔍 Analysis:**')
        text = text.replace('**Executed Query:**', '**⚡ Executed Query:**')

        return text.strip()