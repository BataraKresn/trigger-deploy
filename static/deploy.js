let selectedServer = null;
let serverLogs = {};

function openModal(server) {
  selectedServer = server;
  document.getElementById("deployTokenInput").value = "";
  document.getElementById("authModal").style.display = "flex";
}

function closeModal() {
  selectedServer = null;
  document.getElementById("authModal").style.display = "none";
}

function submitDeploy() {
  const token = document.getElementById("deployTokenInput").value;
  if (!token) {
    alert("❌ Token cannot be empty!");
    return;
  }

  const serverId = selectedServer;

  const statusEl = document.getElementById(`status-${serverId}`);
  const logBox = document.getElementById(`log-${serverId}`);
  const logContainer = document.getElementById(`log-container-${serverId}`);
  const clearBtn = document.getElementById(`clear-${serverId}`);
  const spinner = document.getElementById("spinner");

  if (!statusEl || !logBox || !logContainer || !clearBtn) {
    alert(`❌ Error: Required UI elements for "${serverId}" not found.`);
    if (spinner) spinner.style.display = "none";
    closeModal();
    return;
  }

  // 🟢 PING dulu
  statusEl.textContent = "🔍 Checking connectivity...";
  if (spinner) spinner.style.display = "block";

  fetch("/ping", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ server: selectedServer })
  })
    .then(res => res.json())
    .then(ping => {
      if (ping.status !== "ok") {
        statusEl.textContent = "❌ Unreachable";
        logBox.textContent = "SSH connection failed.";
        clearBtn.disabled = false;
        if (spinner) spinner.style.display = "none";
        return;
      }

      // ✅ Kalau ping berhasil, lanjut deploy
      statusEl.textContent = "🟡 Deploying...";
      logBox.textContent = "";
      logContainer.style.display = "block";
      clearBtn.disabled = true;

      return fetch("/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, server: serverId })
      });
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {
        const logUrl = data.stream_log_url;
        const es = new EventSource(logUrl);
        serverLogs[serverId] = es;

        es.onmessage = (event) => {
          logBox.textContent += event.data + "\n";
          logBox.scrollTop = logBox.scrollHeight;

          if (event.data.includes("✅ Deploy complete.")) {
            es.close();
            statusEl.textContent = "✅ Done";
            clearBtn.disabled = false;
            if (spinner) spinner.style.display = "none";
          }
        };
      } else {
        throw new Error(data.error || data.message || "Unknown error");
      }
    })
    .catch((err) => {
      statusEl.textContent = "❌ Error";
      logBox.textContent = err.message || err;
      clearBtn.disabled = false;
      if (spinner) spinner.style.display = "none";
    })
    .finally(() => {
      closeModal();
    });
}

function clearLog(server) {
  const logBox = document.getElementById(`log-${server}`);
  const statusEl = document.getElementById(`status-${server}`);
  const logContainer = document.getElementById(`log-container-${server}`);

  logBox.textContent = "";
  statusEl.textContent = "Idle";
  logContainer.style.display = "none";

  if (serverLogs[server]) {
    serverLogs[server].close();
    delete serverLogs[server];
  }
}

function renderServers(servers) {
  const container = document.getElementById("server-list");
  container.innerHTML = "";

  servers.forEach((srv) => {
    const rawId = srv.alias || srv.ip;
    const serverId = rawId.replace(/[^a-zA-Z0-9_-]/g, "_");

    const div = document.createElement("div");
    div.className = "server-card";

    div.innerHTML = `
      <div class="left">
        <div class="server-name">${srv.name} (${srv.ip})</div>
        <div class="server-status" id="status-${serverId}">Idle</div>
      </div>
      <div class="right">
        <button onclick="openModal('${serverId}')">Deploy</button>
        <button id="clear-${serverId}" onclick="clearLog('${serverId}')" disabled>🗑️ Clear</button>
      </div>
    `;

    const logPanel = document.createElement("div");
    logPanel.className = "log-panel";
    logPanel.id = `log-container-${serverId}`;
    logPanel.style.display = "none";

    logPanel.innerHTML = `
      <pre id="log-${serverId}" class="log-box"></pre>
    `;

    container.appendChild(div);
    container.appendChild(logPanel);
  });

  if (!document.getElementById("spinner")) {
    const spinnerEl = document.createElement("div");
    spinnerEl.id = "spinner";
    spinnerEl.innerText = "⏳ Deploying...";
    spinnerEl.style.cssText = `
      position: fixed; top: 10px; right: 20px;
      background: #333; color: #fff;
      padding: 0.5rem 1rem; border-radius: 6px;
      display: none; z-index: 1000;
    `;
    document.body.appendChild(spinnerEl);
  }
}

fetch("/servers")
  .then((res) => res.json())
  .then(renderServers)
  .catch((err) => {
    document.getElementById("server-list").innerHTML =
      "❌ Failed to load servers.json";
  });
