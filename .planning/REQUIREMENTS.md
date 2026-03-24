# Requirements: AbletonMCP v1.1 — Theory Engine

**Defined:** 2026-03-23
**Core Value:** Claude composes with harmonic intelligence — chords, progressions, and voice leading flow from music theory knowledge, not brute-force pitch guessing.

## Theory Foundation (3)

- [x] **THRY-01**: music21 installed as MCP_Server dependency and importable at server startup
- [x] **THRY-02**: Theory engine module (`MCP_Server/tools/theory.py` + `MCP_Server/theory/` library) with music21-powered utilities for chord, scale, progression, and analysis operations
- [x] **THRY-03**: Bidirectional MIDI pitch ↔ note name mapping (e.g., 60 ↔ "C4", 63 ↔ "Eb4") consistent with Ableton's 0-127 range and music21's pitch representation

## Chord Tools (5)

- [ ] **CHRD-01**: User can build a chord from root note + quality (e.g., root="C", quality="maj7" → MIDI pitches [60, 64, 67, 71]) with configurable octave
- [ ] **CHRD-02**: User can get chord inversions (root position, 1st, 2nd, 3rd inversion) for any chord
- [ ] **CHRD-03**: User can get chord voicings (close, open, drop-2, drop-3) for any chord
- [ ] **CHRD-04**: User can identify a chord from a set of MIDI pitches (e.g., [60, 64, 67] → "C major")
- [ ] **CHRD-05**: User can get all diatonic chords (triads and 7ths) for a given key/scale

## Scale & Mode Tools (5)

- [ ] **SCLE-01**: User can list all available scales and modes with their interval patterns
- [ ] **SCLE-02**: User can get scale degrees as MIDI pitches for a given root, scale, and octave range
- [ ] **SCLE-03**: User can check whether a note or set of notes belongs to a given scale
- [ ] **SCLE-04**: User can get related scales/modes (parallel, relative, modes of a parent scale)
- [ ] **SCLE-05**: User can detect which scales contain a given set of notes

## Progression Tools (4)

- [ ] **PROG-01**: User can retrieve common chord progressions by genre/style (jazz ii-V-I, pop I-V-vi-IV, 12-bar blues, etc.) with MIDI pitch output
- [ ] **PROG-02**: User can generate a chord progression with voice leading applied, given a key and Roman numeral sequence
- [ ] **PROG-03**: User can analyze a sequence of chords as Roman numeral progression in a given key
- [ ] **PROG-04**: User can get next-chord suggestions given current progression context and style

## Harmonic Analysis Tools (3)

- [ ] **ANLY-01**: User can detect the key and scale of a clip from its MIDI notes (using music21's key detection algorithms)
- [ ] **ANLY-02**: User can segment a clip's notes into chords by time position and identify each chord
- [ ] **ANLY-03**: User can analyze harmonic rhythm — chord change frequency, chord durations, and progression structure

## Voice Leading Tools (2)

- [ ] **VOIC-01**: User can get voice-led connection between two chords (minimal movement voicing)
- [ ] **VOIC-02**: User can generate a full voice-led chord progression from a Roman numeral sequence

## Rhythm Pattern Tools (2)

- [ ] **RHYM-01**: User can retrieve rhythm pattern templates (arpeggios, bass lines, comping patterns, strumming) by style
- [ ] **RHYM-02**: User can apply a rhythm pattern to a chord or progression to get time-positioned MIDI notes ready for `add_notes_to_clip`

## Summary

| Category | Count |
|----------|-------|
| Theory Foundation | 3 |
| Chord Tools | 5 |
| Scale & Mode Tools | 5 |
| Progression Tools | 4 |
| Harmonic Analysis | 3 |
| Voice Leading | 2 |
| Rhythm Patterns | 2 |
| **Total** | **24** |
