import React from 'react';
import Layout from '@/components/Layout';

const LogsPage = () => {
  return (
    <Layout>
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Logs</h1>
        <p>View system logs here.</p>
      </div>
    </Layout>
  );
};

export default LogsPage;
