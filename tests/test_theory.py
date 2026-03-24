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

    # --- Harmonic minor diatonic chords ---

    def test_diatonic_harmonic_minor_triads(self):
        """C harmonic minor diatonic triads: 7 chords."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "harmonic_minor", 4)
        assert len(result["triads"]) == 7

    def test_diatonic_harmonic_minor_augmented_III(self):
        """C harmonic minor triad degree 3 has augmented quality."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "harmonic_minor", 4)
        third = result["triads"][2]  # degree 3, index 2
        assert "III" in third["roman"]
        assert "augmented" in third["quality"].lower()

    def test_diatonic_harmonic_minor_major_V(self):
        """C harmonic minor triad degree 5 has major quality."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "harmonic_minor", 4)
        fifth = result["triads"][4]  # degree 5, index 4
        assert fifth["roman"] == "V"
        assert "major" in fifth["quality"].lower()

    def test_diatonic_harmonic_minor_sevenths(self):
        """C harmonic minor has 7 seventh chords."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "harmonic_minor", 4)
        assert len(result["sevenths"]) == 7

    # --- Melodic minor diatonic chords ---

    def test_diatonic_melodic_minor_triads(self):
        """C melodic minor diatonic triads: 7 chords."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "melodic_minor", 4)
        assert len(result["triads"]) == 7

    def test_diatonic_melodic_minor_major_IV(self):
        """C melodic minor triad degree 4 has major quality."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "melodic_minor", 4)
        fourth = result["triads"][3]  # degree 4, index 3
        assert fourth["roman"] == "IV"
        assert "major" in fourth["quality"].lower()

    def test_diatonic_melodic_minor_sevenths(self):
        """C melodic minor has 7 seventh chords."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "melodic_minor", 4)
        assert len(result["sevenths"]) == 7

    # --- Regression tests ---

    def test_diatonic_major_still_works(self):
        """get_diatonic_chords major still works after extension."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("C", "major", 4)
        assert len(result["triads"]) == 7
        assert result["triads"][0]["roman"] == "I"

    def test_diatonic_minor_still_works(self):
        """get_diatonic_chords minor still works after extension."""
        from MCP_Server.theory.chords import get_diatonic_chords

        result = get_diatonic_chords("A", "minor", 4)
        assert len(result["triads"]) == 7
        assert result["triads"][0]["roman"] == "i"

    def test_diatonic_pentatonic_still_raises(self):
        """get_diatonic_chords pentatonic still raises ValueError."""
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


