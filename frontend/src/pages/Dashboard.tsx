import React, { useState } from 'react';
import ServerTable from '@/components/ServerTable';
import DeployModal from '@/components/DeployModal';
import HealthCard from '@/components/HealthCard';

function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">🚀 Trigger Deploy Dashboard</h1>
      <p className="text-gray-600 mb-4">
        Manage your server deployments, view logs, and check system health.
      </p>

      <div className="flex gap-4 mb-4">
        <button
          className={`py-2 px-4 rounded ${
            activeTab === 'overview' ? 'bg-blue-500 text-white' : 'bg-gray-200'
          }`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`py-2 px-4 rounded ${
            activeTab === 'logs' ? 'bg-blue-500 text-white' : 'bg-gray-200'
          }`}
          onClick={() => setActiveTab('logs')}
        >
          Logs
        </button>
        <button
          className={`py-2 px-4 rounded ${
            activeTab === 'health' ? 'bg-blue-500 text-white' : 'bg-gray-200'
          }`}
          onClick={() => setActiveTab('health')}
        >
          Health
        </button>
      </div>

      {activeTab === 'overview' && (
        <div>
          <h2 className="text-xl font-bold mb-4">Overview</h2>
          <p>Start a new deployment process for your server.</p>
          <button className="py-2 px-4 bg-green-500 text-white rounded hover:bg-green-600 transition-all">
            Deploy Now
          </button>
        </div>
      )}

      {activeTab === 'logs' && (
        <div>
          <h2 className="text-xl font-bold mb-4">Logs</h2>
          <p>View recent activity logs and error reports.</p>
          <button className="py-2 px-4 bg-gray-500 text-white rounded hover:bg-gray-600 transition-all">
            View Logs
          </button>
        </div>
      )}

      {activeTab === 'health' && (
        <div>
          <h2 className="text-xl font-bold mb-4">Health</h2>
          <p>Monitor the health and status of your system.</p>
          <button className="py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600 transition-all">
            Check Health
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div>
          <ServerTable servers={[]} onEdit={() => {}} onDelete={() => {}} onDeploy={() => {}} />
        </div>
        <div>
          <DeployModal isOpen={true} onClose={() => {}} onDeploy={() => {}} />
        </div>
      </div>
      <div className="mt-4">
        <HealthCard healthData={[]} />
      </div>
    </div>
  );
}

export default Dashboard;
