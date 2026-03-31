"""Tests for sounds package: auto-discovery catalog, alias resolution, and wavetable profile."""

import pytest

from MCP_Server.sounds import get_profile, list_profiles


class TestAutoDiscovery:
    """Verify pkgutil auto-discovery finds instrument profiles."""

    def test_wavetable_discovered(self):
        """list_profiles() returns at least 1 profile with id 'wavetable'."""
        profiles = list_profiles()
        ids = [p["id"] for p in profiles]
        assert "wavetable" in ids

    def test_skip_catalog_module(self):
        """'catalog' does not appear as a profile id in list_profiles()."""
        profiles = list_profiles()
        ids = [p["id"] for p in profiles]
        assert "catalog" not in ids

    def test_list_profiles_metadata(self):
        """list_profiles() returns dicts with keys 'id', 'name', 'aliases'."""
        profiles = list_profiles()
        assert len(profiles) >= 1
        for p in profiles:
            assert "id" in p
            assert "name" in p
            assert "aliases" in p


class TestGetProfile:
    """Verify get_profile returns profile data or None."""

    def test_canonical_id(self):
        """get_profile('wavetable') returns a dict (not None)."""
        profile = get_profile("wavetable")
        assert profile is not None
        assert isinstance(profile, dict)

    def test_unknown_returns_none(self):
        """get_profile('nonexistent_instrument') returns None."""
        result = get_profile("nonexistent_instrument")
        assert result is None


class TestAliasResolution:
    """Verify alias normalization resolves various name forms."""

    def test_abbreviation(self):
        """get_profile('wt') returns profile with id 'wavetable'."""
        profile = get_profile("wt")
        assert profile is not None
        assert profile["id"] == "wavetable"

    def test_case_insensitive(self):
        """get_profile('Wavetable') returns profile with id 'wavetable'."""
        profile = get_profile("Wavetable")
        assert profile is not None
        assert profile["id"] == "wavetable"

    def test_space_normalization(self):
        """get_profile('wave table') returns profile with id 'wavetable'."""
        profile = get_profile("wave table")
        assert profile is not None
        assert profile["id"] == "wavetable"

    def test_hyphen_normalization(self):
        """get_profile('wave-table') returns profile with id 'wavetable'."""
        profile = get_profile("wave-table")
        assert profile is not None
        assert profile["id"] == "wavetable"


class TestProfileShape:
    """Verify the wavetable profile has all required keys with correct types."""

    @pytest.fixture
    def profile(self):
        """Load wavetable profile for shape tests."""
        p = get_profile("wavetable")
        assert p is not None
        return p

    def test_required_keys(self, profile):
        """Profile has all required top-level keys."""
        required = [
            "id", "name", "aliases", "sonic_character",
            "strengths", "weaknesses", "descriptor_affinities", "browser",
        ]
        for key in required:
            assert key in profile, f"Missing required key: {key}"

    def test_sonic_character_is_string(self, profile):
        """profile['sonic_character'] is a non-empty str."""
        assert isinstance(profile["sonic_character"], str)
        assert len(profile["sonic_character"]) > 0

    def test_strengths_is_list(self, profile):
        """profile['strengths'] is a non-empty list of strings."""
        assert isinstance(profile["strengths"], list)
        assert len(profile["strengths"]) > 0
        for item in profile["strengths"]:
            assert isinstance(item, str)

    def test_weaknesses_is_list(self, profile):
        """profile['weaknesses'] is a non-empty list of strings."""
        assert isinstance(profile["weaknesses"], list)
        assert len(profile["weaknesses"]) > 0
        for item in profile["weaknesses"]:
            assert isinstance(item, str)

    def test_affinity_axes(self, profile):
        """profile['descriptor_affinities'] has keys 'role' and 'character'."""
        affinities = profile["descriptor_affinities"]
        assert "role" in affinities
        assert "character" in affinities

    def test_affinity_weights_range(self, profile):
        """All values in role and character dicts are floats between 0.0 and 1.0."""
        affinities = profile["descriptor_affinities"]
        for axis_name in ("role", "character"):
            axis = affinities[axis_name]
            assert isinstance(axis, dict)
            assert len(axis) > 0
            for key, value in axis.items():
                assert isinstance(value, float), f"{axis_name}.{key} is not a float"
                assert 0.0 <= value <= 1.0, f"{axis_name}.{key}={value} out of range"

    def test_browser_has_root(self, profile):
        """profile['browser']['root'] is a non-empty string."""
        assert isinstance(profile["browser"]["root"], str)
        assert len(profile["browser"]["root"]) > 0

    def test_browser_has_categories(self, profile):
        """profile['browser']['categories'] is a non-empty dict."""
        cats = profile["browser"]["categories"]
        assert isinstance(cats, dict)
        assert len(cats) > 0
