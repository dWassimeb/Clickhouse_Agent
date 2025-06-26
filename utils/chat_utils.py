"""
Chat management utilities for handling chat sessions and message formatting
Enhanced with file attachment support - NO Streamlit calls during import
"""

import json
import re
from typing import Dict, Any, List, Optional
import html

# Don't import streamlit at module level to avoid early execution
# Import it only when needed inside functions

def initialize_chat_session(username: str):
    """Initialize chat session for user"""
    import streamlit as st
    from database.users.user_db import UserDatabase

    user_db = UserDatabase()

    if 'current_chat_session' not in st.session_state:
        # Get user
        user = user_db.get_user_by_username(username)
        if not user:
            return

        # Get or create active session
        sessions = user_db.get_user_chat_sessions(user['id'])

        if sessions:
            # Use most recent session
            st.session_state.current_chat_session = sessions[0]['session_id']
        else:
            # Create new session
            session_id = user_db.create_chat_session(user['id'], "New Chat")
            st.session_state.current_chat_session = session_id

def create_new_chat_session(username: str) -> bool:
    """Create a new chat session for user"""
    import streamlit as st
    from database.users.user_db import UserDatabase

    user_db = UserDatabase()

    try:
        user = user_db.get_user_by_username(username)
        if not user:
            return False

        session_id = user_db.create_chat_session(user['id'], "New Chat")
        if session_id:
            st.session_state.current_chat_session = session_id
            return True

        return False

    except Exception as e:
        st.error(f"Error creating new chat session: {e}")
        return False

def add_message_to_history(username: str, role: str, content: str, attachments: Dict[str, Any] = None):
    """Add message to chat history with attachment support"""
    import streamlit as st
    from database.users.user_db import UserDatabase

    user_db = UserDatabase()

    try:
        # Get current session
        session_id = st.session_state.get('current_chat_session')
        if not session_id:
            initialize_chat_session(username)
            session_id = st.session_state.get('current_chat_session')

        if not session_id:
            st.error("No active chat session")
            return

        # Convert attachments to JSON string
        attachments_json = json.dumps(attachments) if attachments else None

        # Add message to database
        success = user_db.add_chat_message(session_id, role, content, attachments_json)

        if not success:
            st.error("Failed to save message")

        # Update session title if this is the first user message
        if role == 'user':
            update_session_title_from_message(session_id, content, username)

    except Exception as e:
        st.error(f"Error adding message to history: {e}")

def get_chat_history(username: str) -> List[Dict[str, Any]]:
    """Get chat history for current session with attachment processing"""
    import streamlit as st
    from database.users.user_db import UserDatabase

    user_db = UserDatabase()

    try:
        session_id = st.session_state.get('current_chat_session')
        if not session_id:
            return []

        messages = user_db.get_chat_messages(session_id)

        # Process messages and add attachments
        processed_messages = []
        for message in messages:
            processed_message = {
                'role': message['role'],
                'content': message['content'],
                'timestamp': message['timestamp']
            }

            # Parse attachments if present
            if message['attachments']:
                try:
                    processed_message['attachments'] = json.loads(message['attachments'])
                except:
                    pass

            processed_messages.append(processed_message)

        return processed_messages

    except Exception as e:
        # Don't call st.error here during import - just print
        print(f"Error getting chat history: {e}")
        return []

def get_user_chat_sessions(username: str) -> List[Dict[str, Any]]:
    """Get all chat sessions for user"""
    import streamlit as st
    from database.users.user_db import UserDatabase

    user_db = UserDatabase()

    try:
        user = user_db.get_user_by_username(username)
        if not user:
            return []

        return user_db.get_user_chat_sessions(user['id'])

    except Exception as e:
        st.error(f"Error getting chat sessions: {e}")
        return []

def delete_chat_session(session_id: str, username: str) -> bool:
    """Delete a chat session"""
    import streamlit as st
    from database.users.user_db import UserDatabase

    user_db = UserDatabase()

    try:
        user = user_db.get_user_by_username(username)
        if not user:
            return False

        success = user_db.delete_chat_session(session_id, user['id'])

        # If current session was deleted, create new one
        if success and st.session_state.get('current_chat_session') == session_id:
            create_new_chat_session(username)

        return success

    except Exception as e:
        st.error(f"Error deleting chat session: {e}")
        return False

def update_session_title_from_message(session_id: str, message: str, username: str):
    """Update session title based on first user message"""
    from database.users.user_db import UserDatabase

    user_db = UserDatabase()

    try:
        user = user_db.get_user_by_username(username)
        if not user:
            return

        # Check if this session already has a custom title
        sessions = user_db.get_user_chat_sessions(user['id'])
        current_session = next((s for s in sessions if s['session_id'] == session_id), None)

        if current_session and current_session['title'] != 'New Chat':
            return  # Already has a custom title

        # Generate title from message (first 50 characters)
        title = generate_session_title(message)
        user_db.update_chat_session_title(session_id, title, user['id'])

    except Exception as e:
        print(f"Error updating session title: {e}")

