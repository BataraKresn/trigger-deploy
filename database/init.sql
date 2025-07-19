-- Deploy Server Database Initialization Script
-- This script will run when the database container starts for the first time

-- Create additional extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance (will be created by migrations, but kept here for reference)
-- CREATE INDEX IF NOT EXISTS idx_servers_ip ON servers(ip);
-- CREATE INDEX IF NOT EXISTS idx_deploy_logs_server_id ON deploy_logs(server_id);
-- CREATE INDEX IF NOT EXISTS idx_deploy_logs_timestamp ON deploy_logs(created_at);

-- Insert default admin user (will be handled by Flask app)
-- This is just a placeholder for any initial data setup

-- Set default timezone
SET timezone = 'Asia/Jakarta';

-- Log initialization completion
DO $$
BEGIN
    RAISE NOTICE 'Deploy Server Database initialized successfully!';
END $$;
