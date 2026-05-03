# Dockerfile for Railway deployment - EmagScrapper-Py
FROM python:3.12-slim

# Install system dependencies required by Playwright/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    # Playwright system dependencies
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Install Playwright Chromium browser
RUN playwright install chromium

# Expose the port (Railway will set PORT env var)
EXPOSE 8000

# Run the FastAPI application
CMD ["sh", "-c", "if echo \"$DATABASE_URL\" | grep -qE 'localhost|127\\.0\\.0\\.1|::1'; then echo 'Skipping migrations (local DB)'; else alembic upgrade head; fi && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