class TestScaleLibrary:
    """Unit tests for MCP_Server.theory.scales functions (no MCP, no mocks)."""

    # --- SCLE-01: list_scales ---

    def test_list_scales_returns_list_of_dicts(self):
        from MCP_Server.theory.scales import list_scales

        result = list_scales()
        assert isinstance(result, list)
        for entry in result:
            assert isinstance(entry, dict)
            assert "name" in entry
            assert "intervals" in entry
            assert "category" in entry
            assert "note_count" in entry

    def test_list_scales_38_entries(self):
        from MCP_Server.theory.scales import list_scales

        result = list_scales()
        assert len(result) == 38

    def test_list_scales_all_categories(self):
        from MCP_Server.theory.scales import list_scales

        result = list_scales()
        categories = {e["category"] for e in result}
        expected = {"diatonic", "modal", "minor_variant", "pentatonic", "blues", "symmetric", "bebop", "world"}
        assert categories == expected

    def test_major_scale_intervals_sum_to_12(self):
        from MCP_Server.theory.scales import list_scales

        result = list_scales()
        major = [s for s in result if s["name"] == "major"][0]
        assert sum(major["intervals"]) == 12

    def test_all_intervals_sum_correctly(self):
        from MCP_Server.theory.scales import list_scales

        result = list_scales()
        for scale in result:
            total = sum(scale["intervals"])
            assert total == 12, f"{scale['name']} intervals sum to {total}, expected 12"

    # --- SCLE-02: get_scale_pitches ---

    def test_get_scale_pitches_c_major_one_octave(self):
        from MCP_Server.theory.scales import get_scale_pitches

        result = get_scale_pitches("C", "major", 4, 4)
        pitches = result["pitches"]
        assert len(pitches) == 8  # C D E F G A B C
        assert pitches[0]["midi"] == 60
        assert pitches[-1]["midi"] == 72

    def test_get_scale_pitches_c_major_two_octaves(self):
        from MCP_Server.theory.scales import get_scale_pitches

        result = get_scale_pitches("C", "major", 4, 5)
        pitches = result["pitches"]
        assert pitches[0]["midi"] == 60
        assert pitches[-1]["midi"] == 72

    def test_get_scale_pitches_rich_note_objects(self):
        from MCP_Server.theory.scales import get_scale_pitches

        result = get_scale_pitches("C", "major", 4, 4)
        for p in result["pitches"]:
            assert "midi" in p
            assert "name" in p

    def test_get_scale_pitches_minor_pentatonic(self):
        from MCP_Server.theory.scales import get_scale_pitches

        result = get_scale_pitches("C", "minor_pentatonic", 4, 4)
        pitches = result["pitches"]
        # C Eb F G Bb C -> 6 notes for one octave including top
        assert len(pitches) == 6
        # Check pitch classes: C, D#/Eb, F, G, A#/Bb, C
        midi_values = [p["midi"] for p in pitches]
        assert midi_values[0] == 60  # C4
        assert midi_values[-1] == 72  # C5

    def test_get_scale_pitches_invalid_scale_raises(self):
        from MCP_Server.theory.scales import get_scale_pitches

        with pytest.raises(ValueError):
            get_scale_pitches("C", "nonexistent_scale", 4, 5)

    # --- SCLE-03: check_notes_in_scale ---

    def test_check_notes_all_in_scale(self):
        from MCP_Server.theory.scales import check_notes_in_scale

        result = check_notes_in_scale([60, 64, 67], "C", "major")
        assert result["all_in_scale"] is True
        assert len(result["in_scale"]) == 3
        assert len(result["out_of_scale"]) == 0

    def test_check_notes_some_out_of_scale(self):
        from MCP_Server.theory.scales import check_notes_in_scale

        result = check_notes_in_scale([60, 63, 67], "C", "major")
        assert result["all_in_scale"] is False
        # midi 63 = Eb/D# is not in C major
        out_midis = [n["midi"] for n in result["out_of_scale"]]
        assert 63 in out_midis

    def test_check_notes_result_keys(self):
        from MCP_Server.theory.scales import check_notes_in_scale

        result = check_notes_in_scale([60, 64, 67], "C", "major")
        assert "scale" in result
        assert "root" in result
        assert "in_scale" in result
        assert "out_of_scale" in result
        assert "all_in_scale" in result

    # --- SCLE-04: get_related_scales ---

    def test_get_related_scales_keys(self):
        from MCP_Server.theory.scales import get_related_scales

        result = get_related_scales("C", "major")
        assert "parallel" in result
        assert "relative" in result
        assert "modes" in result

    def test_get_related_scales_relative_minor(self):
        from MCP_Server.theory.scales import get_related_scales

        result = get_related_scales("C", "major")
        relative_scales = [(r["root"], r["scale"]) for r in result["relative"]]
        assert ("A", "natural_minor") in relative_scales

    def test_get_related_scales_modes(self):
        from MCP_Server.theory.scales import get_related_scales

        result = get_related_scales("C", "major")
        mode_scales = [(m["root"], m["scale"]) for m in result["modes"]]
        assert len(result["modes"]) == 7
        assert ("D", "dorian") in mode_scales
        assert ("E", "phrygian") in mode_scales

    def test_get_related_scales_parallel(self):
        from MCP_Server.theory.scales import get_related_scales

        result = get_related_scales("C", "major")
        parallel_scales = [(p["root"], p["scale"]) for p in result["parallel"]]
        assert ("C", "natural_minor") in parallel_scales
        assert ("C", "harmonic_minor") in parallel_scales
        assert ("C", "melodic_minor") in parallel_scales

    # --- SCLE-05: detect_scales_from_notes ---

    def test_detect_c_major(self):
        from MCP_Server.theory.scales import detect_scales_from_notes

        result = detect_scales_from_notes([60, 62, 64, 65, 67, 69, 71])
        assert len(result) > 0
        top = result[0]
        assert top["root"] == "C"
        assert top["scale"] == "major"
        assert top["coverage"] == 1.0

    def test_detect_max_5_results(self):
        from MCP_Server.theory.scales import detect_scales_from_notes

        result = detect_scales_from_notes([60, 62, 64, 65, 67, 69, 71])
        assert len(result) <= 5

    def test_detect_result_keys(self):
        from MCP_Server.theory.scales import detect_scales_from_notes

        result = detect_scales_from_notes([60, 62, 64, 65, 67, 69, 71])
        for entry in result:
            assert "root" in entry
            assert "scale" in entry
            assert "coverage" in entry
            assert "matched_notes" in entry
            assert "total_notes" in entry

    def test_detect_empty_raises(self):
        from MCP_Server.theory.scales import detect_scales_from_notes

        with pytest.raises(ValueError):
            detect_scales_from_notes([])


