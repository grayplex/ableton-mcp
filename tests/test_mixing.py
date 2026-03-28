"""Tests for mixing recipe catalog, auto-discovery, alias resolution, and data validation.

Validates that:
- pkgutil auto-discovery finds all genre recipe modules
- get_recipe() resolves role and genre aliases
- Every recipe param name exists in the device CATALOG
- Every genre recipe has all 9 canonical ROLES
- Recipe data structure is correct (role -> device_class -> param_dict)
"""

import json
import sys
import types
from unittest.mock import MagicMock

import pytest

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

from MCP_Server.devices.catalog import CATALOG, ROLES  # noqa: E402
from MCP_Server.mixing import get_recipe, list_recipes  # noqa: E402
from MCP_Server.mixing.catalog import _ensure_initialized, _registry  # noqa: E402
from MCP_Server.tools.mixing import get_mix_recipe  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_device_param_names(device_class: str) -> set:
    """Get all parameter names for a device from the catalog."""
    entry = CATALOG.get(device_class)
    if entry is None:
        return set()
    return {p["name"] for p in entry["parameters"]}


# ---------------------------------------------------------------------------
# Auto-Discovery Tests
# ---------------------------------------------------------------------------


class TestAutoDiscovery:
    """Verify pkgutil auto-discovery populates the registry."""

    def test_registry_populated_after_init(self):
        _ensure_initialized()
        assert len(_registry) > 0, "Registry should contain at least one genre"

    def test_skip_modules_not_in_registry(self):
        _ensure_initialized()
        assert "catalog" not in _registry, "catalog module should be skipped"

    def test_underscore_modules_not_in_registry(self):
        _ensure_initialized()
        for key in _registry:
            assert not key.startswith("_"), f"Module '{key}' starts with underscore"


# ---------------------------------------------------------------------------
# get_recipe Tests
# ---------------------------------------------------------------------------


class TestGetRecipe:
    """Verify get_recipe returns correct data or None for invalid inputs."""

    def test_valid_role_and_genre_returns_dict(self):
        result = get_recipe("kick", "house")
        assert isinstance(result, dict), "get_recipe should return a dict for valid input"

    def test_invalid_role_returns_none(self):
        result = get_recipe("invalid_role", "house")
        assert result is None

    def test_invalid_genre_returns_none(self):
        result = get_recipe("kick", "invalid_genre")
        assert result is None

    def test_result_contains_device_classes(self):
        result = get_recipe("kick", "house")
        assert result is not None
        for device_class in result:
            assert device_class in CATALOG, (
                f"Device class '{device_class}' not in CATALOG"
            )


# ---------------------------------------------------------------------------
# Alias Resolution Tests
# ---------------------------------------------------------------------------


class TestAliasResolution:
    """Verify role and genre aliases resolve correctly."""

    def test_genre_alias_dnb(self):
        """dnb -> drum_and_bass recipe."""
        result = get_recipe("kick", "dnb")
        direct = get_recipe("kick", "drum_and_bass")
        # Both should resolve to the same recipe (or both None if DnB not yet authored)
        assert result == direct

    def test_role_alias_kick_drum(self):
        """'kick drum' -> kick role."""
        result = get_recipe("kick drum", "house")
        direct = get_recipe("kick", "house")
        assert result is not None
        assert result == direct

    def test_role_alias_vocals(self):
        """'vocals' -> vocal role."""
        result = get_recipe("vocals", "house")
        direct = get_recipe("vocal", "house")
        assert result is not None
        assert result == direct

    def test_role_alias_vox(self):
        """'vox' -> vocal role."""
        result = get_recipe("vox", "house")
        direct = get_recipe("vocal", "house")
        assert result is not None
        assert result == direct

    def test_role_alias_atmosphere(self):
        """'atmosphere' -> atmospheric role."""
        result = get_recipe("atmosphere", "house")
        direct = get_recipe("atmospheric", "house")
        assert result is not None
        assert result == direct


# ---------------------------------------------------------------------------
# Recipe Parameter Name Validation
# ---------------------------------------------------------------------------


