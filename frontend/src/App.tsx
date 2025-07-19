import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import axios from 'axios';

import useGlobalState from '@/store/globalState';
import AppRoutes from '@/routes';

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
      axios.post('/api/validate-token', { token })
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
    <Router>
      <ErrorBoundary FallbackComponent={ErrorFallback}>
            <AppRoutes />
      </ErrorBoundary>
    </Router>
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
