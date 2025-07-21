# 🚀 Trigger Deploy Server

Automated deployment management platform with comprehensive monitoring and analytics.

## 📁 Project Structure

```
trigger-deploy/
├── 📁 src/                     # Source code
│   ├── 📁 models/              # Data models
│   │   ├── config.py           # Configuration model
│   │   └── entities.py         # Server, Service, Deployment models
│   ├── 📁 routes/              # Route handlers
│   │   ├── main.py             # Main web routes
│   │   ├── api.py              # API endpoints
│   │   └── deploy.py           # Deployment routes
│   └── 📁 utils/               # Utility functions
│       └── helpers.py          # Helper functions
├── 📁 static/                  # Static assets
│   ├── 📁 css/                 # Stylesheets
│   ├── 📁 js/                  # JavaScript files
│   └── 📁 images/              # Images and favicons
├── 📁 templates/               # HTML templates
├── 📁 config/                  # Configuration files
│   ├── servers.json            # Server configurations
│   └── services.json           # Service configurations
├── 📁 scripts/                 # Shell scripts
├── 📁 logs/                    # Application logs
├── 📁 trigger-logs/            # Deployment logs
├── 📁 tests/                   # Test files
├── 📁 data/                    # Database data
├── app.py                      # Main Flask application
├── wsgi.py                     # WSGI entry point
├── docker-compose.yml          # Docker compose configuration
├── Dockerfile                  # Docker image configuration
└── requirements.txt            # Python dependencies
```

## ✨ Features

- **🖥️ Server Management**: Multi-server deployment with health monitoring
- **📊 Real-time Metrics**: Comprehensive dashboard with deployment statistics
- **🔍 Service Monitoring**: HTTP/HTTPS service health checks
- **📝 Deployment History**: Detailed logs and deployment tracking
- **🔒 Authentication**: Token-based security
- **📱 Responsive Design**: Mobile-friendly interface
- **📧 Email Notifications**: Deployment status alerts
- **🐳 Docker Support**: Container deployment capabilities
- **🗃️ PostgreSQL Integration**: Robust database with health monitoring
- **📺 Telegram Notifications**: Real-time deployment alerts

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (recommended)
- PostgreSQL (if not using Docker)
- SSH access to target servers

### Installation

#### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trigger-deploy
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

3. **Setup server configurations**
   ```bash
   # Edit config/servers.json
   # Edit config/services.json
   ```

4. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   ```bash
   # Application: http://localhost:3111
   # PostgreSQL: localhost:5432
   ```

#### Option 2: Manual Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trigger-deploy
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup PostgreSQL database**
   ```bash
   # Install PostgreSQL and create database
   createdb trigger_deploy
   psql trigger_deploy < scripts/init-db.sql
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

6. **Setup server configurations**
   ```bash
   # Edit config/servers.json
   # Edit config/services.json
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Security
DEPLOY_TOKEN=your-secure-token
LOGIN_PASSWORD=admin123
JWT_SECRET=your-jwt-secret-key

# PostgreSQL Database Configuration
POSTGRES_DB=trigger_deploy
POSTGRES_USER=trigger_deploy_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://trigger_deploy_user:secure_password_123@localhost:5432/trigger_deploy

# Application Configuration
APP_PORT=3111
FLASK_ENV=production

# Logging
LOG_DIR=trigger-logs
LOG_RETENTION_DAYS=7
MAX_LOG_SIZE=10485760

# Server Configuration
SERVERS_FILE=config/servers.json
SERVICES_FILE=config/services.json

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Email Notifications
EMAIL_ENABLED=false
EMAIL_TO=admin@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
TELEGRAM_ENABLED=false

# Docker Configuration
DOCKER_ENABLED=true
SHOW_DEMO_CREDENTIALS=false

# Security Headers
SECURE_HEADERS=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
```

### Server Configuration (config/servers.json)

```json
[
  {
    "name": "Production Server",
    "ip": "192.168.1.100",
    "user": "ubuntu",
    "description": "Main production server",
    "alias": "prod-server",
    "path": "/home/ubuntu/app",
    "type": "Production Server",
    "port": 22
  }
]
```

### Service Configuration (config/services.json)

```json
[
  {
    "name": "Main Website",
    "url": "https://example.com",
    "check_interval": 300,
    "timeout": 10
  }
]
```

## 🎯 API Endpoints

### Authentication
All deployment endpoints require authentication via `DEPLOY_TOKEN`.

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Home page |
| `GET` | `/deploy-servers` | Server deployment interface |
| `GET` | `/metrics` | Metrics dashboard |
| `GET` | `/services-monitor` | Service monitoring |
| `POST` | `/trigger` | Trigger deployment |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/metrics/stats` | Deployment statistics |
| `GET` | `/api/metrics/history` | Deployment history |
| `GET` | `/api/metrics/servers` | Server metrics |
| `GET` | `/api/metrics/system` | System information |
| `POST` | `/api/health` | Health check |

