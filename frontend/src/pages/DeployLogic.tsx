import React, { useState } from 'react';

function DeployLogic() {
  const [selectedServerId, setSelectedServerId] = useState<number | null>(null);
  const [selectedServerIP, setSelectedServerIP] = useState<string | null>(null);
  const [token, setToken] = useState('');
  const [status, setStatus] = useState('');
  const [logs, setLogs] = useState('');
  const [isDeploying, setDeploying] = useState(false);

  const openModal = (serverId: number, ip: string) => {
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

      <button
        className="bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        onClick={() => openModal(1, '192.168.1.1')}
      >
        Open Modal for Server 1
      </button>

      {selectedServerId && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">🔒 Enter Your Token</h2>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Enter token..."
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
            />
            <div className="flex justify-end space-x-4">
              <button
                className="bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500"
                onClick={closeModal}
              >
                Cancel
              </button>
              <button
                className="bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                onClick={submitDeploy}
              >
                Deploy
              </button>
            </div>
          </div>
        </div>
      )}

      {isDeploying && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500 mb-4"></div>
            <p className="text-white text-lg">⏳ Deploying...</p>
          </div>
        </div>
      )}

      {status && <p className="text-green-500 mt-4">Status: {status}</p>}
      {logs && (
        <div className="mt-4 bg-gray-100 p-4 rounded-lg">
          <pre>{logs}</pre>
        </div>
      )}
    </div>
  );
}

export default DeployLogic;
