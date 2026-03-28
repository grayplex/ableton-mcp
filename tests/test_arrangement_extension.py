"""Tests for ARNG-01/02/03: ArrangementEntry schema extension with energy, roles, transition_in.

Covers:
- Schema extension: ArrangementEntry TypedDict optional fields
- Validator backward-compatibility and new field validation
- All 12 genre blueprints carry energy, roles, and transition_in on every section
- Intro/first section omits transition_in (D-04)
- Non-intro sections have transition_in
- Subgenre overrides with arrangement data also carry new fields
"""

import pytest

from MCP_Server.genres.catalog import get_blueprint
from MCP_Server.genres.schema import validate_blueprint


ALL_GENRES = [
    "house",
    "techno",
    "hip_hop_trap",
    "ambient",
    "drum_and_bass",
    "dubstep",
    "trance",
    "neo_soul_rnb",
    "synthwave",
    "lo_fi",
    "future_bass",
    "disco_funk",
]

# Subgenres that override arrangement.sections (must also carry new fields)
SUBGENRE_OVERRIDES = [
    ("house", "progressive_house"),
    ("techno", "melodic"),
    ("techno", "peaktime_driving"),
    ("ambient", "cinematic"),
]


def _make_valid_blueprint() -> dict:
    """Minimal valid blueprint (no new optional fields) — backward-compat fixture."""
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


class TestArrangementExtension:
    """Tests that verify all 12 genre blueprints carry energy, roles, and transition_in."""

    def test_all_genres_sections_have_energy(self):
        """Every section in every genre blueprint has energy (int, 1-10)."""
        for genre in ALL_GENRES:
            bp = get_blueprint(genre)
            sections = bp["arrangement"]["sections"]
            for section in sections:
                assert "energy" in section, (
                    f"Genre '{genre}' section '{section['name']}' missing 'energy'"
                )
                assert isinstance(section["energy"], int), (
                    f"Genre '{genre}' section '{section['name']}' energy must be int, "
                    f"got {type(section['energy']).__name__}"
                )
                assert 1 <= section["energy"] <= 10, (
                    f"Genre '{genre}' section '{section['name']}' energy {section['energy']} "
                    f"out of range 1-10"
                )

    def test_all_genres_sections_have_roles(self):
        """Every section in every genre blueprint has roles (non-empty list of str)."""
        for genre in ALL_GENRES:
            bp = get_blueprint(genre)
            sections = bp["arrangement"]["sections"]
            for section in sections:
                assert "roles" in section, (
                    f"Genre '{genre}' section '{section['name']}' missing 'roles'"
                )
                assert isinstance(section["roles"], list), (
                    f"Genre '{genre}' section '{section['name']}' roles must be list"
                )
                assert len(section["roles"]) > 0, (
                    f"Genre '{genre}' section '{section['name']}' roles must not be empty"
                )
                for role in section["roles"]:
                    assert isinstance(role, str), (
                        f"Genre '{genre}' section '{section['name']}' role items must be str"
                    )

    def test_all_genres_intro_no_transition_in(self):
        """The first section (intro) of every genre has NO transition_in key (D-04)."""
        for genre in ALL_GENRES:
            bp = get_blueprint(genre)
            first_section = bp["arrangement"]["sections"][0]
            assert "transition_in" not in first_section, (
                f"Genre '{genre}' first section '{first_section['name']}' "
                f"must NOT have 'transition_in' (D-04)"
            )

    def test_all_genres_non_intro_have_transition_in(self):
        """Every section after the first in every genre has transition_in (non-empty str)."""
        for genre in ALL_GENRES:
            bp = get_blueprint(genre)
            sections = bp["arrangement"]["sections"]
            for section in sections[1:]:
                assert "transition_in" in section, (
                    f"Genre '{genre}' section '{section['name']}' missing 'transition_in'"
                )
                assert isinstance(section["transition_in"], str), (
                    f"Genre '{genre}' section '{section['name']}' transition_in must be str"
                )
                assert len(section["transition_in"]) > 0, (
                    f"Genre '{genre}' section '{section['name']}' transition_in must not be empty"
                )

    def test_subgenre_overrides_have_new_fields(self):
        """Subgenre arrangement overrides also carry energy, roles, and transition_in."""
        for genre, subgenre in SUBGENRE_OVERRIDES:
            bp = get_blueprint(genre, subgenre=subgenre)
            sections = bp["arrangement"]["sections"]

            # All sections have energy and roles
            for section in sections:
                assert "energy" in section, (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' missing 'energy'"
                )
                assert isinstance(section["energy"], int), (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' energy must be int"
                )
                assert 1 <= section["energy"] <= 10, (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' energy out of range"
                )
                assert "roles" in section, (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' missing 'roles'"
                )
                assert isinstance(section["roles"], list), (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' roles must be list"
                )
                assert len(section["roles"]) > 0, (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' roles must not be empty"
                )

            # First section has no transition_in
            assert "transition_in" not in sections[0], (
                f"Subgenre '{genre}/{subgenre}' first section must NOT have 'transition_in'"
            )

            # Non-first sections have transition_in
            for section in sections[1:]:
                assert "transition_in" in section, (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' missing 'transition_in'"
                )
                assert isinstance(section["transition_in"], str), (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' transition_in must be str"
                )
                assert len(section["transition_in"]) > 0, (
                    f"Subgenre '{genre}/{subgenre}' section '{section['name']}' transition_in empty"
                )


