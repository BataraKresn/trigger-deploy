FROM python:3.9-slim

LABEL maintainer="sysadmin.app@sateknologi.id"
LABEL service="trigger-deploy"

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install SSH client, jq, ping, net-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client jq bash iputils-ping net-tools \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy .env file (optional)
# COPY .env .env

# Copy entire application
COPY . .

# Expose port (optional if needed for debugging)
EXPOSE 5001

# Run app
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "wsgi:app"]
