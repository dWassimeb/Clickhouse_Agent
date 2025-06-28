"""
CSS Styling and Themes for Telmi
Modern, minimalist ChatGPT-like interface styling
"""

import streamlit as st

def apply_custom_styling():
    """Apply custom CSS styling to the Streamlit app."""

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
    
    /* Login container */
    .login-container {
        background: var(--background-color);
        border-radius: var(--radius-lg);
        padding: 2rem;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
        margin: 2rem 0;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .login-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
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
    
    .message-avatar {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
    }
    
    .user-avatar {
        background: var(--primary-color);
        color: white;
    }
    
    .agent-avatar {
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
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
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 1rem 0;
        padding: 1rem;
        background: var(--surface-color);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
        max-width: 200px;
    }
    
    .typing-dots {
        display: flex;
        gap: 0.25rem;
    }
    
    .typing-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
        animation: typing 1.4s infinite;
    }
    
    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
        }
        30% {
            transform: translateY(-10px);
        }
    }
    
    .typing-text {
        color: var(--text-muted);
        font-size: 0.9rem;
    }
    
    /* Sidebar styling */
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
    
    .sidebar-stats {
        text-align: center;
        padding: 1rem;
        background: var(--surface-color);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
        margin: 1rem 0;
    }
    
    .sidebar-footer {
        text-align: center;
        color: var(--text-muted);
        padding: 1rem 0;
    }
    
    /* Button styling */
    .stButton > button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
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
    
    /* Form styling */
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
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: var(--surface-color);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        color: var(--text-primary);
    }
    
    .streamlit-expanderContent {
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 var(--radius-md) var(--radius-md);
        background: var(--background-color);
    }
    
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
    
    /* Chart container styling */
    .chart-container {
        margin: 1rem 0;
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
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
    
    /* Success/Error messages */
    .stSuccess {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        border-radius: var(--radius-md);
    }
    
    .stError {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #dc2626;
        border-radius: var(--radius-md);
    }
    
    .stInfo {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        border-radius: var(--radius-md);
    }
    
    .stWarning {
        background: #fffbeb;
        border: 1px solid #fed7aa;
        color: #d97706;
        border-radius: var(--radius-md);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
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
    }
    
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