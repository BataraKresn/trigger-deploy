# Build stage for Tailwind CSS
FROM node:18-alpine AS tailwind-builder

WORKDIR /build

# Install Tailwind CSS CLI
RUN npm install -g tailwindcss

# Copy template files to analyze for CSS classes
COPY templates/ ./templates/
COPY static/ ./static/
COPY tailwind.config.js ./

# Create input CSS file
COPY static/css/input.css ./

# Build optimized CSS
RUN tailwindcss -i input.css -o output.css --minify

# Main application stage
FROM python:3.10-slim

LABEL maintainer="sysadmin.app@sateknologi.id"
LABEL service="trigger-deploy"

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client jq bash iputils-ping net-tools curl dnsutils procps nano vim \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy built Tailwind CSS from build stage
COPY --from=tailwind-builder /build/output.css ./static/css/tailwind.css

# Copy application structure
COPY src/ ./src/
COPY config/ ./config/
COPY templates/ ./templates/
COPY static/ ./static/
COPY scripts/ ./scripts/
COPY script_debug/ ./script_debug/
COPY app.py wsgi.py ./

# Create required directories
RUN mkdir -p logs trigger-logs

# Make scripts executable
RUN chmod +x scripts/*.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "--timeout", "600", "--workers=4", "--worker-class=gevent", "--bind", "0.0.0.0:8000", "wsgi:app"]
