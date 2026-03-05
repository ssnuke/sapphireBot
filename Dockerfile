FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create directories for data, logs, results
RUN mkdir -p data/cache logs results

# Environment variables (set during docker run)
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/config.json

# Health check (optional)
HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; print('OK')" || exit 1

# Run bot
CMD ["python3", "main.py"]
