import React, { useState } from 'react';

function TriggerResult() {
  const [logVisible, setLogVisible] = useState(false);
  const [streamVisible, setStreamVisible] = useState(false);

  const toggleLog = () => setLogVisible(!logVisible);
  const toggleStream = () => setStreamVisible(!streamVisible);

  return (
    <div className="container mx-auto p-4">
      <div className="box">
        <div className="status text-green-500 text-xl mb-4">✅ Deploy Triggered Successfully</div>
        <p><strong>Log File:</strong> log_file_path_here</p>

        <div className="log-link cursor-pointer text-blue-500 underline" onClick={toggleLog}>🔗 View Log File</div>
        {logVisible && (
          <div className="log-content bg-gray-100 p-4 rounded-md">
            Log data here...
          </div>
        )}

        <div className="log-link cursor-pointer text-blue-500 underline" onClick={toggleStream}>🔄 Stream Log (Real-time)</div>
        {streamVisible && (
          <div className="stream-content bg-gray-100 p-4 rounded-md">
            Waiting for updates...
          </div>
        )}
      </div>
    </div>
  );
}

export default TriggerResult;
