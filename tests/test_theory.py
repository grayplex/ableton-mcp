"""Tests for theory library (unit) and theory MCP tools (integration)."""

import json

import pytest

from MCP_Server.theory import midi_to_note, note_to_midi


class TestPitchLibrary:
    """Unit tests for MCP_Server.theory.pitch functions (no MCP, no mocks)."""

    def test_midi_to_note_middle_c(self):
        result = midi_to_note(60)
        assert result == {"midi": 60, "name": "C4", "octave": 4, "pitch_class": "C"}

    def test_note_to_midi_middle_c(self):
        result = note_to_midi("C4")
        assert result == {"name": "C4", "midi": 60}

    def test_roundtrip_all_128(self):
        """Every MIDI value 0-127 roundtrips through midi_to_note -> note_to_midi."""
        for i in range(128):
            note_info = midi_to_note(i)
            back = note_to_midi(note_info["name"])
            assert back["midi"] == i, f"Roundtrip failed for MIDI {i}: {note_info['name']} -> {back['midi']}"

    def test_sharps_default(self):
        """Black keys default to sharp spelling (not flats)."""
        assert midi_to_note(61)["name"] == "C#4"
        assert midi_to_note(63)["name"] == "D#4"
        assert midi_to_note(66)["name"] == "F#4"
        assert midi_to_note(68)["name"] == "G#4"
        assert midi_to_note(70)["name"] == "A#4"

    def test_key_aware_enharmonic(self):
        """With key_context='Ab major', pitch class 61 spelled as Db, not C#."""
        result = midi_to_note(61, key_context="Ab major")
        assert result["pitch_class"].startswith("D"), f"Expected Db pitch class, got {result['pitch_class']}"

    def test_boundary_midi_0(self):
        """MIDI 0 is C in octave -1."""
        result = midi_to_note(0)
        assert result["octave"] == -1
        assert result["pitch_class"] == "C"

    def test_boundary_midi_127(self):
        """MIDI 127 is G9."""
        result = midi_to_note(127)
        assert result["midi"] == 127
        assert result["pitch_class"] == "G"
        assert result["octave"] == 9

    def test_note_formats(self):
        """Various note name formats resolve to correct MIDI values."""
        assert note_to_midi("Eb3")["midi"] == 51
        assert note_to_midi("F#5")["midi"] == 78
        assert note_to_midi("Bb2")["midi"] == 46


class TestTheoryTools:
    """Integration tests: MCP tool calls via mcp_server fixture (async, no mock_connection)."""

    @pytest.mark.asyncio
    async def test_tool_registration(self, mcp_server):
        """Both theory tools are registered."""
        tools = await mcp_server.list_tools()
        names = {t.name for t in tools}
        assert "midi_to_note" in names, f"midi_to_note not in {names}"
        assert "note_to_midi" in names, f"note_to_midi not in {names}"

    @pytest.mark.asyncio
    async def test_midi_to_note_tool(self, mcp_server):
        """midi_to_note tool returns JSON with C4 for MIDI 60."""
        result = await mcp_server.call_tool("midi_to_note", {"midi_number": 60})
        text = result[0][0].text
        data = json.loads(text)
        assert data["name"] == "C4"
        assert data["midi"] == 60
        assert data["octave"] == 4
        assert data["pitch_class"] == "C"

    @pytest.mark.asyncio
    async def test_note_to_midi_tool(self, mcp_server):
        """note_to_midi tool returns JSON with midi=60 for C4."""
        result = await mcp_server.call_tool("note_to_midi", {"note_name": "C4"})
        text = result[0][0].text
        data = json.loads(text)
        assert data["midi"] == 60
        assert data["name"] == "C4"

    @pytest.mark.asyncio
    async def test_midi_to_note_with_key_context(self, mcp_server):
        """midi_to_note with key_context returns flat spelling."""
        result = await mcp_server.call_tool(
            "midi_to_note", {"midi_number": 61, "key_context": "Ab major"}
        )
        text = result[0][0].text
        data = json.loads(text)
        assert "D" in data["pitch_class"], f"Expected Db spelling, got {data['pitch_class']}"

    @pytest.mark.asyncio
    async def test_midi_out_of_range_low(self, mcp_server):
        """midi_to_note with -1 returns error, not crash."""
        result = await mcp_server.call_tool("midi_to_note", {"midi_number": -1})
        text = result[0][0].text
        assert "Error" in text or "out of range" in text.lower(), f"Expected error message, got: {text}"

    @pytest.mark.asyncio
    async def test_midi_out_of_range_high(self, mcp_server):
        """midi_to_note with 128 returns error, not crash."""
        result = await mcp_server.call_tool("midi_to_note", {"midi_number": 128})
        text = result[0][0].text
        assert "out of range" in text.lower(), f"Expected 'out of range' in: {text}"

    @pytest.mark.asyncio
    async def test_invalid_note_name(self, mcp_server):
        """note_to_midi with invalid name returns error, not crash."""
        result = await mcp_server.call_tool("note_to_midi", {"note_name": "XYZ"})
        text = result[0][0].text
        assert "Error" in text, f"Expected error message, got: {text}"
