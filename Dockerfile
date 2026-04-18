FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for psycopg2 and pdf parsing if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure Python can find the app module
ENV PYTHONPATH=/app

CMD ["python", "app/main.py"]
