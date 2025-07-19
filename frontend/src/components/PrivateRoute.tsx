import React from 'react';
import { Navigate } from 'react-router-dom';
import useGlobalState from '../store/globalState';

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { token } = useGlobalState();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default PrivateRoute;
