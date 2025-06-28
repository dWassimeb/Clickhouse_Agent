"""
Enhanced Agent Bridge with Timeout and Better Error Handling
"""

import sys
import os
import logging
import signal
import threading
from typing import Dict, Any, Optional
import traceback
from datetime import datetime
import time

# Ensure we can import from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add both current directory and project root to Python path
for path in [project_root, current_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def timeout_handler(signum, frame):
    """Handle timeout signal."""
    raise TimeoutError("Operation timed out")

class TelmiAgentBridge:
    """Enhanced bridge with timeout and debugging capabilities."""

    def __init__(self):
        self.agent = None
        self.connection_tested = False
        self.last_error = None
        self.last_query_result = None  # Store last query result for debugging
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
            raise ImportError(error_msg)
        except Exception as e:
            logger.error(f"❌ Unexpected import error: {e}")
            raise

    def initialize_agent(self, verbose: bool = True) -> bool:
        """Initialize the LangGraph agent with detailed error reporting."""
        try:
            logger.info("🔧 Initializing ClickHouse LangGraph Agent...")

            # Import the agent class
            from core.agent import ClickHouseGraphAgent

            # Create the agent instance with verbose mode for debugging
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

    def process_question_with_timeout(self, user_question: str, timeout_seconds: int = 60) -> Dict[str, Any]:
        """Process question with timeout mechanism."""

        def run_agent():
            """Run the agent in a separate thread."""
            try:
                logger.info(f"🧠 Starting LangGraph processing for: {user_question[:50]}...")
                response = self.agent.process_question(user_question)
                self.thread_result = {
                    'success': True,
                    'response': response,
                    'message': 'Question processed successfully'
                }
                logger.info("✅ LangGraph processing completed successfully")
            except Exception as e:
                error_msg = f"LangGraph processing failed: {e}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"Full traceback: {traceback.format_exc()}")
                self.thread_result = {
                    'success': False,
                    'response': f"""❌ **LangGraph Processing Error**

**Issue:** {str(e)}

**Type:** {type(e).__name__}

**Debug Info:** The agent workflow failed during execution. This could be due to:
• SQL generation issues
• Database query timeout
• Tool execution problems
• LangGraph workflow configuration

**Suggestion:** Check the terminal logs for detailed error information.""",
                    'error': str(e)
                }

        # Initialize result container
        self.thread_result = None

        # Create and start the thread
        agent_thread = threading.Thread(target=run_agent)
        agent_thread.daemon = True
        agent_thread.start()

        # Wait for completion with timeout
        agent_thread.join(timeout=timeout_seconds)

        if agent_thread.is_alive():
            # Thread is still running - timeout occurred
            logger.error(f"❌ Agent processing timed out after {timeout_seconds} seconds")
            return {
                'success': False,
                'response': f"""⏰ **Processing Timeout**

**Issue:** The agent took longer than {timeout_seconds} seconds to process your question.

**Possible Causes:**
• Complex query requiring extensive database processing
• Database server performance issues
• Network connectivity problems
• LangGraph workflow getting stuck

**Suggestions:**
• Try a simpler question first
• Check database server performance
• Restart the application
• Try: "List available tables" or "Show me 5 customers"

**Your Question:** "{user_question}" """,
                'error': 'Processing timeout'
            }

        # Return the result from the thread
        if self.thread_result:
            return self.thread_result
        else:
            return {
                'success': False,
                'response': "❌ **Unknown Error**: Agent processing completed but no result was returned.",
                'error': 'No result returned'
            }

    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process user question through the LangGraph agent with enhanced debugging."""
        try:
            logger.info(f"🤔 Processing question: {user_question[:50]}...")

            # Ensure agent is initialized
            if self.agent is None:
                logger.info("🔧 Agent not initialized, attempting to initialize...")
                if not self.initialize_agent(verbose=True):  # Enable verbose for debugging
                    return {
                        'success': False,
                        'response': f"""❌ **Agent Initialization Failed**

**Issue:** Could not initialize the Telmi LangGraph agent.

**Last Error:** {self.last_error or 'Unknown error'}

**Debug Steps:**
1. Test CLI agent: `python3 main.py`
2. Check imports: `python3 -c "from core.agent import ClickHouseGraphAgent; print('OK')"`
3. Check database: `python3 -c "from database.connection import clickhouse_connection; print(clickhouse_connection.test_connection())"`""",
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
**Suggestion:** {db_test.get('suggestion', 'Check database configuration')}""",
                        'error': db_test['message']
                    }

            # Process with timeout (60 seconds)
            return self.process_question_with_timeout(user_question, timeout_seconds=60)

        except Exception as e:
            error_msg = f"Question processing failed: {e}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            return {
                'success': False,
                'response': f"""❌ **Processing Error**

**Issue:** {str(e)}
**Type:** {type(e).__name__}

**Debug Info:** Check the terminal for full error details.

**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}""",
                'error': str(e)
            }

    def test_simple_query(self) -> Dict[str, Any]:
        """Test a simple query to verify the agent is working."""
        return self.process_question("List available tables")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the agent and database connection."""
        status = {
            'agent_initialized': self.agent is not None,
            'database_tested': self.connection_tested,
            'ready': False,
            'last_error': self.last_error,
            'project_structure_ok': self._check_project_structure(),
            'timestamp': datetime.now().isoformat()
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
            status['initialization_attempted'] = self.initialize_agent(verbose=True)
            if status['initialization_attempted']:
                return self.get_agent_status()  # Recursive call after initialization

        return status

    def _check_project_structure(self) -> bool:
        """Check if the required project structure exists."""
        required_dirs = ['core', 'database', 'tools']
        required_files = ['main.py', 'core/agent.py', 'database/connection.py']

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

# Global instance
telmi_bridge = TelmiAgentBridge()