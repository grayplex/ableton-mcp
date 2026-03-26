# Roadmap: AbletonMCP

## Completed Milestones

- [x] **v1.0** — Production-quality Ableton Live 12 MCP bridge: 13 phases, 33 plans, 178 handler commands, 174 MCP tools, 204 tests, 53 requirements complete (Mar 13–23, 2026) → [archived](milestones/v1.0-ROADMAP.md)

## Current Milestone: v1.1 — Theory Engine

**Goal:** Add a comprehensive music theory intelligence layer powered by music21, giving Claude harmonic awareness for composing, analyzing, and arranging.

**Requirements:** 24 (THRY: 3, CHRD: 5, SCLE: 5, PROG: 4, ANLY: 3, VOIC: 2, RHYM: 2)

### Phases

| # | Phase | Goal | Requirements |
|---|-------|------|-------------|
| 14 | 2/2 | Complete    | 2026-03-24 |
| 15 | 2/2 | Complete    | 2026-03-24 |
| 16 | 2/2 | Complete    | 2026-03-24 |
| 17 | 2/2 | Complete    | 2026-03-24 |
| 18 | 2/2 | Complete    | 2026-03-25 |
| 19 | 2/2 | Complete    | 2026-03-26 |

### Phase Details

#### Phase 14: Theory Foundation
**Goal:** music21 is installed, importable, and wrapped in a theory library that converts between music21 objects and MCP-friendly JSON. The module structure is established for all subsequent phases.

**Plans:** 2/2 plans complete

Plans:
- [x] 14-01-PLAN.md — Install music21 dependency, create theory/ package with pitch mapping utilities
- [x] 14-02-PLAN.md — Wire MCP tools, register with FastMCP, create comprehensive test suite

**Delivers:**
- `music21` in MCP_Server dependencies (pyproject.toml / requirements.txt)
- `MCP_Server/theory/` package with core utilities (pitch mapping, chord builder, scale utils)
- `MCP_Server/tools/theory.py` tool module registered with FastMCP
- Bidirectional MIDI ↔ note name conversion verified against Ableton's pitch range
- Test infrastructure for theory tools

**Requirements:** THRY-01, THRY-02, THRY-03

#### Phase 15: Chord Engine
**Goal:** Claude can build any chord by name, get inversions and voicings, identify chords from pitches, and enumerate all diatonic chords in a key.

**Plans:** 2/2 plans complete

Plans:
- [x] 15-01-PLAN.md — Chord library with all 5 functions (build, inversions, voicings, identify, diatonic) and unit tests
- [x] 15-02-PLAN.md — Wire 5 MCP chord tools, update barrel exports, add integration tests

**Delivers:**
- `build_chord` tool — root + quality → MIDI pitches
- `get_chord_inversions` tool — all inversions of a chord
- `get_chord_voicings` tool — close/open/drop-2/drop-3 voicings
- `identify_chord` tool — MIDI pitches → chord name + quality
- `get_diatonic_chords` tool — key → all triads and 7th chords with Roman numerals

**Requirements:** CHRD-01, CHRD-02, CHRD-03, CHRD-04, CHRD-05

#### Phase 16: Scale & Mode Explorer
**Goal:** Claude can explore all available scales/modes, generate pitch sets for composition, validate notes against scales, and discover related tonalities.

**Plans:** 2/2 plans complete

Plans:
- [x] 16-01-PLAN.md — Scale library with SCALE_CATALOG (38 scales), 5 functions, extended diatonic chords, and unit tests
- [x] 16-02-PLAN.md — Wire 5 MCP scale tools, update diatonic chords tool, add integration tests

**Delivers:**
- `list_scales` tool — all available scales/modes with intervals
- `get_scale_pitches` tool — root + scale + octave range → MIDI pitches
- `check_notes_in_scale` tool — validate pitches against a scale
- `get_related_scales` tool — parallel, relative, and modal relationships
- `detect_scales_from_notes` tool — find scales containing given pitches

**Requirements:** SCLE-01, SCLE-02, SCLE-03, SCLE-04, SCLE-05

