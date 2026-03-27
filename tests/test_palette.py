"""Integration tests for get_genre_palette MCP tool.

Exercises real theory engine + genre catalog end-to-end with no mocking (D-09).
"""

import json
import re

import pytest

from MCP_Server.tools.genres import get_genre_palette


class TestPaletteBridge:
    """Integration tests for the palette bridge tool."""

    # ------------------------------------------------------------------
    # Structure
    # ------------------------------------------------------------------

    def test_house_palette_structure(self):
        """Palette result has all required top-level keys."""
        raw = get_genre_palette(None, "house", "C")
        result = json.loads(raw)
        assert result["genre"] == "house"
        assert result["key"] == "C"
        for key in ("scales", "chord_types", "progressions"):
            assert key in result, f"Missing key: {key}"

    # ------------------------------------------------------------------
    # Scales
    # ------------------------------------------------------------------

    def test_house_palette_scales(self):
        """House palette in C contains all four expected scales."""
        result = json.loads(get_genre_palette(None, "house", "C"))
        expected = [
            "C natural_minor",
            "C dorian",
            "C mixolydian",
            "C major",
        ]
        for s in expected:
            assert s in result["scales"], f"Missing scale: {s}"

    def test_palette_scales_format(self):
        """Each scale follows '{key} {scale_name}' format."""
        result = json.loads(get_genre_palette(None, "house", "C"))
        for s in result["scales"]:
            assert s.startswith("C "), f"Scale not prefixed with key: {s}"
            parts = s.split(" ", 1)
            assert len(parts) == 2, f"Scale missing name part: {s}"

    # ------------------------------------------------------------------
    # Chord types
    # ------------------------------------------------------------------

    def test_house_palette_chord_types(self):
        """House palette in C contains all six expected chord types."""
        result = json.loads(get_genre_palette(None, "house", "C"))
        expected = ["Cmin7", "Cmaj7", "Cdom7", "Cmin9", "Csus4", "Cadd9"]
        for ct in expected:
            assert ct in result["chord_types"], f"Missing chord type: {ct}"

    def test_palette_chord_types_format(self):
        """Each chord type follows '{key}{quality}' format."""
        result = json.loads(get_genre_palette(None, "house", "C"))
        for ct in result["chord_types"]:
            assert ct.startswith("C"), f"Chord not prefixed with key: {ct}"

    # ------------------------------------------------------------------
    # Progressions
    # ------------------------------------------------------------------

    def test_house_palette_progressions_resolved(self):
        """Progressions are lists of chord name strings, not Roman numerals."""
        result = json.loads(get_genre_palette(None, "house", "C"))
        assert isinstance(result["progressions"], list)
        assert len(result["progressions"]) > 0
        roman_pattern = re.compile(r"^[ivIV]+$")
        for prog in result["progressions"]:
            assert isinstance(prog, list)
            for chord_name in prog:
                assert isinstance(chord_name, str)
                assert not roman_pattern.match(chord_name), (
                    f"Unresolved Roman numeral found: {chord_name}"
                )

    # ------------------------------------------------------------------
    # Different keys
    # ------------------------------------------------------------------

    def test_palette_different_key(self):
        """Palette in F# produces F#-prefixed names."""
        result = json.loads(get_genre_palette(None, "house", "F#"))
        for s in result["scales"]:
            assert s.startswith("F#"), f"Scale not in F#: {s}"
        for ct in result["chord_types"]:
            assert ct.startswith("F#"), f"Chord not in F#: {ct}"

    # ------------------------------------------------------------------
    # Multiple genres
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("genre", ["techno", "ambient", "drum_and_bass"])
    def test_palette_multiple_genres(self, genre):
        """Palette works for genres beyond house."""
        result = json.loads(get_genre_palette(None, genre, "A"))
        for key in ("genre", "key", "scales", "chord_types", "progressions"):
            assert key in result, f"Missing key '{key}' for genre '{genre}'"
        assert len(result["scales"]) > 0
        assert len(result["chord_types"]) > 0
        assert len(result["progressions"]) > 0

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_palette_invalid_genre(self):
        """Invalid genre returns an error string."""
        raw = get_genre_palette(None, "nonexistent_genre", "C")
        assert "Error" in raw or "error" in raw
        assert "Genre not found" in raw

    # ------------------------------------------------------------------
    # Graceful degradation
    # ------------------------------------------------------------------

    def test_palette_no_unresolved_for_valid_genres(self):
        """House palette has no unresolved items (all types are valid)."""
        result = json.loads(get_genre_palette(None, "house", "C"))
        assert "unresolved" not in result
