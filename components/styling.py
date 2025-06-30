"""
CSS Styling and Themes for Telmi - FIXED VERSION
Modern, minimalist ChatGPT-like interface styling with better section headers and form fixes
"""

import streamlit as st

def apply_custom_styling():
    """Apply custom CSS styling to the Streamlit app with improved visual hierarchy and fixed forms."""

    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Root variables for consistent theming - ChatGPT-like colors */
    :root {
        --primary-color: #4299e1;
        --primary-hover: #3182ce;
        --primary-light: #63b3ed;
        --secondary-color: #f7fafc;
        --background-color: #ffffff;
        --surface-color: #f7fafc;
        --text-primary: #1a202c;
        --text-secondary: #4a5568;
        --text-muted: #a0aec0;
        --border-color: #e2e8f0;
        --success-color: #48bb78;
        --error-color: #f56565;
        --warning-color: #ed8936;
        --shadow-sm: 0 1px 3px 0 rgb(0 0 0 / 0.1);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
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

    /* === ENHANCED Authentication Page Styling === */

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

    /* Enhanced login container */
    .login-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        margin: 2rem 0;
        backdrop-filter: blur(10px);
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

    /* Fixed input boxes for authentication forms */
    .stForm .stTextInput > div > div > input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        background: #ffffff !important;
        color: #2d3748 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        transition: all 0.2s ease !important;
        height: 48px !important;
        line-height: 1.4 !important;
        text-align: left !important;
        vertical-align: middle !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }

    .stForm .stTextInput > div > div > input:focus {
        border-color: #4299e1 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1) !important;
    }

    .stForm .stTextInput > div > div > input::placeholder {
        color: #a0aec0 !important;
        font-weight: 400 !important;
        opacity: 1 !important;
    }

    /* Remove the "Press Enter to submit" message for auth forms */
    .stForm .stTextInput > div > div > div[data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Hide the show/hide password button for auth forms to prevent overlap */
    .stForm .stTextInput button[kind="tertiary"] {
        display: none !important;
    }

    /* Fixed button styling for authentication forms */
    .stForm button[kind="primary"] {
        background: linear-gradient(135deg, #4299e1, #3182ce) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        height: 48px !important;
        line-height: 48px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3) !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        cursor: pointer !important;
    }

    .stForm button[kind="primary"]:hover {
        background: linear-gradient(135deg, #3182ce, #2c5aa0) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4) !important;
    }

    .stForm button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    /* Ensure button text is white and centered */
    .stForm button[kind="primary"] p {
        color: white !important;
        margin: 0 !important;
        font-weight: 600 !important;
        text-align: center !important;
        line-height: 1 !important;
    }

    /* Fixed form labels */
    .stForm .stTextInput > label {
        font-weight: 600 !important;
        color: #2d3748 !important;
        font-size: 14px !important;
        margin-bottom: 6px !important;
        display: block !important;
    }

    /* === CHAT INTERFACE FIXES === */

    /* Chat input box - different styling, keep "Press Enter" message and show/hide button */
    .main .stForm:not(.stForm .stForm) .stTextInput > div > div > input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        background: #ffffff !important;
        color: #2d3748 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        transition: all 0.2s ease !important;
        height: 44px !important;
        line-height: 1.4 !important;
        text-align: left !important;
        vertical-align: middle !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }

    /* Chat input focus state */
    .main .stForm:not(.stForm .stForm) .stTextInput > div > div > input:focus {
        border-color: #4299e1 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1) !important;
    }

    /* Chat send button - match input height */
    .main .stForm:not(.stForm .stForm) button[kind="primary"] {
        background: #4299e1 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        height: 44px !important;
        line-height: 44px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 4px rgba(66, 153, 225, 0.2) !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        cursor: pointer !important;
    }

    .main .stForm:not(.stForm .stForm) button[kind="primary"]:hover {
        background: #3182ce !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(66, 153, 225, 0.3) !important;
    }

    /* Ensure chat button text is properly styled */
    .main .stForm:not(.stForm .stForm) button[kind="primary"] p {
        color: white !important;
        margin: 0 !important;
        font-weight: 600 !important;
        text-align: center !important;
        line-height: 1 !important;
    }

    /* Keep "Press Enter" message visible for chat input only */
    .main .stForm:not(.stForm .stForm) .stTextInput > div > div > div[data-testid="InputInstructions"] {
        display: block !important;
        font-size: 12px !important;
        color: #718096 !important;
        margin-top: 4px !important;
    }

    /* Allow show/hide password button for chat (though rare) */
    .main .stForm:not(.stForm .stForm) .stTextInput button[kind="tertiary"] {
        display: block !important;
    }

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
        border-bottom-right-radius: var(--radius-sm);
    }

    .agent-bubble {
        background: var(--surface-color);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-bottom-left-radius: var(--radius-sm);
    }

    /* Avatar alignment */
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

    /* IMPROVED: Section titles - BIGGER size for better visual hierarchy */
    .message-bubble h3,
    .message-bubble strong,
    h3, h4, .section-title {
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

    /* Sidebar styling - IMPROVED SECTION HEADERS */
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

    /* IMPROVED: Sidebar section headers - BOLD and BIGGER */
    .streamlit-expanderHeader {
        font-weight: 700 !important;          /* BOLD */
        font-size: 17px !important;           /* BIGGER */
        color: #2d3748 !important;
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        margin: 8px 0 !important;
        padding: 12px 16px !important;        /* More padding for prominence */
        letter-spacing: 0.3px !important;     /* Slight letter spacing */
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

    /* IMPROVED: Stats container - LEFT ALIGNED with better emoji */
    .sidebar-stats-improved {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
        text-align: left !important;
    }

    .stats-text-improved {
        font-size: 13px !important;
        color: #4a5568 !important;
        line-height: 1.4 !important;
        margin: 0 !important;
    }

    .account-section {
        margin: 1rem 0;
    }

    .user-info {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem;
        background: var(--surface-color);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
    }

    .user-avatar {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        background: var(--primary-color);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
    }

    .username {
        font-weight: 500;
        color: var(--text-primary);
    }

    .session-item {
        margin: 0.5rem 0;
    }

    .session-item.current {
        opacity: 0.6;
    }

    .sidebar-footer {
        text-align: center;
        color: var(--text-muted);
        padding: 1rem 0;
    }

    /* === GENERAL FORM IMPROVEMENTS === */

    /* Better spacing between form elements */
    .stForm > div {
        margin-bottom: 16px;
    }

    .stForm > div:last-child {
        margin-bottom: 0;
    }

    /* Improved form section headers */
    .stForm h3 {
        color: #2d3748 !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
        margin-bottom: 8px !important;
        line-height: 1.3 !important;
    }

    .stForm p {
        color: #718096 !important;
        font-size: 1rem !important;
        margin-bottom: 1rem !important;
        line-height: 1.5 !important;
    }

    /* Remove any conflicting styles */
    .stTextInput > div > div {
        border-radius: 0 !important;
        border: none !important;
    }

    /* Ensure consistent button appearance across all forms */
    button[kind="primary"] div p {
        color: white !important;
        font-weight: 600 !important;
    }

    /* Fix any alignment issues with form containers */
    .stForm {
        width: 100%;
    }

    .stForm > div > div {
        width: 100%;
    }

    /* === BUTTON STYLING FIXES === */

    /* Regular buttons (non-form) */
    .stButton > button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
        height: auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .stButton > button:hover {
        background: var(--primary-hover);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    .stButton > button:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }

    /* === OTHER INPUT STYLING === */

    /* General input styling (non-form) */
    .stTextInput > div > div > input {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 0.75rem;
        background: var(--background-color);
        color: var(--text-primary);
        transition: border-color 0.2s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        outline: none;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }

    .stSelectbox > div > div > select {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        background: var(--background-color);
        color: var(--text-primary);
    }

    .stNumberInput > div > div > input {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        background: var(--background-color);
        color: var(--text-primary);
    }

    /* === RESPONSIVE FIXES === */

    /* Mobile responsiveness for forms */
    @media (max-width: 768px) {
        .stForm .stTextInput > div > div > input {
            font-size: 14px !important;
            height: 44px !important;
            padding: 10px 14px !important;
        }

        .stForm button[kind="primary"] {
            height: 44px !important;
            line-height: 44px !important;
            font-size: 14px !important;
        }

        .main .stForm:not(.stForm .stForm) .stTextInput > div > div > input {
            height: 40px !important;
            font-size: 14px !important;
        }

        .main .stForm:not(.stForm .stForm) button[kind="primary"] {
            height: 40px !important;
            line-height: 40px !important;
            font-size: 13px !important;
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px;
            font-size: 14px;
            padding: 0 16px;
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

        .welcome-message {
            margin: 1rem;
            padding: 1.5rem;
        }

        .chat-header h1 {
            font-size: 1.5rem;
        }

        .login-header h1 {
            font-size: 2rem;
        }

        /* IMPROVED: Sidebar section headers on mobile */
        .streamlit-expanderHeader {
            font-size: 15px !important;
            padding: 10px 12px !important;
        }
    }

    /* === SUCCESS/ERROR/INFO MESSAGES === */

    /* Enhanced Success/Error messages for auth */
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

    /* === HELP TEXT AND ANIMATIONS === */

    /* Help text styling */
    .stTextInput div[data-testid="help"] {
        color: #718096 !important;
        font-size: 0.875rem !important;
        margin-top: 0.25rem !important;
    }

    /* Slide up animation */
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

    /* === DOWNLOAD BUTTON STYLING === */

    /* Download button styling - Modern design */
    .stDownloadButton > button {
        background: var(--success-color);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
        margin: 0.25rem 0;
    }

    .stDownloadButton > button:hover {
        background: #38a169;
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }

    /* Secondary download button styling */
    .stDownloadButton > button[kind="secondary"] {
        background: var(--primary-color);
        color: white;
    }

    .stDownloadButton > button[kind="secondary"]:hover {
        background: var(--primary-hover);
    }

    /* === CHART AND TABLE STYLING === */

    /* Chart container styling */
    .chart-container {
        margin: 1rem 0;
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
        max-height: 600px;
    }

    /* Download buttons container */
    .download-buttons-container {
        margin: 1rem 0;
        padding: 1rem;
        background: var(--surface-color);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
    }

    /* Code block styling */
    .stCode {
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 1rem;
    }

    /* Table styling */
    .dataframe {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        overflow: hidden;
    }

    .dataframe th {
        background: var(--surface-color);
        color: var(--text-primary);
        font-weight: 600;
    }

    .dataframe td {
        color: var(--text-primary);
    }

    /* === SCROLLBAR STYLING === */

    /* Custom scrollbar */
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

    /* === STREAMLIT LAYOUT FIXES === */

    /* Hide Streamlit's main menu and footer in the sidebar */
    .css-1d391kg {
        padding-top: 1rem;
    }

    .css-1y4p8pa {
        padding: 1rem;
    }

    /* Ensure the main content area uses full width */
    .block-container {
        padding-top: 0;
        padding-bottom: 0;
        max-width: none;
    }

    </style>
    """, unsafe_allow_html=True)