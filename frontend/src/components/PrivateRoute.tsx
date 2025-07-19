import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useGlobalState from '@/store/globalState';

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { token } = useGlobalState();
  const location = useLocation();

  const verifyToken = (token: string) => {
    // Add your token verification logic here
    return true; // Return true if valid, false otherwise
  };

  if (!token || !verifyToken(token)) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};

export default PrivateRoute;
