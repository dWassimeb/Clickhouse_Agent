"""
CSS Styling for Telmi - OPTIMIZED AND FIXED VERSION
Cleaner, focused styling with proper form alignment and reduced complexity
"""

import streamlit as st

def apply_custom_styling():
    """Apply optimized CSS styling with fixed form alignment and reduced complexity."""

    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Root variables for consistent theming */
    :root {
        --primary-color: #4299e1;
        --primary-hover: #3182ce;
        --primary-light: #63b3ed;
        --background-color: #ffffff;
        --surface-color: #f7fafc;
        --text-primary: #1a202c;
        --text-secondary: #4a5568;
        --text-muted: #a0aec0;
        --border-color: #e2e8f0;
        --success-color: #48bb78;
        --error-color: #f56565;
        --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        --radius-md: 8px;
        --radius-lg: 12px;
    }

    /* Global styles */
    .main {
        padding: 0;
        max-width: none;
    }

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: var(--background-color);
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    .stActionButton {display: none;}

    /* === ENHANCED AUTHENTICATION STYLING === */

    /* Tab styling for login/register */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #f8fafc;
        border-radius: 10px;
        padding: 4px;
        margin-bottom: 1.5rem;
        width: 100%;
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        background: transparent;
        border: none;
        color: #718096;
        font-weight: 500;
        font-size: 15px;
        padding: 0 20px;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 1;
        min-width: 120px;
    }

    .stTabs [aria-selected="true"] {
        background: white !important;
        color: #2d3748 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: #edf2f7;
        color: #4a5568;
    }

    /* Login container */
    .login-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        margin: 2rem 0;
        animation: slideUp 0.6s ease-out;
    }

    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .login-header h1 {
        font-size: 3rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        background: linear-gradient(135deg, #4299e1, #63b3ed, #90cdf4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
    }

    .login-header p {
        color: #718096;
        font-size: 1.2rem;
        margin: 0.8rem 0 0 0;
        font-weight: 400;
    }

    /* === FIXED FORM STYLING === */

    /* FIXED: Authentication form inputs with perfect alignment - NO OVERLAPPING */
    .login-container .stTextInput > div > div > input,
    .stForm .stTextInput > div > div > input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        background: #ffffff !important;
        color: #2d3748 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        font-family: 'Inter', sans-serif !important;
        height: 50px !important;
        line-height: 1.2 !important;
        box-sizing: border-box !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        position: relative !important;
        outline: none !important;
    }

    /* FIXED: Remove any potential overlapping containers */
    .login-container .stTextInput > div > div,
    .stForm .stTextInput > div > div {
        position: relative !important;
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* FIXED: Focus state without overlapping */
    .login-container .stTextInput > div > div > input:focus,
    .stForm .stTextInput > div > div > input:focus {
        border-color: #4299e1 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1) !important;
        z-index: 1 !important;
    }

    /* FIXED: Authentication form buttons with perfect alignment and white text */
    .login-container .stButton > button,
    .stForm .stButton > button {
        background: linear-gradient(135deg, #4299e1, #3182ce) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        height: 50px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3) !important;
        cursor: pointer !important;
    }

    .login-container .stButton > button:hover,
    .stForm .stButton > button:hover {
        background: linear-gradient(135deg, #3182ce, #2c5aa0) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4) !important;
        color: white !important;
    }

    /* FIXED: Ensure button text is white and properly centered */
    .login-container .stButton > button p,
    .stForm .stButton > button p,
    .login-container .stButton > button span,
    .stForm .stButton > button span,
    .login-container .stButton > button div,
    .stForm .stButton > button div {
        color: white !important;
        margin: 0 !important;
        font-weight: 600 !important;
        text-align: center !important;
        line-height: 1 !important;
    }

    /* FIXED: Remove conflicting placeholder text for auth forms */
    .login-container .stTextInput > div > div > div[data-testid="InputInstructions"],
    .stForm .stTextInput > div > div > div[data-testid="InputInstructions"] {
        display: none !important;
    }

    /* FIXED: Hide show/hide password button for auth forms to prevent overlap */
    .login-container .stTextInput button[kind="tertiary"],
    .stForm .stTextInput button[kind="tertiary"] {
        display: none !important;
    }

    /* === CHAT INPUT STYLING (Different from auth forms) === */

    /* Chat input - keep it separate from auth forms */
    .main .stTextInput > div > div > input:not(.login-container .stTextInput > div > div > input):not(.stForm .stTextInput > div > div > input) {
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        background: #ffffff !important;
        color: #2d3748 !important;
        font-size: 15px !important;
        height: 46px !important;
        line-height: 1.4 !important;
        box-sizing: border-box !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }

    .main .stTextInput > div > div > input:not(.login-container .stTextInput > div > div > input):not(.stForm .stTextInput > div > div > input):focus {
        border-color: #4299e1 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1) !important;
    }

    /* FIXED: Chat form layout - perfect alignment */
    .main form[data-testid="stForm"]:not(.login-container form):not(.stForm form) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important; /* Prevent wrapping */
        gap: 8px !important;
        align-items: center !important;
        width: 100% !important;
        overflow: hidden !important; /* Prevent mobile overflow-induced wrapping */
    }

    .main form[data-testid="stForm"]:not(.login-container form):not(.stForm form) > div:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important; /* Prevents overflowing on small screens */
        margin: 0 !important;
    }
    
    .main form[data-testid="stForm"]:not(.login-container form):not(.stForm form) > div:last-child {
        flex-shrink: 0 !important;
        margin: 0 !important;
    }

    /* FIXED: Chat send button - matches input height exactly */
    .main form[data-testid="stForm"]:not(.login-container form):not(.stForm form) .stButton > button {
        background: #4299e1 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        height: 46px !important;
        min-height: 46px !important;
        padding: 0 20px !important;
        margin: 0 !important;
        white-space: nowrap !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(66, 153, 225, 0.2) !important;
    }

    .main form[data-testid="stForm"]:not(.login-container form):not(.stForm form) .stButton > button:hover {
        background: #3182ce !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(66, 153, 225, 0.3) !important;
    }

    /* === CHAT INTERFACE === */

    /* Chat header */
    .chat-header {
        text-align: center;
        padding: 1.5rem 0;
        border-bottom: 1px solid var(--border-color);
        background: var(--background-color);
        margin-bottom: 1rem;
    }

    .chat-header h1 {
        font-size: 2rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .chat-header p {
        color: var(--text-secondary);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }

    /* Message containers */
    .message-container {
        display: flex;
        margin: 1rem 0;
        gap: 0.75rem;
        max-width: 100%;
        align-items: flex-start;
    }

    .message-container.user-message {
        flex-direction: row-reverse;
        margin-left: 2rem;
    }

    .message-container.agent-message {
        flex-direction: row;
        margin-right: 2rem;
    }

    .message-bubble {
        padding: 1rem 1.25rem;
        border-radius: var(--radius-lg);
        max-width: 70%;
        word-wrap: break-word;
        position: relative;
        box-shadow: var(--shadow-sm);
    }

    .user-bubble {
        background: var(--primary-color);
        color: white;
        border-bottom-right-radius: 6px;
    }

    .agent-bubble {
        background: var(--surface-color);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-bottom-left-radius: 6px;
    }

    .message-avatar {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
        align-self: flex-start;
        margin-top: 0.5rem;
    }

    .user-avatar {
        background: var(--primary-color);
        color: white;
    }

    .agent-avatar {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        color: var(--text-primary);
    }

    /* Section titles */
    .message-bubble h3,
    .message-bubble strong,
    h3, h4 {
        font-size: 1.25rem !important;
        font-weight: 600;
        color: var(--text-primary);
        margin: 1rem 0 0.5rem 0;
        line-height: 1.3;
    }

    .message-bubble h3:first-child,
    .message-bubble strong:first-child {
        margin-top: 0.5rem;
    }

    /* Welcome message */
    .welcome-message {
        text-align: center;
        padding: 2rem;
        background: var(--surface-color);
        border-radius: var(--radius-lg);
        margin: 2rem auto;
        max-width: 600px;
        border: 1px solid var(--border-color);
    }

    .welcome-message h3 {
        color: var(--text-primary);
        margin-bottom: 1rem;
        font-weight: 600;
    }

    .welcome-message p {
        color: var(--text-secondary);
        margin-bottom: 1rem;
        line-height: 1.6;
    }

    .welcome-message ul {
        text-align: left;
        color: var(--text-secondary);
        margin: 1rem 0;
        padding-left: 1.5rem;
    }

    .welcome-message li {
        margin: 0.5rem 0;
        line-height: 1.5;
    }

    /* === SIDEBAR STYLING === */

    .sidebar-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }

    .sidebar-header h2 {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .sidebar-header p {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin: 0.25rem 0 0 0;
    }

    /* Sidebar section headers */
    .streamlit-expanderHeader {
        font-weight: 700 !important;
        font-size: 17px !important;
        color: #2d3748 !important;
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        margin: 8px 0 !important;
        padding: 12px 16px !important;
    }

    .streamlit-expanderHeader:hover {
        background: #edf2f7 !important;
        border-color: #cbd5e0 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    .streamlit-expanderContent {
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        background: #ffffff !important;
        margin-bottom: 8px !important;
    }

    /* === REGULAR BUTTONS (Non-form) === */

    .stButton > button:not(.login-container .stButton > button):not(.stForm .stButton > button) {
        background: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton > button:not(.login-container .stButton > button):not(.stForm .stButton > button):hover {
        background: var(--primary-hover) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
    }

    /* === SUCCESS/ERROR MESSAGES === */

    .stSuccess {
        background: #f0fdf4 !important;
        border: 1px solid #bbf7d0 !important;
        color: #166534 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 500 !important;
    }

    .stError {
        background: #fef2f2 !important;
        border: 1px solid #fecaca !important;
        color: #dc2626 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 500 !important;
    }

    .stInfo {
        background: #eff6ff !important;
        border: 1px solid #bfdbfe !important;
        color: #1d4ed8 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 500 !important;
    }

    .stWarning {
        background: #fffbeb !important;
        border: 1px solid #fed7aa !important;
        color: #d97706 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 500 !important;
    }

    /* === DOWNLOAD BUTTONS === */

    .stDownloadButton > button {
        background: var(--success-color) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
        margin: 0.25rem 0 !important;
    }

    .stDownloadButton > button:hover {
        background: #38a169 !important;
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
    }

    /* === RESPONSIVE DESIGN === */

    @media (max-width: 768px) {
        .login-container .stTextInput > div > div > input,
        .stForm .stTextInput > div > div > input {
            height: 46px !important;
            font-size: 14px !important;
            padding: 12px 14px !important;
        }

        .login-container .stButton > button,
        .stForm .stButton > button {
            height: 46px !important;
            font-size: 14px !important;
        }

        .main .stTextInput > div > div > input:not(.login-container .stTextInput > div > div > input):not(.stForm .stTextInput > div > div > input) {
            height: 42px !important;
            font-size: 14px !important;
        }

        .main form[data-testid="stForm"]:not(.login-container form):not(.stForm form) .stButton > button {
            height: 42px !important;
            min-height: 42px !important;
            font-size: 13px !important;
            padding: 0 16px !important;
        }

        .message-bubble {
            max-width: 85%;
        }

        .message-container.user-message {
            margin-left: 1rem;
        }

        .message-container.agent-message {
            margin-right: 1rem;
        }

        .login-header h1 {
            font-size: 2.2rem;
        }

        .chat-header h1 {
            font-size: 1.5rem;
        }
    }

    /* === ANIMATIONS === */

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* === SCROLLBAR === */

    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--surface-color);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }

    /* === LAYOUT FIXES === */

    .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: none;
    }

    </style>
    """, unsafe_allow_html=True)