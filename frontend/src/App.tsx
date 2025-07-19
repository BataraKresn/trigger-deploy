import React, { useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';

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
    console.log('%c[App Mounted]', 'color: green');
    console.log('Token:', token ?? '(no token)');
  }, [token]);

  return (
    <Router>
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <AppRoutes />
      </ErrorBoundary>
    </Router>
  );
}

export default App;
