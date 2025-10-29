from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect

from scripts import init_database as initdb


def test_init_database_development_creates_schema(tmp_path: Path) -> None:
    # Ensure no leftover DB file
    db_file = Path("orchestrator.db")
    if db_file.exists():
        db_file.unlink()

    # Run initialization
    rc = initdb.main(["--env", "development"])
    assert rc == 0
    assert db_file.exists()

    # Verify schema
    engine = create_engine(f"sqlite:///{db_file}")
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    assert {"workers", "jobs", "resource_allocations", "idempotency_keys"}.issubset(tables)

    # Cleanup
    db_file.unlink()
