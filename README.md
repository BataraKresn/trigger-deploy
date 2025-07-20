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
├── app.py                      # Legacy main application (deprecated)
├── app_new.py                  # New clean main application
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

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker (optional)
- SSH access to target servers

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trigger-deploy
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

4. **Setup server configurations**
   ```bash
   # Edit config/servers.json
   # Edit config/services.json
   ```

5. **Run the application**
   ```bash
   python app_new.py
   ```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Security
DEPLOY_TOKEN=your-secure-token

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

# Email Notifications (optional)
EMAIL_ENABLED=false
EMAIL_TO=admin@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
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
python app_new.py
```

### Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app_new:app
```

### Docker
```bash
docker-compose up -d
```

## 📊 Monitoring

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

## 🆘 Support

For issues and questions:
1. Check the logs in `logs/` directory
2. Review configuration files
3. Ensure all dependencies are installed
4. Verify server connectivity

---

**Built with ❤️ for streamlined deployment management**
