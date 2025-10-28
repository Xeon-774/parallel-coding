"""
Database configuration module for Parallel AI Coding Orchestrator.

Provides SQLAlchemy engine, session management, and database utilities.
Supports both PostgreSQL (production) and SQLite (development/testing).

Security:
- SQL parameterization via SQLAlchemy ORM (Excellence AI Standard)
- Environment-based configuration (no hardcoded secrets)

Type Safety:
- Explicit type annotations (no 'any' types)
- Pydantic settings validation

Usage:
    from orchestrator.core.database import get_db, engine, Base

    # Dependency injection in FastAPI
    @app.get("/items")
    def list_items(db: Session = Depends(get_db)):
        return db.query(Item).all()

    # Create all tables
    Base.metadata.create_all(bind=engine)
"""

import logging
from typing import Generator
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """
    Database configuration settings with validation.

    Attributes:
        database_url: SQLAlchemy connection URL
        echo_sql: Whether to log all SQL statements
        pool_size: Connection pool size (PostgreSQL only)
        max_overflow: Max overflow connections (PostgreSQL only)
        pool_timeout: Pool timeout in seconds (PostgreSQL only)

    Environment Variables:
        DB_DATABASE_URL: Override database URL
        DB_ECHO_SQL: Enable SQL logging (default: False)
        DB_POOL_SIZE: Connection pool size (default: 5)
        DB_MAX_OVERFLOW: Max overflow (default: 10)
        DB_POOL_TIMEOUT: Pool timeout seconds (default: 30)

    Example:
        # Development (SQLite)
        DB_DATABASE_URL=sqlite:///./parallel_ai.db

        # Production (PostgreSQL)
        DB_DATABASE_URL=postgresql://user:pass@localhost:5432/parallel_ai
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DB_",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env file
    )

    database_url: str = "sqlite:///./parallel_ai.db"
    echo_sql: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30


def _enable_sqlite_foreign_keys(
    dbapi_connection: object,
    connection_record: object
) -> None:
    """
    Enable foreign key constraints for SQLite connections.

    SQLite requires explicit PRAGMA to enforce foreign keys.
    This event listener ensures constraints are enabled.

    Args:
        dbapi_connection: Database API connection
        connection_record: Connection record (unused)
    """
    cursor = dbapi_connection.cursor()  # type: ignore
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_db_engine(settings: DatabaseSettings) -> Engine:
    """
    Create SQLAlchemy engine with appropriate configuration.

    Handles both PostgreSQL and SQLite with optimal settings.

    Args:
        settings: Database configuration settings

    Returns:
        Configured SQLAlchemy engine

    Raises:
        ValueError: If database URL is invalid
    """
    is_sqlite = settings.database_url.startswith("sqlite")

    if is_sqlite:
        # SQLite: Use StaticPool for in-memory, NullPool for file-based
        connect_args = {"check_same_thread": False}
        engine_kwargs = {
            "connect_args": connect_args,
            "poolclass": StaticPool if ":memory:" in settings.database_url else None,
        }
    else:
        # PostgreSQL: Use connection pooling
        engine_kwargs = {
            "pool_size": settings.pool_size,
            "max_overflow": settings.max_overflow,
            "pool_timeout": settings.pool_timeout,
            "pool_pre_ping": True,  # Verify connections before use
        }

    engine = create_engine(
        settings.database_url,
        echo=settings.echo_sql,
        **engine_kwargs  # type: ignore
    )

    # Enable foreign keys for SQLite
    if is_sqlite:
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)

    logger.info(
        f"Database engine created: {_mask_password(settings.database_url)}"
    )

    return engine


def _mask_password(url: str) -> str:
    """
    Mask password in database URL for safe logging.

    Security: Prevents password leaks in logs (Excellence AI Standard).

    Args:
        url: Database connection URL

    Returns:
        URL with password masked as '***'

    Example:
        >>> _mask_password("postgresql://user:secret@localhost/db")
        'postgresql://user:***@localhost/db'
    """
    if "@" not in url or "://" not in url:
        return url

    protocol, rest = url.split("://", 1)
    if "@" not in rest:
        return url

    credentials, host_part = rest.split("@", 1)
    if ":" in credentials:
        username, _ = credentials.split(":", 1)
        return f"{protocol}://{username}:***@{host_part}"

    return url


# Global configuration
settings = DatabaseSettings()

# SQLAlchemy engine
engine = create_db_engine(settings)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Provides a database session that is automatically closed
    after the request completes.

    Yields:
        SQLAlchemy session

    Example:
        @app.get("/items")
        def list_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.

    Creates all tables defined by SQLAlchemy models that inherit
    from Base. Safe to call multiple times (idempotent).

    Example:
        from orchestrator.core.database import init_db
        from orchestrator.core.models import Worker, Job

        init_db()  # Creates workers, jobs tables
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_all_tables() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data. Use only for testing
    or development environments.

    Example:
        # In test setup
        drop_all_tables()
        init_db()
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")
