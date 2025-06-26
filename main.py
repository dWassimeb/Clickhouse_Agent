"""
ClickHouse LangGraph Agent - Main Entry Point
Clean, efficient LangGraph implementation
"""

import sys
import logging
from core.agent import ClickHouseGraphAgent
from database.clickhouse.connection import clickhouse_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function with proper LangGraph structure."""

    # ===== CONFIGURATION =====
    VERBOSE_MODE = True  # Set to False for clean output
    # =========================

    # Command line overrides
    if "--verbose" in sys.argv or "-v" in sys.argv:
        verbose = True
    elif "--quiet" in sys.argv or "-q" in sys.argv:
        verbose = False
    else:
        verbose = VERBOSE_MODE

    print("🚀 ClickHouse LangGraph Agent Starting...")
    if verbose:
        print("🔍 Verbose mode - showing full LangGraph workflow")
        print("💡 Architecture: Agent (reasoning) + Tools (execution) + Router (decisions)")
    else:
        print("🤫 Quiet mode - clean output only")

    # Test database connection
    print("🔌 Testing database connection...")

    try:
        if clickhouse_connection.test_connection():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
            print("💡 Please check if ClickHouse server is running and accessible.")
            return
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("💡 The agent will still start, but database queries will fail.")

    print("Type 'exit' to quit, 'help' for assistance")
    if verbose:
        print("💡 Tip: You'll see the complete AI reasoning process")
        print("💡 Use 'python3 main.py --quiet' to disable verbose mode")
    else:
        print("💡 Use 'python3 main.py --verbose' to see AI reasoning process")
    print()

    # Create the LangGraph agent
    agent = ClickHouseGraphAgent(verbose=verbose)

    # Main interaction loop
    while True:
        try:
            user_input = input("📝 Your question: ").strip()

            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break

            if not user_input:
                print("❌ Please enter a question.")
                continue

            print("\n🔄 Processing your question through LangGraph...")
            response = agent.process_question(user_input)
            print(f"\n{response}\n")
            print("-" * 80)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"\n❌ An error occurred: {e}")
            print("Please try again.\n")

if __name__ == "__main__":
    main()