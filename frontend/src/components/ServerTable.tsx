import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Server, 
  Edit3, 
  Trash2, 
  Rocket, 
  MoreVertical, 
  Calendar,
  User,
  FolderOpen,
  Monitor,
  Globe
} from 'lucide-react';
import useGlobalState, { Server as ServerType } from '@/store/globalState';

interface ServerTableProps {
  servers: ServerType[];
  onEdit: (server: ServerType) => void;
  onDelete: (server: ServerType) => void;
  onDeploy: (server: ServerType) => void;
}

const ServerTable: React.FC<ServerTableProps> = ({ servers, onEdit, onDelete, onDeploy }) => {
  const { darkMode, deployingServers } = useGlobalState();
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  const getStatusColor = (status: ServerType['status']) => {
    switch (status) {
      case 'online':
        return 'bg-green-500 text-green-50';
      case 'offline':
        return 'bg-red-500 text-red-50';
      case 'deploying':
        return 'bg-blue-500 text-blue-50';
      case 'error':
        return 'bg-yellow-500 text-yellow-50';
      default:
        return 'bg-gray-500 text-gray-50';
    }
  };

  const getStatusDot = (status: ServerType['status']) => {
    switch (status) {
      case 'online':
        return 'status-dot status-online';
      case 'offline':
        return 'status-dot status-offline';
      case 'deploying':
        return 'status-dot bg-blue-500 animate-pulse';
      case 'error':
        return 'status-dot status-warning';
      default:
        return 'status-dot bg-gray-500';
    }
  };

  if (servers.length === 0) {
    return (
      <div className="card text-center py-12">
        <Server className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No servers configured
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          Add your first server to start managing deployments
        </p>
        <button className="btn-primary">
          <Server className="w-4 h-4 mr-2" />
          Add Server
        </button>
      </div>
    );
  }

  return (
    <div className="card p-0 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
              <Server className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Servers
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {servers.length} server{servers.length !== 1 ? 's' : ''} configured
              </p>
            </div>
          </div>
          <button className="btn-primary">
            <Server className="w-4 h-4 mr-2" />
            Add Server
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Server
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Details
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Last Deploy
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            <AnimatePresence mode="popLayout">
              {servers.map((server, index) => (
                <motion.tr
                  key={server.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors duration-200"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={getStatusDot(server.status)}></div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                            {server.name}
                          </h3>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            ({server.alias})
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 mt-1">
                          <Globe className="w-3 h-3" />
                          {server.ip}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-300">
                        <User className="w-3 h-3" />
                        <span>{server.user}</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                        <FolderOpen className="w-3 h-3" />
                        <span className="truncate max-w-40" title={server.scriptPath}>
                          {server.scriptPath}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`
                      inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                      ${getStatusColor(server.status)}
                    `}>
                      {server.status === 'deploying' ? 'Deploying...' : server.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                      <Calendar className="w-3 h-3" />
                      {server.lastDeployed ? new Date(server.lastDeployed).toLocaleDateString() : 'Never'}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onDeploy(server)}
                        disabled={deployingServers.has(server.id)}
                        className="btn-success text-xs px-3 py-1 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deployingServers.has(server.id) ? (
                          <>
                            <div className="loading-spinner w-3 h-3 mr-1" />
                            Deploying
                          </>
                        ) : (
                          <>
                            <Rocket className="w-3 h-3 mr-1" />
                            Deploy
                          </>
                        )}
                      </button>
                      
                      <div className="relative">
                        <button
                          onClick={() => setActiveDropdown(activeDropdown === server.id ? null : server.id)}
                          className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                          <MoreVertical className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        </button>
                        
                        <AnimatePresence>
                          {activeDropdown === server.id && (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.95, y: -10 }}
                              animate={{ opacity: 1, scale: 1, y: 0 }}
                              exit={{ opacity: 0, scale: 0.95, y: -10 }}
                              transition={{ duration: 0.15 }}
                              className="absolute right-0 top-full mt-2 w-32 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-10"
                            >
                              <button
                                onClick={() => {
                                  onEdit(server);
                                  setActiveDropdown(null);
                                }}
                                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                              >
                                <Edit3 className="w-3 h-3" />
                                Edit
                              </button>
                              <button
                                onClick={() => {
                                  onDelete(server);
                                  setActiveDropdown(null);
                                }}
                                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                              >
                                <Trash2 className="w-3 h-3" />
                                Delete
                              </button>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ServerTable;