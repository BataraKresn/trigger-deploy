# 🚀 Trigger Deploy Server

A comprehensive, production-ready webhook deployment server with real-time service monitoring, multi-server management, authentication system, and advanced logging capabilities.

---

## 📁 Project Structure

```
trigger-deploy/
├── app.py                    # Main Flask application
├── deploy-wrapper.sh         # Deployment execution script
├── deployment_history.py     # Deployment tracking module
├── service_monitor.py        # Service monitoring module
├── test_app.py              # Unit tests
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── wsgi.py                  # WSGI entry point
├── docker-compose.yml       # Docker configuration
├── Dockerfile               # Docker container config
├── static/
│   ├── servers.json         # Server configuration
│   ├── services.json        # Services monitoring config
│   ├── styles.css           # Enhanced UI styles
│   ├── home.js              # Home page functionality
│   ├── deploy.js            # Deployment interface
│   ├── services-monitor.js  # Services monitoring interface
│   ├── metrics.js           # Metrics dashboard
│   └── favicon.ico          # Application icon
├── templates/
│   ├── home.html            # Enhanced landing page
│   ├── deploy_servers.html  # Deployment interface
│   ├── services_monitor.html # Real-time services monitoring
│   ├── metrics.html         # System metrics dashboard
│   ├── trigger_result.html  # Deployment result display
│   └── invalid_token.html   # Authentication error page
├── trigger-logs/            # Deployment logs (auto-created)
└── logs/                    # Application logs (auto-created)
    ├── app.log              # Main application log
    ├── deployment.log       # Deployment specific logs
    ├── security.log         # Security events log
    └── error.log            # Error tracking log
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Security Configuration
DEPLOY_TOKEN=your_secure_token_here

# Logging Configuration
LOG_DIR=trigger-logs
LOG_RETENTION_DAYS=7
MAX_LOG_SIZE=10485760

# Server Configuration
SERVERS_FILE=static/servers.json

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=trigger-deploy@yourdomain.com
EMAIL_TO=admin@yourdomain.com

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=false

# Service Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=60
HEALTH_CHECK_TIMEOUT=30
ALERT_COOLDOWN=300
```
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
```

### Server Configuration (`static/servers.json`)

```json
[
  {
    "ip": "192.168.1.100",
    "user": "deploy",
    "name": "Production Server 1",
    "description": "Main production server"
  },
  {
    "ip": "192.168.1.101", 
    "user": "deploy",
    "name": "Staging Server",
    "description": "Testing environment"
  }
]
```

### Services Monitoring Configuration (`static/services.json`)

```json
{
  "local_services": [
    {
      "name": "Web Server",
      "type": "docker",
      "container_name": "nginx",
      "description": "Main web server",
      "critical": true
    },
    {
      "name": "Database",
      "type": "docker", 
      "container_name": "postgres",
      "description": "PostgreSQL database",
      "critical": true
    }
  ],
  "remote_services": [
    {
      "name": "Production API",
      "type": "http",
      "url": "https://api.yourdomain.com/health",
      "expected_status": 200,
      "timeout": 10,
      "description": "External API service",
      "critical": true
    },
    {
      "name": "CDN Service",
      "type": "http",
      "url": "https://cdn.yourdomain.com",
      "expected_status": 200,
      "timeout": 5,
      "description": "Content delivery network",
      "critical": false
    },
    {
      "name": "Remote Database",
      "type": "tcp",
      "host": "db.yourdomain.com",
      "port": 5432,
      "timeout": 5,
      "description": "Backup database server",
      "critical": false
    }
  ]
}
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Configure Services (Optional)

```bash
# Copy example services configuration
cp static/services.json.example static/services.json
# Edit services.json with your monitoring requirements
```

### 4. Run Application

#### Development Mode
```bash
python app.py
```

#### Production Mode (Docker)
```bash
docker-compose up -d
```

#### Production Mode (WSGI)
```bash
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

### 5. Access Web Interface

- **Home Dashboard**: `http://localhost:5000/`
- **Services Monitor**: `http://localhost:5000/services-monitor`
- **Metrics Dashboard**: `http://localhost:5000/metrics-dashboard`
- **Deploy Servers**: `http://localhost:5000/deploy-servers`

### 6. Run Tests

```bash
python test_app.py
```

---

## 🧠 Features

### 🔐 Enhanced Security
- **Token-based authentication** with secure HMAC comparison
- **Session storage** for seamless user experience
- **Rate limiting** (configurable per endpoint)
- **Input validation** for all parameters
- **Path traversal protection** for file operations
- **IP address validation** for server endpoints
- **Security event logging** with detailed audit trails

