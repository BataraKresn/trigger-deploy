# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

WORKDIR /usr/share/nginx/html
COPY --from=builder /app/dist ./

EXPOSE 8082
CMD ["nginx", "-g", "daemon off;"]