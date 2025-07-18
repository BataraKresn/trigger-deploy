import React, { useState } from 'react';

function Home() {
  const [status, setStatus] = useState('');
  const [logs, setLogs] = useState('');

  const fetchStatus = () => {
    // Simulate API call
    setTimeout(() => {
      setStatus('Success');
    }, 1000);
  };

  const fetchLogs = () => {
    // Simulate API call
    setTimeout(() => {
      setLogs('Log data here...');
    }, 1000);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Trigger Deploy</h1>
      <button className="btn" onClick={fetchStatus}>Check Status</button>
      <button className="btn" onClick={fetchLogs}>View Logs</button>

      {status && <p className="status success">Status: {status}</p>}
      {logs && (
        <div className="log-output">
          <pre>{logs}</pre>
        </div>
      )}
    </div>
  );
}

export default Home;