### 📊 Real-time Service Monitoring
- **Docker container monitoring** with health checks
- **Remote service monitoring** (HTTP/HTTPS, TCP)
- **Configurable health check intervals** and timeouts
- **Critical service alerts** with email/Telegram notifications
- **Service status dashboard** with real-time updates
- **Monitoring pause/resume controls**
- **Service configuration management** via web interface

### 📈 Advanced Monitoring & Logging
- **Structured logging** with rotation and retention
- **Real-time log streaming** via Server-Sent Events
- **Multiple log levels** (app, deployment, security, error)
- **Health check endpoints** with comprehensive system metrics
- **Deployment history tracking** with detailed records
- **Automatic log cleanup** based on retention policy
- **Performance metrics** and system resource monitoring

### 🖥️ Multi-Server Support
- **SSH-based deployment** to multiple servers
- **Server configuration management** via JSON
- **Server health checks** before deployment
- **Parallel deployment support**
- **Deployment status tracking** per server

### 🌐 Enhanced Web Interface
- **Fully responsive UI** for all screen sizes
- **Modern dark/light theme** with smooth animations
- **Real-time status updates** using WebSockets
- **Interactive dashboards** for monitoring and metrics
- **Modal-based configuration** with JSON editing
- **Toast notifications** for user feedback
- **Progressive Web App** features

### 📧 Notification System
- **Email notifications** for deployment events
- **Telegram bot integration** for instant alerts
- **Configurable notification triggers**
- **Rich notification content** with logs and status

---

## 📡 API Endpoints

### Core Deployment Endpoints

| Method | Endpoint | Description | Rate Limit | Authentication |
|--------|----------|-------------|------------|----------------|
| `POST/GET` | `/trigger` | Trigger deployment to servers | 5/min | Token required |
| `POST` | `/ping` | Check server connectivity | 20/min | Token required |
| `GET` | `/health` | System health check | 30/min | Public |
| `GET` | `/metrics` | Application metrics | 10/min | Token required |

### Services Monitoring Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| `GET` | `/api/services/status` | Get all services status | Public |
| `GET` | `/api/services/config` | Get services configuration | Public |
| `POST` | `/api/services/config` | Update services configuration | Token required |
| `POST` | `/api/services/toggle-monitoring` | Toggle monitoring on/off | Token required |

### Management Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| `GET` | `/servers` | List configured servers | Public |
| `GET` | `/logs/<filename>` | Download specific log file | Token required |
| `GET` | `/api/logs` | List available log files | Token required |
| `GET` | `/api/deployment-history` | Get deployment history | Token required |

### Web Interface Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Home dashboard |
| `GET` | `/deploy-servers` | Server deployment interface |
| `GET` | `/services-monitor` | Real-time services monitoring |
| `GET` | `/metrics-dashboard` | System metrics dashboard |
| `GET` | `/logs` | List deployment logs |
| `GET` | `/log-content` | Get log file content |
| `GET` | `/stream-log` | Stream log in real-time |

---

## 🔍 Services Monitor Usage

### Accessing Services Monitor

Navigate to `http://localhost:5000/services-monitor` to access the real-time services monitoring dashboard.

### Features Overview

**Status Dashboard:**
- Real-time service status updates every 60 seconds
- Summary cards showing total, healthy, unhealthy, and critical services
- Visual indicators for service health status
- Last updated timestamp with countdown to next check

**Control Panel:**
- Start/Pause monitoring toggle
- Manual refresh services status
- Configure services via web interface
- Responsive design for mobile and desktop

**Service Types Supported:**
- **Docker Containers**: Monitor local Docker containers by name
- **HTTP/HTTPS Services**: Monitor web services with expected status codes
- **TCP Services**: Monitor network services by host and port

### Configuration Management

**Via Web Interface:**
1. Click "⚙️ Configure Services" button
2. Edit the JSON configuration in the modal
3. Save changes to apply new monitoring settings

**Configuration Structure:**
```json
{
  "local_services": [
    {
      "name": "Web Server",
      "type": "docker",
      "container_name": "nginx",
      "description": "Main web server",
      "critical": true
    }
  ],
  "remote_services": [
    {
      "name": "Production API",
      "type": "http",
      "url": "https://api.example.com/health",
      "expected_status": 200,
      "timeout": 10,
      "description": "External API service",
      "critical": true
    },
    {
      "name": "Database Server",
      "type": "tcp",
      "host": "db.example.com",
      "port": 5432,
      "timeout": 5,
      "description": "PostgreSQL database",
      "critical": true
    }
  ]
}
```

