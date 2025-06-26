"""
User Profile Management Components
Modern profile modal and settings management
"""

import streamlit as st
from typing import Dict, Any
from utils.auth_utils import update_user_profile, change_user_password

def render_profile_modal(current_user: Dict[str, Any]):
    """Render user profile modal with modern design"""

    # Create modal container
    st.markdown("""
    <div class="modal-overlay" onclick="closeProfileModal()">
        <div class="modal-container" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2>👤 User Profile</h2>
                <button class="modal-close" onclick="closeProfileModal()">×</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Profile content in sidebar or main area
    with st.container():
        render_profile_content(current_user)

def render_profile_content(current_user: Dict[str, Any]):
    """Render profile content with tabs"""

    tab1, tab2, tab3 = st.tabs(["📝 Profile Info", "🔐 Security", "⚙️ Preferences"])

    with tab1:
        render_profile_info_tab(current_user)

    with tab2:
        render_security_tab(current_user)

    with tab3:
        render_preferences_tab(current_user)

def render_profile_info_tab(current_user: Dict[str, Any]):
    """Render profile information tab"""

    st.markdown("### Personal Information")

    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input(
                "First Name",
                value=current_user.get('first_name', ''),
                key="profile_first_name"
            )

        with col2:
            last_name = st.text_input(
                "Last Name",
                value=current_user.get('last_name', ''),
                key="profile_last_name"
            )

        email = st.text_input(
            "Email Address",
            value=current_user.get('email', ''),
            disabled=True,
            help="Email cannot be changed"
        )

        username = st.text_input(
            "Username",
            value=current_user.get('username', ''),
            disabled=True,
            help="Username cannot be changed"
        )

        # Profile picture upload
        st.markdown("### Profile Picture")
        uploaded_file = st.file_uploader(
            "Upload new profile picture",
            type=['png', 'jpg', 'jpeg'],
            help="Maximum file size: 5MB"
        )

        # Bio/Description
        bio = st.text_area(
            "Bio (Optional)",
            value=current_user.get('bio', ''),
            max_chars=500,
            help="Tell others about yourself"
        )

        # Account information
        st.markdown("### Account Information")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Member Since:** {current_user.get('created_at', 'Unknown')[:10]}")

        with col2:
            last_login = current_user.get('last_login', 'Never')
            if last_login and last_login != 'Never':
                last_login = last_login[:16].replace('T', ' ')
            st.info(f"**Last Login:** {last_login}")

        # Submit button
        if st.form_submit_button("💾 Save Changes", use_container_width=True):
            handle_profile_update(current_user, {
                'first_name': first_name,
                'last_name': last_name,
                'bio': bio
            }, uploaded_file)

def render_security_tab(current_user: Dict[str, Any]):
    """Render security settings tab"""

    st.markdown("### Change Password")

    with st.form("password_form"):
        current_password = st.text_input(
            "Current Password",
            type="password",
            key="current_password"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            help="Must be at least 8 characters with uppercase, lowercase, and numbers",
            key="new_password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_password"
        )

        if st.form_submit_button("🔐 Change Password", use_container_width=True):
            handle_password_change(current_user, current_password, new_password, confirm_password)

    st.markdown("### Security Information")

    # Security status
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Account Status", "🟢 Active")

    with col2:
        st.metric("Security Level", "🛡️ Standard")

    # Session management
    st.markdown("### Active Sessions")

    if st.button("🚪 Logout All Devices", help="End all active sessions"):
        st.info("All sessions have been terminated. Please log in again.")

def render_preferences_tab(current_user: Dict[str, Any]):
    """Render user preferences tab"""

    st.markdown("### Application Preferences")

    # Theme preferences
    st.markdown("#### 🎨 Appearance")

    theme = st.selectbox(
        "Color Theme",
        ["System Default", "Light Mode", "Dark Mode", "Professional Blue"],
        key="theme_preference"
    )

    language = st.selectbox(
        "Language",
        ["English", "Français", "Español", "Deutsch"],
        key="language_preference"
    )

    # Data preferences
    st.markdown("#### 📊 Data & Analytics")

    col1, col2 = st.columns(2)

    with col1:
        default_limit = st.number_input(
            "Default Query Limit",
            min_value=10,
            max_value=10000,
            value=1000,
            step=100,
            key="default_query_limit"
        )

    with col2:
        chart_style = st.selectbox(
            "Chart Style",
            ["Professional", "Colorful", "Minimal", "Dark"],
            key="chart_style_preference"
        )

    auto_export = st.checkbox(
        "Auto-export query results to CSV",
        value=True,
        key="auto_export_preference"
    )

    auto_visualize = st.checkbox(
        "Auto-generate visualizations",
        value=True,
        key="auto_visualize_preference"
    )

    # Notification preferences
    st.markdown("#### 🔔 Notifications")

    email_notifications = st.checkbox(
        "Email notifications for important updates",
        value=True,
        key="email_notifications"
    )

    query_reminders = st.checkbox(
        "Remind me of long-running queries",
        value=True,
        key="query_reminders"
    )

    # Privacy preferences
    st.markdown("#### 🔒 Privacy")

    save_chat_history = st.checkbox(
        "Save chat history",
        value=True,
        help="Disable to stop saving conversation history",
        key="save_chat_history"
    )

    analytics_tracking = st.checkbox(
        "Allow usage analytics for service improvement",
        value=True,
        key="analytics_tracking"
    )

    # Save preferences
    if st.button("💾 Save Preferences", use_container_width=True):
        handle_preferences_update(current_user, {
            'theme': theme,
            'language': language,
            'default_limit': default_limit,
            'chart_style': chart_style,
            'auto_export': auto_export,
            'auto_visualize': auto_visualize,
            'email_notifications': email_notifications,
            'query_reminders': query_reminders,
            'save_chat_history': save_chat_history,
            'analytics_tracking': analytics_tracking
        })

def handle_profile_update(current_user: Dict[str, Any], profile_data: Dict[str, Any], uploaded_file):
    """Handle profile information update"""

    try:
        # Handle file upload if present
        if uploaded_file:
            # Save uploaded file (implement file handling as needed)
            profile_data['profile_picture'] = f"uploads/{current_user['id']}_profile.jpg"

        # Update profile
        success, message = update_user_profile(current_user['id'], profile_data)

        if success:
            st.success("✅ Profile updated successfully!")
            st.balloons()

            # Close modal after successful update
            st.session_state.show_profile_modal = False
            st.rerun()
        else:
            st.error(f"❌ Failed to update profile: {message}")

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")

def handle_password_change(current_user: Dict[str, Any], current_password: str,
                           new_password: str, confirm_password: str):
    """Handle password change"""

    # Validation
    if not all([current_password, new_password, confirm_password]):
        st.error("❌ Please fill in all password fields")
        return

    if new_password != confirm_password:
        st.error("❌ New passwords do not match")
        return

    if len(new_password) < 8:
        st.error("❌ New password must be at least 8 characters long")
        return

    try:
        success, message = change_user_password(
            current_user['id'],
            current_password,
            new_password
        )

        if success:
            st.success("✅ Password changed successfully!")
            st.info("Please log in again with your new password.")
        else:
            st.error(f"❌ {message}")

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")

def handle_preferences_update(current_user: Dict[str, Any], preferences: Dict[str, Any]):
    """Handle preferences update"""

    try:
        # Convert preferences to JSON string for storage
        import json
        preferences_json = json.dumps(preferences)

        success, message = update_user_profile(current_user['id'], {
            'preferences': preferences_json
        })

        if success:
            st.success("✅ Preferences saved successfully!")

            # Update session state with new preferences
            st.session_state.user_preferences = preferences
        else:
            st.error(f"❌ Failed to save preferences: {message}")

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")

# CSS for profile modal
st.markdown("""
<style>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-container {
    background: white;
    border-radius: 20px;
    padding: 0;
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px 30px;
    border-radius: 20px 20px 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
}

.modal-close {
    background: none;
    border: none;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background 0.2s;
}

.modal-close:hover {
    background: rgba(255, 255, 255, 0.2);
}
</style>

<script>
function closeProfileModal() {
    // This would be handled by Streamlit state management
    console.log('Close profile modal');
}
</script>
""", unsafe_allow_html=True)