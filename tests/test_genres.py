"""Tests for genre blueprint schema, catalog, alias resolution, subgenre merge, and house genre."""

import pytest

from MCP_Server.genres import get_blueprint, list_genres, resolve_alias
from MCP_Server.genres.schema import (
    GenreBlueprint,
    validate_blueprint,
)


def _make_valid_blueprint() -> dict:
    """Return a minimal valid blueprint dict for testing."""
    return {
        "name": "Test Genre",
        "id": "test_genre",
        "bpm_range": [120, 130],
        "aliases": ["test"],
        "instrumentation": {"roles": ["kick", "bass", "pad"]},
        "harmony": {
            "scales": ["minor"],
            "chord_types": ["min7"],
            "common_progressions": [["i", "iv"]],
        },
        "rhythm": {
            "time_signature": "4/4",
            "bpm_range": [120, 130],
            "swing": "none",
            "note_values": ["1/4", "1/8"],
            "drum_pattern": "four-on-the-floor",
        },
        "arrangement": {
            "sections": [{"name": "intro", "bars": 16}, {"name": "drop", "bars": 32}],
        },
        "mixing": {
            "frequency_focus": "low-end",
            "stereo_field": "wide pads, mono bass",
            "common_effects": ["sidechain compression"],
            "compression_style": "heavy sidechain",
        },
        "production_tips": {
            "techniques": ["layer kicks"],
            "pitfalls": ["muddy low-end"],
        },
    }


class TestSchema:
    def test_schema_has_six_dimensions(self):
        """GenreBlueprint TypedDict has keys for all 6 dimensions."""
        annotations = GenreBlueprint.__annotations__
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in annotations, f"Missing dimension: {dim}"

    def test_validate_valid_blueprint(self):
        """validate_blueprint accepts a well-formed blueprint without raising."""
        validate_blueprint(_make_valid_blueprint())  # should not raise

    def test_validate_missing_top_level_key(self):
        """validate_blueprint raises ValueError when a required top-level key is missing."""
        bp = _make_valid_blueprint()
        del bp["harmony"]
        with pytest.raises(ValueError, match="harmony"):
            validate_blueprint(bp)

    def test_validate_missing_section_key(self):
        """validate_blueprint raises ValueError when a section sub-key is missing."""
        bp = _make_valid_blueprint()
        del bp["harmony"]["scales"]
        with pytest.raises(ValueError, match="scales"):
            validate_blueprint(bp)

    def test_validate_wrong_type(self):
        """validate_blueprint raises ValueError when a field has the wrong type."""
        bp = _make_valid_blueprint()
        bp["bpm_range"] = "fast"
        with pytest.raises(ValueError):
            validate_blueprint(bp)

    def test_validate_empty_section(self):
        """validate_blueprint raises ValueError when a required list is empty."""
        bp = _make_valid_blueprint()
        bp["instrumentation"]["roles"] = []
        with pytest.raises(ValueError):
            validate_blueprint(bp)


class TestCatalog:
    """INFR-02: Auto-discovery tests."""

    def test_house_discovered(self):
        """House genre is auto-discovered without manual registration."""
        genres = list_genres()
        genre_ids = [g["id"] for g in genres]
        assert "house" in genre_ids

    def test_list_genres_metadata(self):
        """list_genres returns id, name, bpm_range, subgenres for each genre."""
        genres = list_genres()
        house = [g for g in genres if g["id"] == "house"][0]
        assert house["name"] == "House"
        assert house["bpm_range"] == [120, 130]
        assert "deep_house" in house["subgenres"]

    def test_get_blueprint_returns_full(self):
        """get_blueprint returns all 6 dimensions."""
        bp = get_blueprint("house")
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in bp, f"Missing dimension: {dim}"


