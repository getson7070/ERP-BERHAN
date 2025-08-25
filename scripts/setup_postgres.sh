#!/usr/bin/env bash
set -euo pipefail

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

# verify connectivity
pg_isready -d postgresql://postgres:postgres@localhost:5432/erp

echo "PostgreSQL ready on localhost:5432 with user 'postgres' and database 'erp'"