## 🔧 Development

### Project Architecture

The application follows a clean architecture pattern:

- **Models**: Data structures and configuration
- **Routes**: HTTP request handlers organized by feature
- **Utils**: Reusable helper functions
- **Static Assets**: Organized by type (CSS, JS, Images)

### Code Organization

- **Separation of Concerns**: Each module has a single responsibility
- **Modular Design**: Easy to extend and maintain
- **Clean Dependencies**: Clear import structure
- **Type Safety**: Using dataclasses and type hints

### Adding New Features

1. **Models**: Define data structures in `src/models/`
2. **Routes**: Add endpoints in appropriate route files
3. **Utils**: Add helper functions in `src/utils/`
4. **Frontend**: Add assets in organized static folders

## 🚀 Deployment

### Development
```bash
# Manual
python app.py

# Or with Docker
docker-compose up
```

### Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Docker Production
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Update and rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Health Checks

The application includes comprehensive health monitoring:

- **Application Health**: `GET /api/health`
- **PostgreSQL Health**: Automated health checks in Docker
- **Service Monitoring**: Real-time HTTP endpoint monitoring

## � Docker Configuration

The project includes a comprehensive Docker setup with the following services:

### Services

- **PostgreSQL**: Database service with persistent storage
- **Trigger Deploy App**: Main application service

### Docker Compose Features

- **Health Checks**: Automated service health monitoring
- **Volume Persistence**: Data and logs persistence
- **Network Isolation**: Custom bridge network for security
- **Environment Configuration**: Flexible environment variable setup
- **Development Mode**: Hot reload with volume mounting

### Container Details

```yaml
# PostgreSQL Container
- Image: postgres:15-alpine
- Port: 5432
- Health Check: pg_isready
- Volumes: postgres_data, init-db.sql, logs

# Application Container
- Build: Custom Dockerfile
- Port: 3111 (configurable via APP_PORT)
- Health Check: curl /api/health
- Volumes: SSH keys, logs, config, development files
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Execute commands in container
docker-compose exec dev-trigger-deploy bash
docker-compose exec postgres psql -U trigger_deploy_user -d trigger_deploy

# Restart specific service
docker-compose restart [service-name]

# Remove containers and volumes
docker-compose down -v
```

## �📊 Monitoring

The application provides comprehensive monitoring:

- **Server Health**: Real-time server status
- **Deployment Metrics**: Success rates, duration, history
- **Service Monitoring**: HTTP endpoint health checks
- **System Metrics**: CPU, memory, disk usage
- **Log Management**: Centralized logging with rotation

## 🔒 Security

- **Token Authentication**: Secure API access
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Secure request handling
- **Log Security**: Sensitive data filtering

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the architecture patterns
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support & Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# View PostgreSQL logs
docker-compose logs postgres

# Connect to database
docker-compose exec postgres psql -U trigger_deploy_user -d trigger_deploy
```

#### Application Issues
```bash
# Check application logs
docker-compose logs dev-trigger-deploy

# Check application health
curl http://localhost:3111/api/health

# Restart application
docker-compose restart dev-trigger-deploy
```

#### SSH Key Issues
```bash
# Ensure SSH keys exist and have correct permissions
ls -la ~/.ssh/
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

#### Port Conflicts
```bash
# If port 3111 is in use, change APP_PORT in .env
APP_PORT=3112

# If PostgreSQL port 5432 is in use
POSTGRES_PORT=5433
```

### Debug Mode

To run in debug mode:
```bash
# Set environment variable
FLASK_ENV=development

# Or in .env file
echo "FLASK_ENV=development" >> .env
```

### Logs Location

- Application logs: `logs/app.log`
- Deployment logs: `trigger-logs/`
- PostgreSQL logs: `logs/postgresql/`
- Docker logs: `docker-compose logs`

For additional issues and questions:
1. Check the logs in respective directories
2. Review configuration files
3. Ensure all dependencies are installed
4. Verify server connectivity and SSH access

---

## 🚀 Quick Reference

### Essential Commands

```bash
# Start the application
docker-compose up -d

# View all logs
docker-compose logs -f

# Stop the application
docker-compose down

# Update and restart
docker-compose down && docker-compose build && docker-compose up -d

# Database access
docker-compose exec postgres psql -U trigger_deploy_user -d trigger_deploy

# Application shell
docker-compose exec dev-trigger-deploy bash
```

### Default Access

- **Web Interface**: http://localhost:3111
- **PostgreSQL**: localhost:5432
- **Default Login**: admin123 (configurable via LOGIN_PASSWORD)
- **API Token**: SATindonesia2026 (configurable via DEPLOY_TOKEN)

### Important Files

- **Main Config**: `.env`
- **Servers**: `config/servers.json`
- **Services**: `config/services.json`
- **Docker**: `docker-compose.yml`
- **Logs**: `logs/` and `trigger-logs/`

**Built with ❤️ for streamlined deployment management**
