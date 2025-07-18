import React, { useState } from 'react';

function DeployServers() {
  const [token, setToken] = useState('');
  const [isModalOpen, setModalOpen] = useState(false);
  const [isDeploying, setDeploying] = useState(false);

  const openModal = () => setModalOpen(true);
  const closeModal = () => setModalOpen(false);

  const submitDeploy = () => {
    if (!token) {
      alert('Token cannot be empty!');
      return;
    }
    setDeploying(true);
    // Simulate API call
    setTimeout(() => {
      alert('Deploy successful!');
      setDeploying(false);
      closeModal();
    }, 2000);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">🚀 Deploy to Servers</h1>
      <button className="btn" onClick={openModal}>Open Deploy Modal</button>

      {isModalOpen && (
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
    </div>
  );
}

export default DeployServers;