class TestValidatorExtension:
    """Tests for validate_blueprint backward-compatibility and new field type checking."""

    def test_validator_accepts_sections_without_new_fields(self):
        """validate_blueprint still accepts sections with only name+bars (backward compat)."""
        bp = _make_valid_blueprint()
        validate_blueprint(bp)  # Should NOT raise

    def test_validator_accepts_sections_with_new_fields(self):
        """validate_blueprint accepts sections that include all new optional fields."""
        bp = _make_valid_blueprint()
        # Add new fields to both sections
        bp["arrangement"]["sections"][0]["energy"] = 2
        bp["arrangement"]["sections"][0]["roles"] = ["kick", "pad"]
        bp["arrangement"]["sections"][1]["energy"] = 8
        bp["arrangement"]["sections"][1]["roles"] = ["kick", "bass", "lead"]
        bp["arrangement"]["sections"][1]["transition_in"] = "filter sweep + riser"
        validate_blueprint(bp)  # Should NOT raise

    def test_validator_rejects_invalid_energy_type(self):
        """validate_blueprint raises ValueError for energy that is not an int."""
        bp = _make_valid_blueprint()
        bp["arrangement"]["sections"][0]["energy"] = "high"
        with pytest.raises(ValueError, match="energy must be int 1-10"):
            validate_blueprint(bp)

    def test_validator_rejects_energy_out_of_range_low(self):
        """validate_blueprint raises ValueError for energy=0 (below range)."""
        bp = _make_valid_blueprint()
        bp["arrangement"]["sections"][0]["energy"] = 0
        with pytest.raises(ValueError, match="energy must be int 1-10"):
            validate_blueprint(bp)

    def test_validator_rejects_energy_out_of_range_high(self):
        """validate_blueprint raises ValueError for energy=11 (above range)."""
        bp = _make_valid_blueprint()
        bp["arrangement"]["sections"][0]["energy"] = 11
        with pytest.raises(ValueError, match="energy must be int 1-10"):
            validate_blueprint(bp)

    def test_validator_rejects_invalid_roles_type(self):
        """validate_blueprint raises ValueError when roles is a string, not a list."""
        bp = _make_valid_blueprint()
        bp["arrangement"]["sections"][0]["roles"] = "kick"
        with pytest.raises(ValueError, match="roles must be a list"):
            validate_blueprint(bp)

    def test_validator_rejects_invalid_transition_in_type(self):
        """validate_blueprint raises ValueError when transition_in is not a string."""
        bp = _make_valid_blueprint()
        bp["arrangement"]["sections"][0]["transition_in"] = 123
        with pytest.raises(ValueError, match="transition_in must be a string"):
            validate_blueprint(bp)
