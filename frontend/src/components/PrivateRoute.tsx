import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useGlobalState from '@/store/globalState';

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { token, isAuthenticated } = useGlobalState();
  const location = useLocation();

  // Check if user is authenticated
  const isLoggedIn = isAuthenticated && token;

  if (!isLoggedIn) {
    // Redirect to login page with return url
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};

export default PrivateRoute;
