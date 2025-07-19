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
