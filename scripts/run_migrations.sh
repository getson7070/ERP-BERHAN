#!/bin/sh
# Run Alembic migrations to upgrade database schema.
# Intended to be executed as a separate deployment step before starting the app.
set -e
alembic upgrade head
