# Task E: Alembic Database Migration Setup

**Task ID**: Task E
**Module**: Database Migration
**Target**: Production-ready database versioning
**Estimated Time**: 2h
**Worker Type**: Codex Worker (use `--use-codex` flag)

---

## 🎯 Mission

Setup Alembic for database migration management, create initial migration for Week 2 MVP database schema, and ensure production-ready database versioning.

---

## 📋 Prerequisites (Already Complete)

✅ Database models: `orchestrator/core/db_models.py` (698 lines)
  - Worker, Job, ResourceAllocation, IdempotencyKey models
  - State enums, relationships, indexes, constraints
✅ Database config: `orchestrator/core/database.py` (283 lines)
  - SQLAlchemy engine + session management
  - PostgreSQL/SQLite support

---

## 📁 Files to Create

```
alembic/
├── env.py                          ← Create: Alembic environment config
├── script.py.mako                  ← Create: Migration template
├── versions/                       ← Directory for migrations
│   └── 001_initial_schema.py       ← Create: Initial migration
└── README                          ← Create: Migration usage guide

orchestrator/
└── alembic.ini                     ← Create: Alembic configuration

scripts/
└── init_database.py                ← Create: Database initialization script
```

---

## 🔨 Implementation Tasks

### Task E.1: Alembic Initialization (0.5h)

**File**: `alembic.ini`

**Requirements**:
- Configure Alembic for SQLAlchemy integration
- Support both PostgreSQL (production) and SQLite (development)
- Configure logging and script location

**Pattern**:
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# Database URL (override with environment variable)
sqlalchemy.url = postgresql://user:pass@localhost/orchestrator

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**File**: `alembic/env.py`

**Requirements**:
- Import all models from db_models.py
- Configure target metadata for autogenerate
- Support offline and online migration modes
- Handle environment-specific database URLs

**Pattern**:
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add parent directory to path to import orchestrator modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrator.core.database import Base
from orchestrator.core.db_models import (
    Worker, Job, ResourceAllocation, IdempotencyKey
)

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata

def get_url():
    """Get database URL from environment or config"""
    return os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode"""
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
    """Run migrations in 'online' mode"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Success Criteria**:
- [ ] `alembic.ini` configured with PostgreSQL + SQLite support
- [ ] `alembic/env.py` imports all models
- [ ] `alembic init` command completes successfully
- [ ] NO hardcoded credentials (use environment variables)

---

### Task E.2: Initial Migration Creation (1h)

**Command**:
```bash
alembic revision --autogenerate -m "Initial schema - Week 2 MVP"
```

**File**: `alembic/versions/001_initial_schema.py` (auto-generated, may need review)

**Requirements**:
- Create all tables (workers, jobs, resource_allocations, idempotency_keys)
- Create all indexes (worker_id_idx, job_id_idx, etc.)
- Create all constraints (foreign keys, unique constraints, check constraints)
- Create all enums (WorkerStatus, JobStatus, WorkerType)

**Expected Migration Content** (review and validate):
```python
"""Initial schema - Week 2 MVP

Revision ID: 001
Revises:
Create Date: 2025-10-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum types
    worker_status = postgresql.ENUM(
        'IDLE', 'BUSY', 'FAILED', 'TERMINATED',
        name='workerstatus',
        create_type=False
    )
    worker_status.create(op.get_bind(), checkfirst=True)

    job_status = postgresql.ENUM(
        'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED',
        name='jobstatus',
        create_type=False
    )
    job_status.create(op.get_bind(), checkfirst=True)

    # Create workers table
    op.create_table(
        'workers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('IDLE', 'BUSY', 'FAILED', 'TERMINATED', name='workerstatus'), nullable=False),
        sa.Column('current_job_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('worker_id')
    )
    op.create_index('ix_workers_worker_id', 'workers', ['worker_id'], unique=True)
    op.create_index('ix_workers_status', 'workers', ['status'], unique=False)

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='jobstatus'), nullable=False),
        sa.Column('task_description', sa.Text(), nullable=False),
        sa.Column('assigned_worker_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id'),
        sa.ForeignKeyConstraint(['assigned_worker_id'], ['workers.worker_id'], ondelete='SET NULL')
    )
    op.create_index('ix_jobs_job_id', 'jobs', ['job_id'], unique=True)
    op.create_index('ix_jobs_status', 'jobs', ['status'], unique=False)

    # Create resource_allocations table
    op.create_table(
        'resource_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(100), nullable=False),
        sa.Column('worker_id', sa.String(100), nullable=False),
        sa.Column('allocated_at', sa.DateTime(), nullable=False),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.worker_id'], ondelete='CASCADE')
    )

    # Create idempotency_keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('ix_idempotency_keys_key', 'idempotency_keys', ['key'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_idempotency_keys_key', table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
    op.drop_table('resource_allocations')
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_job_id', table_name='jobs')
    op.drop_table('jobs')
    op.drop_index('ix_workers_status', table_name='workers')
    op.drop_index('ix_workers_worker_id', table_name='workers')
    op.drop_table('workers')

    # Drop enum types
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='workerstatus').drop(op.get_bind(), checkfirst=True)
```

