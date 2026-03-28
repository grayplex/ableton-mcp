"""Tests for MCP_Server/devices/convert.py: natural-to-normalized conversion.

Validates:
- Log conversion (e.g., Eq8 frequency)
- Linear/linear_db conversion (e.g., Compressor2 threshold)
- Passthrough for params with conversion=None
- Clamping of out-of-range values
- Unknown device/param returns value unchanged
- convert_recipe_to_payload output structure
"""

import math
import sys
import types
from unittest.mock import MagicMock

# Mock the mcp module hierarchy so tool imports work without mcp installed
_mock_mcp = types.ModuleType("mcp")
_mock_fastmcp = types.ModuleType("mcp.server.fastmcp")
_mock_server = types.ModuleType("mcp.server")
_mock_fastmcp.Context = type("Context", (), {})
_mock_mcp.server = _mock_server
_mock_server.fastmcp = _mock_fastmcp
sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", _mock_server)
sys.modules.setdefault("mcp.server.fastmcp", _mock_fastmcp)

if "MCP_Server.server" not in sys.modules:
    _mock_app_server = types.ModuleType("MCP_Server.server")
    _mcp_instance = MagicMock()
    _mcp_instance.tool.return_value = lambda fn: fn
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server

import pytest  # noqa: E402

from MCP_Server.devices.convert import (  # noqa: E402
    convert_recipe_to_payload,
    natural_to_normalized,
)


# ---------------------------------------------------------------------------
# natural_to_normalized
# ---------------------------------------------------------------------------


class TestNaturalToNormalized:
    """Test natural_to_normalized with known CATALOG entries."""

    def test_log_conversion_eq8_frequency(self):
        """Eq8 '1 Frequency A': log(1000/20) / log(22050/20) ~= 0.5596"""
        result = natural_to_normalized("Eq8", "1 Frequency A", 1000)
        expected = math.log(1000 / 20) / math.log(22050 / 20)
        assert isinstance(result, float)
        assert abs(result - expected) < 1e-6

    def test_log_conversion_returns_0_at_min(self):
        """Eq8 '1 Frequency A' at natural_min=20 -> 0.0"""
        result = natural_to_normalized("Eq8", "1 Frequency A", 20)
        assert abs(result - 0.0) < 1e-6

    def test_log_conversion_returns_1_at_max(self):
        """Eq8 '1 Frequency A' at natural_max=22050 -> 1.0"""
        result = natural_to_normalized("Eq8", "1 Frequency A", 22050)
        assert abs(result - 1.0) < 1e-6

    def test_passthrough_no_conversion(self):
        """Compressor2 'Ratio' has conversion=None, value in [0, 1] range."""
        result = natural_to_normalized("Compressor2", "Ratio", 0.6)
        assert result == 0.6

    def test_linear_db_conversion_compressor_threshold(self):
        """Compressor2 'Threshold': linear_db from [-40, 0] dB."""
        # natural_min=-40, natural_max=0  ->  (-18 - (-40)) / (0 - (-40)) = 22/40 = 0.55
        result = natural_to_normalized("Compressor2", "Threshold", -18)
        expected = (-18 - (-40)) / (0 - (-40))
        assert abs(result - expected) < 1e-6

    def test_clamp_below_natural_min(self):
        """Value below natural_min gets clamped before conversion."""
        # Eq8 '1 Frequency A': natural_min=20.  Pass 5 -> clamped to 20 -> result 0.0
        result = natural_to_normalized("Eq8", "1 Frequency A", 5)
        assert abs(result - 0.0) < 1e-6

    def test_clamp_above_natural_max(self):
        """Value above natural_max gets clamped before conversion."""
        # Eq8 '1 Frequency A': natural_max=22050.  Pass 30000 -> clamped to 22050 -> result 1.0
        result = natural_to_normalized("Eq8", "1 Frequency A", 30000)
        assert abs(result - 1.0) < 1e-6

    def test_clamp_no_conversion_to_min_max(self):
        """Param with conversion=None clamps to [param min, param max]."""
        # Compressor2 'Ratio': min=0, max=1. Pass 1.5 -> clamped to 1.0
        result = natural_to_normalized("Compressor2", "Ratio", 1.5)
        assert result == 1.0

    def test_unknown_device_returns_unchanged(self):
        """Unknown device class returns value unchanged."""
        result = natural_to_normalized("FakeDevice", "FakeParam", 42.0)
        assert result == 42.0

    def test_unknown_param_returns_unchanged(self):
        """Unknown param name for known device returns value unchanged."""
        result = natural_to_normalized("Eq8", "Nonexistent Param", 99.0)
        assert result == 99.0

    def test_result_is_float(self):
        """Conversion always returns a float."""
        result = natural_to_normalized("Eq8", "1 Frequency A", 1000)
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# convert_recipe_to_payload
# ---------------------------------------------------------------------------


class TestConvertRecipeToPayload:
    """Test convert_recipe_to_payload output structure."""

    def test_basic_structure(self):
        """Returns list of dicts with class_name and params."""
        recipe = {
            "Eq8": {"1 Frequency A": 1000, "1 Filter On A": 1},
        }
        result = convert_recipe_to_payload(recipe)
        assert isinstance(result, list)
        assert len(result) == 1
        entry = result[0]
        assert entry["class_name"] == "Eq8"
        assert isinstance(entry["params"], dict)
        assert "1 Frequency A" in entry["params"]
        assert "1 Filter On A" in entry["params"]

    def test_values_are_normalized(self):
        """Param values in the payload are normalized, not natural."""
        recipe = {
            "Eq8": {"1 Frequency A": 1000},
        }
        result = convert_recipe_to_payload(recipe)
        norm_val = result[0]["params"]["1 Frequency A"]
        expected = math.log(1000 / 20) / math.log(22050 / 20)
        assert abs(norm_val - expected) < 1e-6

    def test_multiple_devices(self):
        """Multiple device classes produce multiple payload entries."""
        recipe = {
            "Eq8": {"1 Frequency A": 440},
            "Compressor2": {"Threshold": -20},
        }
        result = convert_recipe_to_payload(recipe)
        assert len(result) == 2
        class_names = {e["class_name"] for e in result}
        assert class_names == {"Eq8", "Compressor2"}

    def test_empty_recipe(self):
        """Empty recipe returns empty list."""
        result = convert_recipe_to_payload({})
        assert result == []
