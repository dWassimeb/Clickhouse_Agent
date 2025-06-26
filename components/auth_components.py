"""
Modern Authentication Components
Beautiful login/register forms with professional design
"""
import streamlit as st
import re
from typing import Optional, Dict, Any
from utils.auth_utils import authenticate_user, register_user, validate_email, validate_password


def render_auth_page():
    """Render the main authentication page with modern design"""

    # Create centered layout
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # App branding
        st.markdown("""
        <div class="auth-container">
            <div class="auth-header">
                <div class="auth-logo">🤖</div>
                <h1 class="auth-title">Welcome to Telmi</h1>
                <p class="auth-subtitle">Your AI-powered Telecom Analytics Assistant</p>
            </div>
        """, unsafe_allow_html=True)

        # Auth tabs
        tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])

        with tab1:
            render_login_form()

        with tab2:
            render_register_form()

        st.markdown('</div>', unsafe_allow_html=True)

        # Add authentication styling
        add_auth_styling()


def render_login_form():
    """Render modern login form"""

    st.markdown('<div class="auth-form">', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        st.markdown("### Sign in to your account")

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            remember_me = st.checkbox("Remember me", key="remember_me")

        with col2:
            # Display forgot password as text since we can't use button in form
            st.markdown('<p style="text-align: right; color: #667eea; font-size: 0.9rem; margin-top: 1rem;">Forgot password?</p>', unsafe_allow_html=True)

        submit_button = st.form_submit_button(
            "🚀 Sign In",
            use_container_width=True
        )

        if submit_button:
            handle_login(email, password, remember_me)

    # Forgot password button outside the form
    if st.button("🔑 Reset Password", help="Reset your password", key="forgot_password_outside"):
        st.info("Password reset functionality will be implemented soon. Please contact support.")

    st.markdown('</div>', unsafe_allow_html=True)


def render_register_form():
    """Render modern registration form"""

    st.markdown('<div class="auth-form">', unsafe_allow_html=True)

    with st.form("register_form", clear_on_submit=False):
        st.markdown("### Create your account")

        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input(
                "First Name",
                placeholder="First name",
                key="register_first_name"
            )

        with col2:
            last_name = st.text_input(
                "Last Name",
                placeholder="Last name",
                key="register_last_name"
            )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address",
            key="register_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a strong password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password",
            key="register_confirm_password"
        )

        # Terms and conditions
        terms_agreed = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            key="terms_agreed"
        )

        submit_button = st.form_submit_button(
            "✨ Create Account",
            use_container_width=True
        )

        if submit_button:
            handle_registration(
                first_name, last_name, email,
                password, confirm_password, terms_agreed
            )

    st.markdown('</div>', unsafe_allow_html=True)


def handle_login(email: str, password: str, remember_me: bool):
    """Handle user login"""

    # Validation
    if not email or not password:
        st.error("Please fill in all fields")
        return

    if not validate_email(email):
        st.error("Please enter a valid email address")
        return

    # Attempt authentication
    user = authenticate_user(email, password)

    if user:
        st.session_state.authentication_status = True
        st.session_state.current_user = user

        if remember_me:
            st.session_state.remember_user = True

        st.success("Login successful! Welcome back.")
        st.rerun()
    else:
        st.error("Invalid email or password. Please try again.")


def handle_registration(first_name: str, last_name: str, email: str, password: str, confirm_password: str, terms_agreed: bool):
    """Handle user registration"""

    # Validation
    errors = []

    if not all([first_name, last_name, email, password, confirm_password]):
        errors.append("Please fill in all fields")

    if not validate_email(email):
        errors.append("Please enter a valid email address")

    if not validate_password(password):
        errors.append("Password must be at least 8 characters long and contain uppercase, lowercase, and numbers")

    if password != confirm_password:
        errors.append("Passwords do not match")

    if not terms_agreed:
        errors.append("Please agree to the Terms of Service and Privacy Policy")

    if errors:
        for error in errors:
            st.error(error)
        return

    # Attempt registration
    success, message = register_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    if success:
        st.success("Account created successfully! Please sign in.")
        st.balloons()
    else:
        st.error(f"Registration failed: {message}")


def add_auth_styling():
    """Add custom CSS for authentication components"""

    st.markdown("""
    <style>
    .auth-container {
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(20px);
        margin: 40px 0;
    }

    .auth-header {
        text-align: center;
        margin-bottom: 40px;
    }

    .auth-logo {
        font-size: 4rem;
        margin-bottom: 20px;
        display: block;
    }

    .auth-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }

    .auth-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 400;
        margin-bottom: 0;
    }

    .auth-form {
        margin-top: 20px;
    }

    .auth-form h3 {
        color: #1e293b;
        font-weight: 600;
        margin-bottom: 25px;
        text-align: center;
    }

    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 12px 16px;
        font-size: 1rem;
        transition: all 0.3s ease;
        background: white;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }

    /* Checkbox styling */
    .stCheckbox {
        margin: 15px 0;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background: transparent;
        border-bottom: 2px solid #f1f5f9;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        padding: 12px 24px;
        color: #64748b;
        font-weight: 500;
        border-radius: 8px 8px 0 0;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    /* Form styling */
    .stForm {
        background: transparent;
        border: none;
        padding: 0;
    }

    /* Form submit button styling */
    .stForm button[kind="formSubmit"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        width: 100% !important;
    }

    .stForm button[kind="formSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }

    /* Regular button styling for buttons outside forms */
    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
        font-size: 0.9rem;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }

    /* Error and success message styling */
    .stAlert {
        border-radius: 12px;
        border: none;
        padding: 15px 20px;
        margin: 15px 0;
    }

    .stAlert[data-baseweb="notification"] {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #dc2626;
    }

    .stSuccess {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        color: #16a34a;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .auth-container {
            margin: 20px 0;
            padding: 30px 20px;
        }

        .auth-title {
            font-size: 2rem;
        }

        .auth-subtitle {
            font-size: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)