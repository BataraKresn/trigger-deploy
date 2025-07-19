import React from 'react';

interface HealthData {
  id: string;
  ip: string;
  pingTime: number;
  dnsResolved: string;
  memoryUsage: number;
  ramUsage: number;
  diskUsage: number;
  status: 'up' | 'down';
}

interface HealthCardProps {
  healthData: HealthData[];
}

const HealthCard: React.FC<HealthCardProps> = ({ healthData }) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-700">
        <thead>
          <tr className="bg-gray-100 dark:bg-gray-800">
            <th className="border border-gray-300 dark:border-gray-700 px-4 py-2">IP/Domain</th>
            <th className="border border-gray-300 dark:border-gray-700 px-4 py-2">Ping Time</th>
            <th className="border border-gray-300 dark:border-gray-700 px-4 py-2">DNS Resolved</th>
            <th className="border border-gray-300 dark:border-gray-700 px-4 py-2">Memory Usage</th>
            <th className="border border-gray-300 dark:border-gray-700 px-4 py-2">RAM Usage</th>
            <th className="border border-gray-300 dark:border-gray-700 px-4 py-2">Disk Usage</th>
            <th className="border border-gray-300 dark:border-gray-700 px-4 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {healthData.map((data) => (
            <tr key={data.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <td className="border border-gray-300 dark:border-gray-700 px-4 py-2">{data.ip}</td>
              <td className="border border-gray-300 dark:border-gray-700 px-4 py-2">{data.pingTime} ms</td>
              <td className="border border-gray-300 dark:border-gray-700 px-4 py-2">{data.dnsResolved}</td>
              <td className="border border-gray-300 dark:border-gray-700 px-4 py-2">{data.memoryUsage}%</td>
              <td className="border border-gray-300 dark:border-gray-700 px-4 py-2">{data.ramUsage}%</td>
              <td className="border border-gray-300 dark:border-gray-700 px-4 py-2">{data.diskUsage}%</td>
              <td className="border border-gray-300 dark:border-gray-700 px-4 py-2">
                <span
                  className={`inline-block w-4 h-4 rounded-full ${
                    data.status === 'up' ? 'bg-green-500' : 'bg-red-500'
                  }`}
                ></span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default HealthCard;