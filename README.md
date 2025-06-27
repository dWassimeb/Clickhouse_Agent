ClickHouse Natural Language Query Agent
A robust agent built with LangGraph and ClickHouse that converts natural language questions into SQL queries, executes them against a ClickHouse database, and provides clear, structured responses.
Features

Natural language to SQL translation
Direct connection to ClickHouse database
Error handling and query correction
Detailed explanations of SQL queries
Nicely formatted query results
Interactive command-line interface

Architecture
The agent uses a LangGraph workflow with the following components:

SQL Generation: Converts natural language questions to ClickHouse SQL
SQL Execution: Runs queries against the ClickHouse database
Result Formatting: Presents query results in a clear, structured manner
Error Handling: Retries with improved queries when errors occur

Database Schema
The agent works with a ClickHouse database containing the following tables:

RM_AGGREGATED_DATA: Mobile data sessions including volume, duration, and device identifiers
PLMN: Information about mobile network operators
CELL: Mobile network cell location and association with PLMN
CUSTOMER: Customer reference information

Installation

Clone this repository:
bashgit clone https://github.com/yourusername/clickhouse-agent.git
cd clickhouse-agent

Create and activate a virtual environment:
bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
bashpip install -r requirements.txt

Configure your ClickHouse connection in the .env file:
CLICKHOUSE_HOST=172.20.157.162
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=Default
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

GPT_API_KEY=2b24fef721d14c94a333ab2e4f686f40
MODEL_NAME=gpt-4o
MODEL_VERSION=2024-02-01


Usage
Interactive Mode
Run the agent in interactive mode:
bashpython main.py
This will start a command-line interface where you can enter natural language questions.
Single Query Mode
Execute a single query:
bashpython main.py "What is the total data volume by operator in the last month?"
Example Questions

"How many data sessions were recorded yesterday?"
"What is the average download volume by device type?"
"Which customers had the highest upload volume last week?"
"What is the distribution of connection types across different regions?"
"Show me the top 10 cell towers with the most traffic"

Web Interface (Streamlit)
------------------------
A modern web interface is available. To launch it:

```bash
streamlit run web_app.py
```

This will open a professional chatbot UI in your browser, allowing you to ask questions and view chat history in the sidebar.

Project Structure
clickhouse-agent/
├── .env                    # Environment variables
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── src/
│   ├── __init__.py
│   ├── agent.py            # LangGraph agent implementation
│   ├── clickhouse_client.py # ClickHouse connection and query execution
│   ├── config.py           # Configuration and environment variables
│   ├── llm.py              # Custom LLM implementation
│   ├── prompts.py          # Agent prompts
│   ├── schema.py           # Database schema definitions
│   └── utils.py            # Utility functions
└── main.py                 # Application entry point
Extending the Agent
Adding New Tables
To add new tables to the schema, update the SCHEMA_METADATA dictionary in src/schema.py with the table and column definitions.
Customizing Prompts
The agent's prompting system can be customized by modifying the templates in src/prompts.py.
Changing the LLM
The agent uses a custom GPT implementation that can be replaced with any LangChain-compatible LLM by updating src/llm.py.
License
MIT