"""Tests for sounds package: auto-discovery catalog, alias resolution, and wavetable profile."""

import pytest

from MCP_Server.sounds import get_profile, list_profiles
from MCP_Server.sounds.catalog import recommend, list_descriptors


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


# ---------------------------------------------------------------------------
# All-six-profile coverage
# ---------------------------------------------------------------------------

ALL_PROFILE_IDS = ["wavetable", "analog", "operator", "drift", "simpler", "drum_rack"]


class TestAllSixProfiles:
    """Verify all 6 instrument profiles are discovered, aliased, and schema-valid."""

    def test_six_profiles_discovered(self):
        """list_profiles() returns exactly 6 profiles."""
        profiles = list_profiles()
        assert len(profiles) == 6, f"Expected 6 profiles, got {len(profiles)}: {[p['id'] for p in profiles]}"

    def test_all_profile_ids(self):
        """Profile ids include all of: wavetable, analog, operator, drift, simpler, drum_rack."""
        ids = [p["id"] for p in list_profiles()]
        for expected in ALL_PROFILE_IDS:
            assert expected in ids, f"Missing profile id: {expected}"

    def test_analog_aliases(self):
        """get_profile('al') returns profile with id 'analog'."""
        profile = get_profile("al")
        assert profile is not None
        assert profile["id"] == "analog"

    def test_operator_aliases(self):
        """get_profile('op') returns profile with id 'operator'."""
        profile = get_profile("op")
        assert profile is not None
        assert profile["id"] == "operator"

    def test_drift_aliases(self):
        """get_profile('drift') returns profile with id 'drift'."""
        profile = get_profile("drift")
        assert profile is not None
        assert profile["id"] == "drift"

    def test_simpler_aliases(self):
        """get_profile('smplr') returns profile with id 'simpler'."""
        profile = get_profile("smplr")
        assert profile is not None
        assert profile["id"] == "simpler"

    def test_drum_rack_aliases(self):
        """get_profile('dr') returns profile with id 'drum_rack'."""
        profile = get_profile("dr")
        assert profile is not None
        assert profile["id"] == "drum_rack"

    def test_drum_rack_percussion_roles(self):
        """Drum Rack profile has kick, snare, hihat keys in descriptor_affinities['role']."""
        profile = get_profile("drum_rack")
        assert profile is not None
        roles = profile["descriptor_affinities"]["role"]
        for key in ("kick", "snare", "hihat"):
            assert key in roles, f"Drum Rack missing percussion role: {key}"

    def test_simpler_mentions_modes(self):
        """Simpler sonic_character contains 'Classic', 'One-Shot', and 'Slice'."""
        profile = get_profile("simpler")
        assert profile is not None
        sc = profile["sonic_character"]
        for mode in ("Classic", "One-Shot", "Slice"):
            assert mode in sc, f"Simpler sonic_character missing mode: {mode}"

    @pytest.mark.parametrize("profile_id", ALL_PROFILE_IDS)
    def test_all_profiles_have_required_keys(self, profile_id):
        """Each profile has all required top-level keys."""
        profile = get_profile(profile_id)
        assert profile is not None, f"Profile not found: {profile_id}"
        required = [
            "id", "name", "aliases", "sonic_character",
            "strengths", "weaknesses", "descriptor_affinities", "browser",
        ]
        for key in required:
            assert key in profile, f"Profile '{profile_id}' missing required key: {key}"

    @pytest.mark.parametrize("profile_id", ALL_PROFILE_IDS)
    def test_all_affinity_weights_in_range(self, profile_id):
        """All affinity weights are floats between 0.0 and 1.0."""
        profile = get_profile(profile_id)
        assert profile is not None, f"Profile not found: {profile_id}"
        affinities = profile["descriptor_affinities"]
        for axis_name in ("role", "character"):
            assert axis_name in affinities, f"Profile '{profile_id}' missing axis: {axis_name}"
            axis = affinities[axis_name]
            for key, value in axis.items():
                assert isinstance(value, float), f"{profile_id}.{axis_name}.{key} is not a float"
                assert 0.0 <= value <= 1.0, f"{profile_id}.{axis_name}.{key}={value} out of range"

    @pytest.mark.parametrize("profile_id", ALL_PROFILE_IDS)
    def test_all_browser_roots_non_empty(self, profile_id):
        """Each profile's browser['root'] is a non-empty string."""
        profile = get_profile(profile_id)
        assert profile is not None, f"Profile not found: {profile_id}"
        root = profile["browser"]["root"]
        assert isinstance(root, str) and len(root) > 0, f"Profile '{profile_id}' has empty browser root"


# ---------------------------------------------------------------------------
# Scoring engine: recommend() and list_descriptors()
# ---------------------------------------------------------------------------


