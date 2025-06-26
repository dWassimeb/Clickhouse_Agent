"""
Telmi - Modern ClickHouse Agent Streamlit Interface
Ultra-professional, modern design with authentication and chat interface
"""
import streamlit as st
import os
import sys
from pathlib import Path

project_root = Path(file).parent
sys.path.insert(0, str(project_root))

from components.auth_components import render_auth_page
from components.chat_interface import render_chat_interface
from components.sidebar import render_sidebar
from utils.auth_utils import check_authentication, get_current_user
from utils.chat_utils import initialize_chat_session
from config.settings import APP_CONFIG

# Page Configuration

st.set_page_config( page_title="Telmi - Telecom Analytics AI",
                    page_icon="🤖",
                    layout="wide",
                    initial_sidebar_state="expanded",
                    menu_items={'Get Help': None,
                                'Report a bug': None,
                                'About': "Telmi - Your AI-powered Telecom Analytics Assistant"
                                }
                    )

# Custom CSS

def load_custom_css():
            """Load custom CSS for modern design"""
            css_file = project_root / "static" / "css" / "custom.css"
            if css_file.exists():
            with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Additional inline CSS for ultra-modern design
st.markdown("""
<style>
/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Modern app container */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

/* Main content area */
.main-content {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    margin: 20px;
    padding: 30px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Professional header */
.app-header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px 0;
    border-bottom: 2px solid #f0f2f6;
}

.app-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

.app-subtitle {
    font-size: 1.2rem;
    color: #64748b;
    font-weight: 400;
}

/* Modern buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

/* Modern sidebar */
.css-1d391kg {
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

/* Chat messages styling */
.chat-message {
    padding: 15px 20px;
    margin: 10px 0;
    border-radius: 18px;
    max-width: 80%;
    animation: slideIn 0.3s ease-out;
}

.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin-left: auto;
    text-align: right;
}

.assistant-message {
    background: #f8fafc;
    color: #1e293b;
    border: 1px solid #e2e8f0;
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

/* Professional loading indicator */
.loading-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    color: #667eea;
}

.loading-dots {
    display: inline-block;
    position: relative;
    width: 80px;
    height: 80px;
}

.loading-dots div {
    position: absolute;
    top: 33px;
    width: 13px;
    height: 13px;
    border-radius: 50%;
    background: #667eea;
    animation-timing-function: cubic-bezier(0, 1, 1, 0);
}

.loading-dots div:nth-child(1) {
    left: 8px;
    animation: lds-ellipsis1 0.6s infinite;
}

.loading-dots div:nth-child(2) {
    left: 8px;
    animation: lds-ellipsis2 0.6s infinite;
}

.loading-dots div:nth-child(3) {
    left: 32px;
    animation: lds-ellipsis2 0.6s infinite;
}

.loading-dots div:nth-child(4) {
    left: 56px;
    animation: lds-ellipsis3 0.6s infinite;
}

@keyframes lds-ellipsis1 {
    0% { transform: scale(0); }
    100% { transform: scale(1); }
}

@keyframes lds-ellipsis3 {
    0% { transform: scale(1); }
    100% { transform: scale(0); }
}

@keyframes lds-ellipsis2 {
    0% { transform: translate(0, 0); }
    100% { transform: translate(24px, 0); }
}
</style>
""", unsafe_allow_html=True)


if name == "main":
    main()
