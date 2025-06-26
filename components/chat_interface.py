"""
Professional Chat Interface Component
Modern, clean chat UI with advanced features
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
    """Render the main chat interface with modern design"""# Initialize agent
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
    """Render chat history with modern message bubbles"""

    chat_history = get_chat_history(username)

    if not chat_history:
        render_welcome_message()
        return

    # Create scrollable chat area
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)

    for message in chat_history:
        render_message_bubble(message)

    st.markdown('</div>', unsafe_allow_html=True)


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
                <div class="example-query" onclick="document.querySelector('input[type=text]').value = this.innerText;">
                    📊 Show me the top 10 customers by data usage
                </div>
                <div class="example-query" onclick="document.querySelector('input[type=text]').value = this.innerText;">
                    🌍 What's the geographic distribution of our users?
                </div>
                <div class="example-query" onclick="document.querySelector('input[type=text]').value = this.innerText;">
                    📈 Show the evolution of data usage over the last 6 months
                </div>
                <div class="example-query" onclick="document.querySelector('input[type=text]').value = this.innerText;">
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
    """, unsafe_allow_html=True)



def render_message_bubble(message: Dict[str, Any]):
    """Render individual message bubble with modern styling"""

    is_user = message['role'] == 'user'
    timestamp = datetime.fromisoformat(message['timestamp']).strftime("%H:%M")

    # Message container
    bubble_class = "user-message" if is_user else "assistant-message"

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
        st.markdown(f"""
        <div class="message-row assistant-row">
            <div class="message-avatar assistant-avatar">🤖</div>
            <div class="chat-message assistant-message">
                {format_message_content(message['content'])}
            </div>
            <div class="message-info">
                <span class="message-time">{timestamp}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Handle file attachments (CSV, HTML charts)
        if 'attachments' in message:
            render_message_attachments(message['attachments'])


def render_csv_download(csv_info: Dict[str, Any]):
    """Render CSV download button with modern styling"""

    if csv_info.get('success'):
        file_path = csv_info.get('file_path', '')
        filename = csv_info.get('filename', 'data.csv')
        file_size = csv_info.get('file_stats', {}).get('size_human', 'Unknown')

        if Path(file_path).exists():
            with open(file_path, 'rb') as file:
                file_data = file.read()

            st.markdown("""
            <div class="download-card">
                <div class="download-icon">📄</div>
                <div class="download-info">
                    <div class="download-title">CSV Export Ready</div>
                    <div class="download-meta">""" + f"{filename} • {file_size}" + """</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📥 Download CSV",
                data=file_data,
                file_name=filename,
                mime="text/csv",
                key=f"download_{filename}",
                help="Download the query results as CSV file"
            )


def render_html_chart(chart_info: Dict[str, Any]):
    """Render HTML chart inline with modern styling"""

    if chart_info.get('success'):
        file_path = chart_info.get('html_file', '')
        chart_type = chart_info.get('visualization_type', 'chart')

        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            st.markdown(f"""
            <div class="chart-card">
                <div class="chart-header">
                    <div class="chart-icon">📊</div>
                    <div class="chart-info">
                        <div class="chart-title">Interactive {chart_type.replace('_', ' ').title()} Chart</div>
                        <div class="chart-meta">Professional visualization • Responsive design</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Display chart in expandable container
            with st.expander("📈 View Interactive Chart", expanded=True):
                st.components.v1.html(html_content, height=600, scrolling=True)


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
    """Handle user message and generate AI response"""

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

        # Add assistant response to history
        add_message_to_history(username, "assistant", agent_response)

        # Force refresh to show new messages
        st.rerun()

    except Exception as e:
        thinking_placeholder.empty()
        error_message = f"❌ **Error:** I encountered an issue while processing your question: {str(e)}"
        add_message_to_history(username, "assistant", error_message)
        st.rerun()

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
    </style>
    """, unsafe_allow_html=True)

    # Add some delay to show the thinking animation
    time.sleep(0.5)


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

.download-card, .chart-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.download-icon, .chart-icon {
    font-size: 1.5rem;
}

.download-info, .chart-info {
    flex: 1;
}

.download-title, .chart-title {
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 2px;
}

.download-meta, .chart-meta {
    font-size: 0.875rem;
    color: #64748b;
}
</style>
""", unsafe_allow_html=True)


