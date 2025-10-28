"""Alembic environment configuration.

Sets up autogenerate metadata from orchestrator models when available and
supports both online and offline migration modes.

Environment
-----------
- Respects `DATABASE_URL` if provided; otherwise uses `sqlalchemy.url` from ini.

Usage
-----
- Invoked automatically by Alembic commands, e.g. `alembic upgrade head`.
"""
from __future__ import annotations

import os
import sys
from typing import Optional
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure project root is importable for orchestrator.*
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import target metadata if models are available. Keep migrations runnable even
# if models are missing (e.g., in a minimal environment running only migrations).
target_metadata = None
try:
    from orchestrator.core.database import Base  # type: ignore
    target_metadata = Base.metadata
except Exception:
    target_metadata = None


def get_url() -> str:
    """Resolve the database URL.

    Returns:
        Database URL from `DATABASE_URL` env var or Alembic config.
    """
    env_url = os.getenv("DATABASE_URL")
    return env_url or config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with a URL and emits SQL to the script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

