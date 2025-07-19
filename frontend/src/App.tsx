import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import useGlobalState from './store/globalState';
import type { FallbackProps } from 'react-error-boundary';

const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));

import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error }: FallbackProps) {
  return <div>Error occurred: {error.message}</div>;
}

function App() {
  const { token } = useGlobalState();

  useEffect(() => {
    console.log('App component mounted');
    console.log('Token:', token);
    console.log('Token status:', token ? 'Valid' : 'Invalid');
  }, [token]);

  return (
    <Router>
      <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={token ? <Dashboard /> : <LoginPage />}
          />
        </Routes>
      </Suspense>
    </ErrorBoundary>
      <footer>
        <p>© 2024 Dev Tiger</p>
      </footer>
    </Router>
  );
}

export default App;
