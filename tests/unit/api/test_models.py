"""Unit tests for API configuration models.

Tests Pydantic model validation, defaults, and constraints for orchestrator configuration.
"""

import pytest
from pydantic import ValidationError

from orchestrator.api.models import OrchestratorConfig, OrchestratorConfigRecursion

# ======================= OrchestratorConfigRecursion Tests =======================


class TestOrchestratorConfigRecursionDefaults:
    """Test default values for OrchestratorConfigRecursion."""

    def test_default_values(self):
        """Test that defaults are properly set."""
        config = OrchestratorConfigRecursion()

        assert config.max_recursion_depth == 3
        assert config.current_depth == 0
        assert config.orchestrator_api_url is None
        assert config.orchestrator_api_key is None
        assert config.workers_by_depth == {
            0: 10,
            1: 8,
            2: 5,
            3: 3,
            4: 2,
            5: 1,
        }

    def test_workers_by_depth_default_factory(self):
        """Test that workers_by_depth creates separate instances."""
        config1 = OrchestratorConfigRecursion()
        config2 = OrchestratorConfigRecursion()

        # Modify one instance
        config1.workers_by_depth[0] = 20

        # Verify the other instance is unaffected
        assert config2.workers_by_depth[0] == 10


class TestOrchestratorConfigRecursionValidation:
    """Test validation rules for OrchestratorConfigRecursion."""

    def test_max_recursion_depth_minimum(self):
        """Test max_recursion_depth minimum constraint (ge=0)."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            OrchestratorConfigRecursion(max_recursion_depth=-1)

    def test_max_recursion_depth_maximum(self):
        """Test max_recursion_depth maximum constraint (le=5)."""
        with pytest.raises(ValidationError, match="less than or equal to 5"):
            OrchestratorConfigRecursion(max_recursion_depth=6)

    def test_max_recursion_depth_valid_range(self):
        """Test valid max_recursion_depth values."""
        for depth in range(0, 6):  # 0 - 5 inclusive
            config = OrchestratorConfigRecursion(max_recursion_depth=depth)
            assert config.max_recursion_depth == depth

    def test_current_depth_minimum(self):
        """Test current_depth minimum constraint (ge=0)."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            OrchestratorConfigRecursion(current_depth=-1)

    def test_current_depth_maximum(self):
        """Test current_depth maximum constraint (le=5)."""
        with pytest.raises(ValidationError, match="less than or equal to 5"):
            OrchestratorConfigRecursion(current_depth=6)

    def test_current_depth_exceeds_max_depth(self):
        """Test custom validator: current_depth cannot exceed max_recursion_depth."""
        with pytest.raises(
            ValidationError, match="Current depth \\(4\\) exceeds max depth \\(3\\)"
        ):
            OrchestratorConfigRecursion(
                max_recursion_depth=3,
                current_depth=4,
            )

    def test_current_depth_equals_max_depth_valid(self):
        """Test that current_depth can equal max_recursion_depth."""
        config = OrchestratorConfigRecursion(
            max_recursion_depth=3,
            current_depth=3,
        )
        assert config.current_depth == 3

    def test_orchestrator_api_url_http_valid(self):
        """Test that http:// URLs are valid."""
        config = OrchestratorConfigRecursion(orchestrator_api_url="http://localhost:8000")
        assert config.orchestrator_api_url == "http://localhost:8000"

    def test_orchestrator_api_url_https_valid(self):
        """Test that https:// URLs are valid."""
        config = OrchestratorConfigRecursion(
            orchestrator_api_url="https://orchestrator.example.com"
        )
        assert config.orchestrator_api_url == "https://orchestrator.example.com"

    def test_orchestrator_api_url_invalid_scheme(self):
        """Test that URLs without http / https scheme are rejected."""
        with pytest.raises(ValidationError, match="API URL must start with http:// or https://"):
            OrchestratorConfigRecursion(orchestrator_api_url="ftp://example.com")

    def test_orchestrator_api_url_no_scheme(self):
        """Test that URLs without scheme are rejected."""
        with pytest.raises(ValidationError, match="API URL must start with http:// or https://"):
            OrchestratorConfigRecursion(orchestrator_api_url="example.com")

    def test_orchestrator_api_url_none_valid(self):
        """Test that None is valid for orchestrator_api_url."""
        config = OrchestratorConfigRecursion(orchestrator_api_url=None)
        assert config.orchestrator_api_url is None

    def test_orchestrator_api_key_optional(self):
        """Test that orchestrator_api_key is optional."""
        config1 = OrchestratorConfigRecursion()
        assert config1.orchestrator_api_key is None

        config2 = OrchestratorConfigRecursion(orchestrator_api_key="secret - key - 123")
        assert config2.orchestrator_api_key == "secret - key - 123"


class TestOrchestratorConfigRecursionCustomization:
    """Test customizing OrchestratorConfigRecursion fields."""

    def test_custom_max_recursion_depth(self):
        """Test setting custom max_recursion_depth."""
        config = OrchestratorConfigRecursion(max_recursion_depth=2)
        assert config.max_recursion_depth == 2

    def test_custom_current_depth(self):
        """Test setting custom current_depth."""
        config = OrchestratorConfigRecursion(
            max_recursion_depth=3,
            current_depth=2,
        )
        assert config.current_depth == 2

    def test_custom_workers_by_depth(self):
        """Test setting custom workers_by_depth."""
        custom_workers = {0: 5, 1: 3, 2: 1}
        config = OrchestratorConfigRecursion(workers_by_depth=custom_workers)
        assert config.workers_by_depth == custom_workers

    def test_partial_workers_by_depth_override(self):
        """Test partial override of workers_by_depth."""
        # Start with defaults, then modify
        config = OrchestratorConfigRecursion()
        config.workers_by_depth[0] = 15
        config.workers_by_depth[1] = 12

        assert config.workers_by_depth[0] == 15
        assert config.workers_by_depth[1] == 12
        assert config.workers_by_depth[2] == 5  # Default unchanged

    def test_full_configuration_with_recursion(self):
        """Test complete configuration for recursive orchestration."""
        config = OrchestratorConfigRecursion(
            max_recursion_depth=4,
            current_depth=2,
            orchestrator_api_url="https://parent.orchestrator.com / api",
            orchestrator_api_key="parent - api - key - xyz",
            workers_by_depth={0: 12, 1: 10, 2: 6, 3: 4, 4: 2},
        )

        assert config.max_recursion_depth == 4
        assert config.current_depth == 2
        assert config.orchestrator_api_url == "https://parent.orchestrator.com / api"
        assert config.orchestrator_api_key == "parent - api - key - xyz"
        assert config.workers_by_depth[2] == 6


class TestOrchestratorConfigRecursionEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_max_recursion_depth(self):
        """Test max_recursion_depth=0 (no recursion allowed)."""
        config = OrchestratorConfigRecursion(
            max_recursion_depth=0,
            current_depth=0,
        )
        assert config.max_recursion_depth == 0
        assert config.current_depth == 0

    def test_max_recursion_depth_five(self):
        """Test max_recursion_depth=5 (maximum allowed)."""
        config = OrchestratorConfigRecursion(
            max_recursion_depth=5,
            current_depth=5,
        )
        assert config.max_recursion_depth == 5
        assert config.current_depth == 5

    def test_empty_workers_by_depth(self):
        """Test with empty workers_by_depth dict."""
        config = OrchestratorConfigRecursion(workers_by_depth={})
        assert config.workers_by_depth == {}

    def test_url_with_port(self):
        """Test orchestrator_api_url with port number."""
        config = OrchestratorConfigRecursion(
            orchestrator_api_url="http://localhost:8080 / api / v1"
        )
        assert config.orchestrator_api_url == "http://localhost:8080 / api / v1"

    def test_url_with_path(self):
        """Test orchestrator_api_url with path."""
        config = OrchestratorConfigRecursion(
            orchestrator_api_url="https://example.com / orchestrator / api"
        )
        assert config.orchestrator_api_url == "https://example.com / orchestrator / api"


# ======================= OrchestratorConfig Tests =======================


class TestOrchestratorConfig:
    """Test top - level OrchestratorConfig model."""

    def test_default_recursion_config(self):
        """Test that default recursion config is created."""
        config = OrchestratorConfig()

        assert config.recursion is not None
        assert isinstance(config.recursion, OrchestratorConfigRecursion)
        assert config.recursion.max_recursion_depth == 3
        assert config.recursion.current_depth == 0

    def test_custom_recursion_config(self):
        """Test providing custom recursion config."""
        recursion_cfg = OrchestratorConfigRecursion(
            max_recursion_depth=2,
            current_depth=1,
        )
        config = OrchestratorConfig(recursion=recursion_cfg)

        assert config.recursion.max_recursion_depth == 2
        assert config.recursion.current_depth == 1

    def test_recursion_config_dict_input(self):
        """Test providing recursion config as dict."""
        config = OrchestratorConfig(
            recursion={
                "max_recursion_depth": 4,
                "current_depth": 2,
                "orchestrator_api_url": "https://example.com",
            }
        )

        assert config.recursion.max_recursion_depth == 4
        assert config.recursion.current_depth == 2
        assert config.recursion.orchestrator_api_url == "https://example.com"

    def test_recursion_validation_through_top_level(self):
        """Test that recursion validation works through top - level config."""
        with pytest.raises(ValidationError, match="Current depth .* exceeds max depth"):
            OrchestratorConfig(
                recursion={
                    "max_recursion_depth": 2,
                    "current_depth": 3,
                }
            )

    def test_multiple_configs_independent(self):
        """Test that multiple OrchestratorConfig instances are independent."""
        config1 = OrchestratorConfig()
        config2 = OrchestratorConfig()

        config1.recursion.max_recursion_depth = 5
        assert config2.recursion.max_recursion_depth == 3  # Default unchanged


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_recursion_config_to_dict(self):
        """Test converting OrchestratorConfigRecursion to dict."""
        config = OrchestratorConfigRecursion(
            max_recursion_depth=4,
            current_depth=2,
        )
        config_dict = config.dict()

        assert config_dict["max_recursion_depth"] == 4
        assert config_dict["current_depth"] == 2
        assert isinstance(config_dict["workers_by_depth"], dict)

    def test_orchestrator_config_to_dict(self):
        """Test converting OrchestratorConfig to dict."""
        config = OrchestratorConfig()
        config_dict = config.dict()

        assert "recursion" in config_dict
        assert config_dict["recursion"]["max_recursion_depth"] == 3

    def test_recursion_config_from_json(self):
        """Test parsing OrchestratorConfigRecursion from JSON."""
        json_str = '{"max_recursion_depth": 2, "current_depth": 1}'
        config = OrchestratorConfigRecursion.parse_raw(json_str)

        assert config.max_recursion_depth == 2
        assert config.current_depth == 1

    def test_orchestrator_config_json_round_trip(self):
        """Test JSON serialization round trip."""
        config1 = OrchestratorConfig(
            recursion=OrchestratorConfigRecursion(
                max_recursion_depth=4,
                orchestrator_api_url="https://example.com",
            )
        )

        # Serialize to JSON
        json_str = config1.json()

        # Deserialize back
        config2 = OrchestratorConfig.parse_raw(json_str)

        assert config2.recursion.max_recursion_depth == 4
        assert config2.recursion.orchestrator_api_url == "https://example.com"
