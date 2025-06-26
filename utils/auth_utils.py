"""
Authentication utilities for user management and session handling
"""
import streamlit as st
import hashlib
import re
import uuid
from typing import Optional, Dict, Any, Tuple
from database.users.user_db import UserDatabase


## Initialize user database

user_db = UserDatabase()


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with email and password"""

    try:
        # Hash the password
        password_hash = hash_password(password)

        # Check credentials in database
        user = user_db.get_user_by_email(email)

        if user and user['password_hash'] == password_hash:
            # Update last login
            user_db.update_last_login(user['id'])

            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': f"{user['first_name']} {user['last_name']}",
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'created_at': user['created_at'],
                'last_login': user['last_login']
            }

        return None

    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None



def register_user(email: str, password: str, first_name: str, last_name: str) -> Tuple[bool, str]:
    """Register a new user"""

    try:
        # Check if user already exists
        existing_user = user_db.get_user_by_email(email)
        if existing_user:
            return False, "A user with this email already exists"

        # Generate username from email
        username = email.split('@')[0]
        base_username = username
        counter = 1

        # Ensure username is unique
        while user_db.get_user_by_username(username):
            username = f"{base_username}{counter}"
            counter += 1

        # Hash password
        password_hash = hash_password(password)

        # Create user
        user_id = user_db.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name
        )

        if user_id:
            return True, "User registered successfully"
        else:
            return False, "Failed to create user account"

    except Exception as e:
        return False, f"Registration error: {str(e)}"



def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False

    # Check for uppercase, lowercase, and numbers
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    return has_upper and has_lower and has_digit


def check_authentication() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authentication_status', False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user"""
    return st.session_state.get('current_user', None)


def logout_user():
    """Logout current user"""
    st.session_state.authentication_status = False
    st.session_state.current_user = None

    # Clear other session data
    for key in list(st.session_state.keys()):
        if key.startswith('chat_') or key in ['current_chat_session', 'show_profile_modal']:
            del st.session_state[key]


def generate_session_token() -> str:
    """Generate a unique session token"""
    return str(uuid.uuid4())


def is_admin_user(user: Dict[str, Any]) -> bool:
    """Check if user has admin privileges"""
    # For now, simple email-based admin check
    admin_emails = ['admin@telmi.ai', 'support@telmi.ai']
    return user.get('email', '') in admin_emails


def get_user_permissions(user: Dict[str, Any]) -> Dict[str, bool]:
    """Get user permissions"""
    is_admin = is_admin_user(user)

    return {
        'can_export_data': True,
        'can_view_visualizations': True,
        'can_access_all_tables': is_admin,
        'can_manage_users': is_admin,
        'can_modify_settings': is_admin,
        'max_query_limit': 10000 if is_admin else 1000
    }


def update_user_profile(user_id: int, profile_data: Dict[str, Any]) -> Tuple[bool, str]:
    """Update user profile information"""

    try:
        success = user_db.update_user_profile(user_id, profile_data)

        if success:
            # Update session data
            current_user = st.session_state.get('current_user', {})
            current_user.update(profile_data)
            st.session_state.current_user = current_user

            return True, "Profile updated successfully"
        else:
            return False, "Failed to update profile"

    except Exception as e:
        return False, f"Update error: {str(e)}"



def change_user_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Change user password"""

    try:
        # Verify old password
        user = user_db.get_user_by_id(user_id)
        if not user:
            return False, "User not found"

        old_password_hash = hash_password(old_password)
        if user['password_hash'] != old_password_hash:
            return False, "Current password is incorrect"

        # Validate new password
        if not validate_password(new_password):
            return False, "New password does not meet requirements"

        # Update password
        new_password_hash = hash_password(new_password)
        success = user_db.update_user_password(user_id, new_password_hash)

        if success:
            return True, "Password changed successfully"
        else:
            return False, "Failed to change password"

    except Exception as e:
        return False, f"Password change error: {str(e)}"





