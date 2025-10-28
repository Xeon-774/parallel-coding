"""Initial schema - Week 2 MVP

Revision ID: 001
Revises:
Create Date: 2025-10-28

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from typing import Optional

# For PostgreSQL ENUM creation when using a PostgreSQL connection
try:
    from sqlalchemy.dialects import postgresql
except Exception:  # pragma: no cover - fallback for environments without dialect
    postgresql = None  # type: ignore


# revision identifiers
revision: str = "001"
down_revision: Optional[str] = None
branch_labels = None
depends_on = None


def _is_postgresql() -> bool:
    bind = op.get_bind()
    return bool(getattr(getattr(bind, "dialect", None), "name", "") == "postgresql")


def upgrade() -> None:
    # Create enum types for PostgreSQL if applicable
    if _is_postgresql() and postgresql is not None:
        worker_status = postgresql.ENUM(
            "IDLE", "BUSY", "FAILED", "TERMINATED", name="workerstatus", create_type=False
        )
        worker_status.create(op.get_bind(), checkfirst=True)

        job_status = postgresql.ENUM(
            "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", name="jobstatus", create_type=False
        )
        job_status.create(op.get_bind(), checkfirst=True)

    # Create workers table
    op.create_table(
        "workers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("IDLE", "BUSY", "FAILED", "TERMINATED", name="workerstatus"),
            nullable=False,
        ),
        sa.Column("current_job_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("worker_id"),
    )
    op.create_index("ix_workers_worker_id", "workers", ["worker_id"], unique=True)
    op.create_index("ix_workers_status", "workers", ["status"], unique=False)

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", name="jobstatus"
            ),
            nullable=False,
        ),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("assigned_worker_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
        sa.ForeignKeyConstraint(["assigned_worker_id"], ["workers.worker_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_jobs_job_id", "jobs", ["job_id"], unique=True)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)

    # Create resource_allocations table
    op.create_table(
        "resource_allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(100), nullable=False),
        sa.Column("worker_id", sa.String(100), nullable=False),
        sa.Column("allocated_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["worker_id"], ["workers.worker_id"], ondelete="CASCADE"),
    )

    # Create idempotency_keys table
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_idempotency_keys_key", "idempotency_keys", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_key", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
    op.drop_table("resource_allocations")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_job_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_workers_status", table_name="workers")
    op.drop_index("ix_workers_worker_id", table_name="workers")
    op.drop_table("workers")

    # Drop enum types for PostgreSQL
    if _is_postgresql():
        sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="workerstatus").drop(op.get_bind(), checkfirst=True)

