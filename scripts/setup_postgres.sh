#!/usr/bin/env bash
set -euo pipefail

# Optional MySQL setup for environments without PostgreSQL
if [[ "${USE_MYSQL:-0}" -eq 1 ]]; then
  if ! command -v mysql >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y mysql-server
  fi
  sudo service mysql start
  mysql -u root -e "CREATE DATABASE IF NOT EXISTS erp;"
  echo "MySQL ready on localhost with database 'erp'"
  exit 0
fi

# Install PostgreSQL if not already installed
if ! command -v psql >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y postgresql postgresql-contrib
fi

# Start PostgreSQL cluster
sudo pg_ctlcluster 16 main start

# Ensure postgres user has password and database exists
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='postgres'" | grep -q 1 || {
  echo "Creating postgres role"
  sudo -u postgres createuser postgres
}
# set password (idempotent)
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# create default erp database if absent
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='erp'" | grep -q 1 || sudo -u postgres createdb erp

# create KPI materialized view for analytics
sudo -u postgres psql erp <<'SQL'
CREATE MATERIALIZED VIEW IF NOT EXISTS inventory_kpi AS
  SELECT org_id,
         COUNT(*) AS item_count,
         SUM(quantity) AS total_quantity
  FROM inventory_items
  GROUP BY org_id;
SQL

# run basic connectivity and troubleshooting checks (see docs/postgres_troubleshooting.md)
pg_isready -d postgresql://postgres:postgres@localhost:5432/erp?sslmode=require
"$(dirname "$0")/run_migrations.sh" || true

echo "PostgreSQL ready on localhost:5432 with user 'postgres' and database 'erp'"
