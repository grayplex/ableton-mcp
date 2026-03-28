"""Tests for execution tools: section checklists and arrangement progress.

Tests cover:
- get_section_checklist: role-to-track mapping, device status, edge cases
- get_arrangement_progress: empty track detection, all-loaded case
- Tool registration
"""

import json

import pytest

from MCP_Server.tools.scaffold import _deduplicate_roles


# ---------------------------------------------------------------------------
# Mock factory for get_arrangement_state with device presence
# ---------------------------------------------------------------------------

def _mock_execution_factory(tracks=None, cue_points=None, song_length=256.0, time_sig=(4, 4)):
    """Return a side_effect for mocking get_arrangement_state with device info."""
    if tracks is None:
        tracks = [
            {"name": "kick", "has_devices": True},
            {"name": "bass", "has_devices": False},
            {"name": "lead", "has_devices": True},
        ]
    if cue_points is None:
        cue_points = []

    def side_effect(cmd, params=None):
        if cmd == "get_arrangement_state":
            return {
                "cue_points": cue_points,
                "tracks": tracks,
                "song_length": song_length,
                "signature_numerator": time_sig[0],
                "signature_denominator": time_sig[1],
            }
        return {}

    return side_effect


# ---------------------------------------------------------------------------
# get_section_checklist tests
# ---------------------------------------------------------------------------

class TestSectionChecklist:
    """Tests for get_section_checklist MCP tool."""

    async def test_returns_roles_with_status(self, mcp_server, mock_connection):
        """Returns per-role status for a named section."""
        mock_connection.send_command.side_effect = _mock_execution_factory(
            tracks=[
                {"name": "kick", "has_devices": True},
                {"name": "bass", "has_devices": False},
            ]
        )
        plan = {
            "sections": [
                {"name": "intro", "roles": ["kick", "bass"]},
            ]
        }
        result = await mcp_server.call_tool("get_section_checklist", {
            "plan": plan, "section_name": "intro"
        })
        parsed = json.loads(result[0][0].text)

        assert parsed["section"] == "intro"
        assert len(parsed["roles"]) == 2
        assert parsed["roles"][0] == {"role": "kick", "track_name": "kick", "status": "done"}
        assert parsed["roles"][1] == {"role": "bass", "track_name": "bass", "status": "pending"}
        assert parsed["pending_count"] == 1
        assert parsed["total_count"] == 2

    async def test_role_to_track_mapping_dedup(self, mcp_server, mock_connection):
        """Roles in multiple sections get correct numbered track names."""
        mock_connection.send_command.side_effect = _mock_execution_factory(
            tracks=[
                {"name": "lead", "has_devices": True},
                {"name": "lead 2", "has_devices": False},
                {"name": "lead 3", "has_devices": True},
                {"name": "pad", "has_devices": True},
                {"name": "pad 2", "has_devices": False},
                {"name": "bass", "has_devices": True},
            ]
        )
        plan = {
            "sections": [
                {"name": "intro", "roles": ["lead", "pad"]},
                {"name": "drop", "roles": ["lead", "bass"]},
                {"name": "outro", "roles": ["lead", "pad"]},
            ]
        }
        # Check the "drop" section: lead appears in intro(1st), drop(2nd) -> "lead 2"
        result = await mcp_server.call_tool("get_section_checklist", {
            "plan": plan, "section_name": "drop"
        })
        parsed = json.loads(result[0][0].text)

        assert parsed["section"] == "drop"
        role_map = {r["role"]: r["track_name"] for r in parsed["roles"]}
        assert role_map["lead"] == "lead 2"
        assert role_map["bass"] == "bass"

    async def test_section_not_found(self, mcp_server, mock_connection):
        """Nonexistent section_name returns format_error."""
        plan = {
            "sections": [
                {"name": "intro", "roles": ["kick"]},
            ]
        }
        result = await mcp_server.call_tool("get_section_checklist", {
            "plan": plan, "section_name": "nonexistent"
        })
        text = result[0][0].text
        assert "Error" in text
        assert "nonexistent" in text

    async def test_track_not_found(self, mcp_server, mock_connection):
        """Role whose track was renamed in Ableton gets status 'not_found'."""
        mock_connection.send_command.side_effect = _mock_execution_factory(
            tracks=[
                {"name": "kick", "has_devices": True},
                # "bass" track is missing (user renamed it)
            ]
        )
        plan = {
            "sections": [
                {"name": "intro", "roles": ["kick", "bass"]},
            ]
        }
        result = await mcp_server.call_tool("get_section_checklist", {
            "plan": plan, "section_name": "intro"
        })
        parsed = json.loads(result[0][0].text)

        bass_role = [r for r in parsed["roles"] if r["role"] == "bass"][0]
        assert bass_role["status"] == "not_found"

    async def test_dedup_within_section(self, mcp_server, mock_connection):
        """Duplicate roles within a single section are deduplicated."""
        mock_connection.send_command.side_effect = _mock_execution_factory(
            tracks=[{"name": "lead", "has_devices": True}]
        )
        plan = {
            "sections": [
                {"name": "intro", "roles": ["lead", "lead"]},  # duplicate
            ]
        }
        result = await mcp_server.call_tool("get_section_checklist", {
            "plan": plan, "section_name": "intro"
        })
        parsed = json.loads(result[0][0].text)

        # Should only have one "lead" entry, not two
        assert len(parsed["roles"]) == 1


# ---------------------------------------------------------------------------
# get_arrangement_progress tests
# ---------------------------------------------------------------------------

class TestArrangementProgress:
    """Tests for get_arrangement_progress MCP tool."""

    async def test_returns_empty_tracks(self, mcp_server, mock_connection):
        """Returns only tracks with no devices loaded."""
        mock_connection.send_command.side_effect = _mock_execution_factory(
            tracks=[
                {"name": "kick", "has_devices": True},
                {"name": "bass", "has_devices": False},
                {"name": "lead", "has_devices": True},
                {"name": "pad", "has_devices": False},
            ]
        )
        result = await mcp_server.call_tool("get_arrangement_progress", {})
        parsed = json.loads(result[0][0].text)

        assert parsed["empty_tracks"] == ["bass", "pad"]
        assert parsed["total_tracks"] == 4
        assert parsed["empty_count"] == 2

    async def test_all_tracks_loaded(self, mcp_server, mock_connection):
        """All tracks have instruments -> empty list."""
        mock_connection.send_command.side_effect = _mock_execution_factory(
            tracks=[
                {"name": "kick", "has_devices": True},
                {"name": "bass", "has_devices": True},
            ]
        )
        result = await mcp_server.call_tool("get_arrangement_progress", {})
        parsed = json.loads(result[0][0].text)

        assert parsed["empty_tracks"] == []
        assert parsed["total_tracks"] == 2
        assert parsed["empty_count"] == 0

    async def test_no_tracks(self, mcp_server, mock_connection):
        """Empty session -> zero tracks."""
        mock_connection.send_command.side_effect = _mock_execution_factory(tracks=[])
        result = await mcp_server.call_tool("get_arrangement_progress", {})
        parsed = json.loads(result[0][0].text)

        assert parsed["empty_tracks"] == []
        assert parsed["total_tracks"] == 0
        assert parsed["empty_count"] == 0


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

async def test_execution_tools_registered(mcp_server):
    """Both execution tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_section_checklist" in names
    assert "get_arrangement_progress" in names
