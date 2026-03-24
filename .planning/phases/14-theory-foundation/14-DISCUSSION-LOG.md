# Phase 14: Theory Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 14-theory-foundation
**Areas discussed:** Module structure, Output format, Foundation scope, Enharmonic naming, Dependency type, Octave convention, Import strategy, Tool naming, MIDI range validation

---

## Module Structure

| Option | Description | Selected |
|--------|-------------|----------|
| One file per domain | theory/chords.py, theory/scales.py, etc. Matches tools/ organization | ✓ |
| Single utils module | theory/utils.py with all wrappers. Simpler but grows large | |

**User's choice:** One file per domain
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Single tools/theory.py | All theory tool defs in one file. Matches existing flat tools/ pattern | ✓ |
| Sub-package tools/theory/ | Mirrors library structure. Breaks flat convention | |

**User's choice:** Single tools/theory.py
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Barrel exports | theory/__init__.py exports all public functions | ✓ |
| Direct submodule imports | Import from specific submodules directly | |

**User's choice:** Barrel exports
**Notes:** None

---

## Output Format

| Option | Description | Selected |
|--------|-------------|----------|
| Both MIDI + names | {midi: 60, name: "C4"} — human and machine readable | ✓ |
| MIDI numbers only | {pitches: [60, 64, 67]} — minimal, matches get_notes | |

**User's choice:** Both MIDI + names
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Rich objects | [{midi: 60, name: "C4"}, ...] — notes as objects | ✓ |
| Flat parallel arrays | {midi: [60, 64], names: ["C4", "E4"]} — parallel arrays | |

**User's choice:** Rich objects
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| JSON strings | json.dumps() matching existing tools | ✓ |
| Native Python objects | Raw dicts, let FastMCP serialize | |

**User's choice:** JSON strings
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Wrap in status envelope | {status: "success", chord: "Cmaj7", ...} | |
| Direct data + format_error | Data directly on success, format_error on failure | ✓ |

**User's choice:** Direct data + format_error
**Notes:** None

---

## Foundation Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Pitch tools ship | Working midi_to_note / note_to_midi MCP tools in Phase 14 | ✓ |
| Library only, no tools | Package structure and pitch utils, tools start Phase 15 | |

**User's choice:** Pitch tools ship
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Both unit + integration | Unit tests for theory lib + integration via mcp_server fixture | ✓ |
| Unit tests only | Only test theory/ library functions directly | |

**User's choice:** Both unit + integration
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone tests | No mock_connection needed — theory is pure computation | ✓ |
| Match existing test pattern | Use mock_connection + mcp_server fixtures | |

**User's choice:** Standalone tests
**Notes:** None

---

## Enharmonic Naming

| Option | Description | Selected |
|--------|-------------|----------|
| Key-aware / music21 default | C# in A major, Db in Ab major. Musically correct | ✓ |
| Always sharps | Simple but wrong in flat keys | |
| Always flats | Simple but wrong in sharp keys | |

**User's choice:** Key-aware / music21 default
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Sharps default, key overrides | midi_to_note(60) → "C4" with sharps; key param for context | ✓ |
| Key always required | No default behavior, key param mandatory | |

**User's choice:** Sharps default, key overrides
**Notes:** None

---

## Dependency Type

| Option | Description | Selected |
|--------|-------------|----------|
| Required dependency | music21 in [project.dependencies]. Always installed | ✓ |
| Optional extra | pip install ableton-mcp[theory]. Users opt-in | |

**User's choice:** Required dependency
**Notes:** None

---

## Octave Convention

| Option | Description | Selected |
|--------|-------------|----------|
| C4 = MIDI 60 | Scientific pitch notation, music21 default, ISO standard | ✓ |
| C3 = MIDI 60 | Ableton's display convention | |
| Configurable | Support both with parameter | |

**User's choice:** C4 = MIDI 60
**Notes:** None

---

## Import Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy import | Import music21 inside functions on first call. Fast startup | ✓ |
| Eager import | Import at module level. Simpler but slower startup | |

**User's choice:** Lazy import
**Notes:** None

---

## Tool Naming

| Option | Description | Selected |
|--------|-------------|----------|
| No prefix | midi_to_note, build_chord. Clean and concise | ✓ |
| theory_ prefix | theory_midi_to_note. Explicit grouping, avoids collision | |

**User's choice:** No prefix
**Notes:** None

---

## MIDI Range Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Validate at tool boundary | 0-127 check at MCP tool layer. Internal functions accept any range | ✓ |
| No validation | Let music21 handle whatever it handles | |

**User's choice:** Validate at tool boundary
**Notes:** None

---

## Claude's Discretion

- Theory/ library internal API design
- music21 object conversion patterns
- Test organization
- pyproject.toml packaging updates

## Deferred Ideas

None — discussion stayed within phase scope
