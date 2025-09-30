# migrations/env.py
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("No database URL provided. Set DATABASE_URL.")
config.set_main_option("sqlalchemy.url", db_url)

# ... rest unchanged 