class TestRecipeParameterNames:
    """Every param name in every recipe must exist in the device CATALOG."""

    @pytest.fixture(autouse=True)
    def init_registry(self):
        _ensure_initialized()

    def test_all_recipe_params_in_catalog(self):
        for genre_id, recipe in _registry.items():
            for role, devices in recipe.items():
                for device_class, params in devices.items():
                    assert device_class in CATALOG, (
                        f"{genre_id}/{role}: device '{device_class}' not in CATALOG"
                    )
                    valid_names = _get_device_param_names(device_class)
                    for param_name in params:
                        assert param_name in valid_names, (
                            f"{genre_id}/{role}/{device_class}: "
                            f"param '{param_name}' not in catalog. "
                            f"Valid: {sorted(valid_names)}"
                        )


# ---------------------------------------------------------------------------
# Recipe Completeness
# ---------------------------------------------------------------------------


class TestRecipeCompleteness:
    """Every genre recipe must have all 9 canonical ROLES."""

    @pytest.fixture(autouse=True)
    def init_registry(self):
        _ensure_initialized()

    def test_all_genres_have_all_roles(self):
        for genre_id, recipe in _registry.items():
            for role in ROLES:
                assert role in recipe, (
                    f"Genre '{genre_id}' missing role '{role}'"
                )

    def test_no_extra_roles(self):
        """Recipe should only contain canonical roles."""
        role_set = set(ROLES)
        for genre_id, recipe in _registry.items():
            for role in recipe:
                assert role in role_set, (
                    f"Genre '{genre_id}' has unexpected role '{role}'"
                )


# ---------------------------------------------------------------------------
# Recipe Data Structure
# ---------------------------------------------------------------------------


class TestRecipeData:
    """Verify recipe data structure: role -> device_class -> param_dict."""

    @pytest.fixture(autouse=True)
    def init_registry(self):
        _ensure_initialized()

    def test_every_role_maps_to_dict_of_devices(self):
        for genre_id, recipe in _registry.items():
            for role, devices in recipe.items():
                assert isinstance(devices, dict), (
                    f"{genre_id}/{role}: expected dict, got {type(devices)}"
                )

    def test_device_class_keys_are_valid_catalog_keys(self):
        for genre_id, recipe in _registry.items():
            for role, devices in recipe.items():
                for device_class in devices:
                    assert device_class in CATALOG, (
                        f"{genre_id}/{role}: device '{device_class}' not in CATALOG"
                    )

    def test_param_values_are_numeric(self):
        for genre_id, recipe in _registry.items():
            for role, devices in recipe.items():
                for device_class, params in devices.items():
                    for param_name, value in params.items():
                        assert isinstance(value, (int, float)), (
                            f"{genre_id}/{role}/{device_class}/{param_name}: "
                            f"expected numeric, got {type(value)}: {value}"
                        )


# ---------------------------------------------------------------------------
# list_recipes
# ---------------------------------------------------------------------------


class TestListRecipes:
    """Verify list_recipes returns a sorted list of genre IDs."""

    def test_returns_list_of_strings(self):
        result = list_recipes()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    def test_returns_sorted(self):
        result = list_recipes()
        assert result == sorted(result)

    def test_contains_discovered_genres(self):
        _ensure_initialized()
        result = list_recipes()
        for genre_id in _registry:
            assert genre_id in result


# ---------------------------------------------------------------------------
# MCP Tool Tests
# ---------------------------------------------------------------------------


class TestMixRecipeTool:
    """Verify get_mix_recipe MCP tool returns JSON or error."""

    def test_valid_recipe_returns_json(self):
        result = get_mix_recipe(None, "kick", "house")
        data = json.loads(result)
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_invalid_returns_error(self):
        result = get_mix_recipe(None, "invalid", "house")
        assert "Error:" in result

    def test_invalid_genre_returns_error(self):
        result = get_mix_recipe(None, "kick", "invalid_genre")
        assert "Error:" in result

    def test_alias_resolution_dnb(self):
        result = get_mix_recipe(None, "kick", "dnb")
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "Eq8" in data or "Compressor2" in data

    def test_alias_resolution_vocals(self):
        result = get_mix_recipe(None, "vocals", "house")
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_result_contains_device_params(self):
        result = get_mix_recipe(None, "pad", "ambient")
        data = json.loads(result)
        assert "Eq8" in data
        assert isinstance(data["Eq8"], dict)
