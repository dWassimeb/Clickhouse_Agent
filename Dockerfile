# Telmi Streamlit Application Dockerfile
# Multi-stage build for production deployment

# Build stage
FROM python:3.9-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=3001 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_BASE_URL_PATH=/clickhouseagent \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN groupadd -r telmi && useradd -r -g telmi telmi

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p data exports visualizations logs && \
    chown -R telmi:telmi /app

# Copy application code
COPY --chown=telmi:telmi . .

# Create default .env if it doesn't exist
RUN if [ ! -f .env ]; then \
    echo "CLICKHOUSE_HOST=172.20.157.162" > .env && \
    echo "CLICKHOUSE_PORT=8123" >> .env && \
    echo "CLICKHOUSE_DATABASE=default" >> .env && \
    echo "CLICKHOUSE_USERNAME=default" >> .env && \
    echo "CLICKHOUSE_PASSWORD=" >> .env && \
    echo "APP_URL=/clickhouseagent" >> .env && \
    echo "DEBUG=false" >> .env && \
    echo "SESSION_SECRET_KEY=production-secret-key-$(date +%s)" >> .env; \
    fi

# Switch to non-root user
USER telmi

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3001/clickhouseagent/_stcore/health || exit 1

# Expose port
EXPOSE 3001

# Default command
CMD ["streamlit", "run", "app.py", \
     "--server.port", "3001", \
     "--server.address", "0.0.0.0", \
     "--server.baseUrlPath", "/clickhouseagent", \
     "--server.enableCORS", "false", \
     "--server.enableXsrfProtection", "false", \
     "--browser.gatherUsageStats", "false", \
     "--global.developmentMode", "false"]