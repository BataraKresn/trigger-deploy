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
      <h1 className="text-2xl font-bold mb-4">
        🚀 Deploy to Servers
      </h1>
      <button
        className="py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600 transition-all"
        onClick={openModal}
      >
        Open Deploy Modal
      </button>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded shadow-lg w-96">
            <h2 className="text-xl font-bold mb-4">🔒 Enter Your Token</h2>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Enter token..."
              className="w-full p-2 border rounded mb-4"
            />
            <div className="flex justify-end gap-4">
              <button
                className="py-2 px-4 bg-gray-300 rounded hover:bg-gray-400 transition-all"
                onClick={closeModal}
              >
                Cancel
              </button>
              <button
                className="py-2 px-4 bg-green-500 text-white rounded hover:bg-green-600 transition-all"
                onClick={submitDeploy}
              >
                Deploy
              </button>
            </div>
          </div>
        </div>
      )}

      {isDeploying && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="text-white text-lg">Deploying...</div>
        </div>
      )}
    </div>
  );
}

export default DeployServers;