def generate_session_title(message: str) -> str:
    """Generate a descriptive title from the first message"""

    # Clean message
    clean_message = re.sub(r'[^\w\s]', '', message)
    clean_message = re.sub(r'\s+', ' ', clean_message).strip()

    # Truncate to reasonable length
    if len(clean_message) <= 50:
        return clean_message

    # Find a good break point
    words = clean_message[:50].split()
    if len(words) > 1:
        words.pop()  # Remove potentially truncated last word
        return ' '.join(words) + "..."

    return clean_message[:47] + "..."

def format_message_content(content: str) -> str:
    """Format message content for display with enhanced chat-friendly styling"""

    # Escape HTML first
    content = html.escape(content)

    # Convert markdown-style formatting
    content = format_markdown_elements(content)

    # Format code blocks and inline code
    content = format_code_elements(content)

    # Format tables
    content = format_tables(content)

    # Format lists
    content = format_lists(content)

    # Format download links (ChatGPT style)
    content = format_download_links(content)

    # Add line breaks
    content = content.replace('\n', '<br>')

    return content

def format_download_links(content: str) -> str:
    """Format download links in ChatGPT style"""

    # CSV download links
    content = re.sub(
        r'📊 \*\*\[Download CSV file\]\(([^)]+)\)\*\* \(([^)]+)\)',
        r'<div class="download-link-container"><a href="#" class="download-link csv-download" data-filename="\1">📊 Download CSV file</a> <span class="file-size">(\2)</span></div>',
        content
    )

    # Chart download links
    content = re.sub(
        r'📁 \*\*\[Download Chart\]\(([^)]+)\)\*\* \(([^)]+)\)',
        r'<div class="download-link-container"><a href="#" class="download-link chart-download" data-filename="\1">📈 Download Chart</a> <span class="file-size">(\2)</span></div>',
        content
    )

    return content

def format_markdown_elements(content: str) -> str:
    """Format basic markdown elements"""

    # Headers
    content = re.sub(r'^### (.*?)$', r'<h3 class="msg-h3">\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.*?)$', r'<h2 class="msg-h2">\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.*?)$', r'<h1 class="msg-h1">\1</h1>', content, flags=re.MULTILINE)

    # Bold and italic
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)

    # Strikethrough
    content = re.sub(r'~~(.*?)~~', r'<del>\1</del>', content)

    return content

def format_code_elements(content: str) -> str:
    """Format code blocks and inline code"""

    # Code blocks (```language\ncode\n```)
    def replace_code_block(match):
        language = match.group(1) or 'text'
        code = match.group(2)
        return f'''<div class="code-block">
            <div class="code-header">
                <span class="code-language">{language}</span>
                <button class="copy-btn" onclick="copyCode(this)">📋 Copy</button>
            </div>
            <pre class="code-content"><code>{html.escape(code)}</code></pre>
        </div>'''

    content = re.sub(r'```(\w+)?\n(.*?)\n```', replace_code_block, content, flags=re.DOTALL)

    # Inline code
    content = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', content)

    return content

def format_tables(content: str) -> str:
    """Format markdown-style tables"""

    # Simple table detection and formatting
    lines = content.split('\n')
    in_table = False
    table_lines = []
    formatted_content = []

    for line in lines:
        if '|' in line and line.strip():
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line.strip())
        else:
            if in_table:
                # Process accumulated table
                formatted_table = format_table_lines(table_lines)
                formatted_content.append(formatted_table)
                in_table = False
                table_lines = []
            formatted_content.append(line)

    # Handle table at end of content
    if in_table and table_lines:
        formatted_table = format_table_lines(table_lines)
        formatted_content.append(formatted_table)

    return '\n'.join(formatted_content)

def format_table_lines(table_lines: List[str]) -> str:
    """Format table lines into HTML table"""

    if len(table_lines) < 2:
        return '\n'.join(table_lines)

    # Parse table
    rows = []
    for line in table_lines:
        if '---' in line or '===' in line:
            continue  # Skip separator lines
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if cells:
            rows.append(cells)

    if not rows:
        return '\n'.join(table_lines)

    # Generate HTML table
    html_table = '<div class="table-container"><table class="data-table">'

    # Header row
    if rows:
        html_table += '<thead><tr>'
        for cell in rows[0]:
            html_table += f'<th>{cell}</th>'
        html_table += '</tr></thead>'

    # Data rows
    if len(rows) > 1:
        html_table += '<tbody>'
        for row in rows[1:]:
            html_table += '<tr>'
            for cell in row:
                html_table += f'<td>{cell}</td>'
            html_table += '</tr>'
        html_table += '</tbody>'

    html_table += '</table></div>'

    return html_table