#### Phase 17: Progression Engine
**Goal:** Claude can retrieve genre-specific progressions, generate voice-led chord sequences, analyze existing progressions as Roman numerals, and get next-chord suggestions.

**Plans:** 2/2 plans complete

Plans:
- [x] 17-01-PLAN.md — Progression library with PROGRESSION_CATALOG (25 progressions), 4 functions, and unit tests
- [x] 17-02-PLAN.md — Wire 4 MCP progression tools, add integration tests

**Delivers:**
- `get_common_progressions` tool — genre/style → progression templates with MIDI output
- `generate_progression` tool — key + Roman numerals → voice-led MIDI chords
- `analyze_progression` tool — chord sequence → Roman numeral analysis
- `suggest_next_chord` tool — context-aware chord suggestion

**Requirements:** PROG-01, PROG-02, PROG-03, PROG-04

#### Phase 18: Harmonic Analysis
**Goal:** Claude can analyze existing clip content — detecting the key, identifying chords at each time position, and understanding the harmonic rhythm.

**Plans:** 2/2 plans complete

Plans:
- [x] 18-01-PLAN.md — Analysis library with 3 functions (detect_key, analyze_clip_chords, analyze_harmonic_rhythm) and unit tests
- [x] 18-02-PLAN.md — Wire 3 MCP analysis tools, update barrel exports, add integration tests

**Delivers:**
- `detect_key` tool — MIDI notes → detected key with confidence score
- `analyze_clip_chords` tool — time-segmented chord identification
- `analyze_harmonic_rhythm` tool — chord change frequency, durations, structure

**Requirements:** ANLY-01, ANLY-02, ANLY-03
**Note:** These tools accept note data as input (from `get_notes` output), not clip references directly. The AI reads the clip first, then passes notes to analysis.

#### Phase 19: Voice Leading & Rhythm
**Goal:** Claude can connect chords with smooth voice leading and apply rhythm patterns to turn chord progressions into playable MIDI note sequences.

**Plans:** 2/2 plans complete

Plans:
- [x] 19-01-PLAN.md — Voice leading library (voicing.py) + rhythm library (rhythm.py) + unit tests
- [x] 19-02-PLAN.md — Wire 4 MCP tools, update barrel exports, add integration tests

**Delivers:**
- `voice_lead_chords` tool — connect two chords with minimal movement
- `voice_lead_progression` tool — full progression with voice leading applied
- `get_rhythm_patterns` tool — style-based rhythm templates (arpeggio, bass, comping)
- `apply_rhythm_pattern` tool — pattern + chords → time-positioned MIDI notes

**Requirements:** VOIC-01, VOIC-02, RHYM-01, RHYM-02

### Requirement Coverage

| Requirement | Phase | Tool |
|-------------|-------|------|
| THRY-01 | 14 | (dependency setup) |
| THRY-02 | 14 | (module structure) |
| THRY-03 | 14 | (pitch mapping) |
| CHRD-01 | 15 | build_chord |
| CHRD-02 | 15 | get_chord_inversions |
| CHRD-03 | 15 | get_chord_voicings |
| CHRD-04 | 15 | identify_chord |
| CHRD-05 | 15 | get_diatonic_chords |
| SCLE-01 | 16 | list_scales |
| SCLE-02 | 16 | get_scale_pitches |
| SCLE-03 | 16 | check_notes_in_scale |
| SCLE-04 | 16 | get_related_scales |
| SCLE-05 | 16 | detect_scales_from_notes |
| PROG-01 | 17 | get_common_progressions |
| PROG-02 | 17 | generate_progression |
| PROG-03 | 17 | analyze_progression |
| PROG-04 | 17 | suggest_next_chord |
| ANLY-01 | 18 | detect_key |
| ANLY-02 | 18 | analyze_clip_chords |
| ANLY-03 | 18 | analyze_harmonic_rhythm |
| VOIC-01 | 19 | voice_lead_chords |
| VOIC-02 | 19 | voice_lead_progression |
| RHYM-01 | 19 | get_rhythm_patterns |
| RHYM-02 | 19 | apply_rhythm_pattern |
