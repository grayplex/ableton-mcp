# Phase 19: Voice Leading & Rhythm - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver 4 MCP tools: connect two chords with smooth voice leading (parallel 5ths/octaves avoidance), generate a full voice-led progression, retrieve rhythm pattern templates by style/category, and apply a rhythm pattern to a chord to produce time-positioned MIDI notes ready for `add_notes_to_clip`. Voice leading logic lives in `MCP_Server/theory/voicing.py`, rhythm logic in `MCP_Server/theory/rhythm.py`, tools registered in `MCP_Server/tools/theory.py`.

</domain>

<decisions>
## Implementation Decisions

### Voice Leading (voice_lead_chords, voice_lead_progression) — VOIC-01, VOIC-02
- **D-01:** Nearest-voice algorithm (minimize total pitch movement) PLUS parallel 5ths and octaves avoidance. Upgrades Phase 17's basic `_voice_lead_pair()` which has no parallel motion checking
- **D-02:** Input format: MIDI pitch arrays (e.g., `[60, 64, 67]`), not chord name strings. Matches how Claude already works with `build_chord` output
- **D-03:** `voice_lead_chords` returns the re-voiced target chord as rich note objects only — no voice motion details or labels
- **D-04:** `voice_lead_progression` accepts key + Roman numeral sequence (like Phase 17's `generate_progression`) but uses the upgraded voice leading algorithm with parallel avoidance

### Rhythm Pattern Catalog (get_rhythm_patterns) — RHYM-01
- **D-05:** Core 4 categories: arpeggios (up, down, alternating), bass lines (root-5th, walking), comping (block, syncopated), strumming (down, up-down). ~15-20 patterns total
- **D-06:** Each pattern step: chord tone reference (root, 3rd, 5th, 7th, octave), beat position (in beats), duration (in beats), velocity (0-127)
- **D-07:** Flat list output with category field per pattern. Optional category and style filter parameters (consistent with scales and progressions catalogs)

### MIDI Output (apply_rhythm_pattern) — RHYM-02
- **D-08:** Output format matches `add_notes_to_clip` exactly: `{"pitch": int, "start_time": float, "duration": float, "velocity": int}` per note. Zero transformation needed to write to clip
- **D-09:** Accepts single chord (MIDI pitches) + pattern name per call. Claude calls it per chord in a loop for full progressions — simple, composable
- **D-10:** `start_beat` offset parameter positions notes in the clip timeline (e.g., chord at bar 3 = start_beat 8 in 4/4)
- **D-11:** `duration` parameter in beats controls pattern length. Pattern plays once within that duration. Claude controls repetition by calling multiple times with different start_beat offsets

### Carried Forward from Phase 14-17
- **D-12:** Library code split by domain: `MCP_Server/theory/voicing.py` (voice leading) and `MCP_Server/theory/rhythm.py` (rhythm patterns). Tools in `MCP_Server/tools/theory.py` (Phase 14 D-01, D-02)
- **D-13:** Barrel exports from `MCP_Server/theory/__init__.py` (Phase 14 D-03)
- **D-14:** No prefix on tool names — `voice_lead_chords`, not `theory_voice_lead_chords` (Phase 14 D-15)
- **D-15:** MIDI validation (0-127) at tool boundary layer, not in library functions (Phase 14 D-16)
- **D-16:** Rich note objects `{"midi": int, "name": str}` for voice leading output (Phase 14 D-04/D-05)
- **D-17:** `json.dumps()` string returns; errors use `format_error()` (Phase 14 D-06/D-07)
- **D-18:** Standalone tests — no `mock_connection` needed (Phase 14 D-09)
- **D-19:** Lazy music21 imports inside functions (Phase 14 D-14)

### Claude's Discretion
- Exact parallel 5ths/octaves detection algorithm implementation
- How `voice_lead_progression` internally reuses `voice_lead_chords` or shares logic
- Specific rhythm pattern step definitions (exact beat positions, velocities per pattern)
- How chord tone references map to actual MIDI pitches for extended chords (9ths, 11ths)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Theory Engine Architecture
- `.planning/phases/14-theory-foundation/14-CONTEXT.md` — Module structure, output format, naming conventions, lazy imports
- `.planning/phases/15-chord-engine/15-CONTEXT.md` — Chord quality vocabulary, build_chord pattern
- `.planning/phases/17-progression-engine/17-CONTEXT.md` — Voice leading in generate_progression (D-06), unified chord object format (D-15)

### Requirements
- `.planning/REQUIREMENTS.md` §Voice Leading Tools — VOIC-01, VOIC-02 acceptance criteria
- `.planning/REQUIREMENTS.md` §Rhythm Pattern Tools — RHYM-01, RHYM-02 acceptance criteria

### Existing Code
- `MCP_Server/theory/progressions.py` — `_voice_lead_pair()` function (basic nearest-voice, lines ~250-260) to reference/upgrade
- `MCP_Server/theory/progressions.py` — `generate_progression()` for voice-led progression pattern
- `MCP_Server/theory/chords.py` — `build_chord()` for chord construction from root + quality
- `MCP_Server/tools/theory.py` — Existing tool registration pattern (19 theory tools)
- `MCP_Server/theory/__init__.py` — Barrel export pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_voice_lead_pair(prev_midis, next_pitch_classes)` in `progressions.py` — basic nearest-voice algorithm. Can be referenced as starting point for the upgraded version with parallel avoidance
- `build_chord(root, quality, octave)` in `chords.py` — needed by `voice_lead_progression` to resolve Roman numerals to MIDI pitches
- `get_diatonic_chords(key, scale_type)` in `chords.py` — needed to map Roman numerals to chord qualities
- All existing theory tools in `tools/theory.py` — 19 tools following the same pattern

### Established Patterns
- Theory library functions are pure Python + music21, no Ableton dependencies
- Tools call library functions, serialize to JSON, return string
- Tests use `mcp_server` fixture for integration tests, direct function calls for unit tests
- One library file per domain — Phase 19 adds two: `voicing.py` and `rhythm.py`

### Integration Points
- Two new library files: `MCP_Server/theory/voicing.py` and `MCP_Server/theory/rhythm.py`
- New functions exported from `MCP_Server/theory/__init__.py`
- 4 new tool functions added to `MCP_Server/tools/theory.py`
- Tests added to `tests/test_theory.py`
- `apply_rhythm_pattern` output feeds directly into existing `add_notes_to_clip` MCP tool

</code_context>

<specifics>
## Specific Ideas

- `apply_rhythm_pattern` is the bridge from theory to actual music — its output goes directly to `add_notes_to_clip` with zero transformation. This is the payoff of the entire theory engine
- Pattern step format uses chord tone references (root, 3rd, 5th) rather than absolute pitches, making patterns reusable across any chord
- Single-chord-at-a-time design for `apply_rhythm_pattern` keeps it composable — Claude orchestrates multi-chord patterns by calling the tool in a loop with different start_beat offsets

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-voice-leading-rhythm*
*Context gathered: 2026-03-25*
