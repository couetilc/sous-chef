# syntax=docker/dockerfile:1.7

# Development container with both Python and Node.js environments
FROM python:3.13-slim

# Prevent interactive prompts and Python bytecode
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # Node environment
    NODE_VERSION=24.9.0 \
    PNPM_HOME="/root/.local/share/pnpm" \
    PATH="/root/.local/share/pnpm:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    # Git for version control
    git \
    # PostgreSQL client for database access
    postgresql-client \
    # Node.js installation dependencies
    curl \
    ca-certificates \
    gnupg \
    # Useful utilities
    vim \
    less \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 24.9.0
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Node version and enable pnpm
RUN node --version && npm --version \
    && corepack enable \
    && corepack prepare pnpm@latest --activate

# Install Python development tools
RUN pip install --no-cache-dir \
    # Django development
    django-stubs \
    djangorestframework-stubs \
    # Type checking and static analysis
    mypy \
    # Testing
    pytest \
    pytest-django \
    pytest-cov \
    # Code formatting (optional, can be project-specific)
    black \
    isort

# Set working directory
WORKDIR /workspace

# Keep container running
CMD ["sleep", "infinity"]
