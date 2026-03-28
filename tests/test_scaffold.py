"""Tests for scaffold_arrangement MCP tool and helpers.

Tests cover:
- Role deduplication: flattening section roles into unique track names
- Bar-to-beat conversion: mapping 1-based bar numbers to beat positions
- scaffold_arrangement tool: end-to-end with mocked Ableton connection
"""

import json

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


# ---------------------------------------------------------------------------
# scaffold_arrangement MCP tool tests
# ---------------------------------------------------------------------------

def _mock_send_command_factory(time_sig=(4, 4), track_count=0):
    """Return a side_effect function for mock_connection.send_command.

    Handles get_session_info, create_locator_at, and scaffold_tracks
    with configurable time signature.
    """
    created_tracks = []

    def side_effect(cmd, params=None):
        if cmd == "get_session_info":
            return {
                "signature_numerator": time_sig[0],
                "signature_denominator": time_sig[1],
            }
        elif cmd == "create_locator_at":
            return {
                "name": params["name"],
                "beat_position": params["beat_position"],
                "existed": False,
            }
        elif cmd == "scaffold_tracks":
            names = params["track_names"]
            for i, n in enumerate(names):
                created_tracks.append({"index": track_count + i, "name": n})
            return {"created_tracks": created_tracks, "count": len(names)}
        return {}

    return side_effect


class TestScaffoldArrangement:
    """Tests for scaffold_arrangement MCP tool with mocked Ableton connection."""

    async def test_creates_locators_and_tracks(self, mcp_server, mock_connection):
        """scaffold_arrangement creates locators for each section and tracks for deduplicated roles."""
        mock_connection.send_command.side_effect = _mock_send_command_factory()

        plan = {
            "genre": "house",
            "key": "Am",
            "bpm": 125,
            "time_signature": "4/4",
            "sections": [
                {"name": "intro", "bar_start": 1, "bars": 16, "roles": ["kick", "bass"]},
                {"name": "drop", "bar_start": 17, "bars": 32, "roles": ["kick", "lead"]},
            ],
        }
        result = await mcp_server.call_tool("scaffold_arrangement", {"plan": plan})
        text = result[0][0].text
        parsed = json.loads(text)

        assert parsed["locators_created"] == 2
        assert parsed["tracks_created"] == 4
        # kick in 2 sections -> kick, kick 2; bass 1x; lead 1x = 4 tracks
        assert parsed["track_names"] == ["kick", "kick 2", "bass", "lead"]

    async def test_bar_to_beat_4_4(self, mcp_server, mock_connection):
        """4/4 time: bar_start=1 -> beat 0.0, bar_start=5 -> beat 16.0."""
        calls = []

        def capture_side_effect(cmd, params=None):
            if cmd == "create_locator_at":
                calls.append(params)
            return _mock_send_command_factory()(cmd, params)

        mock_connection.send_command.side_effect = capture_side_effect

        plan = {
            "sections": [
                {"name": "intro", "bar_start": 1, "bars": 16, "roles": []},
                {"name": "drop", "bar_start": 5, "bars": 32, "roles": []},
            ],
        }
        await mcp_server.call_tool("scaffold_arrangement", {"plan": plan})

        locator_calls = [c for c in calls if c is not None]
        assert locator_calls[0]["beat_position"] == 0.0
        assert locator_calls[1]["beat_position"] == 16.0

    async def test_bar_to_beat_3_4(self, mcp_server, mock_connection):
        """3/4 time: beat positions use beats_per_bar=3."""
        calls = []

        def capture_side_effect(cmd, params=None):
            if cmd == "create_locator_at":
                calls.append(params)
            return _mock_send_command_factory(time_sig=(3, 4))(cmd, params)

        mock_connection.send_command.side_effect = capture_side_effect

        plan = {
            "sections": [
                {"name": "intro", "bar_start": 1, "bars": 8, "roles": []},
                {"name": "verse", "bar_start": 5, "bars": 8, "roles": []},
            ],
        }
        await mcp_server.call_tool("scaffold_arrangement", {"plan": plan})

        locator_calls = [c for c in calls if c is not None]
        assert locator_calls[0]["beat_position"] == 0.0
        assert locator_calls[1]["beat_position"] == 12.0  # (5-1)*3

    async def test_missing_sections_key(self, mcp_server, mock_connection):
        """Plan without 'sections' returns format_error."""
        plan = {"genre": "house", "key": "Am", "bpm": 125}
        result = await mcp_server.call_tool("scaffold_arrangement", {"plan": plan})
        text = result[0][0].text
        assert "Error" in text
        assert "sections" in text.lower()

    async def test_partial_failure_reports_error(self, mcp_server, mock_connection):
        """If one locator creation fails, result contains locator_errors."""
        call_count = [0]

        def failing_side_effect(cmd, params=None):
            if cmd == "create_locator_at":
                call_count[0] += 1
                if call_count[0] == 2:
                    raise RuntimeError("Locator creation failed")
            return _mock_send_command_factory()(cmd, params)

        mock_connection.send_command.side_effect = failing_side_effect

        plan = {
            "sections": [
                {"name": "intro", "bar_start": 1, "bars": 16, "roles": []},
                {"name": "drop", "bar_start": 17, "bars": 32, "roles": []},
            ],
        }
        result = await mcp_server.call_tool("scaffold_arrangement", {"plan": plan})
        text = result[0][0].text
        parsed = json.loads(text)

        assert parsed["locators_created"] == 1
        assert len(parsed["locator_errors"]) == 1
        assert parsed["locator_errors"][0]["section"] == "drop"


async def test_scaffold_tools_registered(mcp_server):
    """scaffold_arrangement is registered as an MCP tool."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "scaffold_arrangement" in names
