import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Rocket, 
  Server, 
  Terminal, 
  CheckCircle, 
  AlertCircle, 
  Loader,
  PlayCircle
} from 'lucide-react';
import useGlobalState, { Server as ServerType } from '@/store/globalState';
import LogViewer from './LogViewer';

interface DeployModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeploy: (serverId: string) => void;
  servers: ServerType[];
  selectedServerId?: string;
}

const DeployModal: React.FC<DeployModalProps> = ({ 
  isOpen, 
  onClose, 
  onDeploy, 
  servers, 
  selectedServerId 
}) => {
  const [selectedServer, setSelectedServer] = useState(selectedServerId || '');
  const [deployStatus, setDeployStatus] = useState<'idle' | 'deploying' | 'success' | 'error'>('idle');
  const [deployLogs, setDeployLogs] = useState<string[]>([]);
  const { darkMode, deployingServers } = useGlobalState();

  useEffect(() => {
    if (selectedServerId) {
      setSelectedServer(selectedServerId);
    }
  }, [selectedServerId]);

  useEffect(() => {
    if (!isOpen) {
      setDeployStatus('idle');
      setDeployLogs([]);
    }
  }, [isOpen]);

  const selectedServerData = servers.find(s => s.id === selectedServer);
  const isDeploying = deployingServers.has(selectedServer);

  const handleDeploy = async () => {
    if (!selectedServer) return;
    
    setDeployStatus('deploying');
    setDeployLogs(['🚀 Starting deployment...', `📡 Connecting to ${selectedServerData?.name} (${selectedServerData?.ip})...`]);
    
    try {
      // Simulate deployment process
      await new Promise(resolve => setTimeout(resolve, 1000));
      setDeployLogs(prev => [...prev, '✅ Connection established', '📦 Transferring files...']);
      
      await new Promise(resolve => setTimeout(resolve, 1500));
      setDeployLogs(prev => [...prev, '🔧 Running deployment script...', `$ ${selectedServerData?.scriptPath}`]);
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      setDeployLogs(prev => [...prev, '✅ Deployment completed successfully!']);
      
      onDeploy(selectedServer);
      setDeployStatus('success');
    } catch (error) {
      setDeployLogs(prev => [...prev, '❌ Deployment failed!', 'Error: Connection timeout']);
      setDeployStatus('error');
    }
  };

  const getStatusIcon = () => {
    switch (deployStatus) {
      case 'deploying':
        return <Loader className="w-5 h-5 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Rocket className="w-5 h-5 text-primary-600" />;
    }
  };

  const getStatusText = () => {
    switch (deployStatus) {
      case 'deploying':
        return 'Deploying...';
      case 'success':
        return 'Deployment Successful!';
      case 'error':
        return 'Deployment Failed';
      default:
        return 'Ready to Deploy';
    }
  };

  const getStatusColor = () => {
    switch (deployStatus) {
      case 'deploying':
        return 'text-blue-600 dark:text-blue-400';
      case 'success':
        return 'text-green-600 dark:text-green-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-900 dark:text-white';
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2 }}
          className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              {getStatusIcon()}
              <div>
                <h2 className={`text-xl font-semibold ${getStatusColor()}`}>
                  {getStatusText()}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Deploy to remote server
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Server Selection */}
            {deployStatus === 'idle' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Select Server
                </label>
                <select
                  value={selectedServer}
                  onChange={(e) => setSelectedServer(e.target.value)}
                  className="input-primary"
                  disabled={isDeploying}
                >
                  <option value="">Choose a server...</option>
                  {servers.map((server) => (
                    <option key={server.id} value={server.id}>
                      {server.name} ({server.ip}) - {server.alias}
                    </option>
                  ))}
                </select>

                {selectedServerData && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4"
                  >
                    <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Server className="w-4 h-4" />
                      Server Details
                    </h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Name:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">{selectedServerData.name}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">IP:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">{selectedServerData.ip}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">User:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">{selectedServerData.user}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Status:</span>
                        <span className={`ml-2 capitalize ${
                          selectedServerData.status === 'online' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {selectedServerData.status}
                        </span>
                      </div>
                      <div className="col-span-2">
                        <span className="text-gray-500 dark:text-gray-400">Script Path:</span>
                        <span className="ml-2 text-gray-900 dark:text-white font-mono text-xs">
                          {selectedServerData.scriptPath}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Deployment Logs */}
            {deployStatus !== 'idle' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-gray-500" />
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    Deployment Output
                  </h3>
                </div>
                <LogViewer 
                  logs={deployLogs} 
                  isLive={deployStatus === 'deploying'}
                  className="h-64"
                />
              </motion.div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              {deployStatus === 'idle' && (
                <>
                  <button
                    onClick={onClose}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeploy}
                    disabled={!selectedServer || isDeploying}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <PlayCircle className="w-4 h-4" />
                    Start Deploy
                  </button>
                </>
              )}
              
              {deployStatus === 'deploying' && (
                <button
                  onClick={onClose}
                  className="btn-secondary"
                  disabled
                >
                  <Loader className="w-4 h-4 animate-spin mr-2" />
                  Deploying...
                </button>
              )}
              
              {(deployStatus === 'success' || deployStatus === 'error') && (
                <>
                  <button
                    onClick={() => {
                      setDeployStatus('idle');
                      setDeployLogs([]);
                      setSelectedServer('');
                    }}
                    className="btn-secondary"
                  >
                    Deploy Another
                  </button>
                  <button
                    onClick={onClose}
                    className="btn-primary"
                  >
                    Close
                  </button>
                </>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default DeployModal;