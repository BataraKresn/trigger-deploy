# 🚀 Trigger Deploy Server

A secure, production-ready webhook deployment server with real-time monitoring, multi-server management, and comprehensive logging.

---

## 📁 Project Structure

```
trigger-deploy/
├── app.py                    # Main Flask application
├── deploy-wrapper.sh         # Deployment execution script
├── test_app.py              # Unit tests
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── static/
│   ├── servers.json         # Server configuration
│   ├── styles.css           # UI styles
│   ├── deploy.js            # Frontend JavaScript
│   └── favicon.ico          # Application icon
├── templates/
│   ├── home.html            # Landing page
│   ├── deploy_servers.html  # Deployment interface
│   └── trigger_result.html  # Result display
├── trigger-logs/            # Deployment logs (auto-created)
├── logs/                    # Application logs (auto-created)
└── docker-compose.yml       # Docker configuration
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Security
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

### 3. Run Application

```bash
python app.py
```

### 4. Run Tests

```bash
python test_app.py
```

---

## 🧠 Features

### 🔐 Security
- **Token-based authentication** with secure comparison
- **Rate limiting** (configurable per endpoint)
- **Input validation** for all parameters
- **Path traversal protection** for file operations
- **IP address validation** for server endpoints

### 📊 Monitoring & Logging
- **Structured logging** with rotation
- **Real-time log streaming** via Server-Sent Events
- **Health check endpoints** with system metrics
- **Deployment tracking** and status monitoring
- **Automatic log cleanup** based on retention policy

### 🖥️ Multi-Server Support
- **SSH-based deployment** to multiple servers
- **Server configuration management** via JSON
- **Server health checks** before deployment
- **Parallel deployment support**

### 🌐 Web Interface
- **Responsive UI** for deployment management
- **Real-time status updates**
- **Log viewing and streaming**
- **Server management interface**

---

## 📡 API Endpoints

### Core Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST/GET` | `/trigger` | Trigger deployment | 5/min |
| `POST` | `/ping` | Check server connectivity | 20/min |
| `GET` | `/health` | System health check | 30/min |
| `GET` | `/metrics` | Application metrics | 10/min |

### Management Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/servers` | List configured servers |
| `GET` | `/logs` | List deployment logs |
| `GET` | `/log-content` | Get log file content |
| `GET` | `/stream-log` | Stream log in real-time |

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

#### Get Metrics

```bash
curl https://your-server.com/metrics
```

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment in Docker

Create `.env` file for Docker:

```bash
DEPLOY_TOKEN=your_secure_token_here
LOG_DIR=/app/trigger-logs
SERVERS_FILE=/app/static/servers.json
```

---

## 🔧 Advanced Configuration

### Rate Limiting

Customize rate limits per endpoint:

```python
@app.route('/api/endpoint')
@rate_limit(max_requests=5, window=60)  # 5 requests per minute
def my_endpoint():
    pass
```

### Logging Configuration

Adjust logging levels and formats:

```python
# In app.py
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

### Security Hardening

1. **Use strong tokens**: Generate cryptographically secure tokens
2. **Enable HTTPS**: Use reverse proxy (nginx/Apache) with SSL
3. **Firewall rules**: Restrict access to trusted IPs
4. **SSH key authentication**: Use SSH keys instead of passwords

---

## 🧪 Testing

### Run Unit Tests

```bash
python test_app.py
```

### Manual Testing

```bash
# Test token validation
curl -X POST localhost:5000/trigger -d '{"token": "wrong"}' -H "Content-Type: application/json"

# Test rate limiting
for i in {1..15}; do curl localhost:5000/metrics; done
```

---

## 📈 Monitoring

### Application Metrics

Access `/metrics` endpoint for:

- **Uptime**: Application runtime
- **Active deployments**: Currently running deployments  
- **System resources**: Memory and disk usage
- **Log statistics**: Total logs and cleanup status

### Log Management

- **Automatic rotation**: Logs rotate at configurable size
- **Retention policy**: Old logs cleaned automatically
- **Structured format**: JSON-friendly log format
- **Real-time streaming**: Live log viewing via SSE

---

## 🔍 Troubleshooting

### Common Issues

1. **Permission denied on SSH**
   - Ensure SSH keys are properly configured
   - Check user permissions on target servers

2. **Rate limit exceeded**
   - Adjust `RATE_LIMIT_REQUESTS` in environment
   - Implement IP whitelisting if needed

3. **Log files not rotating**
   - Check `MAX_LOG_SIZE` configuration
   - Verify write permissions in log directory

4. **Deployment hangs**
   - Check `deploy-wrapper.sh` script for infinite loops
   - Monitor process status via `/metrics` endpoint

### Debug Mode

Enable debug logging:

```bash
export FLASK_DEBUG=true
python app.py
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Add tests** for new functionality
4. **Run tests** and ensure they pass
5. **Submit** a pull request

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with **Flask** and **Python**
- Real-time features powered by **Server-Sent Events**
- Security best practices from **OWASP** guidelines

1. Open `/deploy-servers`
2. Select a server → Enter token → Click `Deploy`
3. Server executes `deploy-wrapper.sh`, which:

   * Maps alias/IP from `servers.json`
   * SSH into server
   * Executes `./deploy.sh` inside defined path
   * Logs output to a timestamped file

### Sample servers.json

```json
[
  {
    "name": "Web Server",
    "ip": "<IP_ADDRESS>",
    "alias": "default",
    "user": "ubuntu",
    "path": "/path/home/project"
  }
]
```

---

## 🚦 Available Endpoints

### 📋 UI Pages

* `/` → Landing page
* `/deploy-servers` → Deploy dashboard UI

### 📡 API

* `GET /servers` → JSON list of servers
* `POST /trigger` → Trigger deploy (with `{ token, server }`)
* `GET /stream-log?file=...` → Live log via SSE
* `GET /logs` → List log filenames
* `GET /log-content?file=...` → View full log file
* `GET /logs/<file>` → Direct access to log
* `POST /ping` → Ping a server (SSH check)
* `GET /health?target=...` → Ping & DNS test

### 🔐 Headers / Auth

All deploy requests (`/trigger`) must include a valid token:

```json
{
  "token": "<TOKEN>",
  "server": "default"
}
```

---

## 📜 Example: Bash Deploy Script on Server (`deploy.sh`)

```bash
#!/bin/bash
set -e
APP_NAME="<Project_name>"
echo "🚀 Starting deployment for $APP_NAME"

git pull origin main || true

echo "♻️ Restarting container..."
docker compose up -d --build

echo "✅ Deployment done"
```

---

## 🛡️ Security Notes

* 🔐 All deploy actions are token-protected.
* 🔒 SSH uses `~/.ssh` from host (mounted as `read-only`).
* ✅ Only servers listed in `servers.json` can be deployed to.
* 🚫 Invalid/missing tokens will be rejected with `403`.

---

## 🧼 Auto Clean Logs

Logs older than 7 days are cleaned automatically on each deploy trigger.

---

## ✅ Healthcheck Endpoint

You can test if the deployment server has internet:

```
curl https://yourdomain.com/health?target=example.com
```

---

## 🧪 Development Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## 👨‍💻 Credits

Built by and for efficient multi-server deployment monitoring with ❤️.
