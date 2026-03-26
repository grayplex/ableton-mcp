# Phase 15: Chord Engine - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver 5 chord-focused MCP tools powered by music21: build chords from root + quality, get all inversions, get all voicings (close/open/drop-2/drop-3), identify chords from MIDI pitches (ranked candidates), and enumerate diatonic chords (triads + 7ths) for a key. All logic lives in `MCP_Server/theory/chords.py` with tools registered in the existing `MCP_Server/tools/theory.py`.

</domain>

<decisions>
## Implementation Decisions

### Chord Quality Vocabulary
- **D-01:** Comprehensive chord type support — triads (maj/min/dim/aug), 7ths (maj7/min7/dom7/dim7/half-dim7), extended (9/11/13), sus2/sus4, add chords, altered (b5/#5/b9/#9/#11)
- **D-02:** Short symbol format for quality strings — `maj7`, `min`, `dim7`, `aug`, `sus4`, `dom7`, `9`, `min11` (standard music notation shorthand)
- **D-03:** `build_chord` takes separate `root` and `quality` parameters (not a combined string like "Cmaj7")
- **D-04:** Default octave 4 (C4 = MIDI 60 region) when octave not specified; user can override

### Voicing & Inversion Output
- **D-05:** Rich note objects consistent with Phase 14 — each note is `{"midi": 60, "name": "C4"}`, not flat MIDI arrays
- **D-06:** No voice assignment labels (soprano/alto/tenor/bass) — notes ordered bottom to top, position implies voice
- **D-07:** `get_chord_inversions` returns ALL inversions at once as a list (root position through highest available inversion)
- **D-08:** `get_chord_voicings` returns ALL voicing types at once as a dict: `{"close": [...], "open": [...], "drop2": [...], "drop3": [...]}`

### Chord Identification
- **D-09:** `identify_chord` returns top 3 ranked candidates (not just best match) to handle ambiguous pitch sets
- **D-10:** Graceful handling of incomplete chords — dyads, power chords, missing 5ths all accepted and identified as best possible
- **D-11:** Inversions reported as inversions (e.g., "C major, 1st inversion" with bass note), not slash chord notation

### Diatonic Chords
- **D-12:** Core metadata per diatonic chord: Roman numeral, quality, root, MIDI pitches as rich note objects, degree number
- **D-13:** Returns both triads and 7th chords as separate arrays in one response
- **D-14:** Supports major and natural minor scales only (harmonic/melodic minor deferred to Phase 16 scale tools)

### Carried Forward from Phase 14
- **D-15:** Library code in `MCP_Server/theory/chords.py`, tools in `MCP_Server/tools/theory.py` (D-01, D-02 from Phase 14)
- **D-16:** Barrel exports from `MCP_Server/theory/__init__.py` (D-03 from Phase 14)
- **D-17:** No prefix on tool names — `build_chord`, not `theory_build_chord` (D-15 from Phase 14)
- **D-18:** MIDI validation (0-127) at tool boundary layer, not in library functions (D-16 from Phase 14)
- **D-19:** `json.dumps()` returns on success, `format_error()` on error (D-06, D-07 from Phase 14)
- **D-20:** Lazy music21 imports inside theory/ functions (D-14 from Phase 14)
- **D-21:** C4 = MIDI 60 scientific pitch notation (D-17 from Phase 14)

### Claude's Discretion
- Internal `chords.py` library API design (function signatures, helper utilities, music21 object handling)
- How to map quality strings to music21 chord types internally
- Confidence scoring approach for ranked chord identification candidates
- Test organization and edge case selection

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Theory Module (Phase 14 output)
- `MCP_Server/theory/__init__.py` — Barrel exports pattern (add new chord functions here)
- `MCP_Server/theory/pitch.py` — Reference library module: lazy imports, music21 patterns, helper functions
- `MCP_Server/tools/theory.py` — Reference tool module: @mcp.tool() pattern, MIDI validation, json.dumps/format_error

### Codebase Patterns
- `MCP_Server/tools/notes.py` — Additional tool module reference (imports, decoration, return format)
- `MCP_Server/connection.py` — `format_error()` utility for error responses
- `MCP_Server/server.py` — FastMCP server setup, `mcp` instance creation

### Testing
- `tests/conftest.py` — `mcp_server` fixture for tool integration tests
- `tests/test_theory.py` — Phase 14 theory tests (pattern for new chord tests)

### Requirements
- `.planning/REQUIREMENTS.md` — CHRD-01 through CHRD-05 acceptance criteria
- `.planning/ROADMAP.md` — Phase 15 deliverables

### Prior Context
- `.planning/phases/14-theory-foundation/14-CONTEXT.md` — Phase 14 decisions (foundation patterns this phase builds on)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/theory/pitch.py` — `_get_pitch_module()` lazy import pattern, `_force_sharp()`, `_format_note_name()`, `_parse_note_name()` — all reusable for chord operations
- `MCP_Server/theory/__init__.py` — Barrel export pattern to extend with chord functions
- `MCP_Server/tools/theory.py` — Existing tool file to add 5 new tool functions to
- `MCP_Server/connection.py:format_error()` — Standard error formatting

### Established Patterns
- Lazy music21 import via module-level `_module = None` + getter function
- Rich note objects: `{"midi": int, "name": str}` (from Phase 14 pitch tools)
- Tool boundary validation (0-127 MIDI range) with `format_error()` for out-of-range
- `json.dumps(result, indent=2)` for all tool returns

### Integration Points
- `MCP_Server/theory/__init__.py` — Add chord function exports
- `MCP_Server/tools/theory.py` — Add 5 new @mcp.tool() functions
- `tests/test_theory.py` — Add chord test cases (both unit and integration)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

- Harmonic/melodic minor diatonic chords — belongs in Phase 16 with scale tools
- Function labels (tonic/subdominant/dominant) for diatonic chords — future enhancement
- Available tensions per diatonic degree — future enhancement
- Slash chord notation output — could add later alongside inversion labels

</deferred>

---

*Phase: 15-chord-engine*
*Context gathered: 2026-03-24*
