import React, { Suspense } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import useGlobalState from './store/globalState';

const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));

function App() {
  const { token } = useGlobalState();

  return (
    <Router>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/dashboard" element={token ? <Dashboard /> : <LoginPage />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;
