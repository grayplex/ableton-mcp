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


class TestChordLibrary:
    """Unit tests for MCP_Server.theory.chords functions (no MCP, no mocks)."""

    # --- CHRD-01: build_chord ---

    def test_build_chord_major_triad(self):
        """C major triad at octave 4: midi [60, 64, 67]."""
        from MCP_Server.theory.chords import build_chord

        result = build_chord("C", "maj", 4)
        assert result["root"] == "C4"
        assert result["quality"] == "major"
        midis = [n["midi"] for n in result["notes"]]
        assert midis == [60, 64, 67]

    def test_build_chord_minor7(self):
        """A minor 7th at octave 3: root A3=57, midi [57, 60, 64, 67]."""
        from MCP_Server.theory.chords import build_chord

        result = build_chord("A", "min7", 3)
        midis = [n["midi"] for n in result["notes"]]
        assert midis == [57, 60, 64, 67]

    def test_build_chord_dom7(self):
        """G dominant 7th at octave 4: midi [67, 71, 74, 77]."""
        from MCP_Server.theory.chords import build_chord

        result = build_chord("G", "dom7", 4)
        midis = [n["midi"] for n in result["notes"]]
        assert midis == [67, 71, 74, 77]

    def test_build_chord_augmented(self):
        """F# augmented triad has correct intervals (4, 4 semitones)."""
        from MCP_Server.theory.chords import build_chord

        result = build_chord("F#", "aug", 4)
        midis = [n["midi"] for n in result["notes"]]
        # F#4=66, A#4=70, C##5=D5=74 -- augmented intervals: root, M3, A5
        assert len(midis) == 3
        assert midis[1] - midis[0] == 4  # major third
        assert midis[2] - midis[1] == 4  # major third

    def test_build_chord_sus4(self):
        """C sus4 at octave 4: midi [60, 65, 67]."""
        from MCP_Server.theory.chords import build_chord

        result = build_chord("C", "sus4", 4)
        midis = [n["midi"] for n in result["notes"]]
        assert midis == [60, 65, 67]

    def test_build_chord_dim7(self):
        """C diminished 7th has correct interval pattern (3, 3, 3 semitones)."""
        from MCP_Server.theory.chords import build_chord

        result = build_chord("C", "dim7", 4)
        midis = [n["midi"] for n in result["notes"]]
        assert len(midis) == 4
        for i in range(1, len(midis)):
            assert midis[i] - midis[i - 1] == 3

    def test_build_chord_invalid_root(self):
        """Invalid root raises ValueError."""
        from MCP_Server.theory.chords import build_chord

        with pytest.raises(ValueError):
            build_chord("X", "maj", 4)

    def test_build_chord_invalid_quality(self):
        """Invalid quality raises ValueError."""
        from MCP_Server.theory.chords import build_chord

        with pytest.raises(ValueError):
            build_chord("C", "invalidquality", 4)

    def test_build_chord_rich_note_objects(self):
        """Each note in result has 'midi' and 'name' keys."""
        from MCP_Server.theory.chords import build_chord

        result = build_chord("C", "maj", 4)
        for note in result["notes"]:
            assert "midi" in note
            assert "name" in note
            assert isinstance(note["midi"], int)
            assert isinstance(note["name"], str)

    # --- CHRD-02: get_chord_inversions ---

    def test_inversions_count_triad(self):
        """C major triad has 3 inversions (root, 1st, 2nd)."""
        from MCP_Server.theory.chords import get_chord_inversions

        result = get_chord_inversions("C", "maj", 4)
        assert len(result) == 3

    def test_inversions_count_7th(self):
        """Cmaj7 has 4 inversions."""
        from MCP_Server.theory.chords import get_chord_inversions

        result = get_chord_inversions("C", "maj7", 4)
        assert len(result) == 4

    def test_inversions_root_position(self):
        """Root position of C major: midi [60, 64, 67]."""
        from MCP_Server.theory.chords import get_chord_inversions

        result = get_chord_inversions("C", "maj", 4)
        midis = [n["midi"] for n in result[0]["notes"]]
        assert midis == [60, 64, 67]
        assert result[0]["inversion"] == 0

    def test_inversions_first_inversion(self):
        """1st inversion of C major: midi [64, 67, 72] (C moved up)."""
        from MCP_Server.theory.chords import get_chord_inversions

        result = get_chord_inversions("C", "maj", 4)
        midis = [n["midi"] for n in result[1]["notes"]]
        assert midis == [64, 67, 72]
        assert result[1]["inversion"] == 1

    def test_inversions_second_inversion(self):
        """2nd inversion of C major: midi [67, 72, 76] (C,E moved up)."""
        from MCP_Server.theory.chords import get_chord_inversions

        result = get_chord_inversions("C", "maj", 4)
        midis = [n["midi"] for n in result[2]["notes"]]
        assert midis == [67, 72, 76]
        assert result[2]["inversion"] == 2

    def test_inversions_have_bass_note(self):
        """Each inversion dict has bass_note and notes fields."""
        from MCP_Server.theory.chords import get_chord_inversions

        result = get_chord_inversions("C", "maj", 4)
        for inv in result:
            assert "inversion" in inv
            assert "bass_note" in inv
            assert "notes" in inv

    # --- CHRD-03: get_chord_voicings ---

    def test_voicings_keys(self):
        """Voicings dict has close, open, drop2, drop3 keys."""
        from MCP_Server.theory.chords import get_chord_voicings

        result = get_chord_voicings("C", "maj7", 4)
        assert "close" in result
        assert "open" in result
        assert "drop2" in result
        assert "drop3" in result

    def test_voicings_close(self):
        """Close voicing of Cmaj7: midi [60, 64, 67, 71]."""
        from MCP_Server.theory.chords import get_chord_voicings

        result = get_chord_voicings("C", "maj7", 4)
        midis = [n["midi"] for n in result["close"]]
        assert midis == [60, 64, 67, 71]

    def test_voicings_drop2(self):
        """Drop-2 of Cmaj7: 2nd from top (G4=67) dropped to G3=55."""
        from MCP_Server.theory.chords import get_chord_voicings

        result = get_chord_voicings("C", "maj7", 4)
        midis = [n["midi"] for n in result["drop2"]]
        assert sorted(midis) == [55, 60, 64, 71]

    def test_voicings_drop3(self):
        """Drop-3 of Cmaj7: 3rd from top (E4=64) dropped to E3=52."""
        from MCP_Server.theory.chords import get_chord_voicings

        result = get_chord_voicings("C", "maj7", 4)
        midis = [n["midi"] for n in result["drop3"]]
        assert sorted(midis) == [52, 60, 67, 71]

    def test_voicings_triad_drop3_null(self):
        """Triad voicing: drop3 is null (needs 4+ notes)."""
        from MCP_Server.theory.chords import get_chord_voicings

        result = get_chord_voicings("C", "maj", 4)
        assert result["drop3"] is None

    # --- CHRD-04: identify_chord ---

    def test_identify_root_position(self):
        """identify_chord([60,64,67]) top candidate is C major, root position."""
        from MCP_Server.theory.chords import identify_chord

        result = identify_chord([60, 64, 67])
        assert len(result) >= 1
        top = result[0]
        assert "C" in top["root"]
        assert top["inversion"] == 0

    def test_identify_inversion(self):
        """identify_chord([64,67,72]) shows inversion=1."""
        from MCP_Server.theory.chords import identify_chord

        result = identify_chord([64, 67, 72])
        top = result[0]
        assert top["inversion"] == 1

    def test_identify_dyad(self):
        """identify_chord([60,67]) returns at least 1 candidate."""
        from MCP_Server.theory.chords import identify_chord

        result = identify_chord([60, 67])
        assert len(result) >= 1

    def test_identify_ambiguous(self):
        """identify_chord([57,60,64,67]) returns multiple candidates (Am7 vs C6)."""
        from MCP_Server.theory.chords import identify_chord

        result = identify_chord([57, 60, 64, 67])
        assert len(result) >= 2

    def test_identify_has_confidence(self):
        """Each candidate has confidence score."""
        from MCP_Server.theory.chords import identify_chord

        result = identify_chord([60, 64, 67])
        for candidate in result:
            assert "confidence" in candidate
            assert isinstance(candidate["confidence"], float)

    def test_identify_max_three_candidates(self):
        """Returns at most 3 candidates."""
        from MCP_Server.theory.chords import identify_chord

        result = identify_chord([60, 64, 67])
        assert len(result) <= 3

    # --- CHRD-05: get_diatonic_chords ---

    def test_diatonic_major_triads(self):
        """C major diatonic triads: 7 chords."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "major", 4)
        assert len(result["triads"]) == 7

    def test_diatonic_major_first_chord(self):
        """C major triad[0]: roman='I', quality contains 'major', root='C'."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "major", 4)
        first = result["triads"][0]
        assert first["roman"] == "I"
        assert "major" in first["quality"].lower()
        assert first["root"] == "C"
        midis = [n["midi"] for n in first["notes"]]
        assert midis == [60, 64, 67]

    def test_diatonic_major_second_chord(self):
        """C major triad[1]: roman='ii', quality contains 'minor'."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "major", 4)
        second = result["triads"][1]
        assert second["roman"] == "ii"
        assert "minor" in second["quality"].lower()
        assert second["root"] == "D"

    def test_diatonic_major_seventh_chord(self):
        """C major triad[6]: roman='viio', quality contains 'diminished'."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "major", 4)
        seventh = result["triads"][6]
        assert seventh["roman"] == "viio"
        assert "diminished" in seventh["quality"].lower()
        assert seventh["root"] == "B"

    def test_diatonic_minor_triads(self):
        """A minor diatonic triads: 7 chords, first is 'i' minor."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("A", "minor", 4)
        assert len(result["triads"]) == 7
        first = result["triads"][0]
        assert first["roman"] == "i"
        assert "minor" in first["quality"].lower()

    def test_diatonic_sevenths(self):
        """C major diatonic 7ths: 7 chords."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "major", 4)
        assert len(result["sevenths"]) == 7

    def test_diatonic_has_degree(self):
        """Each diatonic chord has degree, roman, quality, root, notes."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "major", 4)
        for chord_dict in result["triads"]:
            assert "degree" in chord_dict
            assert "roman" in chord_dict
            assert "quality" in chord_dict
            assert "root" in chord_dict
            assert "notes" in chord_dict

    def test_diatonic_invalid_scale_type(self):
        """Invalid scale_type raises ValueError."""
        from MCP_Server.theory.chords import get_diatonic_chords

        with pytest.raises(ValueError):
            get_diatonic_chords("C", "pentatonic", 4)


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


class TestChordTools:
    """Integration tests: chord MCP tools via mcp_server fixture."""

    @pytest.mark.asyncio
    async def test_chord_tools_registered(self, mcp_server):
        """All 5 chord tools are registered."""
        tools = await mcp_server.list_tools()
        names = {t.name for t in tools}
        for tool in ["build_chord", "get_chord_inversions", "get_chord_voicings", "identify_chord", "get_diatonic_chords"]:
            assert tool in names, f"{tool} not registered"

    @pytest.mark.asyncio
    async def test_build_chord_major(self, mcp_server):
        """build_chord C major at octave 4."""
        result = await mcp_server.call_tool("build_chord", {"root": "C", "quality": "maj", "octave": 4})
        data = json.loads(result[0][0].text)
        midi_values = [n["midi"] for n in data["notes"]]
        assert midi_values == [60, 64, 67]

    @pytest.mark.asyncio
    async def test_build_chord_min7(self, mcp_server):
        """build_chord A minor 7th at octave 3."""
        result = await mcp_server.call_tool("build_chord", {"root": "A", "quality": "min7", "octave": 3})
        data = json.loads(result[0][0].text)
        midi_values = [n["midi"] for n in data["notes"]]
        assert midi_values == [57, 60, 64, 67]

    @pytest.mark.asyncio
    async def test_build_chord_invalid_quality(self, mcp_server):
        """build_chord with invalid quality returns error."""
        result = await mcp_server.call_tool("build_chord", {"root": "C", "quality": "notachord"})
        text = result[0][0].text
        assert "Error" in text

    @pytest.mark.asyncio
    async def test_inversions_triad(self, mcp_server):
        """get_chord_inversions for C major triad returns 3 inversions."""
        result = await mcp_server.call_tool("get_chord_inversions", {"root": "C", "quality": "maj", "octave": 4})
        data = json.loads(result[0][0].text)
        assert len(data) == 3
        assert data[0]["inversion"] == 0
        assert data[1]["inversion"] == 1
        assert data[2]["inversion"] == 2

    @pytest.mark.asyncio
    async def test_voicings_maj7(self, mcp_server):
        """get_chord_voicings for Cmaj7 returns all 4 voicing types."""
        result = await mcp_server.call_tool("get_chord_voicings", {"root": "C", "quality": "maj7", "octave": 4})
        data = json.loads(result[0][0].text)
        assert "close" in data
        assert "open" in data
        assert "drop2" in data
        assert "drop3" in data

    @pytest.mark.asyncio
    async def test_identify_c_major(self, mcp_server):
        """identify_chord [60,64,67] top candidate is C major."""
        result = await mcp_server.call_tool("identify_chord", {"midi_pitches": [60, 64, 67]})
        data = json.loads(result[0][0].text)
        assert len(data) >= 1
        assert "C" in data[0]["root"]
        assert data[0]["inversion"] == 0

    @pytest.mark.asyncio
    async def test_identify_too_few_pitches(self, mcp_server):
        """identify_chord with 1 pitch returns error."""
        result = await mcp_server.call_tool("identify_chord", {"midi_pitches": [60]})
        text = result[0][0].text
        assert "Error" in text or "at least 2" in text.lower()

    @pytest.mark.asyncio
    async def test_identify_out_of_range(self, mcp_server):
        """identify_chord with MIDI > 127 returns error."""
        result = await mcp_server.call_tool("identify_chord", {"midi_pitches": [60, 200]})
        text = result[0][0].text
        assert "Error" in text or "out of range" in text.lower()

    @pytest.mark.asyncio
    async def test_diatonic_c_major(self, mcp_server):
        """get_diatonic_chords C major returns 7 triads and 7 sevenths."""
        result = await mcp_server.call_tool("get_diatonic_chords", {"key_name": "C", "scale_type": "major", "octave": 4})
        data = json.loads(result[0][0].text)
        assert len(data["triads"]) == 7
        assert len(data["sevenths"]) == 7
        assert data["triads"][0]["roman"] == "I"

    @pytest.mark.asyncio
    async def test_diatonic_a_minor(self, mcp_server):
        """get_diatonic_chords A minor returns correct Roman numerals."""
        result = await mcp_server.call_tool("get_diatonic_chords", {"key_name": "A", "scale_type": "minor", "octave": 4})
        data = json.loads(result[0][0].text)
        assert data["triads"][0]["roman"] == "i"
        assert len(data["triads"]) == 7
