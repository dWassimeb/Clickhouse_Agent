"""
Agent Bridge - Integration between Streamlit frontend and LangGraph backend
Ensures proper connection to the existing main.py workflow
"""

import sys
import os
import logging
from typing import Dict, Any, Optional
import streamlit as st

# Add the project root to Python path to import the core modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

class TelmiAgentBridge:
    """Bridge between Streamlit UI and the LangGraph agent backend."""

    def __init__(self):
        self.agent = None
        self.connection_tested = False
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for better debugging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def initialize_agent(self, verbose: bool = False) -> bool:
        """Initialize the LangGraph agent with proper error handling."""
        try:
            # Import the core agent
            from core.agent import ClickHouseGraphAgent

            logger.info("Initializing ClickHouse LangGraph Agent...")
            self.agent = ClickHouseGraphAgent(verbose=verbose)

            # Test the agent initialization
            if self.agent is not None:
                logger.info("✅ Agent initialized successfully")
                return True
            else:
                logger.error("❌ Agent initialization returned None")
                return False

        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.error("Make sure you're running from the correct project directory")
            return False
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            return False

    def test_database_connection(self) -> Dict[str, Any]:
        """Test the ClickHouse database connection."""
        try:
            from database.clickhouse.connection import clickhouse_connection

            logger.info("Testing ClickHouse database connection...")

            if clickhouse_connection.test_connection():
                self.connection_tested = True
                return {
                    'success': True,
                    'message': 'Database connection successful',
                    'status': 'connected'
                }
            else:
                return {
                    'success': False,
                    'message': 'Database connection failed',
                    'status': 'disconnected',
                    'suggestion': 'Check if ClickHouse server is running and accessible'
                }

        except ImportError as e:
            return {
                'success': False,
                'message': f'Database module import failed: {e}',
                'status': 'error',
                'suggestion': 'Check if database modules are properly installed'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Database connection error: {e}',
                'status': 'error',
                'suggestion': 'Check database configuration and network connectivity'
            }

    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process user question through the LangGraph agent."""
        try:
            # Ensure agent is initialized
            if self.agent is None:
                if not self.initialize_agent():
                    return {
                        'success': False,
                        'response': '❌ **Agent Initialization Failed**\n\nCould not initialize the Telmi agent. Please check the backend configuration.',
                        'error': 'Agent not initialized'
                    }

            # Test database connection if not already tested
            if not self.connection_tested:
                db_test = self.test_database_connection()
                if not db_test['success']:
                    return {
                        'success': False,
                        'response': f"❌ **Database Connection Failed**\n\n{db_test['message']}\n\n💡 **Suggestion:** {db_test.get('suggestion', 'Check your database settings')}",
                        'error': db_test['message']
                    }

            logger.info(f"Processing question: {user_question[:50]}...")

            # Process the question through the LangGraph workflow
            response = self.agent.process_question(user_question)

            logger.info("✅ Question processed successfully")

            return {
                'success': True,
                'response': response,
                'message': 'Question processed successfully'
            }

        except Exception as e:
            logger.error(f"❌ Question processing failed: {e}")

            # Provide helpful error message based on error type
            error_message = self._format_error_message(str(e))

            return {
                'success': False,
                'response': error_message,
                'error': str(e)
            }

    def _format_error_message(self, error: str) -> str:
        """Format error messages for user-friendly display."""

        if "connection" in error.lower() or "timeout" in error.lower():
            return f"""❌ **Connection Error**

**Issue:** Database connection problem
**Details:** {error}

**Solutions:**
• Check if ClickHouse database is running
• Verify database host and port settings
• Check network connectivity
• Review database credentials in Account Settings"""

        elif "import" in error.lower() or "module" in error.lower():
            return f"""❌ **Module Error**

**Issue:** Missing or incorrect module imports
**Details:** {error}

**Solutions:**
• Make sure you're in the correct project directory
• Check if all dependencies are installed: `pip install -r requirements.txt`
• Verify the virtual environment is activated"""

        elif "sql" in error.lower() or "query" in error.lower():
            return f"""❌ **Query Error**

**Issue:** SQL execution problem
**Details:** {error}

**Solutions:**
• Try rephrasing your question
• Check if the requested tables/columns exist
• Use simpler queries to test the connection"""

        else:
            return f"""❌ **Unexpected Error**

**Details:** {error}

**Solutions:**
• Try restarting the application
• Check the application logs for more details
• Contact your system administrator if the problem persists"""

    def get_agent_status(self) -> Dict[str, Any]:
        """Get the current status of the agent and database connection."""
        status = {
            'agent_initialized': self.agent is not None,
            'database_tested': self.connection_tested,
            'ready': False
        }

        if status['agent_initialized']:
            # Test database if not already tested
            if not status['database_tested']:
                db_test = self.test_database_connection()
                status['database_connected'] = db_test['success']
                status['database_message'] = db_test['message']
            else:
                status['database_connected'] = True
                status['database_message'] = 'Connected'

            status['ready'] = status['agent_initialized'] and status['database_connected']

        return status

# Global instance for the Streamlit app
telmi_bridge = TelmiAgentBridge()