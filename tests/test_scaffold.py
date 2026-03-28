"""Tests for scaffold_arrangement MCP tool and helpers.

Tests cover:
- Role deduplication: flattening section roles into unique track names
- Bar-to-beat conversion: mapping 1-based bar numbers to beat positions
- scaffold_arrangement tool: end-to-end with mocked Ableton connection
"""

import pytest

from MCP_Server.tools.scaffold import _bar_to_beat, _deduplicate_roles


# ---------------------------------------------------------------------------
# Role deduplication tests
# ---------------------------------------------------------------------------

class TestRoleDeduplication:
    """Tests for _deduplicate_roles pure function."""

    def test_single_occurrence_per_role(self):
        """Each role appears in only one section -> no suffix."""
        sections = [
            {"name": "intro", "roles": ["kick", "bass"]},
            {"name": "drop", "roles": ["lead", "pad"]},
        ]
        result = _deduplicate_roles(sections)
        assert result == ["kick", "bass", "lead", "pad"]

    def test_multiple_occurrences(self):
        """Roles appearing in multiple sections get numbered suffixes."""
        sections = [
            {"name": "intro", "roles": ["lead", "pad"]},
            {"name": "drop", "roles": ["lead", "bass"]},
            {"name": "outro", "roles": ["lead", "pad"]},
        ]
        result = _deduplicate_roles(sections)
        # lead appears 3x, pad appears 2x, bass appears 1x
        assert result == ["lead", "lead 2", "lead 3", "pad", "pad 2", "bass"]

    def test_empty_sections(self):
        """Sections with empty roles produce no track names."""
        sections = [
            {"name": "intro", "roles": []},
            {"name": "drop", "roles": []},
        ]
        result = _deduplicate_roles(sections)
        assert result == []

    def test_preserves_plan_order(self):
        """First-seen role order from sections determines output order."""
        sections = [
            {"name": "intro", "roles": ["pad", "bass"]},
            {"name": "drop", "roles": ["kick", "lead"]},
        ]
        result = _deduplicate_roles(sections)
        assert result == ["pad", "bass", "kick", "lead"]


# ---------------------------------------------------------------------------
# Bar-to-beat conversion tests
# ---------------------------------------------------------------------------

class TestBarToBeat:
    """Tests for _bar_to_beat pure function."""

    def test_4_4_time(self):
        """4/4 time: 4 beats per bar."""
        beats_per_bar = 4.0  # 4 * (4/4)
        assert _bar_to_beat(1, beats_per_bar) == 0.0
        assert _bar_to_beat(5, beats_per_bar) == 16.0

    def test_3_4_time(self):
        """3/4 time: 3 beats per bar."""
        beats_per_bar = 3.0  # 3 * (4/4)
        assert _bar_to_beat(1, beats_per_bar) == 0.0
        assert _bar_to_beat(5, beats_per_bar) == 12.0

    def test_6_8_time(self):
        """6/8 time: 3 beats per bar (6 * 4/8 = 3)."""
        beats_per_bar = 3.0  # 6 * (4/8)
        assert _bar_to_beat(1, beats_per_bar) == 0.0
        assert _bar_to_beat(3, beats_per_bar) == 6.0
