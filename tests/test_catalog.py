"""Tests for device parameter catalog data module and MCP tools.

These tests verify the catalog data structure, role taxonomy, and the
MCP tool wrappers get_device_catalog and get_role_taxonomy.

The mcp package is not available in the test environment, so we mock
the server module and FastMCP decorator before importing the tools.
"""

import json
import sys
import types
from unittest.mock import MagicMock

import pytest

# Mock the mcp module hierarchy so tools/catalog.py can be imported without mcp installed
_mock_mcp = types.ModuleType("mcp")
_mock_fastmcp = types.ModuleType("mcp.server.fastmcp")
_mock_server = types.ModuleType("mcp.server")
_mock_fastmcp.Context = type("Context", (), {})
_mock_mcp.server = _mock_server
_mock_server.fastmcp = _mock_fastmcp
sys.modules.setdefault("mcp", _mock_mcp)
sys.modules.setdefault("mcp.server", _mock_server)
sys.modules.setdefault("mcp.server.fastmcp", _mock_fastmcp)

# Mock MCP_Server.server.mcp so @mcp.tool() is a passthrough decorator
if "MCP_Server.server" not in sys.modules:
    _mock_app_server = types.ModuleType("MCP_Server.server")
    _mcp_instance = MagicMock()
    _mcp_instance.tool.return_value = lambda fn: fn  # @mcp.tool() is identity
    _mock_app_server.mcp = _mcp_instance
    sys.modules["MCP_Server.server"] = _mock_app_server

from MCP_Server.devices.catalog import CATALOG, ROLES  # noqa: E402
from MCP_Server.devices import get_catalog_entry, get_roles  # noqa: E402


# ---------------------------------------------------------------------------
# Catalog data tests
# ---------------------------------------------------------------------------


class TestCatalogData:
    """Tests for the CATALOG dict structure and content."""

    def test_catalog_has_12_devices(self):
        assert len(CATALOG) == 12

    def test_each_device_has_display_name(self):
        for key, entry in CATALOG.items():
            assert "display_name" in entry, f"{key} missing display_name"
            assert isinstance(entry["display_name"], str)
            assert len(entry["display_name"]) > 0, f"{key} display_name is empty"

    def test_each_device_has_parameters(self):
        for key, entry in CATALOG.items():
            assert "parameters" in entry, f"{key} missing parameters"
            assert isinstance(entry["parameters"], list)
            assert len(entry["parameters"]) > 0, f"{key} has empty parameters list"

    def test_parameter_shape(self):
        required_keys = {"name", "index", "min", "max", "is_quantized", "conversion"}
        for device_key, entry in CATALOG.items():
            for param in entry["parameters"]:
                missing = required_keys - set(param.keys())
                assert not missing, f"{device_key} param '{param.get('name')}' missing keys: {missing}"

    def test_conversion_shape(self):
        """conversion is None or dict with type/natural_min/natural_max/unit."""
        for device_key, entry in CATALOG.items():
            for param in entry["parameters"]:
                conv = param["conversion"]
                if conv is None:
                    continue
                assert isinstance(conv, dict), f"{device_key} param '{param['name']}' conversion must be dict or None"
                for key in ("type", "natural_min", "natural_max", "unit"):
                    assert key in conv, f"{device_key} param '{param['name']}' conversion missing '{key}'"

    def test_conversion_type_values(self):
        """conversion type is one of the allowed values."""
        valid_types = {"log", "linear", "linear_db"}
        for device_key, entry in CATALOG.items():
            for param in entry["parameters"]:
                conv = param["conversion"]
                if conv is not None:
                    assert conv["type"] in valid_types, (
                        f"{device_key} param '{param['name']}' has invalid conversion type '{conv['type']}'"
                    )

    def test_device_on_parameter(self):
        """Every device's parameter at index 0 has name 'Device On'."""
        for device_key, entry in CATALOG.items():
            first = entry["parameters"][0]
            assert first["name"] == "Device On", (
                f"{device_key}: first parameter should be 'Device On', got '{first['name']}'"
            )
            assert first["index"] == 0

    def test_catalog_keys_are_class_names(self):
        """Key class names include the expected Ableton class identifiers."""
        assert "Eq8" in CATALOG
        assert "Compressor" in CATALOG
        assert "GlueCompressor" in CATALOG


# ---------------------------------------------------------------------------
# Roles data tests
# ---------------------------------------------------------------------------


class TestRolesData:
    """Tests for the ROLES list."""

    def test_roles_count(self):
        assert len(ROLES) == 9

    def test_roles_contains_kick(self):
        assert "kick" in ROLES

    def test_roles_contains_master(self):
        assert "master" in ROLES

    def test_roles_exact_set(self):
        assert set(ROLES) == {"kick", "bass", "lead", "pad", "chords", "vocal", "atmospheric", "return", "master"}


# ---------------------------------------------------------------------------
# devices package public API tests
# ---------------------------------------------------------------------------


class TestDevicesPackageAPI:
    """Tests for get_catalog_entry() and get_roles() in devices/__init__.py."""

    def test_get_catalog_entry_by_class_name(self):
        entry = get_catalog_entry("Eq8")
        assert entry is not None
        assert entry["display_name"] == "EQ Eight"

    def test_get_catalog_entry_by_display_name(self):
        entry = get_catalog_entry("EQ Eight")
        assert entry is not None
        assert "parameters" in entry

    def test_get_catalog_entry_not_found(self):
        entry = get_catalog_entry("Nonexistent")
        assert entry is None

    def test_get_roles(self):
        roles = get_roles()
        assert isinstance(roles, list)
        assert len(roles) == 9
        assert "kick" in roles


# ---------------------------------------------------------------------------
# MCP tool tests (imported after data module tests to avoid import-order issues)
# ---------------------------------------------------------------------------

from MCP_Server.tools.catalog import get_device_catalog, get_role_taxonomy  # noqa: E402


class TestGetDeviceCatalogTool:
    """Tests for the get_device_catalog MCP tool."""

    def test_lookup_by_display_name(self):
        result = json.loads(get_device_catalog(None, "EQ Eight"))
        assert result["display_name"] == "EQ Eight"
        assert "parameters" in result

    def test_lookup_by_class_name(self):
        result = json.loads(get_device_catalog(None, "Eq8"))
        assert result["display_name"] == "EQ Eight"

    def test_case_insensitive_display_name(self):
        result = json.loads(get_device_catalog(None, "eq eight"))
        assert result["display_name"] == "EQ Eight"

    def test_not_found_returns_error(self):
        result = get_device_catalog(None, "Nonexistent")
        assert "Error:" in result
        assert "not found" in result

    def test_returns_valid_json(self):
        result = get_device_catalog(None, "Compressor")
        data = json.loads(result)
        assert isinstance(data, dict)


class TestGetRoleTaxonomyTool:
    """Tests for the get_role_taxonomy MCP tool."""

    def test_returns_roles_key(self):
        result = json.loads(get_role_taxonomy(None))
        assert "roles" in result

    def test_returns_9_roles(self):
        result = json.loads(get_role_taxonomy(None))
        assert len(result["roles"]) == 9

    def test_contains_kick_and_master(self):
        result = json.loads(get_role_taxonomy(None))
        assert "kick" in result["roles"]
        assert "master" in result["roles"]