class TestScaleTools:
    """Integration tests: scale MCP tools via mcp_server fixture."""

    @pytest.mark.asyncio
    async def test_scale_tools_registered(self, mcp_server):
        """All 5 scale tools are registered."""
        tools = await mcp_server.list_tools()
        names = {t.name for t in tools}
        for tool in [
            "list_scales",
            "get_scale_pitches",
            "check_notes_in_scale",
            "get_related_scales",
            "detect_scales_from_notes",
        ]:
            assert tool in names, f"{tool} not registered"

    @pytest.mark.asyncio
    async def test_list_scales(self, mcp_server):
        """list_scales returns catalog with 38 scales."""
        result = await mcp_server.call_tool("list_scales", {})
        data = json.loads(result[0][0].text)
        assert len(data) == 38
        # Check structure
        first = data[0]
        assert "name" in first
        assert "intervals" in first
        assert "category" in first
        assert "note_count" in first

    @pytest.mark.asyncio
    async def test_get_scale_pitches_c_major(self, mcp_server):
        """get_scale_pitches C major octave 4-5 returns pitches starting at MIDI 60."""
        result = await mcp_server.call_tool(
            "get_scale_pitches",
            {"root": "C", "scale_name": "major", "octave_start": 4, "octave_end": 5},
        )
        data = json.loads(result[0][0].text)
        assert data["root"] == "C"
        assert data["scale"] == "major"
        assert data["pitches"][0]["midi"] == 60
        assert data["pitches"][-1]["midi"] == 72  # C5

    @pytest.mark.asyncio
    async def test_get_scale_pitches_invalid_scale(self, mcp_server):
        """get_scale_pitches with invalid scale returns error."""
        result = await mcp_server.call_tool(
            "get_scale_pitches", {"root": "C", "scale_name": "notascale"}
        )
        text = result[0][0].text
        assert "Error" in text

    @pytest.mark.asyncio
    async def test_check_notes_in_scale_all_in(self, mcp_server):
        """check_notes_in_scale with C major triad in C major -> all_in_scale true."""
        result = await mcp_server.call_tool(
            "check_notes_in_scale",
            {"midi_pitches": [60, 64, 67], "root": "C", "scale_name": "major"},
        )
        data = json.loads(result[0][0].text)
        assert data["all_in_scale"] is True
        assert len(data["out_of_scale"]) == 0

    @pytest.mark.asyncio
    async def test_check_notes_in_scale_out_of_scale(self, mcp_server):
        """check_notes_in_scale with Eb (63) in C major -> out_of_scale."""
        result = await mcp_server.call_tool(
            "check_notes_in_scale",
            {"midi_pitches": [60, 63, 67], "root": "C", "scale_name": "major"},
        )
        data = json.loads(result[0][0].text)
        assert data["all_in_scale"] is False
        assert len(data["out_of_scale"]) == 1

    @pytest.mark.asyncio
    async def test_check_notes_out_of_midi_range(self, mcp_server):
        """check_notes_in_scale with MIDI > 127 returns error."""
        result = await mcp_server.call_tool(
            "check_notes_in_scale",
            {"midi_pitches": [60, 200], "root": "C", "scale_name": "major"},
        )
        text = result[0][0].text
        assert "Error" in text or "out of range" in text.lower()

    @pytest.mark.asyncio
    async def test_get_related_scales_c_major(self, mcp_server):
        """get_related_scales C major returns parallel, relative, modes."""
        result = await mcp_server.call_tool(
            "get_related_scales", {"root": "C", "scale_name": "major"}
        )
        data = json.loads(result[0][0].text)
        assert "parallel" in data
        assert "relative" in data
        assert "modes" in data
        # Relative should include A minor
        relative_names = [(r["root"], r["scale"]) for r in data["relative"]]
        assert any("A" in root for root, scale in relative_names)

    @pytest.mark.asyncio
    async def test_detect_scales_c_major_notes(self, mcp_server):
        """detect_scales_from_notes with C major scale pitches -> C major top result."""
        result = await mcp_server.call_tool(
            "detect_scales_from_notes",
            {"midi_pitches": [60, 62, 64, 65, 67, 69, 71]},
        )
        data = json.loads(result[0][0].text)
        assert len(data) <= 5
        top = data[0]
        assert top["coverage"] == 1.0
        assert "C" in top["root"]
        assert top["scale"] == "major" or top["scale"] == "ionian"

    @pytest.mark.asyncio
    async def test_detect_scales_empty_pitches(self, mcp_server):
        """detect_scales_from_notes with empty list returns error."""
        result = await mcp_server.call_tool(
            "detect_scales_from_notes", {"midi_pitches": []}
        )
        text = result[0][0].text
        assert "Error" in text

    @pytest.mark.asyncio
    async def test_diatonic_harmonic_minor(self, mcp_server):
        """get_diatonic_chords with harmonic_minor returns 7 triads."""
        result = await mcp_server.call_tool(
            "get_diatonic_chords",
            {"key_name": "C", "scale_type": "harmonic_minor", "octave": 4},
        )
        data = json.loads(result[0][0].text)
        assert len(data["triads"]) == 7
        assert len(data["sevenths"]) == 7

    @pytest.mark.asyncio
    async def test_diatonic_melodic_minor(self, mcp_server):
        """get_diatonic_chords with melodic_minor returns 7 triads."""
        result = await mcp_server.call_tool(
            "get_diatonic_chords",
            {"key_name": "A", "scale_type": "melodic_minor", "octave": 4},
        )
        data = json.loads(result[0][0].text)
        assert len(data["triads"]) == 7
        assert len(data["sevenths"]) == 7


