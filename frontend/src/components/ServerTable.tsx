import React from 'react';

interface Server {
  id: string;
  ip: string;
  alias: string;
  name: string;
  user: string;
  scriptPath: string;
  lastDeployed: string;
}

interface ServerTableProps {
  servers: Server[];
  onEdit: (server: Server) => void;
  onDelete: (server: Server) => void;
  onDeploy: (server: Server) => void;
}

const ServerTable: React.FC<ServerTableProps> = ({ servers, onEdit, onDelete, onDeploy }) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100 dark:bg-gray-800">
            <th className="border border-gray-300 px-4 py-2">IP Address</th>
            <th className="border border-gray-300 px-4 py-2">Alias</th>
            <th className="border border-gray-300 px-4 py-2">Name</th>
            <th className="border border-gray-300 px-4 py-2">User</th>
            <th className="border border-gray-300 px-4 py-2">Path to Script</th>
            <th className="border border-gray-300 px-4 py-2">Last Deployed</th>
            <th className="border border-gray-300 px-4 py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {servers.map((server) => (
            <tr key={server.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200">
              <td className="border border-gray-300 px-4 py-2">{server.ip}</td>
              <td className="border border-gray-300 px-4 py-2">{server.alias}</td>
              <td className="border border-gray-300 px-4 py-2">{server.name}</td>
              <td className="border border-gray-300 px-4 py-2">{server.user}</td>
              <td className="border border-gray-300 px-4 py-2">{server.scriptPath}</td>
              <td className="border border-gray-300 px-4 py-2">{server.lastDeployed}</td>
              <td className="border border-gray-300 px-4 py-2">
                <button className="text-blue-500 hover:underline" onClick={() => onEdit(server)}>Edit</button>
                <button className="text-red-500 hover:underline ml-2" onClick={() => onDelete(server)}>Delete</button>
                <button className="text-green-500 hover:underline ml-2" onClick={() => onDeploy(server)}>Deploy</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ServerTable;