-- Creates 'erp' DB on first Postgres boot (runs automatically)
CREATE DATABASE erp OWNER postgres;
GRANT ALL PRIVILEGES ON DATABASE erp TO postgres;