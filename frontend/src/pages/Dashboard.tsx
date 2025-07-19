import React from 'react';

function Dashboard() {
  return (
    <div className="container mt-5">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">
          🚀 Trigger Deploy Dashboard
        </h1>
        <p className="text-muted mb-4">Manage your server deployments, view logs, and check system health.</p>

        <div className="row mb-4">
          <div className="col-md-6">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">Deploy Server</h5>
                <p className="card-text">Start a new deployment process for your server.</p>
                <button className="btn btn-primary">Deploy Now</button>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">Browse Logs</h5>
                <p className="card-text">View recent activity logs and error reports.</p>
                <button className="btn btn-secondary">View Logs</button>
              </div>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-md-12">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">Check Health</h5>
                <p className="card-text">Monitor the health and status of your system.</p>
                <button className="btn btn-success">Check Health</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
