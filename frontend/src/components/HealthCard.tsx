import React from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Network, 
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { HealthMetric } from '@/store/globalState';

interface HealthCardProps {
  healthData: HealthMetric[];
  className?: string;
}

interface MetricCardProps {
  title: string;
  value: number | string;
  unit: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: 'up' | 'down' | 'stable';
  status: 'healthy' | 'warning' | 'critical';
  description?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  unit, 
  icon: Icon, 
  trend, 
  status, 
  description 
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20';
      case 'warning':
        return 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20';
      case 'critical':
        return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20';
      default:
        return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-red-500" />;
      case 'down':
        return <TrendingDown className="w-3 h-3 text-green-500" />;
      default:
        return null;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`relative p-4 rounded-xl border ${getStatusColor()}`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white dark:bg-gray-800 rounded-lg flex items-center justify-center shadow-sm">
            <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </div>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</span>
        </div>
        <div className="flex items-center gap-1">
          {getStatusIcon()}
          {getTrendIcon()}
        </div>
      </div>
      
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </span>
        <span className="text-sm text-gray-500 dark:text-gray-400">{unit}</span>
      </div>
      
      {description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{description}</p>
      )}
    </motion.div>
  );
};

const HealthCard: React.FC<HealthCardProps> = ({ healthData, className = '' }) => {
  // Get the latest metrics for each server
  const latestMetrics = healthData.reduce((acc, metric) => {
    if (!acc[metric.serverId] || new Date(metric.timestamp) > new Date(acc[metric.serverId].timestamp)) {
      acc[metric.serverId] = metric;
    }
    return acc;
  }, {} as Record<string, HealthMetric>);

  const metrics = Object.values(latestMetrics);

  // Calculate overall health statistics
  const overallStats = {
    cpu: metrics.length > 0 ? metrics.reduce((sum, m) => sum + m.cpu, 0) / metrics.length : 0,
    memory: metrics.length > 0 ? metrics.reduce((sum, m) => sum + m.memory, 0) / metrics.length : 0,
    disk: metrics.length > 0 ? metrics.reduce((sum, m) => sum + m.disk, 0) / metrics.length : 0,
    ping: metrics.length > 0 ? metrics.reduce((sum, m) => sum + m.ping, 0) / metrics.length : 0,
    healthyCount: metrics.filter(m => m.status === 'healthy').length,
    warningCount: metrics.filter(m => m.status === 'warning').length,
    criticalCount: metrics.filter(m => m.status === 'critical').length,
  };

  const getStatus = (value: number, type: 'cpu' | 'memory' | 'disk' | 'ping') => {
    switch (type) {
      case 'cpu':
      case 'memory':
      case 'disk':
        return value > 90 ? 'critical' : value > 75 ? 'warning' : 'healthy';
      case 'ping':
        return value > 200 ? 'critical' : value > 100 ? 'warning' : 'healthy';
      default:
        return 'healthy';
    }
  };

  if (metrics.length === 0) {
    return (
      <div className={`card text-center py-12 ${className}`}>
        <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No health data available
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          Health monitoring will appear here once servers are configured
        </p>
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
            <Activity className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              System Health
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {metrics.length} server{metrics.length !== 1 ? 's' : ''} monitored
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="status-dot status-online"></div>
            <span className="text-gray-600 dark:text-gray-400">{overallStats.healthyCount} healthy</span>
          </div>
          {overallStats.warningCount > 0 && (
            <div className="flex items-center gap-1">
              <div className="status-dot status-warning"></div>
              <span className="text-gray-600 dark:text-gray-400">{overallStats.warningCount} warning</span>
            </div>
          )}
          {overallStats.criticalCount > 0 && (
            <div className="flex items-center gap-1">
              <div className="status-dot status-offline"></div>
              <span className="text-gray-600 dark:text-gray-400">{overallStats.criticalCount} critical</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="CPU Usage"
          value={overallStats.cpu}
          unit="%"
          icon={Cpu}
          status={getStatus(overallStats.cpu, 'cpu')}
          description="Average across all servers"
        />
        <MetricCard
          title="Memory Usage"
          value={overallStats.memory}
          unit="%"
          icon={Activity}
          status={getStatus(overallStats.memory, 'memory')}
          description="RAM utilization"
        />
        <MetricCard
          title="Disk Usage"
          value={overallStats.disk}
          unit="%"
          icon={HardDrive}
          status={getStatus(overallStats.disk, 'disk')}
          description="Storage utilization"
        />
        <MetricCard
          title="Network Latency"
          value={overallStats.ping}
          unit="ms"
          icon={Network}
          status={getStatus(overallStats.ping, 'ping')}
          description="Average response time"
        />
      </div>

      {/* Server Details */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Server Details
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-2 text-gray-600 dark:text-gray-400">Server</th>
                <th className="text-center py-2 text-gray-600 dark:text-gray-400">CPU</th>
                <th className="text-center py-2 text-gray-600 dark:text-gray-400">Memory</th>
                <th className="text-center py-2 text-gray-600 dark:text-gray-400">Disk</th>
                <th className="text-center py-2 text-gray-600 dark:text-gray-400">Ping</th>
                <th className="text-center py-2 text-gray-600 dark:text-gray-400">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {metrics.map((metric, index) => (
                <motion.tr
                  key={metric.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
                >
                  <td className="py-2 font-medium text-gray-900 dark:text-white">
                    Server {metric.serverId}
                  </td>
                  <td className="text-center py-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      metric.cpu > 90 ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                      metric.cpu > 75 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                      'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                    }`}>
                      {metric.cpu.toFixed(1)}%
                    </span>
                  </td>
                  <td className="text-center py-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      metric.memory > 90 ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                      metric.memory > 75 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                      'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                    }`}>
                      {metric.memory.toFixed(1)}%
                    </span>
                  </td>
                  <td className="text-center py-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      metric.disk > 90 ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' :
                      metric.disk > 75 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                      'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                    }`}>
                      {metric.disk.toFixed(1)}%
                    </span>
                  </td>
                  <td className="text-center py-2">
                    <span className="text-gray-600 dark:text-gray-400">
                      {metric.ping.toFixed(0)}ms
                    </span>
                  </td>
                  <td className="text-center py-2">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      metric.status === 'healthy' ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400' :
                      metric.status === 'warning' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400' :
                      'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                    }`}>
                      {metric.status}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default HealthCard;