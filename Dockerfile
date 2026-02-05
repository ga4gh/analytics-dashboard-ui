FROM python:3.11-slim

WORKDIR /app

# Install system deps (optional but good for many python wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python deps first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Dash runs on 8050 by default
EXPOSE 8050

# Run with gunicorn (recommended for production)
CMD ["gunicorn", "run:server", "--bind", "0.0.0.0:8050", "--workers", "2"]
