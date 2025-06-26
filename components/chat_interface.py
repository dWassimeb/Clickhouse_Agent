"""
Professional Chat Interface Component with File Downloads and Chart Embedding
"""
import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, Optional
import html
import base64
from pathlib import Path
from core.agent import ClickHouseGraphAgent
from utils.chat_utils import (
    add_message_to_history,
    get_chat_history,
    format_message_content,
    handle_file_downloads
)

def render_chat_interface(current_user: Dict[str, Any]):
    """Render the main chat interface with modern design"""
    # Initialize agent
    if 'agent' not in st.session_state:
        st.session_state.agent = ClickHouseGraphAgent(verbose=False)

    # Chat container
    chat_container = st.container()

    with chat_container:
        # Display chat history
        render_chat_history(current_user['username'])

        # Chat input area
        render_chat_input(current_user)

def render_chat_history(username: str):
    """Render chat history with modern message bubbles and embedded content"""
    chat_history = get_chat_history(username)

    if not chat_history:
        render_welcome_message()
        return

    # Create scrollable chat area
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)

    for message in chat_history:
        render_message_bubble_enhanced(message)

    st.markdown('</div>', unsafe_allow_html=True)

def render_message_bubble_enhanced(message: Dict[str, Any]):
    """Render individual message bubble with enhanced features"""
    is_user = message['role'] == 'user'
    timestamp = datetime.fromisoformat(message['timestamp']).strftime("%H:%M")

    if is_user:
        # User message (right aligned)
        st.markdown(f"""
        <div class="message-row user-row">
            <div class="message-info">
                <span class="message-time">{timestamp}</span>
            </div>
            <div class="chat-message user-message">
                {html.escape(message['content'])}
            </div>
            <div class="message-avatar user-avatar">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Assistant message (left aligned) with special content handling
        content = format_message_content(message['content'])

        # Check for chart placeholder and replace with embedded chart
        if '[CHART_PLACEHOLDER]' in content:
            content = process_chart_placeholder(content, message.get('attachments', {}))

        st.markdown(f"""
        <div class="message-row assistant-row">
            <div class="message-avatar assistant-avatar">🤖</div>
            <div class="chat-message assistant-message">
                {content}
            </div>
            <div class="message-info">
                <span class="message-time">{timestamp}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Handle file downloads
        if 'attachments' in message:
            render_message_downloads(message['attachments'])

def process_chart_placeholder(content: str, attachments: Dict[str, Any]) -> str:
    """Replace chart placeholder with embedded chart or download link"""
    if not attachments or 'chart' not in attachments:
        return content.replace('[CHART_PLACEHOLDER]', '*Chart not available*')

    chart_info = attachments['chart']
    chart_path = chart_info.get('path', '')

    if chart_path and Path(chart_path).exists():
        # Create unique ID for this chart
        chart_id = f"chart_{hash(chart_path) % 10000}"

        # Replace placeholder with embedded chart
        chart_embed = f"""
        <div class="embedded-chart" id="{chart_id}">
            <iframe src="data:text/html;charset=utf-8;base64,{get_chart_base64(chart_path)}" 
                    width="100%" height="400" frameborder="0">
            </iframe>
        </div>
        """
        return content.replace('[CHART_PLACEHOLDER]', chart_embed)
    else:
        return content.replace('[CHART_PLACEHOLDER]', '*Chart file not found*')

def get_chart_base64(chart_path: str) -> str:
    """Get base64 encoded chart content for embedding"""
    try:
        with open(chart_path, 'r', encoding='utf-8') as f:
            chart_content = f.read()
        return base64.b64encode(chart_content.encode('utf-8')).decode('utf-8')
    except Exception as e:
        return base64.b64encode(f"<html><body><h3>Chart Error: {str(e)}</h3></body></html>".encode('utf-8')).decode('utf-8')

def render_message_downloads(attachments: Dict[str, Any]):
    """Render download buttons for message attachments"""
    if not attachments:
        return

    # CSV Download
    if 'csv' in attachments:
        csv_info = attachments['csv']
        if csv_info.get('path') and Path(csv_info['path']).exists():
            with open(csv_info['path'], 'rb') as f:
                csv_data = f.read()

            st.download_button(
                label=f"📊 Download CSV ({csv_info.get('size', 'Unknown')})",
                data=csv_data,
                file_name=csv_info.get('filename', 'data.csv'),
                mime="text/csv",
                key=f"csv_download_{hash(csv_info['path']) % 10000}",
                help="Download the complete dataset as CSV file"
            )

    # Chart HTML Download
    if 'chart' in attachments:
        chart_info = attachments['chart']
        if chart_info.get('path') and Path(chart_info['path']).exists():
            with open(chart_info['path'], 'rb') as f:
                chart_data = f.read()

            st.download_button(
                label=f"📈 Download Chart ({chart_info.get('size', 'Unknown')})",
                data=chart_data,
                file_name=chart_info.get('filename', 'chart.html'),
                mime="text/html",
                key=f"chart_download_{hash(chart_info['path']) % 10000}",
                help="Download interactive chart as HTML file"
            )

def render_welcome_message():
    """Render welcome message for new users"""
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-message">
            <div class="welcome-icon">🤖</div>
            <h2 class="welcome-title">Welcome to Telmi!</h2>
            <p class="welcome-text">
                I'm your AI-powered Telecom Analytics Assistant. I can help you analyze your ClickHouse data 
                with natural language queries. Here are some things you can ask me:
            </p>
            <div class="example-queries">
                <div class="example-query" onclick="setQueryInput(this.innerText);">
                    📊 Show me the top 10 customers by data usage
                </div>
                <div class="example-query" onclick="setQueryInput(this.innerText);">
                    🌍 What's the geographic distribution of our users?
                </div>
                <div class="example-query" onclick="setQueryInput(this.innerText);">
                    📈 Show the evolution of data usage over the last 6 months
                </div>
                <div class="example-query" onclick="setQueryInput(this.innerText);">
                    🔍 List all available tables and their schemas
                </div>
            </div>
        </div>
    </div>

    <style>
    .welcome-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 400px;
        padding: 40px 20px;
    }

    .welcome-message {
        text-align: center;
        max-width: 600px;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }

    .welcome-icon {
        font-size: 4rem;
        margin-bottom: 20px;
    }

    .welcome-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 15px;
    }

    .welcome-text {
        font-size: 1.1rem;
        color: #64748b;
        line-height: 1.6;
        margin-bottom: 30px;
    }

    .example-queries {
        display: grid;
        gap: 12px;
    }

    .example-query {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 15px 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
        color: #374151;
        text-align: left;
    }

    .example-query:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    </style>

    <script>
    function setQueryInput(text) {
        // Find the text input and set its value
        const inputs = parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {
            inputs[inputs.length - 1].value = text;
            inputs[inputs.length - 1].focus();
        }
    }
    </script>
    """, unsafe_allow_html=True)

def render_chat_input(current_user: Dict[str, Any]):
    """Render chat input area with modern styling"""
    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([9, 1])

        with col1:
            user_input = st.text_input(
                "Type your question...",
                placeholder="Ask me anything about your telecom data...",
                key="chat_input",
                label_visibility="collapsed"
            )

        with col2:
            submit_button = st.form_submit_button(
                "🚀",
                help="Send message",
                use_container_width=True
            )

        if submit_button and user_input.strip():
            handle_user_message(user_input.strip(), current_user)

def handle_user_message(user_input: str, current_user: Dict[str, Any]):
    """Handle user message and generate AI response with attachments"""
    username = current_user['username']

    # Add user message to history
    add_message_to_history(username, "user", user_input)

    # Show thinking indicator
    thinking_placeholder = st.empty()
    with thinking_placeholder:
        render_thinking_indicator()

    try:
        # Process with agent
        agent_response = st.session_state.agent.process_question(user_input)

        # Clear thinking indicator
        thinking_placeholder.empty()

        # Extract attachments from agent response if available
        attachments = extract_attachments_from_response(agent_response)

        # Add assistant response to history with attachments
        add_message_to_history(username, "assistant", agent_response, attachments)

        # Force refresh to show new messages
        st.rerun()

    except Exception as e:
        thinking_placeholder.empty()
        error_message = f"❌ **Error:** I encountered an issue while processing your question: {str(e)}"
        add_message_to_history(username, "assistant", error_message)
        st.rerun()

def extract_attachments_from_response(response: str) -> Dict[str, Any]:
    """Extract file attachment information from agent response"""
    attachments = {}

    # Look for download links in the response
    import re

    # CSV download pattern
    csv_match = re.search(r'\[Download CSV file\]\(([^)]+)\)', response)
    if csv_match:
        filename = csv_match.group(1)
        # Find the actual file path in exports directory
        csv_path = find_file_in_exports(filename, 'csv')
        if csv_path:
            attachments['csv'] = {
                'type': 'csv',
                'filename': filename,
                'path': csv_path,
                'size': get_file_size(csv_path)
            }

    # Chart download pattern
    chart_match = re.search(r'\[Download Chart\]\(([^)]+)\)', response)
    if chart_match:
        filename = chart_match.group(1)
        # Find the actual file path in visualizations directory
        chart_path = find_file_in_visualizations(filename)
        if chart_path:
            attachments['chart'] = {
                'type': 'html_chart',
                'filename': filename,
                'path': chart_path,
                'size': get_file_size(chart_path)
            }

    return attachments

def find_file_in_exports(filename: str, file_type: str) -> Optional[str]:
    """Find file in exports directory"""
    exports_dir = Path("exports")
    if exports_dir.exists():
        for file_path in exports_dir.glob(f"*{filename}*"):
            if file_path.suffix.lower() == f'.{file_type}':
                return str(file_path)
        # Also try exact filename
        exact_path = exports_dir / filename
        if exact_path.exists():
            return str(exact_path)
    return None

def find_file_in_visualizations(filename: str) -> Optional[str]:
    """Find file in visualizations directory"""
    viz_dir = Path("visualizations")
    if viz_dir.exists():
        for file_path in viz_dir.glob(f"*{filename}*"):
            if file_path.suffix.lower() == '.html':
                return str(file_path)
        # Also try exact filename
        exact_path = viz_dir / filename
        if exact_path.exists():
            return str(exact_path)
    return None

def get_file_size(file_path: str) -> str:
    """Get human-readable file size"""
    try:
        size_bytes = Path(file_path).stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    except:
        return "Unknown"

def render_thinking_indicator():
    """Render modern thinking/loading indicator"""
    st.markdown("""
    <div class="thinking-container">
        <div class="thinking-avatar">🤖</div>
        <div class="thinking-bubble">
            <div class="thinking-text">Telmi is thinking...</div>
            <div class="thinking-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    </div>

    <style>
    .thinking-container {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 20px;
        margin: 10px 0;
    }

    .thinking-avatar {
        font-size: 2rem;
        flex-shrink: 0;
    }

    .thinking-bubble {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 15px 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .thinking-text {
        color: #64748b;
        font-style: italic;
    }

    .thinking-dots {
        display: flex;
        gap: 4px;
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: thinking 1.4s infinite ease-in-out both;
    }

    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes thinking {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }

    .embedded-chart {
        margin: 15px 0;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .embedded-chart iframe {
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Add some delay to show the thinking animation
    time.sleep(0.5)


# Enhanced CSS for chat interface
st.markdown("""
<style>
.message-row {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    margin: 15px 0;
    max-width: 100%;
}

.user-row {
    justify-content: flex-end;
}

.assistant-row {
    justify-content: flex-start;
}

.message-avatar {
    font-size: 1.5rem;
    flex-shrink: 0;
    margin-bottom: 5px;
}

.message-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 5px;
}

.message-time {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 400;
}

/* Enhanced chat message styling */
.chat-message {
    padding: 15px 20px;
    margin: 10px 0;
    border-radius: 18px;
    max-width: 80%;
    animation: slideIn 0.3s ease-out;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin-left: auto;
    text-align: right;
    border-bottom-right-radius: 6px;
}

.assistant-message {
    background: #f8fafc;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-bottom-left-radius: 6px;
}

/* Code block styling within messages */
.assistant-message pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 15px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 10px 0;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.9rem;
}

/* Table styling within messages */
.assistant-message table {
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.85rem;
    margin: 10px 0;
}

/* Download button styling */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
    margin: 5px !important;
    font-size: 0.9rem !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
""", unsafe_allow_html=True)