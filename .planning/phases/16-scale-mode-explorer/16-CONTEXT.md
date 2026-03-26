# Phase 16: Scale & Mode Explorer - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver 5 scale-focused MCP tools powered by music21: list all available scales/modes with intervals, generate pitch sets for a given scale and octave range, validate notes against a scale, find related scales (parallel/relative/modes), and detect which scales fit a given set of notes. All logic lives in `MCP_Server/theory/scales.py` with tools registered in the existing `MCP_Server/tools/theory.py`. Additionally, extend the existing `get_diatonic_chords` tool (Phase 15) to support harmonic and melodic minor scales.

</domain>

<decisions>
## Implementation Decisions

### Scale Catalog Scope
- **D-01:** Curated practical set of ~30-50 scales — major, natural/harmonic/melodic minor, all 7 modes (Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian), major/minor pentatonic, blues, whole tone, diminished (whole-half and half-whole), chromatic, bebop scales, and other commonly used scales
- **D-02:** Each scale entry includes a `category` field (e.g., "modal", "pentatonic", "symmetric", "minor variant", "bebop") for grouping/filtering
- **D-03:** Interval patterns represented as semitone step lists (e.g., major = `[2, 2, 1, 2, 2, 2, 1]`)

### Scale Detection Strategy
- **D-04:** `detect_scales_from_notes` ranks by coverage percentage (how many input notes belong to the scale), with tiebreak by scale simplicity (major/minor before exotic)
- **D-05:** Returns top 5 ranked candidates (consistent with chord identification pattern but slightly broader for scales)
- **D-06:** Each candidate reports coverage percentage — no extra detail like out-of-scale notes or characteristic notes

### Related Scale Relationships
- **D-07:** `get_related_scales` exposes three relationship types: parallel (same root, different quality), relative (same key signature), and modes of parent scale
- **D-08:** No enharmonic equivalents in output — excluded to reduce noise
- **D-09:** Output grouped by relationship type as a dict: `{"parallel": [...], "relative": [...], "modes": [...]}`

### Harmonic/Melodic Minor Handling
- **D-10:** Harmonic and melodic minor are first-class citizens — fully integrated into all 5 scale tools (list, pitches, validation, detection, relationships)
- **D-11:** Extend existing `get_diatonic_chords` tool to support harmonic and melodic minor scale types (adds augmented III+, diminished vii°, etc.)

### Carried Forward from Phase 14
- **D-12:** Library code in `MCP_Server/theory/scales.py`, tools in `MCP_Server/tools/theory.py` (D-01, D-02 from Phase 14)
- **D-13:** Barrel exports from `MCP_Server/theory/__init__.py` (D-03 from Phase 14)
- **D-14:** No prefix on tool names — `list_scales`, not `theory_list_scales` (D-15 from Phase 14)
- **D-15:** MIDI validation (0-127) at tool boundary layer, not in library functions (D-16 from Phase 14)
- **D-16:** Rich note objects `{"midi": int, "name": str}` for pitch output (D-04/D-05 from Phase 14)
- **D-17:** `json.dumps()` returns on success, `format_error()` on error (D-06, D-07 from Phase 14)
- **D-18:** Lazy music21 imports inside theory/ functions (D-14 from Phase 14)
- **D-19:** C4 = MIDI 60 scientific pitch notation (D-17 from Phase 14)

### Claude's Discretion
- Internal `scales.py` library API design (function signatures, helper utilities, music21 scale object handling)
- How to map scale names to music21 scale types internally
- Simplicity scoring heuristic for scale detection ranking tiebreak
- Curated scale list composition (exact selection of ~30-50 scales within the stated categories)
- Test organization and edge case selection
- How to extend `get_diatonic_chords` internally (refactor vs. add conditional logic)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Theory Module (Phase 14-15 output)
- `MCP_Server/theory/__init__.py` — Barrel exports pattern (add new scale functions here)
- `MCP_Server/theory/pitch.py` — Reference library module: lazy imports, music21 patterns, `_force_sharp()`, `_format_note_name()`, `_parse_note_name()`
- `MCP_Server/theory/chords.py` — Chord library module: lazy import pattern, `get_diatonic_chords()` function to extend for harmonic/melodic minor
- `MCP_Server/tools/theory.py` — Tool module: @mcp.tool() pattern, MIDI validation, json.dumps/format_error, existing chord + pitch tools

### Codebase Patterns
- `MCP_Server/connection.py` — `format_error()` utility for error responses
- `MCP_Server/server.py` — FastMCP server setup, `mcp` instance creation

### Testing
- `tests/conftest.py` — `mcp_server` fixture for tool integration tests
- `tests/test_theory.py` — Phase 14-15 theory tests (pattern for new scale tests)

### Requirements
- `.planning/REQUIREMENTS.md` — SCLE-01 through SCLE-05 acceptance criteria
- `.planning/ROADMAP.md` — Phase 16 deliverables

### Prior Context
- `.planning/phases/14-theory-foundation/14-CONTEXT.md` — Phase 14 decisions (foundation patterns)
- `.planning/phases/15-chord-engine/15-CONTEXT.md` — Phase 15 decisions (chord patterns, deferred harmonic/melodic minor)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/theory/pitch.py` — `_get_pitch_module()` lazy import pattern, `_force_sharp()`, `_format_note_name()`, `_parse_note_name()` — all reusable for scale operations
- `MCP_Server/theory/chords.py` — Lazy import getters (`_get_key_module()`, `_get_pitch_module()`) can be reused or shared for scale operations
- `MCP_Server/theory/__init__.py` — Barrel export pattern to extend with scale functions
- `MCP_Server/tools/theory.py` — Existing tool file to add 5 new tool functions to

### Established Patterns
- Lazy music21 import via module-level `_module = None` + getter function
- Rich note objects: `{"midi": int, "name": str}` (from Phase 14 pitch tools)
- Tool boundary validation (0-127 MIDI range) with `format_error()` for out-of-range
- `json.dumps(result, indent=2)` for all tool returns
- Aliased imports (e.g., `_build_chord`) to avoid name collision between tool function and library function

### Integration Points
- `MCP_Server/theory/__init__.py` — Add scale function exports
- `MCP_Server/tools/theory.py` — Add 5 new @mcp.tool() functions
- `MCP_Server/theory/chords.py` — Modify `get_diatonic_chords()` to accept harmonic/melodic minor
- `tests/test_theory.py` — Add scale test cases (both unit and integration)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

- Function labels (tonic/subdominant/dominant) for diatonic chords — future enhancement (carried from Phase 15)
- Available tensions per diatonic degree — future enhancement (carried from Phase 15)
- Slash chord notation output — could add later alongside inversion labels (carried from Phase 15)
- Enharmonic equivalent scale relationships — excluded from get_related_scales for now

</deferred>

---

*Phase: 16-scale-mode-explorer*
*Context gathered: 2026-03-24*
