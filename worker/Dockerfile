FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker script
COPY worker.py .

# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Run worker
CMD ["python", "-u", "worker.py"]
