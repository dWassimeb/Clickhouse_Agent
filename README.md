# 🔮 Telmi - Intelligent Telecom Analytics Assistant

A modern, ChatGPT-like web interface for natural language querying of ClickHouse telecom data. Built with Streamlit, LangGraph, and advanced AI capabilities.

## ✨ Features

### 🎯 Core Capabilities
- **Natural Language Queries**: Ask questions in plain English or French
- **Intelligent SQL Generation**: AI-powered query construction with business rule awareness
- **Interactive Visualizations**: Professional Chart.js charts with multiple types
- **Automatic CSV Exports**: Download complete datasets
- **Real-time Chat Interface**: ChatGPT-like conversation experience

### 🔐 User Management
- **User Authentication**: Secure login and account management
- **Session Persistence**: Chat history saved across sessions
- **Account Settings**: Customizable database connections and preferences
- **Multi-user Support**: Individual user sessions and data isolation

### 📱 Modern Interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark/Light Themes**: Customizable appearance
- **Typing Indicators**: Real-time feedback during processing
- **File Downloads**: Integrated CSV and chart downloads
- **Inline Charts**: Charts displayed directly in chat

## 🏗️ Architecture

```
Streamlit Frontend → LangGraph Agent → ClickHouse Database
     ↓                    ↓                    ↓
- User Interface    - AI Reasoning       - Data Storage
- Authentication    - SQL Generation     - Query Execution
- Chat Management   - Visualization      - Result Processing
- File Downloads    - Error Handling     - Performance
```

### 🧠 LangGraph Workflow
1. **Smart Router**: Classifies user intent (data query, schema, help)
2. **Intent Analyzer**: Understands business requirements and chart preferences
3. **SQL Generator**: Creates optimized ClickHouse queries with business rules
4. **Query Executor**: Safely executes queries with validation
5. **Visualization Creator**: Generates interactive charts based on data and user preferences
6. **Response Formatter**: Creates clean, chat-friendly output

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- ClickHouse database access
- Node.js (for development only)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd telmi-streamlit
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the interface**
   - Local: http://localhost:3001
   - Production: https://yourdomain.com/clickhouseagent/

## 📋 Configuration

### Environment Variables

Create a `.env` file:

```env
# ClickHouse Configuration
CLICKHOUSE_HOST=172.20.157.162
CLICKHOUSE_PORT=8123
CLICKHOUSE_DATABASE=default
CLICKHOUSE_USERNAME=default
CLICKHOUSE_PASSWORD=

# Application Configuration
APP_URL=/clickhouseagent
DEBUG=false

# Security
SESSION_SECRET_KEY=your-secret-key-here
```

### Reverse Proxy Setup

For deployment with reverse proxy:

```nginx
location /clickhouseagent/ {
    proxy_pass http://10.8.20.96:3001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    
    # Asset rewriting
    sub_filter 'href="/' 'href="/clickhouseagent/';
    sub_filter 'src="/' 'src="/clickhouseagent/';
    sub_filter_once off;
}
```

## 💬 Usage Examples

### Basic Queries
```
"Show me the top 10 customers by data usage"
"What's the traffic distribution by country?"
"How many tickets were created yesterday?"
```

### Advanced Analytics
```
"Compare data usage between France and Spain last month"
"Show device movement from France to Germany"
"Create a line chart of monthly traffic trends"
```

### Schema Exploration
```
"List all available tables"
"Describe the RM_AGGREGATED_DATA table"
"What columns are in the CUSTOMER table?"
```

## 🎨 Customization

### Styling
- Edit `components/styling.py` for CSS customization
- Modify color schemes in the `:root` variables
- Adjust responsive breakpoints

### Chat Interface
- Customize `components/chat.py` for message formatting
- Modify typing speed and animations
- Add custom message types

### Authentication
- Extend `components/auth.py` for additional auth providers
- Add custom user fields
- Implement role-based access

## 📊 Database Schema

### Main Tables
- **RM_AGGREGATED_DATA**: Core telecom session data
- **PLMN**: Mobile operator information
- **CELL**: Cell tower locations
- **CUSTOMER**: Customer reference data

### Key Relationships
```sql
RM_AGGREGATED_DATA → CUSTOMER (via PARTY_ID)
RM_AGGREGATED_DATA → PLMN (via PLMN)
RM_AGGREGATED_DATA → CELL (via CELL_ID)
```

## 🔧 Development

### Project Structure
```
telmi-streamlit/
├── app.py                      # Main Streamlit app
├── components/                 # UI components
│   ├── auth.py                # Authentication
│   ├── chat.py                # Chat interface
│   ├── sidebar.py             # Sidebar management
│   └── styling.py             # CSS styling
├── core/                      # LangGraph agent
├── database/                  # ClickHouse connection
├── tools/                     # LangGraph tools
├── config/                    # Configuration
├── data/                      # User data storage
└── .streamlit/                # Streamlit config
```

### Running in Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run with debug mode
DEBUG=true streamlit run app.py --server.port 3001

# Run with file watching
streamlit run app.py --server.fileWatcherType poll
```

### Adding New Features

1. **New Chart Types**: Extend `tools/modern_visualization_tool.py`
2. **Custom Queries**: Add patterns to `config/schemas.py`
3. **UI Components**: Create new components in `components/`

## 📈 Performance

### Optimization Tips
- **Query Limits**: Automatic LIMIT clauses prevent large result sets
- **Connection Pooling**: Efficient ClickHouse connection management
- **Caching**: Streamlit caching for repeated operations
- **Lazy Loading**: Charts and data loaded on demand

### Monitoring
- Built-in query execution timing
- User session tracking
- Error logging and reporting
- Performance metrics collection

## 🔒 Security

### Features
- **User Authentication**: Secure login system
- **Query Validation**: SQL injection prevention
- **Rate Limiting**: Request throttling
- **Session Management**: Secure session handling

### Best Practices
- Regular security updates
- Strong password requirements
- Database access controls
- Audit logging

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 3001
CMD ["streamlit", "run", "app.py"]
```

### Cloud Deployment
- **AWS**: ECS, Lambda, or EC2
- **Azure**: Container Instances or App Service
- **GCP**: Cloud Run or Compute Engine
- **Docker**: Any container platform

## 🐛 Troubleshooting

### Common Issues

**Connection Errors**
```bash
# Check ClickHouse connectivity
telnet 172.20.157.162 8123
```

**Authentication Issues**
```bash
# Reset user data
rm data/users.json
rm data/chat_sessions.json
```

**Performance Issues**
```bash
# Clear Streamlit cache
streamlit cache clear
```

## 📚 API Reference

### Core Components

#### ChatInterface
```python
from components.chat import ChatInterface

chat = ChatInterface()
chat.render_message_stream(message, "agent")
```

#### AuthManager
```python
from components.auth import AuthManager

auth = AuthManager()
if auth.authenticate_user(username, password):
    # User authenticated
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to all functions
- Write unit tests for new features
- Update documentation

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **LangGraph**: For the agent framework
- **Streamlit**: For the web interface
- **ClickHouse**: For the database engine
- **Chart.js**: For visualizations

## 📞 Support

- **Documentation**: [Link to docs]
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@telmi.ai

---

**Built with ❤️ for the Telecom Industry**