"""
Database initialization script for Week 2 MVP.

Usage:
    python scripts/init_database.py [--env production|development]

This script:
- Resolves the database URL from `--env` and environment variables.
- Applies Alembic migrations up to head.
- Validates that core tables exist.
- Optionally seeds development data when ORM models are available.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


EXPECTED_TABLES: List[str] = [
    "workers",
    "jobs",
    "resource_allocations",
    "idempotency_keys",
]


@dataclass(frozen=True)
class InitOptions:
    """Validated options for initialization.

    Attributes:
        env: Target environment, either "production" or "development".
    """

    env: str

    def __post_init__(self) -> None:  # type: ignore[override]
        allowed = {"production", "development"}
        if self.env not in allowed:
            raise ValueError(f"Invalid env '{self.env}'. Allowed: {sorted(allowed)}")


def _resolve_alembic_ini() -> str:
    """Find an Alembic ini file in conventional locations.

    Returns:
        Path to an ini file. Raises FileNotFoundError if not found.

    Examples:
        >>> isinstance(_resolve_alembic_ini(), str)
        True
    """
    candidates = [PROJECT_ROOT / "alembic.ini", PROJECT_ROOT / "orchestrator" / "alembic.ini"]
    for path in candidates:
        if path.is_file():
            return str(path)
    raise FileNotFoundError("Could not locate alembic.ini in project root or orchestrator/")


def _resolve_db_url(env: str) -> str:
    """Resolve database URL from environment and config.

    Args:
        env: Target environment.
    Returns:
        A SQLAlchemy URL string.
    """
    if env == "production":
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set for production")
        return db_url
    return "sqlite:///./orchestrator.db"


def _apply_migrations(db_url: str) -> None:
    """Apply Alembic migrations to the latest head.

    Args:
        db_url: Database URL to apply migrations against.
    """
    ini_path = _resolve_alembic_ini()
    cfg = Config(ini_path)
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")


def _validate_schema(db_url: str) -> List[str]:
    """Validate that expected tables exist.

    Args:
        db_url: Database URL to inspect.
    Returns:
        List of discovered table names.
    Raises:
        ValueError if an expected table is missing.
    """
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    missing = [t for t in EXPECTED_TABLES if t not in tables]
    if missing:
        raise ValueError(f"Missing table(s): {', '.join(missing)}")
    return tables


def _seed_development_data() -> None:
    """Seed development data if ORM models and Session are available.

    This step is optional and will be skipped if the orchestrator models are not
    importable in the current environment.
    """
    try:
        from orchestrator.core.database import SessionLocal  # type: ignore
        from orchestrator.core.db_models import (  # type: ignore
            Job,
            JobStatus,
            Worker,
            WorkerStatus,
        )
    except Exception:
        # Silently skip seeding if models are not present.
        return

    session = SessionLocal()
    try:
        # Create a test worker and job only if they don't exist
        if not session.query(Worker).filter_by(id="test-worker-1").first():
            session.add(
                Worker(id="test-worker-1", workspace_id="dev-workspace", status=WorkerStatus.IDLE)
            )
        if not session.query(Job).filter_by(id="test-job-1").first():
            session.add(
                Job(
                    id="test-job-1",
                    depth=0,
                    worker_count=1,
                    status=JobStatus.PENDING,
                    task_description="Test task for development",
                )
            )
        session.commit()
    finally:
        session.close()


def init_database(env: str = "development") -> None:
    """Initialize database with Alembic migrations.

    Args:
        env: Environment ("production" or "development").
    """
    opts = InitOptions(env=env)
    db_url = _resolve_db_url(opts.env)

    print(f"Initializing database for {opts.env} environment...")
    print(f"Database URL: {db_url}")

    print("Running Alembic migrations...")
    _apply_migrations(db_url)
    print("✅ Migrations complete")

    print("Validating database schema...")
    tables = _validate_schema(db_url)
    print(f"✅ All tables created: {', '.join(sorted(tables))}")

    if opts.env == "development":
        print("Seeding development data (optional)...")
        _seed_development_data()
        print("✅ Development data step complete")

    print("🎉 Database initialization complete!")


def _parse_args(argv: List[str]) -> InitOptions:
    parser = argparse.ArgumentParser(description="Initialize database with Alembic migrations")
    parser.add_argument(
        "--env",
        choices=["production", "development"],
        default="development",
        help="Environment (default: development)",
    )
    args = parser.parse_args(argv)
    return InitOptions(env=args.env)


def main(argv: List[str] | None = None) -> int:
    try:
        opts = _parse_args(argv or [])
        init_database(opts.env)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