class TestProgressionLibrary:
    """Unit tests for MCP_Server.theory.progressions functions (no MCP, no mocks)."""

    # --- PROGRESSION_CATALOG ---

    def test_catalog_has_25_entries(self):
        from MCP_Server.theory.progressions import PROGRESSION_CATALOG

        assert len(PROGRESSION_CATALOG) == 25

    def test_catalog_covers_7_genres(self):
        from MCP_Server.theory.progressions import PROGRESSION_CATALOG

        genres = set(p["genre"] for p in PROGRESSION_CATALOG)
        assert len(genres) == 7

    # --- get_common_progressions (PROG-01) ---

    def test_get_common_progressions_returns_list_of_dicts(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C")
        assert isinstance(result, list)
        assert len(result) > 0
        for entry in result:
            assert "name" in entry
            assert "genre" in entry
            assert "numerals" in entry
            assert "chords" in entry

    def test_get_common_progressions_all_25(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C")
        assert len(result) == 25

    def test_get_common_progressions_genre_jazz(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C", genre="jazz")
        assert len(result) == 5
        for entry in result:
            assert entry["genre"] == "jazz"

    def test_get_common_progressions_genre_pop(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C", genre="pop")
        assert len(result) == 4

    def test_get_common_progressions_unified_chord_format(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C", genre="pop")
        for entry in result:
            for chord in entry["chords"]:
                assert "numeral" in chord
                assert "root" in chord
                assert "quality" in chord
                assert "notes" in chord

    def test_get_common_progressions_note_format(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C", genre="pop")
        chord = result[0]["chords"][0]
        for note in chord["notes"]:
            assert "midi" in note
            assert "name" in note

    def test_get_common_progressions_axis_of_awesome(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C", genre="pop")
        axis = result[0]
        assert axis["name"] == "Axis of Awesome"
        assert len(axis["chords"]) == 4
        assert axis["numerals"] == ["I", "V", "vi", "IV"]

    def test_get_common_progressions_key_g(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("G", genre="rock")
        # Classic Rock first: I chord root should be G
        classic = result[0]
        first_chord = classic["chords"][0]
        assert "G" in first_chord["root"]

    def test_get_common_progressions_nonexistent_genre(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C", genre="nonexistent")
        assert result == []

    def test_get_common_progressions_octave_3(self):
        from MCP_Server.theory.progressions import get_common_progressions

        result = get_common_progressions("C", genre="rock", octave=3)
        # Classic Rock I chord at octave 3: root C3 = MIDI 48
        classic = result[0]
        first_chord = classic["chords"][0]
        root_midi = first_chord["notes"][0]["midi"]
        assert root_midi == 48, f"Expected C3=48, got {root_midi}"

    # --- generate_progression (PROG-02) ---

    def test_generate_progression_returns_dict_with_keys(self):
        from MCP_Server.theory.progressions import generate_progression

        result = generate_progression("C", ["I", "IV", "V", "I"])
        assert "key" in result
        assert "scale_type" in result
        assert "chords" in result

    def test_generate_progression_four_chords(self):
        from MCP_Server.theory.progressions import generate_progression

        result = generate_progression("C", ["I", "IV", "V", "I"])
        assert len(result["chords"]) == 4

    def test_generate_progression_first_chord_root_c(self):
        from MCP_Server.theory.progressions import generate_progression

        result = generate_progression("C", ["I"])
        first = result["chords"][0]
        assert "C" in first["root"]

    def test_generate_progression_key_g(self):
        from MCP_Server.theory.progressions import generate_progression

        result = generate_progression("G", ["I", "V"])
        first = result["chords"][0]
        assert "G" in first["root"]

    def test_generate_progression_voice_leading(self):
        from MCP_Server.theory.progressions import generate_progression

        result = generate_progression("C", ["I", "IV", "V", "I"])
        chords = result["chords"]

        # Calculate total voice movement with voice leading
        total_vl = 0
        for i in range(1, len(chords)):
            prev = [n["midi"] for n in chords[i - 1]["notes"]]
            curr = [n["midi"] for n in chords[i]["notes"]]
            for p, c in zip(sorted(prev), sorted(curr)):
                total_vl += abs(c - p)

        # Generate without voice leading (naive close position)
        naive = generate_progression.__wrapped__ if hasattr(generate_progression, '__wrapped__') else None
        # Compare: voice-led should have less movement than naive root position
        # Just verify it's reasonable (< 30 semitones for 3 transitions of triads)
        assert total_vl < 30, f"Total voice movement {total_vl} seems too large for voice-led chords"

    def test_generate_progression_dorian(self):
        from MCP_Server.theory.progressions import generate_progression

        result = generate_progression("D", ["I", "IV", "V", "I"], scale_type="dorian")
        assert result["scale_type"] == "dorian"
        assert len(result["chords"]) == 4

    def test_generate_progression_unified_format(self):
        from MCP_Server.theory.progressions import generate_progression

        result = generate_progression("C", ["I", "IV", "V"])
        for chord in result["chords"]:
            assert "numeral" in chord
            assert "root" in chord
            assert "quality" in chord
            assert "notes" in chord

    def test_generate_progression_invalid_numeral(self):
        from MCP_Server.theory.progressions import generate_progression

        with pytest.raises(ValueError):
            generate_progression("C", ["XYZ"])

    def test_generate_progression_empty_numerals(self):
        from MCP_Server.theory.progressions import generate_progression

        with pytest.raises(ValueError):
            generate_progression("C", [])

    # --- analyze_progression (PROG-03) ---

    def test_analyze_progression_c_f_g_c(self):
        from MCP_Server.theory.progressions import analyze_progression

        result = analyze_progression(["C", "F", "G", "C"], "C")
        assert len(result) == 4
        for chord in result:
            assert "numeral" in chord

    def test_analyze_progression_numerals_i_iv_v_i(self):
        from MCP_Server.theory.progressions import analyze_progression

        result = analyze_progression(["C", "F", "G", "C"], "C")
        numerals = [c["numeral"] for c in result]
        assert numerals == ["I", "IV", "V", "I"]

    def test_analyze_progression_ii_v7_i(self):
        from MCP_Server.theory.progressions import analyze_progression

        result = analyze_progression(["Dm", "G7", "C"], "C")
        numerals = [c["numeral"] for c in result]
        assert "ii" in numerals[0].lower()
        assert "V" in numerals[1] or "v" in numerals[1]
        assert "I" in numerals[2] or "i" in numerals[2]

    def test_analyze_progression_borrowed_chord(self):
        from MCP_Server.theory.progressions import analyze_progression

        result = analyze_progression(["C", "Bb", "F", "C"], "C")
        numerals = [c["numeral"] for c in result]
        # Bb in key of C should be bVII
        assert "bVII" in numerals[1] or "VII" in numerals[1]

    def test_analyze_progression_unified_format(self):
        from MCP_Server.theory.progressions import analyze_progression

        result = analyze_progression(["C", "F", "G"], "C")
        for chord in result:
            assert "numeral" in chord
            assert "root" in chord
            assert "quality" in chord
            assert "notes" in chord

    def test_analyze_progression_invalid_chord(self):
        from MCP_Server.theory.progressions import analyze_progression

        with pytest.raises(ValueError):
            analyze_progression(["XYZ_INVALID"], "C")

    def test_analyze_progression_empty_list(self):
        from MCP_Server.theory.progressions import analyze_progression

        with pytest.raises(ValueError):
            analyze_progression([], "C")

    # --- suggest_next_chord (PROG-04) ---

    def test_suggest_next_chord_returns_list(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        result = suggest_next_chord("C", ["V"])
        assert isinstance(result, list)

    def test_suggest_next_chord_includes_tonic_after_v(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        result = suggest_next_chord("C", ["V"])
        numerals = [s["numeral"] for s in result]
        assert any("I" == n or "i" == n for n in numerals), f"Expected I among {numerals}"

    def test_suggest_next_chord_unified_format(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        result = suggest_next_chord("C", ["V"])
        for s in result:
            assert "numeral" in s
            assert "root" in s
            assert "quality" in s
            assert "notes" in s
            assert "reason" in s
            assert "score" in s

    def test_suggest_next_chord_3_to_5_results(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        result = suggest_next_chord("C", ["V"])
        assert 3 <= len(result) <= 5, f"Expected 3-5 results, got {len(result)}"

    def test_suggest_next_chord_context_up_to_4(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        # Should not raise with 4 preceding chords
        result = suggest_next_chord("C", ["I", "V", "vi", "IV"])
        assert len(result) >= 3

    def test_suggest_next_chord_genre_filter(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        result = suggest_next_chord("C", ["V"], genre="pop")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_suggest_next_chord_nonempty_reasons(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        result = suggest_next_chord("C", ["I"])
        for s in result:
            assert s["reason"], f"Expected non-empty reason, got '{s['reason']}'"

    def test_suggest_next_chord_empty_preceding(self):
        from MCP_Server.theory.progressions import suggest_next_chord

        with pytest.raises(ValueError):
            suggest_next_chord("C", [])

    # --- _voice_lead_pair helper ---

    def test_voice_lead_pair_minimizes_movement(self):
        from MCP_Server.theory.progressions import _voice_lead_pair

        prev = [60, 64, 67]  # C E G
        next_pcs = [5, 9, 0]  # F A C (F major pitch classes)
        result = _voice_lead_pair(prev, next_pcs)
        # Voice-led result should have less total movement than naive [65, 69, 72]
        naive = sorted([65, 69, 72])
        vl_movement = sum(abs(r - p) for r, p in zip(sorted(result), sorted(prev)))
        naive_movement = sum(abs(n - p) for n, p in zip(naive, sorted(prev)))
        assert vl_movement <= naive_movement, (
            f"Voice-led movement {vl_movement} should be <= naive {naive_movement}"
        )
