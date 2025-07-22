# 🚀 Trigger Deploy Server

Automated deployment management platform with comprehensive monitoring, analytics, and PostgreSQL integration.

## ✅ Integration Status

**All major integration issues have been resolved!** ✨

- ✅ PostgreSQL user management system  
- ✅ JWT authentication with role-based access
- ✅ Complete API endpoints for deployment
- ✅ Docker containerization with health checks
- ✅ Monitoring and analytics dashboard
- ✅ Audit trail and deployment history

**Quick Start:** See [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md) for detailed setup guide.

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

**Quick Setup (First Time):**
```bash
git clone <repository-url>
cd trigger-deploy
chmod +x setup.sh
./setup.sh
```

**Manual Setup:**
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

3. **Create required directories**
   ```bash
   mkdir -p ./data/postgres ./logs ./trigger-logs ./config
   ```

4. **Setup server configurations**
   ```bash
   # Edit config/servers.json
   # Edit config/services.json
   ```

5. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

6. **Access the application**
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

## 🎨 Frontend Development

This project uses **Tailwind CSS** for styling. Instead of CDN (which causes production warnings), we use a build process to generate optimized CSS.

### CSS Build Process

#### For Docker Deployment (Automatic)
CSS is automatically built during Docker build process using multi-stage build.

#### For Local Development

1. **Install Node.js and Tailwind CSS CLI**:
   ```bash
   # Install Node.js first, then:
   npm install -g tailwindcss
   ```

2. **Build CSS**:
   ```bash
   # Use the build script (with Node.js)
   ./build-tailwind.sh
   
   # Or use Docker-based build (no Node.js required)
   ./build-tailwind-docker.sh
   
   # Or manually:
   tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify
   ```

3. **Watch for changes** (development):
   ```bash
   tailwindcss -i static/css/input.css -o static/css/tailwind.css --watch
   ```

### Tailwind Configuration

- **Config file**: `tailwind.config.js`
- **Input CSS**: `static/css/input.css`
- **Output CSS**: `static/css/tailwind.css`
- **Content sources**: Templates, static JS files

The build process scans all HTML templates and generates only the CSS classes that are actually used, resulting in a much smaller file size compared to the full CDN version.

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

#### Volume/Directory Issues
```bash
# If you get "no such file or directory" errors:
mkdir -p ./data/postgres ./logs ./trigger-logs ./config

# Clean start (removes all data):
docker-compose down -v
docker volume prune -f
./setup.sh

# Fix permissions (if needed):
sudo chown -R $USER:$USER ./data ./logs ./trigger-logs
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
# First time setup (recommended)
./setup.sh

# Start the application
docker-compose up -d

# Update and restart
./update-docker.sh

# Fix network/volume issues
./fix-network.sh

# View all logs
docker-compose logs -f

# Stop the application
docker-compose down

# Clean restart (removes data)
docker-compose down -v && ./setup.sh

# Database access
docker-compose exec postgres psql -U trigger_deploy_user -d trigger_deploy

# Application shell
docker-compose exec dev-trigger-deploy bash
```

### Default Access

- **Landing Page**: http://localhost:3111
- **Dashboard**: http://localhost:3111/home
- **Login Page**: http://localhost:3111/login
- **PostgreSQL**: localhost:5432
- **Default Login**: admin123 (configurable via LOGIN_PASSWORD)
- **API Token**: SATindonesia2026 (configurable via DEPLOY_TOKEN)

### Important Files

- **Main Config**: `.env`
- **Servers**: `config/servers.json`
- **Services**: `config/services.json`
- **Docker**: `docker-compose.yml`
- **Logs**: `logs/` and `trigger-logs/`

---

## 🚀 Future Enhancements

### **💡 Potential Additions**
- **Customer testimonials section** with user success stories
- **Integration screenshots** showcasing platform capabilities  
- **Video demonstrations** for onboarding and tutorials
- **Live chat widget** for real-time user support
- **A/B testing capabilities** for UI optimization
- **Progressive Web App features** for mobile experience
- **Multi-language support** for global users
- **Advanced notification system** with email/SMS alerts

### **📊 Analytics Integration**
- **Google Analytics tracking** for user behavior insights
- **Conversion event tracking** for deployment success rates
- **User behavior analysis** with heatmaps and session recordings
- **Performance monitoring** with real-time metrics dashboard
- **Custom dashboards** for different user roles
- **Data export capabilities** for business intelligence
- **Automated reports** with scheduled delivery
- **Retention analysis** and user engagement metrics

### **📝 Content Management**
- **Dynamic content loading** with CMS integration
- **Multi-language support** with translation management
- **Content personalization** based on user preferences
- **Featured updates section** for product announcements
- **Rich text editor** for documentation updates
- **Version control** for content changes
- **SEO optimization** tools and meta management
- **Content scheduling** and auto-publishing

### **🎯 User Experience Enhancements**
- **Interactive tutorials** with guided onboarding
- **Contextual help system** with smart suggestions
- **Customizable dashboards** with drag-and-drop widgets
- **Advanced search functionality** across all content
- **Keyboard shortcuts** for power users
- **Accessibility improvements** (WCAG 2.1 compliance)
- **Mobile-first responsive design** optimization
- **Offline mode** for critical operations

## 📋 Best Practices

### **⚡ Performance**
- **Optimize images and assets** with lazy loading and compression
- **Minimize HTTP requests** through bundling and caching
- **Use efficient animations** with hardware acceleration
- **Implement caching strategies** at multiple levels
- **Database query optimization** with proper indexing
- **CDN integration** for global content delivery
- **Code splitting** for faster initial load times
- **Service Worker** implementation for offline capabilities

### **👥 User Experience**
- **Clear call-to-action placement** with conversion optimization
- **Intuitive navigation flow** with breadcrumbs and progress indicators
- **Fast loading times** (< 3 seconds for critical pages)
- **Mobile-friendly design** with touch-optimized interfaces
- **Consistent design language** across all components
- **Error handling** with helpful user messages
- **Loading states** and progress indicators
- **Accessibility compliance** for inclusive design

### **🔧 Maintenance**
- **Regular content updates** with automated workflows
- **Performance monitoring** with alerting systems
- **Browser compatibility testing** across major browsers
- **Security best practices** with regular audits
- **Code quality standards** with automated linting
- **Documentation maintenance** with version control
- **Backup strategies** for data protection
- **Disaster recovery** planning and testing

### **📈 Scalability**
- **Microservices architecture** for independent scaling
- **Load balancing** strategies for high availability
- **Database sharding** for large datasets
- **Horizontal scaling** with container orchestration
- **API rate limiting** and throttling
- **Resource monitoring** and auto-scaling
- **Performance benchmarking** and optimization
- **Capacity planning** based on usage patterns

**Built with ❤️ for streamlined deployment management**
