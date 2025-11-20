# QA Agent Test Case Generator - Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Base image with Python dependencies
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN useradd -m -u 1000 qaagent && \
    mkdir -p /app/test_cases_output /app/Related_docs /app/config && \
    chown -R qaagent:qaagent /app

# Copy application code
COPY --chown=qaagent:qaagent . /app/

# Create directories for volumes
RUN mkdir -p \
    /app/test_cases_output/reviewed \
    /app/test_cases_output/processed \
    /app/test_cases_output/errors \
    /app/Related_docs \
    /app/logs \
    && chown -R qaagent:qaagent /app

# Switch to non-root user
USER qaagent

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command
CMD ["streamlit", "run", "app/st.py", "--server.port=8501", "--server.address=0.0.0.0"]
