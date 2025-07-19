import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
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
  const { token, darkMode } = useGlobalState();

  useEffect(() => {
    const storedToken = localStorage.getItem('authToken');
    if (storedToken && !token) {
      // Validate token on app start
      axios.get('/api/validate-token', {
        headers: {
          Authorization: `Bearer ${storedToken}`,
        },
      })
        .catch(() => {
          localStorage.removeItem('authToken');
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        });
    }
  }, [token]);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <Router>
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          <AppRoutes />
        </ErrorBoundary>
      </Router>
      
      {/* Toast Notifications */}
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme={darkMode ? 'dark' : 'light'}
        className="text-sm"
      />
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
