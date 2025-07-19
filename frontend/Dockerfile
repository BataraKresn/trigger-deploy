# -------------------------
# Stage 1: Build React App
# -------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# -----------------------------
# Stage 2: Nginx for Production
# -----------------------------
FROM nginx:alpine

# Set working dir and copy build output
WORKDIR /usr/share/nginx/html
COPY --from=builder /app/dist .

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Fix permission issue (especially if not running as root)
RUN mkdir -p /var/cache/nginx/client_temp

# Expose port and add healthcheck
EXPOSE 8082
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8082 || exit 1

# Run Nginx
CMD ["nginx", "-g", "daemon off;"]
