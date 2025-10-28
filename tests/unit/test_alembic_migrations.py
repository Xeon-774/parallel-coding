from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = ROOT / "alembic.ini"


def _temp_db_url(tmp_path: Path) -> str:
    return f"sqlite:///{tmp_path}/test.db"


def test_upgrade_and_downgrade_cycle(tmp_path: Path) -> None:
    assert ALEMBIC_INI.is_file(), "alembic.ini must exist at project root"
    db_url = _temp_db_url(tmp_path)

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_url)

    # Upgrade to head
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert {"workers", "jobs", "resource_allocations", "idempotency_keys"}.issubset(tables)

    # Downgrade to base
    command.downgrade(cfg, "base")

    insp = inspect(engine)
    tables_after = set(insp.get_table_names())
    assert "workers" not in tables_after
    assert "jobs" not in tables_after
    assert "resource_allocations" not in tables_after
    assert "idempotency_keys" not in tables_after


def test_reupgrade_idempotent(tmp_path: Path) -> None:
    db_url = _temp_db_url(tmp_path)
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_url)

    # Upgrade twice should not fail
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert {"workers", "jobs", "resource_allocations", "idempotency_keys"}.issubset(tables)
