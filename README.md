# 🚀 Deploy Server - Professional DevOps Management Platform

A modern, scalable deployment management platform built with React, Flask, and PostgreSQL. This system provides a comprehensive solution for managing server deployments, monitoring health status, and tracking deployment logs with a professional dashboard interface.

![Deploy Server Dashboard](https://img.shields.io/badge/Deploy%20Server-v1.0-blue?style=for-the-badge&logo=rocket)
![Tech Stack](https://img.shields.io/badge/Stack-React%20%7C%20Flask%20%7C%20PostgreSQL-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge)

## 🌟 Features

### 🎯 **Frontend Dashboard**
- **Modern React UI** with TailwindCSS & TypeScript
- **Real-time monitoring** with live updates
- **Interactive charts** for deployment metrics
- **Responsive design** for desktop and mobile
- **Professional dark/light theme** support
- **Server health monitoring** with ping statistics
- **Deployment history** with detailed logs
- **User authentication** with JWT tokens

### 🔧 **Backend API**
- **RESTful API** with Flask-RESTX & OpenAPI docs
- **PostgreSQL database** integration with SQLAlchemy
- **JWT authentication** & role-based access control
- **Rate limiting** & security middleware
- **Comprehensive logging** with structured logs
- **Input validation** with Pydantic schemas
- **Background tasks** for deployments
- **Health checks** & system monitoring

### 🐳 **DevOps Ready**
- **Docker Compose** orchestration
- **Production-ready** configuration
- **Database migrations** with Flask-Migrate
- **Environment configuration** management
- **Logging & monitoring** integration
- **Scalable architecture** design

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React +      │◄──►│   (Flask +      │◄──►│  (PostgreSQL)   │
│   TailwindCSS)  │    │   SQLAlchemy)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        ├─ React Router v7        ├─ Flask-RESTX API      ├─ User Management
        ├─ Zustand State         ├─ JWT Authentication    ├─ Server Registry
        ├─ Axios HTTP Client     ├─ Rate Limiting         ├─ Deploy Logs

## 📋 Prerequisites

Before you start, make sure you have the following installed:

- **Docker** (v20.10+) & **Docker Compose** (v2.0+)
- **Git** for version control
- **Node.js** (v18+) - for local frontend development
- **Python** (3.9+) - for local backend development

## 🚀 Quick Start

### 1️⃣ **Clone Repository**
```bash
git clone https://github.com/BataraKresn/trigger-deploy.git
cd trigger-deploy
```

### 2️⃣ **Environment Setup**
```bash
# Backend environment files are already configured:
# - backend/.env.development (for development)
# - backend/.env.production (for production)
# - backend/.env.example (template)

# Frontend environment files are already configured:
# - frontend/.env.development (for development)
# - frontend/.env.production (for production)

# For production, edit the production environment files:
nano backend/.env.production
nano frontend/.env.production
```

### 3️⃣ **Start All Services**

#### **🚀 Easy Way (Recommended) - Using Quick Scripts**
```bash
# Development mode (uses .env.development files)
./quick-dev.sh start

# Production mode (uses .env.production files)
./quick-dev.sh start-prod

# Initialize database (first time only)
./quick-dev.sh migrate

# Check services status
./quick-dev.sh status
```

#### **📋 Quick Development Commands**
The `quick-dev.sh` script provides convenient commands for managing your deployment:

| Command | Description | Environment |
|---------|-------------|-------------|
| `./quick-dev.sh start` | Start all services | Development |
| `./quick-dev.sh start-prod` | Start all services | Production |
| `./quick-dev.sh stop` | Stop all services | Both |
| `./quick-dev.sh restart` | Restart all services | Both |
| `./quick-dev.sh logs` | Show logs for all services | Both |
| `./quick-dev.sh backend` | Show backend logs only | Both |
| `./quick-dev.sh frontend` | Show frontend logs only | Both |
| `./quick-dev.sh db` | Connect to database | Both |
| `./quick-dev.sh migrate` | Run database migrations | Both |
| `./quick-dev.sh status` | Show services status | Both |
| `./quick-dev.sh build` | Rebuild all images | Both |
| `./quick-dev.sh clean` | Clean up Docker resources | Both |

#### **🔧 Manual Way (Alternative)**
```bash
# Development mode (uses .env.development files)
docker-compose up -d

# OR Production mode (uses .env.production files)  
docker-compose -f docker-compose.prod.yml up -d

# Initialize database (first time only)
docker-compose exec backend ./init-migrations.sh

# Check services status
docker-compose ps
```

### 4️⃣ **Access Application**
- **Frontend Dashboard**: http://localhost:3111
- **Backend API**: http://localhost:5002/api
- **API Documentation**: http://localhost:5002/docs
- **Database**: localhost:5432 (deployuser/strongpassword)

## � Environment Modes

### **📊 Development vs Production Comparison**

| Aspect | Development Mode | Production Mode |
|--------|------------------|-----------------|
| **Command** | `./quick-dev.sh start` | `./quick-dev.sh start-prod` |
| **Docker Compose** | `docker-compose.yaml` | `docker-compose.prod.yml` |
| **Environment Files** | `.env.development` | `.env.production` |
| **Flask Debug** | Enabled (True) | Disabled (False) |
| **Log Level** | DEBUG (verbose) | INFO (clean) |
| **Secret Keys** | Development keys | Production keys |
| **API URL** | `localhost:5002` | `your-domain.com` |
| **Frontend Debug** | Enabled | Disabled |
| **CORS** | Permissive | Restrictive |
| **Performance** | Slower (dev tools) | Optimized |

### **🛡️ Security Differences**

| Security Feature | Development | Production |
|------------------|-------------|------------|
| **BCRYPT Rounds** | 4 (faster) | 12 (secure) |
| **Token Expiry** | 30 days | 7 days |
| **SQL Echo** | Enabled | Disabled |
| **Error Details** | Full stack trace | Generic messages |
| **HTTPS** | Optional | Required |

## �🛠️ Development Guide

### **Backend Development (Flask)**

#### **Setup Local Environment**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Use development environment
export FLASK_APP=app.py
export FLASK_ENV=development

# Load environment variables from .env.development
set -a; source .env.development; set +a
```

#### **Database Migrations**
```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Your migration message"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

#### **Run Development Server**
```bash
# Start Flask dev server
flask run --host=0.0.0.0 --port=5001

# Or with gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# With auto-reload
gunicorn -w 1 -b 0.0.0.0:5001 --reload app:app
```

#### **API Testing**
```bash
# Test health endpoint
curl http://localhost:5001/health

# Test API status
curl http://localhost:5001/api/status

# Login test
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### **Frontend Development (React)**

#### **Setup Local Environment**
```bash
cd frontend

# Install dependencies
npm install

# Development environment is already configured in:
# - .env.development (for npm run dev)
# - .env.production (for npm run build)
```

#### **Development Commands**
```bash
# Start development server
npm run dev          # http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview      # http://localhost:8082

# Type checking
npx tsc --noEmit
```

#### **Code Quality**
```bash
# Lint code
npm run lint

# Format code
npm run format

# Run tests
npm run test
```

### **Database Management**

#### **Access Database**
```bash
# Connect to PostgreSQL container
docker-compose exec postgres psql -U deployuser -d deploydb

# Or via external client
psql -h localhost -p 5432 -U deployuser -d deploydb
```

#### **Database Backup & Restore**
```bash
# Backup database
docker-compose exec postgres pg_dump -U deployuser deploydb > backup.sql

# Restore database
docker-compose exec -T postgres psql -U deployuser deploydb < backup.sql

# Reset database (⚠️ Destructive)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend ./init-migrations.sh
```

## 🚢 Production Deployment

### **🔧 Production Configuration**

#### **1. Environment Variables**
```bash
# Backend Production Environment (backend/.env.production)
DATABASE_URL=postgresql+psycopg2://user:pass@postgres:5432/deploydb
SECRET_KEY=your-super-secure-secret-key-256-bit
JWT_SECRET_KEY=your-jwt-secret-key-512-bit
FLASK_ENV=production
FLASK_DEBUG=False

# Frontend Production Environment (frontend/.env.production)
NODE_ENV=production
VITE_API_URL=https://your-domain.com/api
VITE_DEBUG=false
```

#### **2. Docker Compose Production**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  postgres:
    restart: always
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  backend:
    restart: always
    environment:
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    
  frontend:
    restart: always
    environment:
      VITE_API_URL: ${VITE_API_URL}
```

### **🚀 Production Deployment Steps**

#### **1. Server Preparation**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create app directory
sudo mkdir -p /opt/deploy-server
sudo chown $USER:$USER /opt/deploy-server
```

#### **2. Deploy Application**

#### **🚀 Easy Way (Recommended) - Using Deployment Script**
```bash
cd /opt/deploy-server

# Clone repository
git clone https://github.com/BataraKresn/trigger-deploy.git .

# Edit production environment files
nano backend/.env.production
nano frontend/.env.production

# One-command deployment
./deploy-production.sh deploy

# Check deployment
./deploy-production.sh check
```

#### **📋 Production Deployment Commands**
The `deploy-production.sh` script provides automated deployment:

| Command | Description |
|---------|-------------|
| `./deploy-production.sh deploy` | Full production deployment |
| `./deploy-production.sh update` | Update existing deployment |
| `./deploy-production.sh check` | Check system requirements |

#### **🔧 Manual Way (Alternative)**
```bash
cd /opt/deploy-server

# Clone repository
git clone https://github.com/BataraKresn/trigger-deploy.git .

# Edit production environment files with your values
nano backend/.env.production
nano frontend/.env.production

# Start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Initialize database
docker-compose -f docker-compose.prod.yml exec backend ./init-migrations.sh

# Check services
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

#### **3. Nginx Reverse Proxy (Optional)**
```nginx
# /etc/nginx/sites-available/deploy-server
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3111;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **📊 Monitoring & Maintenance**

#### **Health Monitoring**
```bash
# Check service health
curl http://localhost:5002/health
curl http://localhost:3111

# Monitor logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# System resources
docker stats
```

#### **Backup Strategy**
```bash
# Create backup script /opt/deploy-server/backup.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U deployuser deploydb > backup_${DATE}.sql
find . -name "backup_*.sql" -mtime +7 -delete

# Setup cron job
0 2 * * * /opt/deploy-server/backup.sh
```

#### **Updates & Maintenance**
```bash
# Update application
git pull origin main
docker-compose down
docker-compose up -d --build

# Update database migrations
docker-compose exec backend flask db upgrade

# Clean up old images
docker system prune -af
```

## 🔐 Security Considerations

### **🛡️ Production Security Checklist**

- [ ] **Strong Secret Keys**: Generate 256-bit random keys
- [ ] **Database Passwords**: Use complex passwords (20+ chars)
- [ ] **JWT Expiration**: Set appropriate token expiration times
- [ ] **HTTPS**: Enable SSL/TLS certificates
- [ ] **Firewall**: Configure iptables/ufw rules
- [ ] **User Permissions**: Run containers with non-root users
- [ ] **Environment Files**: Never commit .env files to git
- [ ] **Rate Limiting**: Configure appropriate API limits
- [ ] **Database Access**: Restrict database network access
- [ ] **Monitoring**: Setup log monitoring and alerts

### **🔑 Generate Secure Keys**
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 📚 API Documentation

The complete API documentation is available at:
- **Development**: http://localhost:5002/docs
- **Production**: https://your-domain.com/docs

### **🔗 Key Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User authentication |
| GET | `/api/servers` | List all servers |
| POST | `/api/deploy` | Trigger deployment |
| GET | `/api/health/<ip>` | Server health check |
| GET | `/api/logs` | Deployment logs |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### **Common Issues**

#### **Database Connection Failed**
```bash
# Check PostgreSQL service
docker-compose logs postgres

# Verify database credentials
docker-compose exec postgres psql -U deployuser -d deploydb

# Reset database
docker-compose down -v && docker-compose up -d
```

#### **Frontend Not Loading**
```bash
# Check frontend logs
docker-compose logs frontend

# Verify environment variables
docker-compose exec frontend env | grep VITE

# Rebuild frontend
docker-compose build --no-cache frontend
```

#### **Backend API Errors**
```bash
# Check backend logs
docker-compose logs backend

# Verify Flask app
docker-compose exec backend python -c "from app import app; print('Flask OK')"

# Check migrations
docker-compose exec backend flask db current
```

### **Performance Optimization**

#### **Database Tuning**
```sql
-- Add indexes for better performance
CREATE INDEX idx_deploy_logs_created_at ON deploy_logs(created_at);
CREATE INDEX idx_servers_status ON servers(status);
CREATE INDEX idx_users_username ON users(username);
```

#### **Docker Optimization**
```bash
# Optimize Docker images
docker-compose build --no-cache --pull

# Clean up resources
docker system prune -af --volumes

# Monitor resource usage
docker stats --no-stream
```

---

## 📞 Support

For support and questions:
- **GitHub Issues**: [Create an issue](https://github.com/BataraKresn/trigger-deploy/issues)
- **Documentation**: [Wiki](https://github.com/BataraKresn/trigger-deploy/wiki)
- **Email**: sysadmin.app@sateknologi.id
        ├─ Framer Motion         ├─ Input Validation      ├─ Health Metrics
        └─ TypeScript            └─ Structured Logging    └─ Audit Trail
```

## 🚀 Quick Start

### Prerequisites
- **Docker** & **Docker Compose**
- **Node.js** 18+ (for development)
- **Python** 3.9+ (for development)

### 1. Clone Repository
```bash
git clone <repository-url>
cd trigger-deploy
```

### 2. Start with Docker Compose
```bash
# Start entire stack (database, backend, frontend)
./deploy-server.sh start

# Or manually with docker-compose
docker-compose up -d
```

### 3. Initialize Database
```bash
# Initialize database and create sample data
./deploy-server.sh init
```

### 4. Access Application
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5001/api
- **API Documentation**: http://localhost:5001/docs
- **Database**: localhost:5432

### 5. Default Credentials
- **Admin**: `admin` / `admin123`
- **Demo User**: `demo` / `demo123`

## 🛠️ Development Setup

### Backend Development
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Start development server
python app.py
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Database Setup
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run migrations
cd backend
flask db upgrade

# Create sample data
python -c "from app import app; from utils.seed_data import create_sample_data; app.app_context(); create_sample_data()"
```

## 📋 Management Commands

### Deploy Server Script
```bash
# Start entire stack
./deploy-server.sh start

# Stop entire stack
./deploy-server.sh stop

# Restart services
./deploy-server.sh restart

# View logs
./deploy-server.sh logs

# Check status
./deploy-server.sh status

# Initialize database
./deploy-server.sh init

# Clean up (removes all data)
./deploy-server.sh clean

# Development mode
./deploy-server.sh dev-backend   # Start backend in dev mode
./deploy-server.sh dev-frontend  # Start frontend in dev mode
```

### Docker Compose Commands
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild containers
docker-compose build --no-cache

# Remove volumes (deletes data)
docker-compose down -v
```

## 🗄️ Database Schema

### Core Tables
- **users**: User authentication & profiles
- **servers**: Server registry & configuration
- **deploy_logs**: Deployment history & outputs
- **health_metrics**: Server health monitoring data

### Relationships
```sql
users (1) ──→ (N) deploy_logs
users (1) ──→ (N) servers
servers (1) ──→ (N) deploy_logs
servers (1) ──→ (N) health_metrics
```

## 🔌 API Documentation

### Authentication Endpoints
```http
POST /api/auth/login          # User login
POST /api/auth/register       # User registration
POST /api/auth/refresh        # Refresh token
GET  /api/auth/me            # Current user info
POST /api/auth/logout        # User logout
```

### Server Management
```http
GET    /api/servers           # List servers
POST   /api/servers           # Create server
GET    /api/servers/{id}      # Get server details
PUT    /api/servers/{id}      # Update server
DELETE /api/servers/{id}      # Delete server
GET    /api/servers/search    # Search servers
```

### Deployment Operations
```http
GET    /api/deploy            # List deployments
POST   /api/deploy            # Trigger deployment
GET    /api/deploy/{id}       # Get deployment details
DELETE /api/deploy/{id}       # Cancel deployment
GET    /api/deploy/stats      # Deployment statistics
```

### Health Monitoring
```http
GET    /api/health            # List health checks
POST   /api/health/check      # Trigger health check
GET    /api/health/stats      # Health statistics
GET    /api/health/server/{alias}  # Server health status
```

### Logging & Monitoring
```http
GET    /api/logs              # List logs
GET    /api/logs/stats        # Log statistics
GET    /api/logs/download     # Export logs
GET    /api/logs/server/{alias}    # Server logs
```

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)
```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:pass@localhost/db
POSTGRES_USER=deployuser
POSTGRES_PASSWORD=deploypass
POSTGRES_DB=deploydb

# Application
API_HOST=0.0.0.0
API_PORT=5001
CORS_ORIGINS=http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/backend.log

# Security
PASSWORD_MIN_LENGTH=6
SESSION_TIMEOUT=3600
RATELIMIT_DEFAULT=100 per hour
```

#### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:5001/api
VITE_APP_NAME=Deploy Server
VITE_APP_VERSION=1.0.0
```

### Docker Compose Configuration
```yaml
services:
  postgres:    # Database service
  backend:     # Flask API service  
  frontend:    # React application
```

## 🔒 Security Features

- **JWT Authentication** with refresh tokens
- **Role-based access control** (Admin/User)
- **Rate limiting** on API endpoints
- **Input validation** & sanitization
- **SQL injection protection** with SQLAlchemy ORM
- **CORS configuration** for cross-origin requests
- **Password hashing** with bcrypt
- **Session management** & timeout

## 📊 Monitoring & Logging

### Structured Logging
- **Application logs** with timestamps & levels
- **Deployment logs** with execution output
- **Health check logs** with response times
- **Error tracking** with stack traces
- **Performance metrics** & statistics

### Health Monitoring
- **Database connectivity** checks
- **API endpoint** health status
- **Server ping** & response times
- **System resource** monitoring
- **Service availability** tracking

## 🧪 Testing

### Backend Testing
```bash
cd backend

# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Frontend Testing
```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Run with coverage
npm run test:coverage
```

## 📦 Deployment

### Production Deployment
1. **Configure environment variables**
2. **Setup SSL certificates**
3. **Configure reverse proxy** (Nginx/Apache)
4. **Setup database backups**
5. **Configure monitoring** & alerting
6. **Deploy with Docker Compose**

### Scaling Considerations
- **Database connection pooling**
- **Load balancer configuration**
- **Horizontal scaling** with multiple backend instances
- **CDN integration** for frontend assets
- **Caching strategies** (Redis/Memcached)

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Documentation

### Getting Help
- **GitHub Issues**: For bug reports & feature requests
- **Discussions**: For questions & community support
- **API Documentation**: Available at `/docs/` endpoint
- **Wiki**: Detailed documentation & tutorials

### Troubleshooting
- **Database connection issues**: Check PostgreSQL service status
- **Authentication errors**: Verify JWT configuration
- **CORS issues**: Check frontend/backend URL configuration
- **Permission errors**: Verify user roles & permissions

---

## 🎯 Roadmap

- [ ] **Multi-tenant support** with organization management
- [ ] **Advanced monitoring** with Prometheus/Grafana
- [ ] **CI/CD pipeline** integration
- [ ] **Kubernetes deployment** manifests
- [ ] **Real-time notifications** with WebSockets
- [ ] **Plugin system** for custom integrations
- [ ] **Advanced reporting** & analytics
- [ ] **Backup & restore** functionality

---

**Made with ❤️ for DevOps Teams**

*Deploy Server - Streamlining deployment management for modern development teams*
