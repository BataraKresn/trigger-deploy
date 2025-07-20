# 📁 Project Structure Documentation

## 🏗️ Directory Structure

```
trigger-deploy/
├── 📱 app_new.py              # Main application file (clean architecture)
├── 📋 requirements_new.txt    # Updated dependencies
├── 🔧 .env                    # Environment configuration
├── 🐳 docker-compose.yml      # Docker configuration
├── 📖 README_NEW.md           # Updated documentation
│
├── 📂 src/                    # Source code (modular architecture)
│   ├── 📂 models/             # Data models and configuration
│   │   ├── config.py          # Application configuration
│   │   └── entities.py        # Data models (Server, Service, Deployment)
│   ├── 📂 routes/             # API and web routes
│   │   ├── main.py            # Main web routes
│   │   ├── api.py             # API endpoints
│   │   └── deploy.py          # Deployment routes
│   └── 📂 utils/              # Utility functions
│       └── helpers.py         # Helper functions
│
├── 📂 config/                 # Configuration files
│   ├── servers.json           # Server configurations
│   └── services.json          # Service configurations
│
├── 📂 static/                 # Static web assets
│   ├── 📂 css/               # Stylesheets
│   │   └── styles.css        # Main stylesheet
│   ├── 📂 js/                # JavaScript files
│   │   ├── home.js           # Home page functionality
│   │   ├── deploy.js         # Deployment page functionality
│   │   ├── metrics.js        # Metrics dashboard
│   │   ├── services-monitor.js # Services monitor
│   │   └── trigger-result.js # Result page functionality
│   └── 📂 images/            # Images and icons
│       ├── favicon.ico       # Main favicon
│       └── 📂 favicon/       # Page-specific favicons
│
├── 📂 templates/             # HTML templates
│   ├── home.html             # Home page
│   ├── deploy_servers.html   # Server deployment page
│   ├── metrics.html          # Metrics dashboard
│   ├── services_monitor.html # Services monitor page
│   ├── trigger_result.html   # Deployment result page
│   └── invalid_token.html    # Error page
│
├── 📂 scripts/               # Shell scripts
│   ├── deploy-wrapper.sh     # Deployment wrapper script
│   ├── update-docker.sh      # Docker update script
│   └── cleanup.sh            # Cleanup old files script
│
├── 📂 logs/                  # Application logs
├── 📂 trigger-logs/          # Deployment logs
└── 📂 tests/                 # Unit tests
```

## 🗂️ File Organization

### 🎯 Core Application Files

| File | Purpose | Status |
|------|---------|---------|
| `app.py` | Main application with modular architecture | ✅ Active |
| `wsgi.py` | WSGI application server entry point | ✅ Active |
| `requirements.txt` | Python dependencies | ✅ Active |
| `README.md` | Project documentation | ✅ Active |

### 📋 Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `servers.json` | Server configurations | `config/` |
| `services.json` | Service monitoring configs | `config/` |
| `.env` | Environment variables | Root |

### 🎨 Frontend Assets

| Category | Files | Location |
|----------|-------|----------|
| **Stylesheets** | `styles.css` | `static/css/` |
| **JavaScript** | `*.js` | `static/js/` |
| **Images** | `favicon.ico`, `favicon/*` | `static/images/` |

### 🧩 Backend Modules

| Module | Files | Purpose |
|--------|-------|---------|
| **Models** | `config.py`, `entities.py` | Data models and configuration |
| **Routes** | `main.py`, `api.py`, `deploy.py` | Web routes and API endpoints |
| **Utils** | `helpers.py` | Utility functions and helpers |

## 🔄 Migration Status

### ✅ Completed
- [x] Reorganized static assets into subdirectories
- [x] Created modular source code structure
- [x] Separated configuration files
- [x] Updated HTML templates with new paths
- [x] Created clean main application file
- [x] Updated documentation

### ⏳ In Progress
- [ ] Remove legacy files (use `scripts/cleanup.sh`)
- [ ] Test new application structure
- [ ] Update Docker configuration if needed

### 🎯 Benefits of New Structure

1. **📦 Modularity**: Code is organized into logical modules
2. **🔧 Maintainability**: Easier to maintain and extend
3. **🧪 Testability**: Better structure for unit testing
4. **📈 Scalability**: Easy to add new features
5. **👥 Collaboration**: Clear separation of concerns
6. **📖 Documentation**: Better organized and documented

## 🚀 Getting Started with New Structure

1. **Install dependencies:**
   ```bash
   pip install -r requirements_new.txt
   ```

2. **Run the application:**
   ```bash
   python app_new.py
   ```

3. **Clean up old files (optional):**
   ```bash
   ./scripts/cleanup.sh
   ```

4. **Access the application:**
   - Home: http://localhost:5000
   - Metrics: http://localhost:5000/metrics
   - Deploy: http://localhost:5000/deploy-servers
   - Services: http://localhost:5000/services-monitor

## 🛠️ Development Guidelines

- **Add new routes**: Use blueprints in `src/routes/`
- **Add new models**: Place in `src/models/`
- **Add utilities**: Place in `src/utils/`
- **Add static assets**: Use appropriate subdirectories in `static/`
- **Update configuration**: Modify files in `config/`

This structure follows modern Flask application patterns and best practices for maintainable web applications.