class TestAliasResolution:
    """INFR-03: Alias resolution tests."""

    def test_canonical_id(self):
        result = resolve_alias("house")
        assert result is not None
        assert result["genre_id"] == "house"

    def test_alias_with_space(self):
        result = resolve_alias("deep house")
        assert result is not None
        assert result["genre_id"] == "house"
        assert result["subgenre_id"] == "deep_house"

    def test_alias_with_underscore(self):
        result = resolve_alias("deep_house")
        assert result is not None
        assert result["genre_id"] == "house"

    def test_alias_case_insensitive(self):
        result = resolve_alias("Deep House")
        assert result is not None
        assert result["genre_id"] == "house"

    def test_unknown_alias_returns_none(self):
        result = resolve_alias("nonexistent_genre")
        assert result is None


class TestSubgenreMerge:
    """INFR-04: Subgenre merge tests."""

    def test_deep_house_overrides_bpm(self):
        bp = get_blueprint("house", subgenre="deep_house")
        assert bp["bpm_range"] == [118, 124]

    def test_deep_house_inherits_instrumentation(self):
        """Deep house has no instrumentation override, so inherits from house base."""
        bp = get_blueprint("house", subgenre="deep_house")
        assert "kick" in bp["instrumentation"]["roles"]

    def test_deep_house_overrides_harmony(self):
        bp = get_blueprint("house", subgenre="deep_house")
        assert "maj9" in bp["harmony"]["chord_types"]

    def test_subgenre_via_alias(self):
        """Calling get_blueprint('deep_house') resolves via alias."""
        bp = get_blueprint("deep_house")
        assert bp is not None
        assert bp["bpm_range"] == [118, 124]

    def test_nonexistent_subgenre_returns_base(self):
        """Unknown subgenre falls back to base genre."""
        bp = get_blueprint("house", subgenre="imaginary_house")
        assert bp["bpm_range"] == [120, 130]


