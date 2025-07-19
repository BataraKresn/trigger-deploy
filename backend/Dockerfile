FROM python:3.9-slim

LABEL maintainer="sysadmin.app@sateknologi.id"
LABEL service="trigger-deploy"

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install OS packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client jq bash iputils-ping net-tools curl dnsutils procps \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app

# Expose port (optional)
EXPOSE 5001

# Run the application with Gunicorn + Uvicorn Worker
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5001", "wsgi:app"]