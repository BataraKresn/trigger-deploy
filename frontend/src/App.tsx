import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import axios from 'axios';

import useGlobalState from '@/store/globalState';
import Sidebar from '@/components/Sidebar';
import Header from '@/components/Header';
import ServerTable from '@/components/ServerTable';
import DeployModal from '@/components/DeployModal';
import HealthCard from '@/components/HealthCard';
import LogViewer from '@/components/LogViewer';
import PingChart from '@/components/PingChart';

function ErrorFallback({ error }: { error: Error }) {
  return (
    <div className="p-4 text-red-600">
      <h2 className="text-xl font-bold">Something went wrong</h2>
      <p>{error.message}</p>
    </div>
  );
}

function App() {
  const { token } = useGlobalState();
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
  }, []);

  useEffect(() => {
    if (!token && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }, [token]);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token && window.location.pathname === '/login') {
      axios.get('/api/validate-token', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then(() => {
          window.location.href = '/dashboard';
        })
        .catch(() => {
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        });
    }
  }, []);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <Router>
        <Sidebar />
        <div className="flex flex-col flex-1">
          <Header onToggleDarkMode={() => setDarkMode(!darkMode)} />
          <ErrorBoundary FallbackComponent={ErrorFallback}>
            <Routes>
              <Route path="/dashboard" element={<div>Dashboard Content</div>} />
              <Route path="/servers" element={<ServerTable servers={[]} onEdit={() => {}} onDelete={() => {}} onDeploy={() => {}} />} />
              <Route path="/deploy" element={<DeployModal isOpen={true} onClose={() => {}} onDeploy={() => {}} />} />
              <Route path="/health" element={<HealthCard healthData={[]} />} />
              <Route path="/logs" element={<LogViewer logs={[]} />} />
              <Route path="/settings" element={<PingChart data={[]} />} />
            </Routes>
          </ErrorBoundary>
        </div>
      </Router>
    </div>
  );
}

// Add Axios interceptor to include token in Authorization header for all requests
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default App;
