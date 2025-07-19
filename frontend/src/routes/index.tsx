import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from '@/components/PrivateRoute';
import NotFound from '@/components/NotFound';

const LoginPage = React.lazy(() => import('@/pages/LoginPage'));
const Dashboard = React.lazy(() => import('@/pages/Dashboard'));
const DeployLogic = React.lazy(() => import('@/pages/DeployLogic'));
const DeployServers = React.lazy(() => import('@/pages/DeployServers'));
const TriggerResult = React.lazy(() => import('@/pages/TriggerResult'));
const Home = React.lazy(() => import('@/pages/Home'));

const AppRoutes = () => (
  <Suspense fallback={<div>Loading...</div>}>
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/deploy"
        element={
          <PrivateRoute>
            <DeployLogic />
          </PrivateRoute>
        }
      />
      <Route
        path="/servers"
        element={
          <PrivateRoute>
            <DeployServers />
          </PrivateRoute>
        }
      />
      <Route
        path="/result"
        element={
          <PrivateRoute>
            <TriggerResult />
          </PrivateRoute>
        }
      />
      <Route
        path="/status"
        element={
          <PrivateRoute>
            <Home />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  </Suspense>
);

export default AppRoutes;