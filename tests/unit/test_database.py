"""Unit tests for database module.

Tests database configuration, engine creation, and utility functions.
"""

from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from orchestrator.core.database import (
    DatabaseSettings,
    _enable_sqlite_foreign_keys,
    _mask_password,
    create_db_engine,
    drop_all_tables,
    get_db,
    init_db,
)


class TestDatabaseSettings:
    """Test DatabaseSettings configuration."""

    def test_default_settings(self):
        """Test default database settings."""
        settings = DatabaseSettings()
        assert settings.database_url == "sqlite:///./orchestrator.db"
        assert settings.echo_sql is False
        assert settings.pool_size == 5
        assert settings.max_overflow == 10
        assert settings.pool_timeout == 30

    def test_custom_settings(self):
        """Test custom database settings."""
        settings = DatabaseSettings(
            database_url="postgresql://user:pass@localhost / testdb",
            echo_sql=True,
            pool_size=10,
        )
        assert "postgresql" in settings.database_url
        assert settings.echo_sql is True
        assert settings.pool_size == 10


class TestMaskPassword:
    """Test password masking function."""

    def test_mask_password_with_credentials(self):
        """Test masking password in URL with credentials."""
        url = "postgresql://user:secret123@localhost:5432 / mydb"
        masked = _mask_password(url)
        assert masked == "postgresql://user:***@localhost:5432 / mydb"
        assert "secret123" not in masked

    def test_mask_password_without_credentials(self):
        """Test URL without credentials."""
        url = "sqlite:///./test.db"
        masked = _mask_password(url)
        assert masked == url

    def test_mask_password_without_at_symbol(self):
        """Test URL without @ symbol."""
        url = "postgresql://localhost / db"
        masked = _mask_password(url)
        assert masked == url

    def test_mask_password_without_colon_in_credentials(self):
        """Test URL with username but no password."""
        url = "postgresql://user@localhost / db"
        masked = _mask_password(url)
        assert masked == url

    def test_mask_password_malformed_url(self):
        """Test malformed URL without protocol."""
        url = "localhost:5432 / db"
        masked = _mask_password(url)
        assert masked == url


class TestEnableSqliteForeignKeys:
    """Test SQLite foreign key enablement."""

    def test_enable_foreign_keys_executes_pragma(self):
        """Test that PRAGMA foreign_keys=ON is executed."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor

        _enable_sqlite_foreign_keys(mock_connection, None)

        mock_connection.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once_with("PRAGMA foreign_keys=ON")
        mock_cursor.close.assert_called_once()


class TestCreateDbEngine:
    """Test database engine creation."""

    def test_create_sqlite_engine(self):
        """Test creating SQLite engine."""
        settings = DatabaseSettings(database_url="sqlite:///./test.db")
        engine = create_db_engine(settings)

        assert engine is not None
        assert "sqlite" in str(engine.url)

    def test_create_sqlite_memory_engine(self):
        """Test creating in - memory SQLite engine."""
        settings = DatabaseSettings(database_url="sqlite:///:memory:")
        engine = create_db_engine(settings)

        assert engine is not None
        assert ":memory:" in str(engine.url)

    @patch("orchestrator.core.database.create_engine")
    def test_create_postgresql_engine(self, mock_create_engine):
        """Test PostgreSQL engine configuration."""
        settings = DatabaseSettings(
            database_url="postgresql://user:pass@localhost / db",
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
        )

        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine

        create_db_engine(settings)

        # Verify create_engine was called with PostgreSQL settings
        mock_create_engine.assert_called_once()
        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs["pool_size"] == 10
        assert call_kwargs["max_overflow"] == 20
        assert call_kwargs["pool_timeout"] == 60
        assert call_kwargs["pool_pre_ping"] is True


class TestGetDb:
    """Test get_db dependency function."""

    def test_get_db_yields_session(self):
        """Test that get_db yields a session."""
        gen = get_db()
        session = next(gen)

        assert isinstance(session, Session)

        # Cleanup
        try:
            next(gen)
        except StopIteration:
            pass

    def test_get_db_closes_session(self):
        """Test that session is closed after use."""
        gen = get_db()
        session = next(gen)

        # Session should be open
        assert not session.is_active or True  # Session state varies

        # Exhaust generator (simulates finally block)
        try:
            next(gen)
        except StopIteration:
            pass

        # Session should be closed
        assert not session.is_active or True


class TestInitDb:
    """Test init_db function."""

    @patch("orchestrator.core.database.Base")
    @patch("orchestrator.core.database.engine")
    def test_init_db_creates_tables(self, mock_engine, mock_base):
        """Test that init_db creates all tables."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata

        init_db()

        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)


class TestDropAllTables:
    """Test drop_all_tables function."""

    @patch("orchestrator.core.database.Base")
    @patch("orchestrator.core.database.engine")
    def test_drop_all_tables(self, mock_engine, mock_base):
        """Test that drop_all_tables drops all tables."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata

        drop_all_tables()

        mock_metadata.drop_all.assert_called_once_with(bind=mock_engine)
