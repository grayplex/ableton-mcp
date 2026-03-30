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
from MCP_Server.mixing import get_master_recipe, get_recipe, list_recipes  # noqa: E402
from MCP_Server.mixing.catalog import (  # noqa: E402
    _ensure_initialized,
    _master_registry,
    _registry,
)
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


# ---------------------------------------------------------------------------
# Master Recipe Data Validation
# ---------------------------------------------------------------------------

_MASTER_DEVICE_KEYS = {"GlueCompressor", "MultibandDynamics", "Limiter"}
def _get_master_genres():
    """Dynamic list of all genres with MASTER_RECIPE."""
    _ensure_initialized()
    return sorted(_master_registry.keys())


def _get_device_param_names(device_class: str) -> set:
    """Get all parameter names for a device from the catalog."""
    entry = CATALOG.get(device_class)
    if entry is None:
        return set()
    return {p["name"] for p in entry["parameters"]}


class TestMasterRecipeData:
    """Validate all genre MASTER_RECIPE constants against CATALOG."""

    @pytest.fixture(autouse=True)
    def init_registry(self):
        _ensure_initialized()

    def test_all_genres_have_master_recipe(self):
        for genre in _get_master_genres():
            assert genre in _master_registry, (
                f"Genre '{genre}' missing from _master_registry"
            )

    def test_master_recipe_has_required_device_keys(self):
        for genre in _get_master_genres():
            recipe = _master_registry[genre]
            assert set(recipe.keys()) == _MASTER_DEVICE_KEYS, (
                f"Genre '{genre}' MASTER_RECIPE keys: {set(recipe.keys())} "
                f"!= expected {_MASTER_DEVICE_KEYS}"
            )

    def test_all_master_recipe_params_in_catalog(self):
        for genre in _get_master_genres():
            recipe = _master_registry[genre]
            for device_class, params in recipe.items():
                assert device_class in CATALOG, (
                    f"{genre}: device '{device_class}' not in CATALOG"
                )
                valid_names = _get_device_param_names(device_class)
                for param_name in params:
                    assert param_name in valid_names, (
                        f"{genre}/{device_class}: param '{param_name}' "
                        f"not in catalog. Valid: {sorted(valid_names)}"
                    )

    def test_master_recipe_values_are_numeric(self):
        for genre in _get_master_genres():
            recipe = _master_registry[genre]
            for device_class, params in recipe.items():
                for param_name, value in params.items():
                    assert isinstance(value, (int, float)), (
                        f"{genre}/{device_class}/{param_name}: "
                        f"expected numeric, got {type(value)}: {value}"
                    )


class TestGetMasterRecipe:
    """Test get_master_recipe public API."""

    def test_house_returns_dict_with_device_keys(self):
        result = get_master_recipe("house")
        assert result is not None
        assert set(result.keys()) == _MASTER_DEVICE_KEYS

    def test_techno_returns_dict(self):
        result = get_master_recipe("techno")
        assert result is not None
        assert "GlueCompressor" in result

    def test_ambient_returns_dict(self):
        result = get_master_recipe("ambient")
        assert result is not None
        assert "Limiter" in result

    def test_drum_and_bass_returns_dict(self):
        result = get_master_recipe("drum_and_bass")
        assert result is not None
        assert "MultibandDynamics" in result

    def test_alias_dnb(self):
        """'dnb' alias resolves to drum_and_bass master recipe."""
        result = get_master_recipe("dnb")
        direct = get_master_recipe("drum_and_bass")
        assert result is not None
        assert result == direct

    def test_nonexistent_returns_none(self):
        result = get_master_recipe("nonexistent_genre")
        assert result is None


# ---------------------------------------------------------------------------
# Phase 31-02: Apply Recipe MCP Tool Tests
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock, patch  # noqa: E402

from MCP_Server.tools.mixing import (  # noqa: E402
    apply_mix_recipe,
    apply_master_recipe,
    set_sidechain_source,
)


class TestApplyMixRecipe:
    """Verify apply_mix_recipe MCP tool converts recipe and sends single command."""

    def test_valid_recipe_calls_send_command(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"applied": True, "devices": []}
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result = apply_mix_recipe(None, 0, "kick", "house")
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "apply_recipe"
        payload = call_args[0][1]
        assert payload["track_type"] == "track"
        assert payload["track_index"] == 0
        assert isinstance(payload["devices"], list)
        assert len(payload["devices"]) > 0

    def test_invalid_role_returns_error(self):
        result = apply_mix_recipe(None, 0, "invalid_role", "house")
        assert "Error" in result
        assert "No recipe found" in result

    def test_payload_has_correct_structure(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"applied": True}
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            apply_mix_recipe(None, 0, "kick", "house")
        payload = mock_conn.send_command.call_args[0][1]
        for device_spec in payload["devices"]:
            assert "class_name" in device_spec, "Each device must have class_name"
            assert "params" in device_spec, "Each device must have params"
            assert isinstance(device_spec["params"], dict)

    def test_payload_params_are_normalized(self):
        """Params should be converted from natural units to normalized 0.0-1.0."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"applied": True}
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            apply_mix_recipe(None, 0, "kick", "house")
        payload = mock_conn.send_command.call_args[0][1]
        for device_spec in payload["devices"]:
            for param_name, value in device_spec["params"].items():
                assert isinstance(value, (int, float)), (
                    f"Param {param_name} value should be numeric, got {type(value)}"
                )


class TestApplyMasterRecipe:
    """Verify apply_master_recipe MCP tool applies to master track."""

    def test_valid_genre_calls_with_master_track_type(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"applied": True, "devices": []}
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result = apply_master_recipe(None, "house")
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "apply_recipe"
        payload = call_args[0][1]
        assert payload["track_type"] == "master"

    def test_master_recipe_contains_expected_devices(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"applied": True}
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            apply_master_recipe(None, "house")
        payload = mock_conn.send_command.call_args[0][1]
        class_names = {d["class_name"] for d in payload["devices"]}
        assert "GlueCompressor" in class_names
        assert "MultibandDynamics" in class_names
        assert "Limiter" in class_names

    def test_invalid_genre_returns_error(self):
        result = apply_master_recipe(None, "invalid_genre")
        assert "Error" in result
        assert "No master recipe" in result


class TestSidechainSource:
    """Verify set_sidechain_source MCP tool sends correct command."""

    def test_valid_params_calls_send_command(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "device_name": "Compressor",
            "source_track": "Kick",
            "routing_type": "Kick",
            "routing_channel": "Post FX",
        }
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            result = set_sidechain_source(None, 1, 0, "Kick")
        mock_conn.send_command.assert_called_once()
        call_args = mock_conn.send_command.call_args
        assert call_args[0][0] == "set_sidechain_source"
        payload = call_args[0][1]
        assert payload["source_track_name"] == "Kick"
        assert payload["track_index"] == 1
        assert payload["device_index"] == 0

    def test_custom_track_type(self):
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"device_name": "Compressor"}
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            set_sidechain_source(None, 0, 0, "Kick", track_type="return")
        payload = mock_conn.send_command.call_args[0][1]
        assert payload["track_type"] == "return"


class TestBatchParameterSetting:
    """Verify apply_mix_recipe sends all params in a single send_command call."""

    def test_single_send_command_call(self):
        """apply_mix_recipe should call send_command exactly once (not N times)."""
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {"applied": True}
        with patch("MCP_Server.tools.mixing.get_ableton_connection", return_value=mock_conn):
            apply_mix_recipe(None, 0, "kick", "house")
        assert mock_conn.send_command.call_count == 1, (
            f"Expected 1 send_command call, got {mock_conn.send_command.call_count}"
        )
