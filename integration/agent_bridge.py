"""
Improved Agent Bridge - Better integration with existing LangGraph backend
"""

import sys
import os
import logging
from typing import Dict, Any, Optional
import traceback

# Ensure we can import from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add both current directory and project root to Python path
for path in [project_root, current_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

logger = logging.getLogger(__name__)

class TelmiAgentBridge:
    """Improved bridge between Streamlit UI and the LangGraph agent backend."""

    def __init__(self):
        self.agent = None
        self.connection_tested = False
        self.last_error = None
        self._setup_logging()

        # Try to initialize immediately
        self._attempt_initial_setup()

    def _setup_logging(self):
        """Configure logging for better debugging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _attempt_initial_setup(self):
        """Attempt initial setup to identify issues early."""
        try:
            # Test imports first
            self._test_imports()
            logger.info("✅ All imports successful")
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"❌ Initial setup failed: {e}")

    def _test_imports(self):
        """Test if we can import the required modules."""
        try:
            # Test core agent import
            from core.agent import ClickHouseGraphAgent
            logger.info("✅ Core agent import successful")

            # Test database import
            from database.connection import clickhouse_connection
            logger.info("✅ Database connection import successful")

            return True

        except ImportError as e:
            error_msg = f"Import failed: {e}"
            logger.error(f"❌ {error_msg}")

            # Provide specific guidance based on what's missing
            if "core.agent" in str(e):
                logger.error("❌ Cannot find core.agent module. Make sure you're running from the project root.")
            elif "database.clickhouse" in str(e):
                logger.error("❌ Cannot find database module. Check if database/ directory exists.")

            raise ImportError(error_msg)
        except Exception as e:
            logger.error(f"❌ Unexpected import error: {e}")
            raise

    def initialize_agent(self, verbose: bool = False) -> bool:
        """Initialize the LangGraph agent with detailed error reporting."""
        try:
            logger.info("🔧 Initializing ClickHouse LangGraph Agent...")

            # Import the agent class
            from core.agent import ClickHouseGraphAgent

            # Create the agent instance
            self.agent = ClickHouseGraphAgent(verbose=verbose)

            if self.agent is not None:
                logger.info("✅ Agent initialized successfully")
                return True
            else:
                error_msg = "Agent initialization returned None"
                logger.error(f"❌ {error_msg}")
                self.last_error = error_msg
                return False

        except ImportError as e:
            error_msg = f"Cannot import required modules: {e}"
            logger.error(f"❌ {error_msg}")
            self.last_error = error_msg

            # Check project structure
            self._diagnose_project_structure()
            return False

        except Exception as e:
            error_msg = f"Agent initialization failed: {e}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.last_error = error_msg
            return False

    def test_database_connection(self) -> Dict[str, Any]:
        """Test the ClickHouse database connection with detailed diagnostics."""
        try:
            logger.info("🔌 Testing ClickHouse database connection...")

            # Import the connection
            from database.connection import clickhouse_connection

            # Test the connection
            if clickhouse_connection.test_connection():
                self.connection_tested = True
                logger.info("✅ Database connection successful")
                return {
                    'success': True,
                    'message': 'Database connection successful',
                    'status': 'connected'
                }
            else:
                error_msg = 'Database connection failed - server may be unreachable'
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'status': 'disconnected',
                    'suggestion': 'Check if ClickHouse server is running at 172.20.157.162:8123'
                }

        except ImportError as e:
            error_msg = f'Database module import failed: {e}'
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'message': error_msg,
                'status': 'import_error',
                'suggestion': 'Check if database/ directory and modules exist'
            }
        except Exception as e:
            error_msg = f'Database connection error: {e}'
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'message': error_msg,
                'status': 'error',
                'suggestion': 'Check database configuration and network connectivity'
            }

    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process user question through the LangGraph agent."""
        try:
            logger.info(f"🤔 Processing question: {user_question[:50]}...")

            # Ensure agent is initialized
            if self.agent is None:
                logger.info("🔧 Agent not initialized, attempting to initialize...")
                if not self.initialize_agent():
                    return {
                        'success': False,
                        'response': f"""❌ **Agent Initialization Failed**

**Issue:** Could not initialize the Telmi LangGraph agent.

**Possible Causes:**
• Missing core modules (core/, database/, tools/)
• Import path issues
• Dependencies not installed

**Last Error:** {self.last_error or 'Unknown error'}

**Solutions:**
• Make sure you're running from the project root directory
• Verify all modules exist: `ls -la core/ database/ tools/`
• Test the CLI agent first: `python3 main.py`
• Check virtual environment: `which python`""",
                        'error': 'Agent not initialized'
                    }

            # Test database connection if not already tested
            if not self.connection_tested:
                logger.info("🔌 Testing database connection...")
                db_test = self.test_database_connection()
                if not db_test['success']:
                    return {
                        'success': False,
                        'response': f"""❌ **Database Connection Failed**

**Issue:** {db_test['message']}

**Status:** {db_test['status']}

**Suggestion:** {db_test.get('suggestion', 'Check database configuration')}

**Quick Tests:**
• Test ClickHouse access: `telnet 172.20.157.162 8123`
• Check your .env file database settings
• Verify network connectivity""",
                        'error': db_test['message']
                    }

            # Process the question through your existing LangGraph workflow
            logger.info("🧠 Sending question to LangGraph agent...")
            response = self.agent.process_question(user_question)

            logger.info("✅ Question processed successfully")

            return {
                'success': True,
                'response': response,
                'message': 'Question processed successfully'
            }

        except Exception as e:
            error_msg = f"Question processing failed: {e}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            return {
                'success': False,
                'response': f"""❌ **Processing Error**

**Issue:** {str(e)}

**Type:** {type(e).__name__}

**Possible Solutions:**
• Restart the Streamlit application
• Check if the CLI agent (`python3 main.py`) works independently
• Verify all dependencies are installed
• Check the terminal for detailed error logs

**Debug Info:** Check the terminal/console for full traceback details.""",
                'error': str(e)
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the agent and database connection."""
        status = {
            'agent_initialized': self.agent is not None,
            'database_tested': self.connection_tested,
            'ready': False,
            'last_error': self.last_error,
            'project_structure_ok': self._check_project_structure()
        }

        # Test database connection if agent is initialized
        if status['agent_initialized']:
            if not status['database_tested']:
                db_test = self.test_database_connection()
                status['database_connected'] = db_test['success']
                status['database_message'] = db_test['message']
                status['database_suggestion'] = db_test.get('suggestion', '')
            else:
                status['database_connected'] = True
                status['database_message'] = 'Connected and tested'

            status['ready'] = status['agent_initialized'] and status.get('database_connected', False)
        else:
            # Try to initialize if not already done
            status['initialization_attempted'] = self.initialize_agent()
            if status['initialization_attempted']:
                return self.get_agent_status()  # Recursive call after initialization

        return status

    def _check_project_structure(self) -> bool:
        """Check if the required project structure exists."""
        required_dirs = ['core', 'database', 'tools']
        required_files = ['main.py', 'core/agent.py', 'database/clickhouse/connection.py']

        missing = []

        # Check directories
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                missing.append(f"Directory: {dir_name}/")

        # Check files
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing.append(f"File: {file_path}")

        if missing:
            logger.warning(f"❌ Missing project components: {', '.join(missing)}")
            return False

        logger.info("✅ Project structure looks good")
        return True

    def _diagnose_project_structure(self):
        """Diagnose and report project structure issues."""
        logger.info("🔍 Diagnosing project structure...")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path[:3]}...")  # Show first 3 entries

        # List current directory contents
        try:
            contents = os.listdir('.')
            logger.info(f"Current directory contents: {contents}")
        except Exception as e:
            logger.error(f"Cannot list directory contents: {e}")

# Global instance
telmi_bridge = TelmiAgentBridge()