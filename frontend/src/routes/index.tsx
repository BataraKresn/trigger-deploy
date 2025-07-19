import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from '@/components/PrivateRoute';
import NotFound from '@/components/NotFound';

const LoginPage = React.lazy(() => import('@/pages/LoginPage'));
const Dashboard = React.lazy(() => import('@/pages/Dashboard'));
// Ensure the correct path to the ServerList module
const ServerList = React.lazy(() => import('@/pages/ServerList'));
const DeployPage = React.lazy(() => import('@/pages/DeployPage'));
const HealthCheck = React.lazy(() => import('@/pages/HealthCheck'));
const LogsPage = React.lazy(() => import('@/pages/LogsPage'));
// Ensure the correct path to the SettingsPage module
const SettingsPage = React.lazy(() => import('@/pages/SettingsPage'));

const AppRoutes = () => (
  <Suspense fallback={<div>Loading...</div>}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/servers"
        element={
          <PrivateRoute>
            <ServerList />
          </PrivateRoute>
        }
      />
      <Route
        path="/deploy"
        element={
          <PrivateRoute>
            <DeployPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/health"
        element={
          <PrivateRoute>
            <HealthCheck />
          </PrivateRoute>
        }
      />
      <Route
        path="/logs"
        element={
          <PrivateRoute>
            <LogsPage />
          </PrivateRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <PrivateRoute>
            <SettingsPage />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  </Suspense>
);

export default AppRoutes;