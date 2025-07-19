import { useState, useCallback } from 'react';
import { toast } from 'react-toastify';
import useGlobalState, { Server, DeployLog } from '@/store/globalState';

export interface DeploymentResult {
  success: boolean;
  output: string[];
  duration: number;
  error?: string;
}

export const useDeployLogic = () => {
  const { 
    setDeployingServer, 
    addDeployLog, 
    updateServerStatus,
    deployingServers 
  } = useGlobalState();
  
  const [deploymentResults, setDeploymentResults] = useState<Record<string, DeploymentResult>>({});

  const simulateDeployment = useCallback(async (server: Server): Promise<DeploymentResult> => {
    const startTime = Date.now();
    const output: string[] = [];
    
    try {
      // Simulate deployment steps
      output.push(`🚀 Starting deployment to ${server.name} (${server.ip})`);
      output.push(`📡 Connecting to server...`);
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (Math.random() > 0.8) { // 20% chance of connection failure
        throw new Error('Connection timeout');
      }
      
      output.push(`✅ Connected successfully`);
      output.push(`📦 Preparing deployment package...`);
      
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      output.push(`🔄 Uploading files to ${server.scriptPath}`);
      output.push(`$ ssh ${server.user}@${server.ip}`);
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      if (Math.random() > 0.9) { // 10% chance of script failure
        throw new Error('Deployment script failed');
      }
      
      output.push(`🔧 Executing deployment script...`);
      output.push(`$ ${server.scriptPath}`);
      output.push(`📝 Script output:`);
      output.push(`   Building application...`);
      output.push(`   Installing dependencies...`);
      output.push(`   Restarting services...`);
      
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      output.push(`✅ Deployment completed successfully!`);
      output.push(`🎉 Application is now live`);
      
      const duration = Date.now() - startTime;
      
      return {
        success: true,
        output,
        duration
      };
      
    } catch (error) {
      const duration = Date.now() - startTime;
      output.push(`❌ Deployment failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      return {
        success: false,
        output,
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }, []);

  const deployToServer = useCallback(async (server: Server): Promise<DeploymentResult> => {
    if (deployingServers.has(server.id)) {
      toast.warning('Deployment already in progress for this server');
      throw new Error('Deployment already in progress for this server');
    }

    // Set deployment state
    setDeployingServer(server.id, true);
    updateServerStatus(server.id, 'deploying');
    
    // Show deployment started toast
    toast.info(`🚀 Deployment started for ${server.name}`, {
      position: 'top-right',
      autoClose: 3000,
    });

    try {
      // Simulate API call or actual deployment
      const result = await simulateDeployment(server);
      
      // Create deploy log entry
      const deployLog: DeployLog = {
        id: `deploy-${Date.now()}-${server.id}`,
        serverId: server.id,
        timestamp: new Date().toISOString(),
        status: result.success ? 'success' : 'error',
        output: result.output.join('\n'),
        duration: result.duration
      };
      
      addDeployLog(deployLog);
      
      // Update server status based on deployment result
      updateServerStatus(server.id, result.success ? 'online' : 'error');
      
      // Store result for UI
      setDeploymentResults(prev => ({
        ...prev,
        [server.id]: result
      }));
      
      // Show success or error toast
      if (result.success) {
        toast.success(`✅ Deployment to ${server.name} completed successfully!`, {
          position: 'top-right',
          autoClose: 5000,
        });
      } else {
        toast.error(`❌ Deployment to ${server.name} failed: ${result.error}`, {
          position: 'top-right',
          autoClose: 7000,
        });
      }
      
      return result;
      
    } finally {
      // Clear deployment state
      setDeployingServer(server.id, false);
    }
  }, [
    deployingServers,
    setDeployingServer,
    updateServerStatus,
    addDeployLog,
    simulateDeployment
  ]);

  const deployToMultipleServers = useCallback(async (servers: Server[]): Promise<Record<string, DeploymentResult>> => {
    const results: Record<string, DeploymentResult> = {};
    
    // Deploy to servers in parallel (or sequentially if preferred)
    const deploymentPromises = servers.map(async (server) => {
      try {
        const result = await deployToServer(server);
        results[server.id] = result;
      } catch (error) {
        results[server.id] = {
          success: false,
          output: [`❌ Failed to start deployment: ${error instanceof Error ? error.message : 'Unknown error'}`],
          duration: 0,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    });
    
    await Promise.all(deploymentPromises);
    return results;
  }, [deployToServer]);

  const getDeploymentResult = useCallback((serverId: string): DeploymentResult | undefined => {
    return deploymentResults[serverId];
  }, [deploymentResults]);

  const clearDeploymentResult = useCallback((serverId: string) => {
    setDeploymentResults(prev => {
      const newResults = { ...prev };
      delete newResults[serverId];
      return newResults;
    });
  }, []);

  const isDeploying = useCallback((serverId: string): boolean => {
    return deployingServers.has(serverId);
  }, [deployingServers]);

  return {
    deployToServer,
    deployToMultipleServers,
    getDeploymentResult,
    clearDeploymentResult,
    isDeploying,
    deploymentResults
  };
};

export default useDeployLogic;
