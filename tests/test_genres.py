"""Tests for genre blueprint schema and validation."""

import pytest

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
