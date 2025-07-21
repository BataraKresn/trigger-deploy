-- PostgreSQL Database Initialization Script
-- This script will be executed when the PostgreSQL container starts

-- Create database if not exists (already handled by POSTGRES_DB environment variable)

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create indexes that might be useful for performance
-- (Tables will be created by the application using asyncpg)

-- Set timezone
SET timezone = 'Asia/Jakarta';

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Note: Tables and triggers will be created by the application
-- This script is mainly for extensions and utility functions
