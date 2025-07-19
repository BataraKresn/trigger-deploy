import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  Activity, 
  Server, 
  Clock,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Rocket
} from 'lucide-react';
import Layout from '@/components/Layout';
import ServerTable from '@/components/ServerTable';
import DeployModal from '@/components/DeployModal';
import HealthCard from '@/components/HealthCard';
import useGlobalState, { Server as ServerType, HealthMetric } from '@/store/globalState';
import useDeployLogic from '@/hooks/useDeployLogic';

const Dashboard = () => {
  const [deployModalOpen, setDeployModalOpen] = useState(false);
  const [selectedServerId, setSelectedServerId] = useState<string>('');
  
  const { 
    servers, 
    healthMetrics, 
    deployLogs, 
    setServers, 
    addHealthMetric 
  } = useGlobalState();
  
  const { deployToServer } = useDeployLogic();

  // Mock data for demonstration
  useEffect(() => {
    // Add some mock servers if none exist
    if (servers.length === 0) {
      const mockServers: ServerType[] = [
        {
          id: '1',
          ip: '192.168.1.100',
          alias: 'web-01',
          name: 'Production Web Server',
          user: 'deploy',
          scriptPath: '/opt/deploy/deploy.sh',
          lastDeployed: '2025-01-19T10:30:00Z',
          status: 'online'
        },
        {
          id: '2',
          ip: '192.168.1.101',
          alias: 'api-01',
          name: 'API Server',
          user: 'deploy',
          scriptPath: '/opt/api/deploy.sh',
          lastDeployed: '2025-01-18T15:20:00Z',
          status: 'online'
        },
        {
          id: '3',
          ip: '192.168.1.102',
          alias: 'db-01',
          name: 'Database Server',
          user: 'admin',
          scriptPath: '/opt/db/maintenance.sh',
          lastDeployed: '2025-01-17T09:15:00Z',
          status: 'offline'
        }
      ];
      setServers(mockServers);
    }

    // Generate mock health metrics
    const interval = setInterval(() => {
      servers.forEach(server => {
        const metric: HealthMetric = {
          id: `metric-${Date.now()}-${server.id}`,
          serverId: server.id,
          timestamp: new Date().toISOString(),
          cpu: Math.random() * 100,
          memory: Math.random() * 100,
          disk: Math.random() * 100,
          ping: Math.random() * 200 + 10,
          status: Math.random() > 0.8 ? 'warning' : 'healthy'
        };
        addHealthMetric(metric);
      });
    }, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, [servers, setServers, addHealthMetric]);

  const handleServerDeploy = async (server: ServerType) => {
    setSelectedServerId(server.id);
    setDeployModalOpen(true);
  };

  const handleDeployModalDeploy = async (serverId: string) => {
    const server = servers.find(s => s.id === serverId);
    if (server) {
      try {
        await deployToServer(server);
      } catch (error) {
        console.error('Deployment failed:', error);
      }
    }
  };

  const handleServerEdit = (server: ServerType) => {
    console.log('Edit server:', server);
    // TODO: Implement server edit modal
  };

  const handleServerDelete = (server: ServerType) => {
    console.log('Delete server:', server);
    // TODO: Implement server delete confirmation
  };

  // Calculate statistics
  const stats = {
    totalServers: servers.length,
    onlineServers: servers.filter(s => s.status === 'online').length,
    deployingServers: servers.filter(s => s.status === 'deploying').length,
    recentDeploys: deployLogs.filter(log => {
      const logDate = new Date(log.timestamp);
      const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      return logDate > dayAgo;
    }).length
  };

  const healthyServers = healthMetrics.filter(m => m.status === 'healthy').length;
  const warningServers = healthMetrics.filter(m => m.status === 'warning').length;
  const criticalServers = healthMetrics.filter(m => m.status === 'critical').length;

  return (
    <Layout title="Dashboard" subtitle="Monitor and manage your server deployments">
      <div className="space-y-6">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Servers</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.totalServers}</p>
                <p className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  {stats.onlineServers} online
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <Server className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Deployments</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.deployingServers}</p>
                <p className="text-sm text-blue-600 dark:text-blue-400 flex items-center gap-1">
                  <Activity className="w-3 h-3" />
                  in progress
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <Rocket className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Recent Deploys</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.recentDeploys}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  last 24h
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="card"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">System Health</p>
                <div className="flex items-center gap-2 mt-1">
                  {healthyServers > 0 && (
                    <div className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-green-600 dark:text-green-400">{healthyServers}</span>
                    </div>
                  )}
                  {warningServers > 0 && (
                    <div className="flex items-center gap-1">
                      <AlertTriangle className="w-4 h-4 text-yellow-500" />
                      <span className="text-sm text-yellow-600 dark:text-yellow-400">{warningServers}</span>
                    </div>
                  )}
                  {criticalServers > 0 && (
                    <div className="flex items-center gap-1">
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                      <span className="text-sm text-red-600 dark:text-red-400">{criticalServers}</span>
                    </div>
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">All systems operational</p>
              </div>
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
          </motion.div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Server Table */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="xl:col-span-2"
          >
            <ServerTable
              servers={servers}
              onEdit={handleServerEdit}
              onDelete={handleServerDelete}
              onDeploy={handleServerDeploy}
            />
          </motion.div>

          {/* Quick Deploy Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="space-y-6"
          >
            <div className="card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
                  <Rocket className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Quick Deploy</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Deploy to any server instantly</p>
                </div>
              </div>
              
              <button
                onClick={() => setDeployModalOpen(true)}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                <Rocket className="w-4 h-4" />
                Open Deploy Modal
              </button>
            </div>

            {/* Recent Activity */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h3>
              <div className="space-y-3">
                {deployLogs.slice(0, 5).map((log) => (
                  <div key={log.id} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className={`w-2 h-2 rounded-full ${
                      log.status === 'success' ? 'bg-green-500' :
                      log.status === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                    }`}></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        Deploy to Server {log.serverId}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(log.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      log.status === 'success' ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400' :
                      log.status === 'error' ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                      'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400'
                    }`}>
                      {log.status}
                    </span>
                  </div>
                ))}
                {deployLogs.length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                    No recent deployments
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Health Monitoring */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <HealthCard healthData={healthMetrics} />
        </motion.div>
      </div>

      {/* Deploy Modal */}
      <DeployModal
        isOpen={deployModalOpen}
        onClose={() => {
          setDeployModalOpen(false);
          setSelectedServerId('');
        }}
        onDeploy={handleDeployModalDeploy}
        servers={servers}
        selectedServerId={selectedServerId}
      />
    </Layout>
  );
};

export default Dashboard;
