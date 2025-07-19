import axios from 'axios';
import useGlobalState from '@/store/globalState';

// Create axios instance with base configuration
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

export const apiClient = axios.create({
  baseURL: baseURL.replace(/\/+$/, ''), // Remove trailing slashes
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const { token } = useGlobalState.getState();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Unauthorized - token expired or invalid
          useGlobalState.getState().logout();
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
          break;
        case 403:
          // Forbidden
          console.error('Access forbidden');
          break;
        case 404:
          // Not found
          console.error('Resource not found');
          break;
        case 500:
          // Internal server error
          console.error('Internal server error');
          break;
        default:
          console.error('API Error:', error.response.data?.message || error.message);
      }
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.message);
    } else {
      // Other error
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    validate: '/auth/validate',
  },
  servers: {
    list: '/servers',
    create: '/servers',
    update: (id: string) => `/servers/${id}`,
    delete: (id: string) => `/servers/${id}`,
    deploy: (id: string) => `/servers/${id}/deploy`,
  },
  health: {
    check: '/health',
    metrics: '/health/metrics',
    server: (id: string) => `/health/servers/${id}`,
  },
  logs: {
    deployment: '/logs/deployment',
    system: '/logs/system',
    server: (id: string) => `/logs/servers/${id}`,
  },
};

// Helper functions for common API calls
export const authAPI = {
  login: (credentials: { username: string; password: string }) =>
    apiClient.post(endpoints.auth.login, credentials),
  
  logout: () =>
    apiClient.post(endpoints.auth.logout),
  
  validate: () =>
    apiClient.get(endpoints.auth.validate),
};

export const serversAPI = {
  getAll: () =>
    apiClient.get(endpoints.servers.list),
  
  create: (server: any) =>
    apiClient.post(endpoints.servers.create, server),
  
  update: (id: string, server: any) =>
    apiClient.put(endpoints.servers.update(id), server),
  
  delete: (id: string) =>
    apiClient.delete(endpoints.servers.delete(id)),
  
  deploy: (id: string, options?: any) =>
    apiClient.post(endpoints.servers.deploy(id), options),
};

export const healthAPI = {
  getMetrics: () =>
    apiClient.get(endpoints.health.metrics),
  
  getServerHealth: (id: string) =>
    apiClient.get(endpoints.health.server(id)),
  
  checkHealth: () =>
    apiClient.get(endpoints.health.check),
};

export const logsAPI = {
  getDeploymentLogs: (params?: any) =>
    apiClient.get(endpoints.logs.deployment, { params }),
  
  getSystemLogs: (params?: any) =>
    apiClient.get(endpoints.logs.system, { params }),
  
  getServerLogs: (id: string, params?: any) =>
    apiClient.get(endpoints.logs.server(id), { params }),
};

export default apiClient;