"""
Modern Sidebar Component
Professional sidebar with chat history, user profile, and navigation
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List
from utils.chat_utils import get_user_chat_sessions, delete_chat_session, create_new_chat_session
from utils.auth_utils import logout_user
from components.profile_components import render_profile_modal


def render_sidebar(current_user: Dict[str, Any]):
    """Render modern sidebar with chat history and user profile"""

    with st.sidebar:
        # User profile section
        render_user_profile_section(current_user)

        # Chat management section
        render_chat_management()

        # Chat history section
        render_chat_history_section(current_user['username'])

        # Settings and help section
        render_settings_section()



def render_user_profile_section(current_user: Dict[str, Any]):
    """Render user profile section with modern design"""

    st.markdown("""
    <div class="profile-section">
        <div class="profile-header">
            <div class="profile-avatar">👤</div>
            <div class="profile-info">
                <div class="profile-name">""" + current_user['full_name'] + """</div>
                <div class="profile-email">""" + current_user['email'] + """</div>
            </div>
        </div>
    </div>
        <style>
       .profile-section {
           background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
           border-radius: 16px;
           padding: 20px;
           margin-bottom: 20px;
           color: white;
           box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
       }
       
       .profile-header {
           display: flex;
           align-items: center;
           gap: 15px;
       }
       
       .profile-avatar {
           width: 50px;
           height: 50px;
           background: rgba(255, 255, 255, 0.2);
           border-radius: 50%;
           display: flex;
           align-items: center;
           justify-content: center;
           font-size: 1.5rem;
           backdrop-filter: blur(10px);
       }
       
       .profile-info {
           flex: 1;
       }
       
       .profile-name {
           font-weight: 600;
           font-size: 1.1rem;
           margin-bottom: 2px;
       }
       
       .profile-email {
           font-size: 0.85rem;
           opacity: 0.9;
       }
       </style>
       """, unsafe_allow_html=True)

   # Profile actions
   col1, col2 = st.columns(2)

   with col1:
       if st.button("⚙️ Profile", use_container_width=True, key="profile_btn"):
           st.session_state.show_profile_modal = True

   with col2:
       if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
           logout_user()
           st.rerun()

   # Profile modal
   if st.session_state.get('show_profile_modal', False):
       render_profile_modal(current_user)

def render_chat_management():
   """Render chat management controls"""

   st.markdown("""
   <div class="section-header">
       <h3>💬 Chat Management</h3>
   </div>
   """, unsafe_allow_html=True)

   # New chat button
   if st.button("✨ New Chat", use_container_width=True, key="new_chat_btn"):
       username = st.session_state.get('current_user', {}).get('username', '')
       if username:
           create_new_chat_session(username)
           st.rerun()

   st.markdown("<br>", unsafe_allow_html=True)

def render_chat_history_section(username: str):
   """Render chat history section with sessions"""

   st.markdown("""
   <div class="section-header">
       <h3>📚 Chat History</h3>
   </div>
   """, unsafe_allow_html=True)

   # Get chat sessions
   chat_sessions = get_user_chat_sessions(username)

   if not chat_sessions:
       st.markdown("""
       <div class="empty-state">
           <div class="empty-icon">💬</div>
           <div class="empty-text">No chat history yet</div>
           <div class="empty-subtext">Start a conversation to see your chat history here</div>
       </div>
       """, unsafe_allow_html=True)
       return

   # Group sessions by date
   sessions_by_date = group_sessions_by_date(chat_sessions)

   # Current session ID
   current_session = st.session_state.get('current_chat_session', '')

   for date_label, sessions in sessions_by_date.items():
       st.markdown(f"""
       <div class="date-group">
           <div class="date-label">{date_label}</div>
       </div>
       """, unsafe_allow_html=True)

       for session in sessions:
           render_chat_session_item(session, current_session)

def render_chat_session_item(session: Dict[str, Any], current_session: str):
   """Render individual chat session item"""

   session_id = session['session_id']
   title = session.get('title', 'Untitled Chat')
   last_message = session.get('last_message', '')
   message_count = session.get('message_count', 0)
   created_at = datetime.fromisoformat(session['created_at'])

   # Truncate title and last message
   display_title = title[:30] + "..." if len(title) > 30 else title
   display_message = last_message[:40] + "..." if len(last_message) > 40 else last_message

   # Check if this is the current session
   is_current = session_id == current_session
   session_class = "session-item current" if is_current else "session-item"

   # Session item HTML
   st.markdown(f"""
   <div class="{session_class}" onclick="selectSession('{session_id}')">
       <div class="session-content">
           <div class="session-title">{display_title}</div>
           <div class="session-preview">{display_message}</div>
           <div class="session-meta">
               <span class="message-count">{message_count} messages</span>
               <span class="session-time">{created_at.strftime('%H:%M')}</span>
           </div>
       </div>
       <div class="session-actions">
           <button class="session-action" onclick="deleteSession('{session_id}')" title="Delete">🗑️</button>
       </div>
   </div>
   """, unsafe_allow_html=True)

   # Handle session selection
   if st.button(f"Select", key=f"select_{session_id}", help=f"Switch to {display_title}"):
       st.session_state.current_chat_session = session_id
       st.rerun()

def group_sessions_by_date(sessions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
   """Group chat sessions by date"""

   grouped = {}
   today = datetime.now().date()
   yesterday = today - timedelta(days=1)

   for session in sessions:
       created_at = datetime.fromisoformat(session['created_at']).date()

       if created_at == today:
           date_label = "Today"
       elif created_at == yesterday:
           date_label = "Yesterday"
       elif created_at >= today - timedelta(days=7):
           date_label = "This Week"
       elif created_at >= today - timedelta(days=30):
           date_label = "This Month"
       else:
           date_label = created_at.strftime("%B %Y")

       if date_label not in grouped:
           grouped[date_label] = []
       grouped[date_label].append(session)

   return grouped

def render_settings_section():
   """Render settings and help section"""

   st.markdown("""
   <div class="section-header">
       <h3>⚙️ Settings & Help</h3>
   </div>
   """, unsafe_allow_html=True)

   # Settings options
   with st.expander("🎨 Theme Settings"):
       theme = st.selectbox(
           "Color Theme",
           ["Professional Blue", "Dark Mode", "Light Mode", "Custom"],
           key="theme_setting"
       )

       if theme == "Custom":
           primary_color = st.color_picker("Primary Color", "#667eea")
           secondary_color = st.color_picker("Secondary Color", "#764ba2")

   with st.expander("📊 Data Settings"):
       default_limit = st.number_input(
           "Default Query Limit",
           min_value=10,
           max_value=10000,
           value=1000,
           key="default_limit"
       )

       auto_visualize = st.checkbox(
           "Auto-generate visualizations",
           value=True,
           key="auto_visualize"
       )

       export_format = st.selectbox(
           "Default Export Format",
           ["CSV", "Excel", "JSON"],
           key="export_format"
       )

   with st.expander("❓ Help & Support"):
       st.markdown("""
       **Quick Tips:**
       - Type natural language questions about your data
       - Use specific time periods for better results
       - Ask for "top N" lists for rankings
       - Request charts for visual insights
       
       **Examples:**
       - "Show customer data usage by country"
       - "Top 10 customers by revenue last month"
       - "Geographic distribution chart"
       
       **Need Help?**
       Contact support at: support@telmi.ai
       """)

       if st.button("📖 User Guide", use_container_width=True):
           st.info("User guide will open in a new tab")

       if st.button("🐛 Report Issue", use_container_width=True):
           st.info("Issue reporting form will open")

# Additional CSS for sidebar styling
st.markdown("""
<style>
.section-header {
   margin: 20px 0 15px 0;
   padding-bottom: 8px;
   border-bottom: 2px solid #f1f5f9;
}

