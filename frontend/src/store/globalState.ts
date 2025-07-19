import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'user';
  avatar?: string;
}

export interface Server {
  id: string;
  ip: string;
  alias: string;
  name: string;
  user: string;
  scriptPath: string;
  lastDeployed: string;
  status: 'online' | 'offline' | 'deploying' | 'error';
}

export interface DeployLog {
  id: string;
  serverId: string;
  timestamp: string;
  status: 'success' | 'error' | 'pending';
  output: string;
  duration?: number;
}

export interface HealthMetric {
  id: string;
  serverId: string;
  timestamp: string;
  cpu: number;
  memory: number;
  disk: number;
  ping: number;
  status: 'healthy' | 'warning' | 'critical';
}

interface GlobalState {
  // Auth
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  
  // UI
  darkMode: boolean;
  sidebarCollapsed: boolean;
  
  // Data
  servers: Server[];
  deployLogs: DeployLog[];
  healthMetrics: HealthMetric[];
  
  // Loading states
  isLoading: boolean;
  deployingServers: Set<string>;
  
  // Actions
  setToken: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  toggleDarkMode: () => void;
  toggleSidebar: () => void;
  setLoading: (loading: boolean) => void;
  setServers: (servers: Server[]) => void;
  updateServerStatus: (serverId: string, status: Server['status']) => void;
  addDeployLog: (log: DeployLog) => void;
  setDeployingServer: (serverId: string, deploying: boolean) => void;
  addHealthMetric: (metric: HealthMetric) => void;
}

const useGlobalState = create<GlobalState>()(
  persist(
    (set, get) => ({
      // Auth
      token: null,
      user: null,
      isAuthenticated: false,
      
      // UI
      darkMode: false,
      sidebarCollapsed: false,
      
      // Data
      servers: [],
      deployLogs: [],
      healthMetrics: [],
      
      // Loading states
      isLoading: false,
      deployingServers: new Set(),
      
      // Actions
      setToken: (token) => {
        localStorage.setItem('authToken', token);
        set({ token, isAuthenticated: true });
      },
      
      setUser: (user) => set({ user }),
      
      logout: () => {
        localStorage.removeItem('authToken');
        set({ 
          token: null, 
          user: null, 
          isAuthenticated: false,
          servers: [],
          deployLogs: [],
          healthMetrics: []
        });
      },
      
      toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
      
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      setLoading: (loading) => set({ isLoading: loading }),
      
      setServers: (servers) => set({ servers }),
      
      updateServerStatus: (serverId, status) => set((state) => ({
        servers: state.servers.map(server =>
          server.id === serverId ? { ...server, status } : server
        )
      })),
      
      addDeployLog: (log) => set((state) => ({
        deployLogs: [log, ...state.deployLogs].slice(0, 100) // Keep only last 100 logs
      })),
      
      setDeployingServer: (serverId, deploying) => set((state) => {
        const newDeployingServers = new Set(state.deployingServers);
        if (deploying) {
          newDeployingServers.add(serverId);
        } else {
          newDeployingServers.delete(serverId);
        }
        return { deployingServers: newDeployingServers };
      }),
      
      addHealthMetric: (metric) => set((state) => ({
        healthMetrics: [metric, ...state.healthMetrics].slice(0, 1000) // Keep only last 1000 metrics
      })),
    }),
    {
      name: 'trigger-deploy-storage',
      partialize: (state) => ({
        darkMode: state.darkMode,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

export default useGlobalState;
