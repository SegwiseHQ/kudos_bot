# Use Python 3.13 slim image
FROM python:3.13-slim AS app

WORKDIR /app

# Install build tools + SQLite CLI
# Works across all Debian slim variants (Bookworm/Bullseye)
RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    for i in 1 2 3; do \
        echo "Attempt $i: apt-get update && install deps..."; \
        apt-get update -o Acquire::CompressionTypes::Order::=gz && \
        apt-get install -y --no-install-recommends \
            build-essential \
            sqlite3 \
        && break || { echo "Attempt $i failed, retrying..."; sleep 3; }; \
    done; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Default command
CMD ["python", "main.py"]
