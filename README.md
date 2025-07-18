# 🚀 Triggered Deployment Platform

A secure and extensible platform to remotely trigger deployments across multiple servers, with real-time logging and simple authentication via token.

---

## 📁 Project Structure

```
.
├── app.py                 # Flask backend (core logic)
├── deploy-wrapper.sh     # Bash wrapper to trigger deployment per server
├── static/
│   ├── servers.json       # List of available servers (IP, alias, path, user)
│   ├── styles.css         # Custom UI styles
│   └── favicon.ico        # Icon
├── templates/
│   ├── home.html          # Landing page (optional)
│   └── deploy_servers.html # Main deployment UI
├── public/
│   └── deploy.js          # JS logic for deploy interaction
├── trigger-logs/         # Deployment log files (auto-generated)
├── .env                  # Environment config file
```

---

## ⚙️ Environment Configuration (`.env`)

```ini
DEPLOY_TOKEN=<TOKEN>
```

---

## 🧠 Features

* 🔐 **Token-based authentication**
* 🖥️ **Multi-server deployment** via SSH
* ⏱️ **Real-time log streaming** using Server-Sent Events (SSE)
* 🗃️ **Deployment log archival**
* 🔎 **Ping check** before executing deploy
* 💻 **Responsive frontend UI**

---

## 🔧 How It Works

### Triggering a Deploy

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