class TestRecommend:
    """Verify recommend() returns correct top-scoring instrument dicts."""

    def test_warm_pad_returns_wavetable(self):
        """recommend('warm pad') returns dict with id='wavetable'.

        wavetable: pad=0.95 + warm=0.7 = 1.65
        analog:    pad=0.55 + warm=0.9 = 1.45
        wavetable wins.
        """
        result = recommend("warm pad")
        assert result is not None
        assert result["id"] == "wavetable"

    def test_punchy_kick_returns_drum_rack(self):
        """recommend('punchy kick') returns dict with id='drum_rack'.

        drum_rack: kick=0.95 + punchy=0.95 = 1.90 — no competition.
        """
        result = recommend("punchy kick")
        assert result is not None
        assert result["id"] == "drum_rack"

    def test_result_has_required_keys(self):
        """Result dict has keys: id, name, score, browser_path, category_hint, reasoning."""
        result = recommend("warm pad")
        assert result is not None
        for key in ("id", "name", "score", "browser_path", "category_hint", "reasoning"):
            assert key in result, f"Missing required key: {key}"

    def test_browser_path_is_root(self):
        """result['browser_path'] equals the profile's browser['root']."""
        result = recommend("warm pad")
        assert result is not None
        profile = get_profile(result["id"])
        assert profile is not None
        assert result["browser_path"] == profile["browser"]["root"]

    def test_reasoning_is_string(self):
        """result['reasoning'] is a non-empty string mentioning the descriptor."""
        result = recommend("warm pad")
        assert result is not None
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 0
        assert "warm pad" in result["reasoning"]

    def test_score_is_positive_float(self):
        """result['score'] is a float > 0."""
        result = recommend("warm pad")
        assert result is not None
        assert isinstance(result["score"], float)
        assert result["score"] > 0.0

    def test_unknown_descriptor_returns_none(self):
        """recommend('zzzunknown_xyz') returns None."""
        assert recommend("zzzunknown_xyz") is None

    def test_empty_descriptor_returns_none(self):
        """recommend('') returns None — empty tokens, all score 0."""
        assert recommend("") is None

    def test_single_role_tag_kick(self):
        """recommend('kick') returns dict with id='drum_rack'."""
        result = recommend("kick")
        assert result is not None
        assert result["id"] == "drum_rack"

    def test_single_character_tag_lush(self):
        """recommend('lush') returns dict with id='wavetable' — only wavetable has lush=0.9."""
        result = recommend("lush")
        assert result is not None
        assert result["id"] == "wavetable"

    def test_single_tag_organic(self):
        """recommend('organic') returns dict with id='simpler' — only simpler has organic."""
        result = recommend("organic")
        assert result is not None
        assert result["id"] == "simpler"


class TestListDescriptors:
    """Verify list_descriptors() returns correct vocabulary grouped by axis."""

    def test_returns_dict_with_two_axes(self):
        """list_descriptors() returns dict with keys 'role' and 'character'."""
        result = list_descriptors()
        assert isinstance(result, dict)
        assert "role" in result
        assert "character" in result

    def test_role_contains_percussion(self):
        """result['role'] contains 'kick', 'snare', 'hihat'."""
        result = list_descriptors()
        for tag in ("kick", "snare", "hihat"):
            assert tag in result["role"], f"Missing percussion role tag: {tag}"

    def test_role_contains_melodic(self):
        """result['role'] contains 'bass', 'lead', 'pad', 'keys'."""
        result = list_descriptors()
        for tag in ("bass", "lead", "pad", "keys"):
            assert tag in result["role"], f"Missing melodic role tag: {tag}"

    def test_character_contains_common_tags(self):
        """result['character'] contains common tags: warm, bright, dark, evolving, punchy, aggressive."""
        result = list_descriptors()
        for tag in ("warm", "bright", "dark", "evolving", "punchy", "aggressive"):
            assert tag in result["character"], f"Missing common character tag: {tag}"

    def test_character_contains_unique_tags(self):
        """result['character'] contains lush (wavetable-only), organic (simpler-only), tight (drum_rack-only)."""
        result = list_descriptors()
        for tag in ("lush", "organic", "tight"):
            assert tag in result["character"], f"Missing unique character tag: {tag}"

    def test_lists_are_sorted(self):
        """Both role and character lists are sorted alphabetically."""
        result = list_descriptors()
        assert result["role"] == sorted(result["role"]), "role list is not sorted"
        assert result["character"] == sorted(result["character"]), "character list is not sorted"

    def test_differentiation_gate(self):
        """At least 4 different instrument ids appear as top-1 across single-tag queries (D-13)."""
        result = list_descriptors()
        all_tags = result["role"] + result["character"]
        top_ids = set()
        for tag in all_tags:
            r = recommend(tag)
            if r is not None:
                top_ids.add(r["id"])
        assert len(top_ids) >= 4, (
            f"Differentiation gate failed: only {len(top_ids)} distinct instruments "
            f"appear as top-1 across all single-tag queries: {top_ids}"
        )
