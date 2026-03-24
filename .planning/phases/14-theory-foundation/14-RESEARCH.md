# Phase 14: Theory Foundation — Research

**Date:** 2026-03-24
**Phase:** 14-theory-foundation
**Researcher:** Inline (agent timeout recovery)

## Executive Summary

Phase 14 integrates music21 (v9.9.1) as the theory engine, establishes the `MCP_Server/theory/` package, and delivers working MIDI↔note mapping tools. All theory logic is server-side only — no Remote Script changes needed. The implementation is straightforward: music21 handles the heavy lifting; we wrap it in a clean library layer and expose MCP tools.

## Key Findings

### music21 Integration

**Version:** 9.9.1 (installed and working in the project's Python environment)

**Pitch API:**
- `music21.pitch.Pitch('C4')` — create from note name, `.midi` gives MIDI number (60)
- `music21.pitch.Pitch(midi=61)` — create from MIDI, `.nameWithOctave` gives "C#4"
- Default enharmonic: sharps (C# not Db) — matches user decision D-12
- Key-aware spelling available via `pitch.simplifyEnharmonic(keyContext=key.Key('Ab'))`

**Import timing:** ~256ms for first `import music21` — validates lazy import decision (D-14). Subsequent imports are cached by Python.

**Octave convention:** music21 uses C4 = MIDI 60 (scientific pitch notation) — matches D-17.

### Existing Codebase Patterns

**Tool module pattern** (from `MCP_Server/tools/notes.py` and others):
```python
import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error
from MCP_Server.server import mcp

@mcp.tool()
def tool_name(ctx: Context, param: type) -> str:
    try:
        # logic
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error("Error message", detail=str(e), suggestion="...")
```

**Tool registration:** Import in `MCP_Server/tools/__init__.py` triggers `@mcp.tool()` decorators.

**Test pattern** (from `tests/conftest.py`):
- `mcp_server` fixture returns live FastMCP instance
- `mock_connection` patches `get_ableton_connection` — NOT needed for theory (pure computation)
- Tests use `await mcp_server.call_tool("tool_name", {"param": value})`

**Packaging** (`pyproject.toml`):
- Dependencies in `[project.dependencies]`: currently `["mcp[cli]>=1.3.0"]`
- Packages in `[tool.setuptools]`: currently `["MCP_Server", "MCP_Server.tools"]`
- Need to add `music21` to dependencies and `MCP_Server.theory` to packages

### MIDI Range

Ableton uses MIDI 0-127. music21's `Pitch(midi=N)` accepts any integer but values outside 0-127 are meaningless for Ableton. Validation at tool boundary (D-16) is the right approach — `format_error()` for out-of-range inputs.

### Lazy Import Pattern

Recommended approach for lazy music21 import:

```python
# MCP_Server/theory/pitch.py
_music21_pitch = None

def _get_pitch_module():
    global _music21_pitch
    if _music21_pitch is None:
        from music21 import pitch as _m21_pitch
        _music21_pitch = _m21_pitch
    return _music21_pitch
```

This caches the import after first use. Alternative: use `functools.lru_cache` on an import helper.

## Technical Approach

### Module Structure

```
MCP_Server/
├── theory/
│   ├── __init__.py          # Barrel exports: midi_to_note, note_to_midi
│   └── pitch.py             # Pitch mapping utilities (Phase 14)
│                             # Future: chords.py (15), scales.py (16),
│                             #         progressions.py (17), analysis.py (18),
│                             #         voicing.py (19)
├── tools/
│   ├── __init__.py           # Add: from . import theory
│   └── theory.py             # MCP tool definitions for theory
└── server.py                 # Unchanged
```

### Output Format

Per decisions D-04, D-05, D-06, D-07:

```json
{
  "midi": 60,
  "name": "C4",
  "octave": 4,
  "pitch_class": "C"
}
```

For `note_to_midi`:
```json
{
  "name": "C4",
  "midi": 60
}
```

### Test Strategy

**Unit tests** (`tests/test_theory.py`):
- Test `MCP_Server.theory.pitch` functions directly
- Cover: all 128 MIDI values, enharmonic edge cases, invalid inputs, boundary values (0, 127)

**Integration tests** (same file or separate):
- Test MCP tools via `mcp_server.call_tool()`
- Verify JSON output format matches decisions
- Verify error handling for invalid inputs

No `mock_connection` needed — theory tools don't call Ableton.

### Requirements Mapping

| Requirement | What it needs | Covered by |
|-------------|---------------|------------|
| THRY-01 | music21 installed and importable | pyproject.toml + import verification test |
| THRY-02 | Theory engine module structure | theory/ package + tools/theory.py registration |
| THRY-03 | Bidirectional MIDI↔note mapping | pitch.py + midi_to_note/note_to_midi tools |

### Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| music21 import time too slow | Low (256ms measured) | Lazy import pattern |
| music21 version conflicts | Low (only dep is mcp[cli]) | Pin music21>=9.0 |
| Enharmonic edge cases | Medium | Comprehensive test coverage for all 128 MIDI values |
| music21 suppresses urllib3 warnings | Low (cosmetic) | Ignore or filter in logging config |

## Validation Architecture

### Testable Invariants

1. **Roundtrip consistency:** `note_to_midi(midi_to_note(n)) == n` for all n in 0-127
2. **Name format:** All note names match pattern `[A-G][#b]?\d+`
3. **MIDI range:** All outputs are integers in 0-127
4. **Octave accuracy:** C4 = 60, C0 = 12, C-1 = 0 (music21 convention)
5. **Enharmonic default:** Without key context, black keys use sharps (C#, D#, F#, G#, A#)
6. **JSON format:** All tool outputs are valid JSON with expected keys

### Coverage Strategy

- Unit: test every MIDI value 0-127 for roundtrip
- Unit: test common note names (C4, A4, Bb3, F#5, etc.)
- Unit: test boundary cases (MIDI 0, 127, -1, 128)
- Integration: test tool registration (tools appear in MCP server)
- Integration: test tool output format matches decisions

## RESEARCH COMPLETE
