# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Nginx Serve as root
FROM nginx:alpine

WORKDIR /usr/share/nginx/html
COPY --from=builder /app/dist .

# Override default config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Fix permission issues
RUN mkdir -p /var/cache/nginx/client_temp

# (NO USER directive – stay as root)

EXPOSE 8082
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8082 || exit 1
CMD ["nginx", "-g", "daemon off;"]