def format_lists(content: str) -> str:
    """Format markdown-style lists"""

    lines = content.split('\n')
    in_ul = False
    in_ol = False
    formatted_lines = []

    for line in lines:
        stripped = line.strip()

        # Unordered list
        if stripped.startswith('• ') or stripped.startswith('- '):
            if not in_ul:
                formatted_lines.append('<ul class="msg-list">')
                in_ul = True
            elif in_ol:
                formatted_lines.append('</ol>')
                formatted_lines.append('<ul class="msg-list">')
                in_ol = False
                in_ul = True

            item = stripped[2:].strip()
            formatted_lines.append(f'<li>{item}</li>')

        # Ordered list
        elif re.match(r'^\d+\.\s', stripped):
            if not in_ol:
                if in_ul:
                    formatted_lines.append('</ul>')
                    in_ul = False
                formatted_lines.append('<ol class="msg-list">')
                in_ol = True

            item = re.sub(r'^\d+\.\s', '', stripped)
            formatted_lines.append(f'<li>{item}</li>')

        # Regular line
        else:
            if in_ul:
                formatted_lines.append('</ul>')
                in_ul = False
            if in_ol:
                formatted_lines.append('</ol>')
                in_ol = False

            formatted_lines.append(line)

    # Close any open lists
    if in_ul:
        formatted_lines.append('</ul>')
    if in_ol:
        formatted_lines.append('</ol>')

    return '\n'.join(formatted_lines)

def handle_file_downloads(attachments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle file downloads for chat messages"""

    download_info = {}

    if attachments.get('csv_file'):
        download_info['csv'] = process_csv_attachment(attachments['csv_file'])

    if attachments.get('html_chart'):
        download_info['chart'] = process_chart_attachment(attachments['html_chart'])

    return download_info

def process_csv_attachment(csv_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process CSV attachment for download"""

    if csv_info.get('success') and csv_info.get('file_path'):
        try:
            with open(csv_info['file_path'], 'rb') as f:
                file_data = f.read()

            return {
                'data': file_data,
                'filename': csv_info.get('filename', 'data.csv'),
                'mime_type': 'text/csv',
                'size': csv_info.get('file_stats', {}).get('size_human', 'Unknown')
            }
        except Exception as e:
            return {'error': f"Failed to read CSV file: {e}"}

    return {'error': 'CSV file not available'}

def process_chart_attachment(chart_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process chart attachment for display"""

    if chart_info.get('success') and chart_info.get('html_file'):
        try:
            with open(chart_info['html_file'], 'r', encoding='utf-8') as f:
                html_content = f.read()

            return {
                'html': html_content,
                'chart_type': chart_info.get('visualization_type', 'chart'),
                'filename': chart_info.get('file_stats', {}).get('filename', 'chart.html')
            }
        except Exception as e:
            return {'error': f"Failed to read chart file: {e}"}

    return {'error': 'Chart file not available'}

# Additional CSS for enhanced message formatting
def get_message_styling_css() -> str:
    """Get CSS for enhanced message content formatting"""

    return """
    <style>
    /* Enhanced message content styling */
    .msg-h1, .msg-h2, .msg-h3 {
        color: #1e293b;
        font-weight: 600;
        margin: 15px 0 10px 0;
        line-height: 1.3;
    }

    .msg-h1 { font-size: 1.4rem; }
    .msg-h2 { font-size: 1.2rem; }
    .msg-h3 { font-size: 1.1rem; }

    .msg-list {
        margin: 10px 0;
        padding-left: 20px;
    }

    .msg-list li {
        margin: 5px 0;
        line-height: 1.4;
    }

    .inline-code {
        background: #f1f5f9;
        color: #e11d48;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 0.9em;
    }

    .code-block {
        background: #1e293b;
        border-radius: 8px;
        margin: 15px 0;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .code-header {
        background: #334155;
        padding: 8px 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
    }

    .code-language {
        color: #94a3b8;
        font-weight: 500;
    }

    .copy-btn {
        background: #667eea;
        color: white;
        border: none;
        padding: 4px 8px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.8rem;
        transition: background 0.2s;
    }

    .copy-btn:hover {
        background: #5a67d8;
    }

    .code-content {
        margin: 0;
        padding: 15px;
        color: #e2e8f0;
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 0.9rem;
        line-height: 1.4;
        overflow-x: auto;
    }

    .table-container {
        overflow-x: auto;
        margin: 15px 0;
    }

    .data-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 0.85rem;
    }

    .data-table th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
        font-size: 0.8rem;
    }

    .data-table td {
        padding: 6px 12px;
        border-bottom: 1px solid #e2e8f0;
        font-size: 0.8rem;
    }

    .data-table tr:hover {
        background: #f8fafc;
    }

    /* Download link styling */
    .download-link-container {
        margin: 10px 0;
        padding: 10px;
        background: #f0f9f4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        display: inline-block;
    }

    .download-link {
        color: #059669;
        text-decoration: none;
        font-weight: 500;
        margin-right: 8px;
    }

    .download-link:hover {
        text-decoration: underline;
    }

    .file-size {
        color: #6b7280;
        font-size: 0.9rem;
    }
    </style>

    <script>
    function copyCode(button) {
        const codeBlock = button.closest('.code-block');
        const code = codeBlock.querySelector('.code-content code').textContent;

        navigator.clipboard.writeText(code).then(function() {
            button.textContent = '✅ Copied!';
            setTimeout(() => {
                button.textContent = '📋 Copy';
            }, 2000);
        }, 2000);
    }
    </script>
    """