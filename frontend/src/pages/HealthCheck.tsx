import React from 'react';
import Layout from '@/components/Layout';

const HealthCheck = () => {
  return (
    <Layout>
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Health Check</h1>
        <p>Monitor the health of your system.</p>
      </div>
    </Layout>
  );
};

export default HealthCheck;
