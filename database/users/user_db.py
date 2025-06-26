"""
User database management using SQLite
Handles user accounts, authentication, and chat history
"""


import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
from config.settings import USER_DATABASE_CONFIG


class UserDatabase:
    """User database management class"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or USER_DATABASE_CONFIG["users_db_path"]
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database tables"""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    profile_picture TEXT,
                    preferences TEXT
                )
            """)

            # Chat sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Chat messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attachments TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
                )
            """)

            # User activity log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_type TEXT NOT NULL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            conn.commit()

   def create_user(self, username: str, email: str, password_hash: str,
                  first_name: str, last_name: str) -> Optional[int]:
       """Create a new user"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               cursor.execute("""
                   INSERT INTO users (username, email, password_hash, first_name, last_name)
                   VALUES (?, ?, ?, ?, ?)
               """, (username, email, password_hash, first_name, last_name))

               user_id = cursor.lastrowid

               # Log user creation
               self.log_user_activity(user_id, "user_registered", "User account created")

               conn.commit()
               return user_id

       except sqlite3.IntegrityError:
           return None
       except Exception as e:
           print(f"Error creating user: {e}")
           return None

   def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
       """Get user by email"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               conn.row_factory = sqlite3.Row
               cursor = conn.cursor()

               cursor.execute("""
                   SELECT * FROM users WHERE email = ? AND is_active = 1
               """, (email,))

               row = cursor.fetchone()
               return dict(row) if row else None

       except Exception as e:
           print(f"Error getting user by email: {e}")
           return None

   def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
       """Get user by username"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               conn.row_factory = sqlite3.Row
               cursor = conn.cursor()

               cursor.execute("""
                   SELECT * FROM users WHERE username = ? AND is_active = 1
               """, (username,))

               row = cursor.fetchone()
               return dict(row) if row else None

       except Exception as e:
           print(f"Error getting user by username: {e}")
           return None

   def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
       """Get user by ID"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               conn.row_factory = sqlite3.Row
               cursor = conn.cursor()

               cursor.execute("""
                   SELECT * FROM users WHERE id = ? AND is_active = 1
               """, (user_id,))

               row = cursor.fetchone()
               return dict(row) if row else None

       except Exception as e:
           print(f"Error getting user by ID: {e}")
           return None

   def update_last_login(self, user_id: int) -> bool:
       """Update user's last login timestamp"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               cursor.execute("""
                   UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
               """, (user_id,))

               # Log login activity
               self.log_user_activity(user_id, "user_login", "User logged in")

               conn.commit()
               return True

       except Exception as e:
           print(f"Error updating last login: {e}")
           return False

   def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
       """Update user profile information"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               # Build dynamic update query
               fields = []
               values = []

               allowed_fields = ['first_name', 'last_name', 'profile_picture', 'preferences']

               for field, value in profile_data.items():
                   if field in allowed_fields:
                       fields.append(f"{field} = ?")
                       values.append(value)

               if not fields:
                   return False

               values.append(user_id)

               query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
               cursor.execute(query, values)

               # Log profile update
               self.log_user_activity(user_id, "profile_updated", "User profile updated")

               conn.commit()
               return True

       except Exception as e:
           print(f"Error updating user profile: {e}")
           return False

   def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
       """Update user password"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               cursor.execute("""
                   UPDATE users SET password_hash = ? WHERE id = ?
               """, (new_password_hash, user_id))

               # Log password change
               self.log_user_activity(user_id, "password_changed", "User changed password")

               conn.commit()
               return True

       except Exception as e:
           print(f"Error updating password: {e}")
           return False

   def create_chat_session(self, user_id: int, title: str = None) -> str:
       """Create a new chat session"""

       try:
           session_id = str(uuid.uuid4())

           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               cursor.execute("""
                   INSERT INTO chat_sessions (session_id, user_id, title)
                   VALUES (?, ?, ?)
               """, (session_id, user_id, title or "New Chat"))

               # Log session creation
               self.log_user_activity(user_id, "chat_session_created", f"New chat session: {session_id}")

               conn.commit()
               return session_id

       except Exception as e:
           print(f"Error creating chat session: {e}")
           return None

   def get_user_chat_sessions(self, user_id: int) -> List[Dict[str, Any]]:
       """Get all chat sessions for a user"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               conn.row_factory = sqlite3.Row
               cursor = conn.cursor()

               cursor.execute("""
                   SELECT 
                       cs.*,
                       COUNT(cm.id) as message_count,
                       (SELECT cm2.content FROM chat_messages cm2 
                        WHERE cm2.session_id = cs.session_id 
                        ORDER BY cm2.timestamp DESC LIMIT 1) as last_message
                   FROM chat_sessions cs
                   LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                   WHERE cs.user_id = ? AND cs.is_active = 1
                   GROUP BY cs.id
                   ORDER BY cs.updated_at DESC
               """, (user_id,))

               rows = cursor.fetchall()
               return [dict(row) for row in rows]

       except Exception as e:
           print(f"Error getting chat sessions: {e}")
           return []

   def add_chat_message(self, session_id: str, role: str, content: str,
                       attachments: str = None) -> bool:
       """Add a message to a chat session"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               # Add message
               cursor.execute("""
                   INSERT INTO chat_messages (session_id, role, content, attachments)
                   VALUES (?, ?, ?, ?)
               """, (session_id, role, content, attachments))

               # Update session timestamp
               cursor.execute("""
                   UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP 
                   WHERE session_id = ?
               """, (session_id,))

               conn.commit()
               return True

       except Exception as e:
           print(f"Error adding chat message: {e}")
           return False

   def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
       """Get all messages for a chat session"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               conn.row_factory = sqlite3.Row
               cursor = conn.cursor()

               cursor.execute("""
                   SELECT * FROM chat_messages 
                   WHERE session_id = ? 
                   ORDER BY timestamp ASC
               """, (session_id,))

               rows = cursor.fetchall()
               return [dict(row) for row in rows]

       except Exception as e:
           print(f"Error getting chat messages: {e}")
           return []

   def delete_chat_session(self, session_id: str, user_id: int) -> bool:
       """Delete a chat session (soft delete)"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               # Verify ownership
               cursor.execute("""
                   SELECT user_id FROM chat_sessions WHERE session_id = ?
               """, (session_id,))

               row = cursor.fetchone()
               if not row or row[0] != user_id:
                   return False

               # Soft delete
               cursor.execute("""
                   UPDATE chat_sessions SET is_active = 0 WHERE session_id = ?
               """, (session_id,))

               # Log deletion
               self.log_user_activity(user_id, "chat_session_deleted", f"Deleted chat session: {session_id}")

               conn.commit()
               return True

       except Exception as e:
           print(f"Error deleting chat session: {e}")
           return False

   def update_chat_session_title(self, session_id: str, title: str, user_id: int) -> bool:
       """Update chat session title"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               cursor.execute("""
                   UPDATE chat_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE session_id = ? AND user_id = ?
               """, (title, session_id, user_id))

               conn.commit()
               return cursor.rowcount > 0

       except Exception as e:
           print(f"Error updating chat session title: {e}")
           return False

   def log_user_activity(self, user_id: int, activity_type: str,
                        description: str, metadata: str = None) -> bool:
       """Log user activity"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               cursor.execute("""
                   INSERT INTO user_activity (user_id, activity_type, description, metadata)
                   VALUES (?, ?, ?, ?)
               """, (user_id, activity_type, description, metadata))

               conn.commit()
               return True

       except Exception as e:
           print(f"Error logging user activity: {e}")
           return False

   def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
       """Get user activity log"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               conn.row_factory = sqlite3.Row
               cursor = conn.cursor()

               cursor.execute("""
                   SELECT * FROM user_activity 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?
               """, (user_id, limit))

               rows = cursor.fetchall()
               return [dict(row) for row in rows]

       except Exception as e:
           print(f"Error getting user activity: {e}")
           return []

   def cleanup_old_sessions(self, days: int = 30) -> int:
       """Clean up old inactive chat sessions"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               # Delete old inactive sessions
               cursor.execute("""
                   DELETE FROM chat_sessions 
                   WHERE is_active = 0 AND updated_at < datetime('now', '-' || ? || ' days')
               """, (days,))

               deleted_sessions = cursor.rowcount

               # Delete orphaned messages
               cursor.execute("""
                   DELETE FROM chat_messages 
                   WHERE session_id NOT IN (SELECT session_id FROM chat_sessions)
               """)

               conn.commit()
               return deleted_sessions

       except Exception as e:
           print(f"Error cleaning up old sessions: {e}")
           return 0

   def get_database_stats(self) -> Dict[str, int]:
       """Get database statistics"""

       try:
           with sqlite3.connect(self.db_path) as conn:
               cursor = conn.cursor()

               stats = {}

               # Count users
               cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
               stats['active_users'] = cursor.fetchone()[0]

               # Count sessions
               cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE is_active = 1")
               stats['active_sessions'] = cursor.fetchone()[0]

               # Count messages
               cursor.execute("SELECT COUNT(*) FROM chat_messages")
               stats['total_messages'] = cursor.fetchone()[0]

               # Count activity logs
               cursor.execute("SELECT COUNT(*) FROM user_activity")
               stats['activity_logs'] = cursor.fetchone()[0]

               return stats

       except Exception as e:
           print(f"Error getting database stats: {e}")
           return {}