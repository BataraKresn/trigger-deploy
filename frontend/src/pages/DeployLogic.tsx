import React, { useState } from 'react';

function DeployLogic() {
  const [selectedServerId, setSelectedServerId] = useState(null);
  const [selectedServerIP, setSelectedServerIP] = useState(null);
  const [token, setToken] = useState('');
  const [status, setStatus] = useState('');
  const [logs, setLogs] = useState('');
  const [isDeploying, setDeploying] = useState(false);

  const openModal = (serverId, ip) => {
    setSelectedServerId(serverId);
    setSelectedServerIP(ip);
  };

  const closeModal = () => {
    setSelectedServerId(null);
    setSelectedServerIP(null);
  };

  const submitDeploy = () => {
    if (!token) {
      alert('Token cannot be empty!');
      return;
    }

    setDeploying(true);
    setStatus('🔍 Checking connectivity...');

    // Simulate API call
    setTimeout(() => {
      setStatus('✅ Deploy successful!');
      setLogs('Log data here...');
      setDeploying(false);
      closeModal();
    }, 2000);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Deploy Logic</h1>

      <button className="btn" onClick={() => openModal(1, '192.168.1.1')}>Open Modal for Server 1</button>

      {selectedServerId && (
        <div className="modal">
          <div className="modal-content">
            <h2 className="text-xl font-bold">🔒 Enter Your Token</h2>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Enter token..."
              className="input"
            />
            <div className="buttons">
              <button className="btn" onClick={closeModal}>Cancel</button>
              <button className="btn" onClick={submitDeploy}>Deploy</button>
            </div>
          </div>
        </div>
      )}

      {isDeploying && (
        <div className="spinner-overlay">
          <div className="spinner"></div>
          <div className="spinner-text">⏳ Deploying...</div>
        </div>
      )}

      {status && <p className="status success">Status: {status}</p>}
      {logs && (
        <div className="log-output">
          <pre>{logs}</pre>
        </div>
      )}
    </div>
  );
}

export default DeployLogic;
