import React from 'react';

interface DeployModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeploy: (serverId: string) => void;
  servers: { id: string; name: string }[];
}

const DeployModal: React.FC<DeployModalProps> = ({ isOpen, onClose, onDeploy, servers }) => {
  const [selectedServer, setSelectedServer] = React.useState('');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 p-6 rounded shadow-lg w-96">
        <h2 className="text-xl font-bold mb-4">Deploy Server</h2>
        <select
          className="w-full p-2 border rounded mb-4 dark:bg-gray-700 dark:text-white"
          value={selectedServer}
          onChange={(e) => setSelectedServer(e.target.value)}
        >
          <option value="">Select a server...</option>
          {servers.map((server) => (
            <option key={server.id} value={server.id}>{server.name}</option>
          ))}
        </select>
        <div className="flex justify-end gap-4">
          <button
            className="py-2 px-4 bg-gray-300 dark:bg-gray-600 rounded hover:bg-gray-400 dark:hover:bg-gray-500 transition-all"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            className="py-2 px-4 bg-green-500 text-white rounded hover:bg-green-600 transition-all"
            onClick={() => onDeploy(selectedServer)}
            disabled={!selectedServer}
          >
            Deploy
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeployModal;