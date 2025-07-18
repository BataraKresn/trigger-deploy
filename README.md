# 🚀 Triggered Deployment Platform

A secure and extensible platform to remotely trigger deployments across multiple servers, with real-time logging and simple authentication via token.

---

## 📁 Project Structure

```
.
├── backend/                # FastAPI backend (core logic)
│   ├── app.py             # Main application entry point
│   ├── routes/            # Modular routes for API endpoints
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Dockerfile for backend
├── frontend/               # React frontend
│   ├── src/               # Source code for React app
│   ├── Dockerfile         # Dockerfile for frontend
│   ├── package.json       # Node.js dependencies
├── docker-compose.yaml     # Docker Compose configuration
├── docker-compose.monitoring.yaml # Monitoring setup with Prometheus and Grafana
└── README.md               # Project documentation
```

---

## ⚙️ Environment Configuration (`.env`)

```ini
DEPLOY_TOKEN=<TOKEN>
```

---

## 🤖 Features

* 🔒 **Token-based authentication**
* 🖥️ **Multi-server deployment** via SSH
* ⏱️ **Real-time log streaming** using Server-Sent Events (SSE)
* 📂 **Deployment log archival**
* 🔍 **Ping check** before executing deploy
* 💻 **Responsive frontend UI**
* 📊 **Monitoring with Prometheus and Grafana**

---

## 🛠️ How to Run

### Using Docker Compose

1. Build and start the services:
   ```bash
   docker-compose up --build
   ```

2. Access the application:
   - Backend API: [http://localhost:5001/docs](http://localhost:5001/docs)
   - Frontend: [http://localhost:5173](http://localhost:5173)

### Monitoring Setup

1. Start Prometheus and Grafana:
   ```bash
   docker-compose -f docker-compose.monitoring.yaml up
   ```

2. Access the monitoring tools:
   - Prometheus: [http://localhost:9090](http://localhost:9090)
   - Grafana: [http://localhost:3000](http://localhost:3000)

---

## 🏗️ Production Setup

- **Frontend**:
  - Built using `npm run build` and served via `nginx`.
- **Backend**:
  - Runs with `gunicorn` and `uvicorn` workers.
- **Docker Compose**:
  - Integrated setup with shared network and environment variables.

---

## 📜 License

MIT License
