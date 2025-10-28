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
            "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELED", name="jobstatus", create_type=False
        )
        job_status.create(op.get_bind(), checkfirst=True)

    # Create workers table
    op.create_table(
        "workers",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("IDLE", "RUNNING", "PAUSED", "COMPLETED", "FAILED", "TERMINATED", name="workerstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workers_workspace_id", "workers", ["workspace_id"], unique=False)
    op.create_index("ix_workers_status", "workers", ["status"], unique=False)
    op.create_index("ix_workers_workspace_status", "workers", ["workspace_id", "status"], unique=False)
    op.create_index("ix_workers_created_at", "workers", ["created_at"], unique=False)

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("parent_job_id", sa.String(36), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "SUBMITTED", "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELED", name="jobstatus"
            ),
            nullable=False,
        ),
        sa.Column("worker_count", sa.Integer(), nullable=False),
        sa.Column("task_description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.CheckConstraint("depth >= 0 AND depth <= 5"),
        sa.CheckConstraint("worker_count >= 1"),
    )
    op.create_index("ix_jobs_parent_job_id", "jobs", ["parent_job_id"], unique=False)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)
    op.create_index("ix_jobs_depth", "jobs", ["depth"], unique=False)

    # Create resource_allocations table
    op.create_table(
        "resource_allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("worker_count", sa.Integer(), nullable=False),
        sa.Column("allocated_at", sa.DateTime(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.CheckConstraint("depth >= 0 AND depth <= 5"),
        sa.CheckConstraint("worker_count >= 1"),
    )
    op.create_index("ix_resource_allocations_job_id", "resource_allocations", ["job_id"], unique=False)

    # Create idempotency_keys table
    op.create_table(
        "idempotency_keys",
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index("ix_idempotency_keys_expires_at", "idempotency_keys", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_idempotency_keys_expires_at", table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
    op.drop_index("ix_resource_allocations_job_id", table_name="resource_allocations")
    op.drop_table("resource_allocations")
    op.drop_index("ix_jobs_depth", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_parent_job_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_workers_created_at", table_name="workers")
    op.drop_index("ix_workers_workspace_status", table_name="workers")
    op.drop_index("ix_workers_status", table_name="workers")
    op.drop_index("ix_workers_workspace_id", table_name="workers")
    op.drop_table("workers")

    # Drop enum types for PostgreSQL
    if _is_postgresql():
        sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
        sa.Enum(name="workerstatus").drop(op.get_bind(), checkfirst=True)

