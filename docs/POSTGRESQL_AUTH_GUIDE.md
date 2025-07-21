# PostgreSQL Authentication Best Practices Guide

## 📋 Overview

Sistem Trigger Deploy menggunakan dual authentication system:
1. **PostgreSQL User Database** - Untuk manajemen user yang proper
2. **Legacy Authentication** - Sebagai fallback menggunakan environment variables

## 🔧 Configuration Setup

### 1. Environment Variables (.env)

```bash
# ================================
# PostgreSQL Database Configuration
# ================================

# Core Database Settings
POSTGRES_DB=trigger_deploy
POSTGRES_USER=trigger_deploy_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_HOST=postgres  # 'postgres' untuk Docker, 'localhost' untuk development
POSTGRES_PORT=5432

# Database URL (Auto-generated dari setting di atas)
DATABASE_URL=postgresql://trigger_deploy_user:secure_password_123@postgres:5432/trigger_deploy

# Database Pool Settings
POSTGRES_MIN_CONNECTIONS=1
POSTGRES_MAX_CONNECTIONS=20
POSTGRES_CONNECTION_TIMEOUT=10
POSTGRES_COMMAND_TIMEOUT=5

# User Authentication Settings
POSTGRES_AUTH_ENABLED=true
AUTO_CREATE_ADMIN=true
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
DEFAULT_ADMIN_EMAIL=admin@trigger-deploy.local

# Security Tokens
DEPLOY_TOKEN=SATindonesia2026
LOGIN_PASSWORD=admin123  # Fallback authentication
JWT_SECRET=ff4ad765ebb762ab6f220b5cb5191a99bd87a8ea
```

### 2. Authentication Flow

```
Request → Check PostgreSQL User → Fallback to Legacy → Reject
```

1. **PostgreSQL User Authentication**: Username/password dicek di database
2. **Legacy Authentication**: Menggunakan LOGIN_PASSWORD environment variable
3. **API Token Authentication**: Menggunakan DEPLOY_TOKEN untuk API calls

## 🚀 Quick Setup

### Option 1: Automated Update (Recommended)
```bash
./update-docker.sh
```

### Option 2: Manual Setup
```bash
# 1. Stop containers
docker-compose down

# 2. Rebuild dengan dependencies baru
docker-compose build --no-cache

# 3. Start services
docker-compose up -d

# 4. Check logs
docker-compose logs -f dev-trigger-deploy
```

## 🔑 Authentication Methods

### 1. Web Interface Login
- **URL**: `http://localhost:3111/login`
- **Default Username**: `admin`
- **Default Password**: `admin123`
- **Use Case**: Dashboard access via browser

### 2. API Token Authentication
- **Header**: `Authorization: Bearer SATindonesia2026`
- **Use Case**: CI/CD pipelines dan automated deployments
- **Example**:
  ```bash
  curl -H "Authorization: Bearer SATindonesia2026" \
       http://localhost:3111/api/stats
  ```

### 3. Quick Token Login
- **URL**: `http://localhost:3111/login` (Quick Access section)
- **Token**: `SATindonesia2026`
- **Use Case**: Quick access menggunakan deployment token

## 🛡️ Security Best Practices

### 1. Production Environment
```bash
# Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -hex 32)
DEPLOY_TOKEN=$(openssl rand -base64 32)

# Set strong admin credentials
DEFAULT_ADMIN_PASSWORD=$(openssl rand -base64 16)
```

### 2. Environment Separation
```bash
# Development
POSTGRES_HOST=localhost
FLASK_ENV=development
SHOW_DEMO_CREDENTIALS=true

# Production
POSTGRES_HOST=postgres
FLASK_ENV=production
SHOW_DEMO_CREDENTIALS=false
```

### 3. Database Security
```bash
# Enable SSL for production
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Use environment-specific users
POSTGRES_USER=trigger_deploy_prod_user  # Production
POSTGRES_USER=trigger_deploy_dev_user   # Development
```

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nama_lengkap VARCHAR(255) NOT NULL DEFAULT '',
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('superadmin', 'user')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE NULL
);
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Check connection from app
docker-compose exec dev-trigger-deploy python -c "
import asyncio
from src.models.database import init_database
asyncio.run(init_database())
"
```

#### 2. Authentication Failed
```bash
# Check if admin user exists
docker-compose exec postgres psql -U trigger_deploy_user -d trigger_deploy -c "
SELECT username, email, role, is_active FROM users WHERE role = 'superadmin';
"

# Reset admin password
docker-compose exec postgres psql -U trigger_deploy_user -d trigger_deploy -c "
UPDATE users SET password_hash = 'new_hash', salt = 'new_salt' 
WHERE username = 'admin';
"
```

#### 3. Missing Dependencies
```bash
# Rebuild container with dependencies
docker-compose build --no-cache dev-trigger-deploy

# Check if aiohttp is installed
docker-compose exec dev-trigger-deploy pip list | grep aiohttp
```

## 📊 Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:3111/api/health

# Database health
docker-compose exec postgres pg_isready -U trigger_deploy_user -d trigger_deploy

# User statistics
curl -H "Authorization: Bearer SATindonesia2026" \
     http://localhost:3111/api/users/stats
```

### Logs
```bash
# Application logs
docker-compose logs -f dev-trigger-deploy

# Database logs
docker-compose logs -f postgres

# Authentication logs
docker-compose exec dev-trigger-deploy tail -f logs/app.log | grep -i auth
```

## 🚀 Advanced Configuration

### Connection Pooling
```bash
# Optimize for high traffic
POSTGRES_MIN_CONNECTIONS=5
POSTGRES_MAX_CONNECTIONS=50
POSTGRES_CONNECTION_TIMEOUT=30

# Optimize for low traffic
POSTGRES_MIN_CONNECTIONS=1
POSTGRES_MAX_CONNECTIONS=10
POSTGRES_CONNECTION_TIMEOUT=10
```

### Multiple Environments
```bash
# docker-compose.prod.yml
services:
  dev-trigger-deploy:
    environment:
      - DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/prod_db
      - FLASK_ENV=production
      - SHOW_DEMO_CREDENTIALS=false

# docker-compose.dev.yml  
services:
  dev-trigger-deploy:
    environment:
      - DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/dev_db
      - FLASK_ENV=development
      - SHOW_DEMO_CREDENTIALS=true
```

## 📝 Migration Guide

### From File-based to PostgreSQL

1. **Backup existing data**:
   ```bash
   cp config/users.json config/users.json.backup
   ```

2. **Update configuration**:
   ```bash
   # Set PostgreSQL settings in .env
   POSTGRES_AUTH_ENABLED=true
   AUTO_CREATE_ADMIN=true
   ```

3. **Run update script**:
   ```bash
   ./update-docker.sh
   ```

4. **Verify migration**:
   ```bash
   # Check if users migrated successfully
   curl -H "Authorization: Bearer SATindonesia2026" \
        http://localhost:3111/api/users
   ```

## 🎯 Next Steps

1. **Implement Role-based Access Control (RBAC)**
2. **Add OAuth2/OpenID Connect integration**  
3. **Implement API rate limiting per user**
4. **Add audit logging for user actions**
5. **Implement session management with Redis**

---

💡 **Pro Tip**: Selalu gunakan environment variables yang berbeda untuk development dan production untuk keamanan yang optimal.
