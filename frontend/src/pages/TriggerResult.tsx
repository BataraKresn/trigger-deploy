import React, { useState } from 'react';
import { motion } from 'framer-motion';

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

        <div
          className="log-link cursor-pointer text-blue-500 underline"
          onClick={toggleLog}
        >
          🔗 View Log File
        </div>
        {logVisible && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="log-content bg-gray-100 p-4 rounded-md shadow-md mt-4"
          >
            Log data here...
          </motion.div>
        )}

        <div
          className="log-link cursor-pointer text-blue-500 underline mt-4"
          onClick={toggleStream}
        >
          🔄 Stream Log (Real-time)
        </div>
        {streamVisible && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="stream-content bg-gray-100 p-4 rounded-md shadow-md mt-4"
          >
            Waiting for updates...
          </motion.div>
        )}
      </div>
    </div>
  );
}

export default TriggerResult;
