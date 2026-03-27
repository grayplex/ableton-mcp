# Milestones

## v1.2 Genre/Style Blueprints (Shipped: 2026-03-27)

**Phases completed:** 5 phases, 9 plans, 16 tasks

**Key accomplishments:**

- 1. [Rule 1 - Bug] Adapted chord type test to avoid music21 dependency
- Two MCP tools (list_genre_blueprints + get_genre_blueprint) exposing Phase 20 genre catalog with section filtering, subgenre support, and alias resolution
- Synthwave (4 subgenres) and lo-fi (3 subgenres) blueprints with D-05 alias migration from hip-hop/trap
- Future bass (5 subgenres) and disco/funk (4 subgenres) blueprints completing the full 12-genre catalog
- get_genre_palette MCP tool bridging genre blueprint harmony data to theory engine with key-resolved chord names, scale names, and progression resolution
- TestTokenBudget (QUAL-01):

---

## v1.1 Theory Engine (Shipped: 2026-03-26)

**Phases completed:** 6 phases (14-19), 12 plans, 224 tests
**Lines of code:** 5,704 Python (theory library + tools + tests)
**Git range:** feat(14-01) → feat(19-02), 15 feature commits
**Timeline:** 2 days (2026-03-24 → 2026-03-25)

**Delivered:** Comprehensive music theory intelligence layer powered by music21, giving Claude harmonic awareness for composing, analyzing, and arranging in Ableton Live.

**Key accomplishments:**

- Music theory foundation with music21 integration and bidirectional MIDI-to-note mapping across 128 pitches
- Chord engine supporting 26 qualities with build/identify/invert/voice operations
- 38-scale catalog with pitch generation, note validation, scale detection, and modal relationships
- Progression engine with 25-genre catalog, Roman numeral analysis, voice-led generation, and next-chord suggestions
- Harmonic analysis: Krumhansl-Schmuckler key detection, time-grid chord segmentation, harmonic rhythm analysis
- Voice leading with parallel-5ths/octaves avoidance + 18 rhythm patterns producing add_notes_to_clip-ready MIDI

---
