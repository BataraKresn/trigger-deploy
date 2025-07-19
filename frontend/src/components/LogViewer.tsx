import React from 'react';

interface LogViewerProps {
  logs: string[];
}

const LogViewer: React.FC<LogViewerProps> = ({ logs }) => {
  return (
    <div className="bg-gray-900 text-white p-4 rounded shadow-lg">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="1.5"
            stroke="currentColor"
            className="w-6 h-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3.75 3v11.25M3.75 14.25v6M3.75 20.25h16.5M20.25 20.25v-6M20.25 14.25V3"
            />
          </svg>
        </span>
        Logs
      </h2>
      <div className="overflow-y-auto h-64 border border-gray-700 rounded">
        {logs.map((log, index) => (
          <p
            key={index}
            className="text-sm font-mono px-2 py-1 hover:bg-gray-800 transition-colors duration-200"
          >
            {log}
          </p>
        ))}
      </div>
    </div>
  );
};

export default LogViewer;