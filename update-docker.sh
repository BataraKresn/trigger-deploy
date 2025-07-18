#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p log-docker-compose

# Get current date and time
current_time=$(date "+%Y-%m-%d_%H-%M-%S")

# Log file path
log_file="log-docker-compose/docker-compose_$current_time.log"

# Stop and remove existing containers
docker-compose down

# Run docker-compose and save logs
docker-compose up --build > "$log_file" 2>&1

echo "Docker Compose logs saved to $log_file"

# Show running containers
docker ps

# Display logs
docker-compose logs
