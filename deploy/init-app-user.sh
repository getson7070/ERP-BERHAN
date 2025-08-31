#!/bin/sh
set -e

# Ensure the application role and database exist and have the proper grants.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-SQL
DO
$$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = 'erp_app'
    ) THEN
        CREATE ROLE erp_app LOGIN PASSWORD '${APP_DB_PASSWORD}';
    END IF;
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'erp'
    ) THEN
        CREATE DATABASE erp;
    END IF;
END
$$;
GRANT ALL PRIVILEGES ON DATABASE erp TO erp_app;
\connect erp
GRANT USAGE ON SCHEMA public TO erp_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO erp_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO erp_app;
SQL
