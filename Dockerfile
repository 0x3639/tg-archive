FROM python:3.13-slim

# Install system dependencies for python-magic, pillow, and git for pip install
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libjpeg62-turbo \
    zlib1g \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Create data directory
RUN mkdir -p /data

WORKDIR /data

# Default command shows help
CMD ["tg-archive", "--help"]