**Validation Steps**:
1. Review auto-generated migration
2. Verify all tables created
3. Verify all indexes created
4. Verify all constraints created
5. Test upgrade + downgrade

**Success Criteria**:
- [ ] Initial migration created successfully
- [ ] All 4 tables defined (workers, jobs, resource_allocations, idempotency_keys)
- [ ] All indexes created (6 indexes total)
- [ ] All foreign keys configured with proper cascades
- [ ] `alembic upgrade head` succeeds
- [ ] `alembic downgrade base` succeeds

---

### Task E.3: Database Initialization Script (0.5h)

**File**: `scripts/init_database.py`

**Requirements**:
- Initialize database with Alembic migrations
- Create initial admin user (for testing)
- Seed development data (optional)
- Validate database schema

**Pattern**:
```python
"""
Database initialization script for Week 2 MVP

Usage:
    python scripts/init_database.py [--env production|development]
"""
import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect
from alembic import command
from alembic.config import Config
from orchestrator.core.database import Base, get_engine
from orchestrator.core.db_models import Worker, Job, WorkerStatus, JobStatus
from orchestrator.core.auth import hash_password

def init_database(env: str = "development"):
    """
    Initialize database with Alembic migrations

    Args:
        env: Environment (production or development)
    """
    print(f"Initializing database for {env} environment...")

    # 1. Get database URL
    if env == "production":
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable not set")
    else:
        db_url = "sqlite:///./orchestrator.db"

    print(f"Database URL: {db_url}")

    # 2. Run Alembic migrations
    print("Running Alembic migrations...")
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")
    print("✅ Migrations complete")

    # 3. Validate schema
    print("Validating database schema...")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    expected_tables = ['workers', 'jobs', 'resource_allocations', 'idempotency_keys']

    for table in expected_tables:
        if table not in tables:
            raise ValueError(f"Missing table: {table}")

    print(f"✅ All tables created: {', '.join(tables)}")

    # 4. Seed development data (optional)
    if env == "development":
        print("Seeding development data...")
        from orchestrator.core.database import SessionLocal
        session = SessionLocal()

        # Create test worker
        test_worker = Worker(
            worker_id="test-worker-1",
            status=WorkerStatus.IDLE
        )
        session.add(test_worker)

        # Create test job
        test_job = Job(
            job_id="test-job-1",
            status=JobStatus.PENDING,
            task_description="Test task for development"
        )
        session.add(test_job)

        session.commit()
        session.close()
        print("✅ Development data seeded")

    print("🎉 Database initialization complete!")

def main():
    parser = argparse.ArgumentParser(description="Initialize database with Alembic migrations")
    parser.add_argument(
        "--env",
        choices=["production", "development"],
        default="development",
        help="Environment (default: development)"
    )
    args = parser.parse_args()

    try:
        init_database(args.env)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Success Criteria**:
- [ ] Script initializes database successfully
- [ ] All migrations applied
- [ ] Schema validated
- [ ] Development data seeded (if development env)
- [ ] Error handling for missing DATABASE_URL

---

## ✅ Success Criteria (Overall)

- [ ] **Alembic configured** with PostgreSQL + SQLite support
- [ ] **Initial migration created** (001_initial_schema.py)
- [ ] **Migration tested**:
  - `alembic upgrade head` succeeds
  - `alembic downgrade base` succeeds
  - `alembic upgrade head` (again) succeeds
- [ ] **Database initialization script** (scripts/init_database.py)
- [ ] **Documentation** (alembic/README)
- [ ] **Excellence AI Standard 100%** compliance
  - Security: NO hardcoded credentials
  - Type Safety: Full type annotations in scripts
  - Documentation: Comprehensive docstrings
  - Code Quality: All functions ≤50 lines
  - NO TODO/FIXME/HACK
- [ ] **Production Ready**: Database versioning functional

---

## 📚 References

**Database Models**:
- [db_models.py:1-698](../../dev-tools/parallel-coding/orchestrator/core/db_models.py) - SQLAlchemy models

**Database Configuration**:
- [database.py:1-283](../../dev-tools/parallel-coding/orchestrator/core/database.py) - Database session management

**Alembic Documentation**:
- https://alembic.sqlalchemy.org/en/latest/tutorial.html - Official tutorial
- https://alembic.sqlalchemy.org/en/latest/autogenerate.html - Autogenerate reference

**Standards**:
- [Excellence AI Standard](../../dev-tools/excellence-ai-standard/.claude_code_config.md) - World-class quality requirements

---

## 🔧 Testing Commands

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema - Week 2 MVP"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade base

# Check current migration
alembic current

# Show migration history
alembic history

# Initialize database (development)
python scripts/init_database.py --env development

# Initialize database (production)
DATABASE_URL=postgresql://user:pass@localhost/db python scripts/init_database.py --env production
```

---

**Generated with**: Excellence AI Standard 100% | Token Efficiency v6.0 | Codex-Driven Development