class TestHouseBlueprint:
    """GENR-01: House blueprint completeness."""

    def test_all_dimensions_present(self):
        bp = get_blueprint("house")
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in bp

    def test_four_subgenres(self):
        genres = list_genres()
        house = [g for g in genres if g["id"] == "house"][0]
        assert set(house["subgenres"]) == {"deep_house", "tech_house", "progressive_house", "acid_house"}

    def test_all_subgenres_pass_validation(self):
        """Each subgenre merged result passes schema validation."""
        for sub_id in ["deep_house", "tech_house", "progressive_house", "acid_house"]:
            bp = get_blueprint("house", subgenre=sub_id)
            validate_blueprint(bp)  # should not raise

    def test_harmony_uses_valid_scale_names(self):
        """All scale names in house blueprint exist in SCALE_CATALOG."""
        from MCP_Server.theory.scales import SCALE_CATALOG
        bp = get_blueprint("house")
        for scale in bp["harmony"]["scales"]:
            assert scale in SCALE_CATALOG, f"Unknown scale: {scale}"

    def test_harmony_uses_valid_chord_types(self):
        """All chord_types in house blueprint exist in theory engine's quality map."""
        from MCP_Server.theory.chords import _QUALITY_MAP
        bp = get_blueprint("house")
        for ct in bp["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Unknown chord_type: {ct}"


class TestTechnoBlueprint:
    """GENR-02: Techno blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.techno import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.techno import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE, f"Missing dimension: {dim}"

    def test_subgenre_count(self):
        from MCP_Server.genres.techno import SUBGENRES
        assert len(SUBGENRES) == 5

    def test_chord_types_valid(self):
        from MCP_Server.genres.techno import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Invalid chord type: {ct}"

    def test_scale_names_valid(self):
        from MCP_Server.genres.techno import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG, f"Invalid scale: {s}"

    def test_aliases_resolve(self):
        assert resolve_alias("techno") is not None
        assert resolve_alias("techno music") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        techno = [g for g in genres if g["id"] == "techno"][0]
        assert set(techno["subgenres"]) == {
            "minimal", "industrial", "melodic", "detroit", "peaktime_driving",
        }

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["minimal", "industrial", "melodic", "detroit", "peaktime_driving"]:
            bp = get_blueprint("techno", subgenre=sub_id)
            validate_blueprint(bp)


class TestHipHopTrapBlueprint:
    """GENR-03: Hip-hop/Trap blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.hip_hop_trap import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.hip_hop_trap import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE, f"Missing dimension: {dim}"

    def test_subgenre_count(self):
        from MCP_Server.genres.hip_hop_trap import SUBGENRES
        assert len(SUBGENRES) == 3

    def test_chord_types_valid(self):
        from MCP_Server.genres.hip_hop_trap import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Invalid chord type: {ct}"

    def test_scale_names_valid(self):
        from MCP_Server.genres.hip_hop_trap import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG, f"Invalid scale: {s}"

    def test_aliases_resolve(self):
        assert resolve_alias("hip_hop_trap") is not None
        assert resolve_alias("hip hop") is not None
        assert resolve_alias("trap") is not None
        assert resolve_alias("rap") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        hip_hop = [g for g in genres if g["id"] == "hip_hop_trap"][0]
        assert set(hip_hop["subgenres"]) == {"boom_bap", "trap", "lo_fi_hip_hop"}

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["boom_bap", "trap", "lo_fi_hip_hop"]:
            bp = get_blueprint("hip_hop_trap", subgenre=sub_id)
            validate_blueprint(bp)


class TestAmbientBlueprint:
    """GENR-04: Ambient blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.ambient import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.ambient import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE, f"Missing dimension: {dim}"

    def test_subgenre_count(self):
        from MCP_Server.genres.ambient import SUBGENRES
        assert len(SUBGENRES) == 3

    def test_chord_types_valid(self):
        from MCP_Server.genres.ambient import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Invalid chord type: {ct}"

    def test_scale_names_valid(self):
        from MCP_Server.genres.ambient import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG, f"Invalid scale: {s}"

    def test_aliases_resolve(self):
        assert resolve_alias("ambient") is not None
        assert resolve_alias("ambient music") is not None
        assert resolve_alias("atmospheric") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        ambient = [g for g in genres if g["id"] == "ambient"][0]
        assert set(ambient["subgenres"]) == {"dark_ambient", "drone", "cinematic"}

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["dark_ambient", "drone", "cinematic"]:
            bp = get_blueprint("ambient", subgenre=sub_id)
            validate_blueprint(bp)


class TestDrumAndBassBlueprint:
    """GENR-05: Drum & Bass blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.drum_and_bass import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.drum_and_bass import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE, f"Missing dimension: {dim}"

    def test_subgenre_count(self):
        from MCP_Server.genres.drum_and_bass import SUBGENRES
        assert len(SUBGENRES) == 4

    def test_chord_types_valid(self):
        from MCP_Server.genres.drum_and_bass import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Invalid chord type: {ct}"

    def test_scale_names_valid(self):
        from MCP_Server.genres.drum_and_bass import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG, f"Invalid scale: {s}"

    def test_aliases_resolve(self):
        assert resolve_alias("drum_and_bass") is not None
        assert resolve_alias("dnb") is not None
        assert resolve_alias("drum and bass") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        dnb = [g for g in genres if g["id"] == "drum_and_bass"][0]
        assert set(dnb["subgenres"]) == {"liquid", "neurofunk", "jungle", "neuro"}

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["liquid", "neurofunk", "jungle", "neuro"]:
            bp = get_blueprint("drum_and_bass", subgenre=sub_id)
            validate_blueprint(bp)


class TestDubstepBlueprint:
    """GENR-06: Dubstep blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.dubstep import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.dubstep import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE, f"Missing dimension: {dim}"

    def test_subgenre_count(self):
        from MCP_Server.genres.dubstep import SUBGENRES
        assert len(SUBGENRES) == 4

    def test_chord_types_valid(self):
        from MCP_Server.genres.dubstep import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Invalid chord type: {ct}"

    def test_scale_names_valid(self):
        from MCP_Server.genres.dubstep import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG, f"Invalid scale: {s}"

    def test_aliases_resolve(self):
        assert resolve_alias("dubstep") is not None
        assert resolve_alias("dubstep music") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        dubstep = [g for g in genres if g["id"] == "dubstep"][0]
        assert set(dubstep["subgenres"]) == {"brostep", "riddim", "melodic_dubstep", "deep_dubstep"}

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["brostep", "riddim", "melodic_dubstep", "deep_dubstep"]:
            bp = get_blueprint("dubstep", subgenre=sub_id)
            validate_blueprint(bp)


class TestTranceBlueprint:
    """GENR-07: Trance blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.trance import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.trance import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE, f"Missing dimension: {dim}"

    def test_subgenre_count(self):
        from MCP_Server.genres.trance import SUBGENRES
        assert len(SUBGENRES) == 3

    def test_chord_types_valid(self):
        from MCP_Server.genres.trance import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Invalid chord type: {ct}"

    def test_scale_names_valid(self):
        from MCP_Server.genres.trance import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG, f"Invalid scale: {s}"

    def test_aliases_resolve(self):
        assert resolve_alias("trance") is not None
        assert resolve_alias("trance music") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        trance = [g for g in genres if g["id"] == "trance"][0]
        assert set(trance["subgenres"]) == {"progressive_trance", "uplifting", "psytrance"}

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["progressive_trance", "uplifting", "psytrance"]:
            bp = get_blueprint("trance", subgenre=sub_id)
            validate_blueprint(bp)


class TestNeoSoulRnbBlueprint:
    """GENR-08: Neo-soul/R&B blueprint completeness."""

    def test_schema_valid(self):
        from MCP_Server.genres.neo_soul_rnb import GENRE
        validate_blueprint(GENRE)

    def test_all_dimensions(self):
        from MCP_Server.genres.neo_soul_rnb import GENRE
        for dim in ["instrumentation", "harmony", "rhythm", "arrangement", "mixing", "production_tips"]:
            assert dim in GENRE, f"Missing dimension: {dim}"

    def test_subgenre_count(self):
        from MCP_Server.genres.neo_soul_rnb import SUBGENRES
        assert len(SUBGENRES) == 3

    def test_chord_types_valid(self):
        from MCP_Server.genres.neo_soul_rnb import GENRE
        from MCP_Server.theory.chords import _QUALITY_MAP
        for ct in GENRE["harmony"]["chord_types"]:
            assert ct in _QUALITY_MAP, f"Invalid chord type: {ct}"

    def test_scale_names_valid(self):
        from MCP_Server.genres.neo_soul_rnb import GENRE
        from MCP_Server.theory.scales import SCALE_CATALOG
        for s in GENRE["harmony"]["scales"]:
            assert s in SCALE_CATALOG, f"Invalid scale: {s}"

    def test_aliases_resolve(self):
        assert resolve_alias("neo_soul_rnb") is not None
        assert resolve_alias("rnb") is not None
        assert resolve_alias("neo soul") is not None

    def test_subgenres_discovered(self):
        genres = list_genres()
        neo_soul = [g for g in genres if g["id"] == "neo_soul_rnb"][0]
        assert set(neo_soul["subgenres"]) == {"neo_soul", "contemporary_rnb", "alternative_rnb"}

    def test_all_subgenres_pass_validation(self):
        for sub_id in ["neo_soul", "contemporary_rnb", "alternative_rnb"]:
            bp = get_blueprint("neo_soul_rnb", subgenre=sub_id)
            validate_blueprint(bp)


class TestAllGenresIntegration:
    """Integration test: all 8 genres discovered and aliases resolve."""

    def test_eight_genres_total(self):
        genres = list_genres()
        assert len(genres) == 8

    def test_all_genre_ids_present(self):
        genres = list_genres()
        ids = {g["id"] for g in genres}
        expected = {
            "house", "techno", "hip_hop_trap", "ambient",
            "drum_and_bass", "dubstep", "trance", "neo_soul_rnb",
        }
        assert ids == expected

    def test_common_aliases_resolve(self):
        alias_map = {
            "dnb": "drum_and_bass",
            "hiphop": "hip_hop_trap",
            "dubstep": "dubstep",
            "trance": "trance",
            "rnb": "neo_soul_rnb",
            "house music": "house",
            "techno": "techno",
            "ambient": "ambient",
        }
        for alias, expected_id in alias_map.items():
            result = resolve_alias(alias)
            assert result is not None, f"Alias '{alias}' did not resolve"
            assert result["genre_id"] == expected_id, (
                f"Alias '{alias}' resolved to '{result['genre_id']}', expected '{expected_id}'"
            )
