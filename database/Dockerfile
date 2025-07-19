FROM postgres:15-alpine

# Set timezone
ENV TZ=Asia/Jakarta

# Copy initialization script
COPY init.sql /docker-entrypoint-initdb.d/

# Set proper permissions
RUN chmod +x /docker-entrypoint-initdb.d/init.sql

# Expose PostgreSQL port
EXPOSE 5432