.section-header h3 {
   color: #1e293b;
   font-size: 1rem;
   font-weight: 600;
   margin: 0;
}

.empty-state {
   text-align: center;
   padding: 30px 20px;
   color: #64748b;
}

.empty-icon {
   font-size: 2rem;
   margin-bottom: 10px;
   opacity: 0.6;
}

.empty-text {
   font-weight: 500;
   margin-bottom: 5px;
}

.empty-subtext {
   font-size: 0.85rem;
   opacity: 0.8;
}

.date-group {
   margin: 15px 0 10px 0;
}

.date-label {
   font-size: 0.85rem;
   font-weight: 600;
   color: #667eea;
   text-transform: uppercase;
   letter-spacing: 0.5px;
}

.session-item {
   background: white;
   border: 1px solid #e2e8f0;
   border-radius: 12px;
   margin-bottom: 8px;
   padding: 12px;
   cursor: pointer;
   transition: all 0.2s ease;
   display: flex;
   align-items: center;
   justify-content: space-between;
}

.session-item:hover {
   background: #f8fafc;
   border-color: #667eea;
   transform: translateX(2px);
}

.session-item.current {
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   color: white;
   border-color: #667eea;
}

.session-content {
   flex: 1;
}

.session-title {
   font-weight: 600;
   font-size: 0.9rem;
   margin-bottom: 4px;
}

.session-preview {
   font-size: 0.8rem;
   opacity: 0.8;
   margin-bottom: 6px;
   line-height: 1.3;
}

.session-meta {
   display: flex;
   justify-content: space-between;
   align-items: center;
   font-size: 0.75rem;
   opacity: 0.7;
}

.session-actions {
   display: flex;
   gap: 4px;
}

.session-action {
   background: none;
   border: none;
   cursor: pointer;
   font-size: 0.9rem;
   opacity: 0.6;
   transition: opacity 0.2s ease;
}

.session-action:hover {
   opacity: 1;
}
</style>

<script>
function selectSession(sessionId) {
   // Handle session selection via Streamlit
   console.log('Selected session:', sessionId);
}

function deleteSession(sessionId) {
   if (confirm('Are you sure you want to delete this chat session?')) {
       // Handle session deletion via Streamlit
       console.log('Delete session:', sessionId);
   }
}
</script>
""", unsafe_allow_html=True)
