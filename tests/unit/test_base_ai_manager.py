"""Unit tests for BaseAIManager abstract base class.

Tests ABC structure, initialization, and abstract method enforcement.
"""

from abc import ABC
from typing import Any, Dict, Optional

import pytest

from orchestrator.core.base_ai_manager import BaseAIManager

# ======================= Concrete Implementation for Testing =======================


class ConcreteAIManager(BaseAIManager):
    """Concrete implementation of BaseAIManager for testing."""

    def __init__(self, name: str):
        super().__init__(name)
        self._configured = False
        self._started = False

    def configure(self, config: Dict[str, Any]) -> None:
        """Apply configuration."""
        self._configured = True
        self._config = config

    async def start(self) -> None:
        """Start manager operations."""
        self._started = True

    async def stop(self) -> None:
        """Stop manager operations."""
        self._started = False

    def status(self) -> Dict[str, Optional[str]]:
        """Return status snapshot."""
        return {
            "name": self._name,
            "configured": str(self._configured),
            "started": str(self._started),
        }


# ======================= BaseAIManager Tests =======================


class TestBaseAIManager:
    """Test BaseAIManager abstract base class."""

    def test_is_abstract_base_class(self):
        """Test that BaseAIManager is an ABC."""
        assert issubclass(BaseAIManager, ABC)

    def test_cannot_instantiate_directly(self):
        """Test that BaseAIManager cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseAIManager("test")

    def test_concrete_implementation_instantiation(self):
        """Test that concrete implementation can be instantiated."""
        manager = ConcreteAIManager("test_manager")
        assert manager is not None
        assert isinstance(manager, BaseAIManager)

    def test_name_property(self):
        """Test name property returns correct value."""
        manager = ConcreteAIManager("my_manager")
        assert manager.name == "my_manager"

    def test_name_stored_as_private_attribute(self):
        """Test that name is stored as _name attribute."""
        manager = ConcreteAIManager("test")
        assert hasattr(manager, "_name")
        assert manager._name == "test"

    def test_configure_method_required(self):
        """Test that configure method must be implemented."""
        with pytest.raises(TypeError):

            class IncompleteManager1(BaseAIManager):
                async def start(self) -> None:
                    pass

                async def stop(self) -> None:
                    pass

                def status(self) -> Dict[str, Optional[str]]:
                    return {}

            IncompleteManager1("test")

    def test_start_method_required(self):
        """Test that start method must be implemented."""
        with pytest.raises(TypeError):

            class IncompleteManager2(BaseAIManager):
                def configure(self, config: Dict[str, Any]) -> None:
                    pass

                async def stop(self) -> None:
                    pass

                def status(self) -> Dict[str, Optional[str]]:
                    return {}

            IncompleteManager2("test")

    def test_stop_method_required(self):
        """Test that stop method must be implemented."""
        with pytest.raises(TypeError):

            class IncompleteManager3(BaseAIManager):
                def configure(self, config: Dict[str, Any]) -> None:
                    pass

                async def start(self) -> None:
                    pass

                def status(self) -> Dict[str, Optional[str]]:
                    return {}

            IncompleteManager3("test")

    def test_status_method_required(self):
        """Test that status method must be implemented."""
        with pytest.raises(TypeError):

            class IncompleteManager4(BaseAIManager):
                def configure(self, config: Dict[str, Any]) -> None:
                    pass

                async def start(self) -> None:
                    pass

                async def stop(self) -> None:
                    pass

            IncompleteManager4("test")

    def test_configure_method_works(self):
        """Test that configure method can be called."""
        manager = ConcreteAIManager("test")
        config = {"key": "value"}
        manager.configure(config)
        assert manager._configured is True
        assert manager._config == config

    @pytest.mark.asyncio
    async def test_start_method_works(self):
        """Test that start method can be called."""
        manager = ConcreteAIManager("test")
        await manager.start()
        assert manager._started is True

    @pytest.mark.asyncio
    async def test_stop_method_works(self):
        """Test that stop method can be called."""
        manager = ConcreteAIManager("test")
        await manager.start()
        await manager.stop()
        assert manager._started is False

    def test_status_method_works(self):
        """Test that status method returns expected format."""
        manager = ConcreteAIManager("status_test")
        status = manager.status()

        assert isinstance(status, dict)
        assert status["name"] == "status_test"
        assert "configured" in status
        assert "started" in status

    def test_full_lifecycle(self):
        """Test complete manager lifecycle."""
        manager = ConcreteAIManager("lifecycle_test")

        # Initial state
        assert manager.name == "lifecycle_test"
        status = manager.status()
        assert status["configured"] == "False"
        assert status["started"] == "False"

        # Configure
        manager.configure({"setting": "value"})
        assert manager.status()["configured"] == "True"

    @pytest.mark.asyncio
    async def test_async_lifecycle(self):
        """Test async start / stop lifecycle."""
        manager = ConcreteAIManager("async_test")

        # Start
        await manager.start()
        assert manager.status()["started"] == "True"

        # Stop
        await manager.stop()
        assert manager.status()["started"] == "False"