### Authentication

Services monitoring uses token-based authentication for configuration changes:
- **Reading status**: No authentication required
- **Configuring services**: Requires deployment token
- **Toggle monitoring**: Requires deployment token

When prompted, enter your `DEPLOY_TOKEN` in the modal dialog.

### API Integration

**Get Services Status:**
```bash
curl http://localhost:5000/api/services/status
```

**Update Configuration:**
```bash
curl -X POST http://localhost:5000/api/services/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d @services.json
```

**Toggle Monitoring:**
```bash
curl -X POST http://localhost:5000/api/services/toggle-monitoring \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"enable": true}'
```

---

## 📊 Deployment Usage

### Example Usage

#### Trigger Deployment

```bash
# POST request
curl -X POST https://your-server.com/trigger \
  -H "Content-Type: application/json" \
  -d '{"token": "your_token", "server": "192.168.1.100"}'

# GET request (for webhooks)
curl "https://your-server.com/trigger?token=your_token&server=192.168.1.100"
```

#### Check Server Health

```bash
curl -X POST https://your-server.com/ping \
  -H "Content-Type: application/json" \
  -d '{"server": "192.168.1.100"}'
```

#### Get System Metrics

```bash
curl "https://your-server.com/metrics?token=your_token"
```

---

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/BataraKresn/trigger-deploy.git
cd trigger-deploy

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build the image
docker build -t trigger-deploy .

# Run the container
docker run -d \
  --name trigger-deploy \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/trigger-logs:/app/trigger-logs \
  -v $(pwd)/static:/app/static \
  --env-file .env \
  trigger-deploy
```

### Production Deployment

For production environments, consider:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  trigger-deploy:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DEPLOY_TOKEN=${DEPLOY_TOKEN}
    volumes:
      - ./logs:/app/logs
      - ./trigger-logs:/app/trigger-logs
      - ./static:/app/static
    command: gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🛠️ Troubleshooting

### Common Issues

**1. Services Monitor Shows No Data**
```bash
# Check if Docker is running
docker ps

# Verify services configuration
cat static/services.json

# Check application logs
tail -f logs/app.log
```

**2. Authentication Errors (HTTP 401)**
- Verify `DEPLOY_TOKEN` in environment variables
- Clear browser session storage and retry
- Check token in JavaScript console: `sessionStorage.getItem('deployToken')`

**3. Deployment Fails**
```bash
# Check SSH connectivity
ssh user@target-server "echo 'Connection successful'"

# Verify server configuration
cat static/servers.json

# Check deployment logs
tail -f trigger-logs/trigger-*.log
```

**4. Service Health Checks Fail**
- Verify network connectivity to target services
- Check timeout settings in services configuration
- Review service monitor logs for detailed errors

### Debug Mode

Enable debug mode for development:

```bash
export FLASK_DEBUG=1
export FLASK_ENV=development
python app.py
```

### Log Locations

- **Application logs**: `logs/app.log`
- **Deployment logs**: `trigger-logs/trigger-*.log`
- **Security logs**: `logs/security.log`
- **Error logs**: `logs/error.log`

### Performance Tuning

**For High-Traffic Environments:**

```python
# Increase worker processes
gunicorn --workers 8 --worker-class gevent wsgi:app

# Adjust rate limiting
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW=60

# Optimize monitoring intervals
MONITORING_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
```

---

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/BataraKresn/trigger-deploy.git
cd trigger-deploy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run tests
python test_app.py

# Start development server
python app.py
```

### Code Structure

- **`app.py`**: Main Flask application with all routes
- **`service_monitor.py`**: Service monitoring logic and health checks
- **`deployment_history.py`**: Deployment tracking and history management
- **`static/`**: Frontend assets (CSS, JavaScript)
- **`templates/`**: HTML templates for web interface

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

For issues and questions:

1. Check the [troubleshooting section](#🛠️-troubleshooting)
2. Review existing [issues](https://github.com/BataraKresn/trigger-deploy/issues)
3. Create a new issue with detailed information

---

## 🎯 Roadmap

- [ ] Database backend for configuration storage
- [ ] Role-based access control (RBAC)
- [ ] Kubernetes deployment support
- [ ] Advanced alerting rules and escalation
- [ ] API versioning and documentation
- [ ] Webhook integrations (Slack, Discord, Teams)
- [ ] Mobile application
- [ ] Grafana dashboard integration

---

**Built with ❤️ for efficient deployment management and service monitoring**
