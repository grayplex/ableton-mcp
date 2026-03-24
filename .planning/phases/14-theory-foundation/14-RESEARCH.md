# Phase 14: Theory Foundation - Research

**Researched:** 2026-03-24
**Domain:** music21 integration, MIDI/pitch mapping, MCP tool patterns
**Confidence:** HIGH

## Summary

Phase 14 integrates music21 as the theory engine and establishes `MCP_Server/theory/` as a library package with `pitch.py` containing bidirectional MIDI-to-note conversion. Two MCP tools (`midi_to_note`, `note_to_midi`) are registered via `MCP_Server/tools/theory.py`, proving the full pipeline from music21 through the theory library to Claude-facing MCP tools.

The codebase has a well-established tool pattern (14 existing modules) that theory tools must follow exactly. The key technical challenges are: (1) music21 uses `-` for flats but the REQUIREMENTS.md specifies `b` notation (e.g., "Eb4"), requiring output translation; (2) music21's default MIDI-to-name mapping uses a mix of sharps and flats, but D-12 requires sharps by default -- needing explicit enharmonic correction; (3) lazy importing music21 to avoid 250ms+ startup penalty when theory tools are unused.

**Primary recommendation:** Follow existing tool patterns exactly, add a thin translation layer between music21's internal notation and user-friendly output (replace `-` with `b` for flats), and validate all MIDI values at the tool boundary per D-16.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `MCP_Server/theory/` package organized as one file per domain -- `pitch.py` (Phase 14), then `chords.py`, `scales.py`, `progressions.py`, `analysis.py`, `voicing.py` in subsequent phases
- **D-02:** Single `MCP_Server/tools/theory.py` file for all theory MCP tool definitions (matching flat `tools/` convention)
- **D-03:** Barrel exports from `MCP_Server/theory/__init__.py` -- tools import via `from MCP_Server.theory import midi_to_note`
- **D-04:** All theory tool output includes both MIDI numbers and note names (e.g., `{"midi": 60, "name": "C4"}`)
- **D-05:** Compound results use rich note objects, not flat parallel arrays
- **D-06:** Tools return `json.dumps()` strings, matching existing tool pattern
- **D-07:** Success returns data directly; errors use `format_error()` -- no status envelope wrapper
- **D-08:** Phase 14 ships working MCP tools (`midi_to_note`, `note_to_midi`) -- not just library scaffolding
- **D-09:** Tests are standalone -- no `mock_connection` needed since theory tools are pure computation
- **D-10:** Both unit tests (theory/ library functions) and integration tests (MCP tool calls via `mcp_server` fixture)
- **D-11:** Key-aware enharmonic spelling via music21 default -- C# in A major, Db in Ab major
- **D-12:** When no key context is provided, default to sharps (e.g., `midi_to_note(61)` -> "C#4")
- **D-13:** music21 is a required dependency in `pyproject.toml` `[project.dependencies]`, not optional
- **D-14:** Lazy import -- music21 imported inside theory/ functions on first call, not at module level
- **D-15:** No prefix on theory tool names -- `midi_to_note`, `build_chord`, not `theory_midi_to_note`
- **D-16:** Validate MIDI values (0-127) at the MCP tool boundary layer. Internal theory/ library functions accept any range
- **D-17:** C4 = MIDI 60 (scientific pitch notation, music21 default). Not Ableton's C3 = 60 display convention

### Claude's Discretion
- Theory/ library internal API design (function signatures, helper utilities)
- music21 object conversion patterns (how to wrap/unwrap music21 Pitch, Chord, etc.)
- Test organization within test file(s)
- `pyproject.toml` packaging updates (adding `MCP_Server.theory` to `[tool.setuptools]`)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| THRY-01 | music21 installed as MCP_Server dependency and importable at server startup | music21 9.9.1 verified available; add to pyproject.toml dependencies; lazy import pattern keeps startup fast |
| THRY-02 | Theory engine module (`MCP_Server/tools/theory.py` + `MCP_Server/theory/` library) with music21-powered utilities | Existing tool pattern fully documented; pitch.py provides core utilities; theory.py registers MCP tools |
| THRY-03 | Bidirectional MIDI pitch <-> note name mapping (60 <-> "C4", 63 <-> "Eb4") consistent with Ableton's 0-127 range | music21.pitch.Pitch verified for full 0-127 range; sharp-default and key-aware enharmonic patterns established |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| music21 | 9.9.1 | Music theory computation engine | Decision D-13, battle-tested library with 15+ years of development |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.3 | Test framework | Already in dev dependencies |
| pytest-asyncio | >=0.25 | Async test support | Already in dev dependencies, needed for `mcp_server.call_tool()` |

### Alternatives Considered
None -- music21 is a locked decision from milestone planning.

**Installation:**
```bash
# music21 added to pyproject.toml [project.dependencies], not installed separately
pip install -e ".[dev]"
```

**Version verification:** music21 9.9.1 confirmed as latest via `pip index versions music21` (2026-03-24).

## Architecture Patterns

### Recommended Project Structure
```
MCP_Server/
  theory/
    __init__.py          # Barrel exports: midi_to_note, note_to_midi
    pitch.py             # Core pitch mapping utilities (Phase 14)
  tools/
    __init__.py          # Add theory import for registration
    theory.py            # MCP tool definitions for all theory tools
tests/
  test_theory.py         # Unit + integration tests
```

### Pattern 1: Lazy music21 Import
**What:** Import music21 inside function bodies, not at module level
**When to use:** All theory/ library functions that use music21
**Why:** music21 takes ~250ms to import. Server startup should not pay this cost when theory tools are unused.
**Example:**
```python
# MCP_Server/theory/pitch.py

def midi_to_note_name(midi: int, key_context: str | None = None) -> str:
    """Convert MIDI number to note name. Accepts any MIDI value (no range validation)."""
    from music21 import pitch as m21pitch  # Lazy import

    p = m21pitch.Pitch(midi=midi)
    # ... conversion logic
```

### Pattern 2: Tool Module (matches existing codebase exactly)
**What:** MCP tool in `tools/theory.py` following the established pattern
**Example:**
```python
# MCP_Server/tools/theory.py
import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error
from MCP_Server.server import mcp

@mcp.tool()
def midi_to_note(ctx: Context, midi: int, key: str | None = None) -> str:
    """Convert a MIDI pitch number to a note name..."""
    try:
        if not 0 <= midi <= 127:
            return format_error(
                "MIDI value out of range",
                detail=f"Got {midi}, expected 0-127",
                suggestion="MIDI pitch values must be between 0 and 127"
            )
        from MCP_Server.theory import midi_to_note as _midi_to_note
        result = _midi_to_note(midi, key_context=key)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error("Failed to convert MIDI to note", detail=str(e))
```

### Pattern 3: Barrel Exports
**What:** `__init__.py` re-exports public API from submodules
**Example:**
```python
# MCP_Server/theory/__init__.py
from MCP_Server.theory.pitch import midi_to_note_name, note_name_to_midi  # noqa: F401
```

### Pattern 4: Tool Registration via Import
**What:** Theory tools registered by importing module in `tools/__init__.py`
**Example:**
```python
# MCP_Server/tools/__init__.py
from . import arrangement, audio_clips, ..., theory  # noqa: F401
```

### Anti-Patterns to Avoid
- **Top-level music21 import:** Adds 250ms to server startup even when theory tools are unused. Always lazy-import inside functions.
- **Returning music21 objects directly:** MCP tools must return JSON strings. Always convert to `{"midi": int, "name": str}` format.
- **Using music21's `-` flat notation in output:** music21 represents Eb as `E-`. Must translate to `b` notation (e.g., `E-4` -> `Eb4`) before returning to user.
- **Validating MIDI range inside theory/ library functions:** Per D-16, validation happens at the tool boundary only. Library functions should accept any integer for flexibility.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MIDI to note conversion | Manual arithmetic (midi % 12 lookup table) | `music21.pitch.Pitch(midi=N)` | Handles octave numbering, double sharps/flats, enharmonic spelling correctly |
| Note name parsing | Regex parser for "C#4", "Eb3" etc. | `music21.pitch.Pitch('Eb4')` | Handles all accidental types, validates octave, edge cases |
| Key-aware enharmonic spelling | Custom scale-degree lookup | music21 Key + Scale objects | Music theory is complex; music21 handles all edge cases |

**Key insight:** music21 handles the full complexity of Western pitch notation. Hand-rolling any of this would miss edge cases (double accidentals, octave boundaries at C, key-context spelling).

## Common Pitfalls

### Pitfall 1: music21 Flat Notation
**What goes wrong:** music21 represents flats as `-` (e.g., `E-4` for Eb4). Returning this directly confuses users and doesn't match REQUIREMENTS.md format.
**Why it happens:** music21 uses its own internal notation convention.
**How to avoid:** Always post-process music21 output: `name.replace('-', 'b')` before returning to users.
**Warning signs:** Test output containing `-` instead of `b` in note names.

### Pitfall 2: Default Enharmonic Not All-Sharps
**What goes wrong:** music21's default MIDI-to-name uses a mix: MIDI 63 = `E-4` (Eb), MIDI 68 = `G#4`, MIDI 70 = `B-4` (Bb). D-12 requires all-sharps default.
**Why it happens:** music21 follows standard music notation conventions where some pitches default to flats.
**How to avoid:** When no key context is provided, check if the pitch has a flat accidental (`p.accidental and p.accidental.alter < 0`), and if so, call `p.getEnharmonic()` to get the sharp equivalent.
**Warning signs:** `midi_to_note(63)` returning "Eb4" instead of "D#4" when no key is specified.

**Verified default behavior (music21 9.9.1):**
| MIDI | music21 Default | D-12 Required (sharps) |
|------|----------------|----------------------|
| 61 | C#4 | C#4 (same) |
| 63 | E-4 (Eb) | D#4 (needs correction) |
| 66 | F#4 | F#4 (same) |
| 68 | G#4 | G#4 (same) |
| 70 | B-4 (Bb) | A#4 (needs correction) |

### Pitfall 3: Octave Boundary at C
**What goes wrong:** MIDI note 0 is C-1 in scientific pitch notation. The octave increments at C, not at A.
**Why it happens:** Common misunderstanding of pitch notation.
**How to avoid:** Rely on music21's `Pitch(midi=N).nameWithOctave` which handles this correctly. Do NOT hand-roll octave calculation.
**Warning signs:** Off-by-one octave errors near C/B boundaries.

### Pitfall 4: Conftest Patch Targets
**What goes wrong:** Theory tools don't use `get_ableton_connection`, so adding theory.py to the `_GAC_PATCH_TARGETS` list in conftest.py is unnecessary and wrong.
**Why it happens:** Copy-paste from other tool modules that DO use the connection.
**How to avoid:** Theory tools are pure computation (D-09). Tests should NOT use `mock_connection` fixture. Use `mcp_server` fixture directly.
**Warning signs:** Tests importing or requiring `mock_connection` for theory tools.

### Pitfall 5: note_to_midi Input Parsing
**What goes wrong:** User might pass "C4", "c4", "C 4", or "c#4" -- inconsistent casing and spacing.
**Why it happens:** User input is unpredictable.
**How to avoid:** music21's `Pitch('c#4')` is case-insensitive and handles most input variations. Test edge cases: lowercase, mixed case, with/without spaces.
**Warning signs:** Tool failing on lowercase input like "eb4".

### Pitfall 6: music21 Environment Warning
**What goes wrong:** music21 may emit a `UserWarning` about not finding a MusicXML reader or MuseScore on the system. This is harmless for pitch operations but can pollute logs.
**Why it happens:** music21 checks for external tools on first import.
**How to avoid:** This can be safely ignored -- pitch/chord/scale operations don't need MuseScore. If log noise is a concern, filter the warning in the lazy import wrapper.
**Warning signs:** Warnings in test output about missing MuseScore.

## Code Examples

Verified patterns from direct testing against music21 9.9.1:

### MIDI to Note Name (sharp default, no key context)
```python
# Source: Verified via direct testing 2026-03-24
from music21 import pitch as m21pitch

def _midi_to_note_name(midi: int) -> str:
    """Convert MIDI to note name with sharp default (D-12)."""
    p = m21pitch.Pitch(midi=midi)
    # music21 defaults some notes to flats; force sharps per D-12
    if p.accidental and p.accidental.alter < 0:
        p = p.getEnharmonic()
    # Replace music21's '-' flat notation with 'b'
    return p.nameWithOctave.replace('-', 'b')
```

### MIDI to Note Name (key-aware enharmonic, D-11)
```python
# Source: Verified via direct testing 2026-03-24
from music21 import pitch as m21pitch, key as m21key

def _midi_to_note_name_in_key(midi: int, key_str: str) -> str:
    """Convert MIDI to note name with key-aware enharmonic spelling."""
    p = m21pitch.Pitch(midi=midi)
    enh = p.getEnharmonic()
    k = m21key.Key(key_str)
    scale_names = [sp.name for sp in k.getScale().pitches]
    # Prefer the spelling that matches the key's scale
    if enh.name in scale_names and p.name not in scale_names:
        p = enh
    return p.nameWithOctave.replace('-', 'b')
```

### Note Name to MIDI
```python
# Source: Verified via direct testing 2026-03-24
from music21 import pitch as m21pitch

def _note_name_to_midi(name: str) -> int:
    """Convert note name to MIDI number. music21 accepts 'Eb4', 'C#4', etc."""
    p = m21pitch.Pitch(name)
    return p.midi
```

### MCP Tool Return Format (D-04, D-06, D-07)
```python
# Matches existing tool pattern in MCP_Server/tools/notes.py
import json
result = {"midi": 60, "name": "C4"}
return json.dumps(result, indent=2)

# Error format (from connection.py format_error)
return format_error(
    "MIDI value out of range",
    detail=f"Got {midi}, expected 0-127",
    suggestion="MIDI pitch values must be between 0 and 127"
)
```

### MCP Integration Test Pattern (D-09, D-10)
```python
# Theory tools are pure computation -- NO mock_connection needed
async def test_midi_to_note_c4(mcp_server):
    result = await mcp_server.call_tool("midi_to_note", {"midi": 60})
    text = result[0][0].text
    data = json.loads(text)
    assert data["midi"] == 60
    assert data["name"] == "C4"

async def test_midi_to_note_out_of_range(mcp_server):
    result = await mcp_server.call_tool("midi_to_note", {"midi": 128})
    text = result[0][0].text
    assert "Error" in text
```

## MIDI Range Reference (Verified)

```
MIDI 0   = C-1  (lowest)
MIDI 21  = A0   (piano low end)
MIDI 60  = C4   (middle C, scientific pitch notation)
MIDI 69  = A4   (concert A, 440Hz)
MIDI 108 = C8   (piano high end)
MIDI 127 = G9   (highest)
```

Note: Ableton displays C3 for MIDI 60, but per D-17 we use scientific pitch notation (C4 = 60), which is music21's default.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| music21 v7-8 | music21 v9.9.1 | 2024-2025 | Python 3.10+ required, improved performance |
| `pitch.Pitch.midi` was property | Still property in v9.9.1 | Stable API | No migration needed |

**Stable:** music21's pitch API has been stable across major versions. The Pitch class, midi property, nameWithOctave, getEnharmonic() are long-standing APIs unlikely to change.

## Open Questions

1. **music21 import warning suppression**
   - What we know: music21 may warn about missing MuseScore/Lilypond on first import
   - What's unclear: Whether this appears in MCP server logs and causes noise
   - Recommendation: Ignore for now; address if it becomes a test/log noise issue

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | Yes | 3.11.14 | -- |
| music21 | Theory engine | Yes | 9.9.1 | -- |
| pytest | Testing | Yes | >=8.3 (in dev deps) | -- |
| pytest-asyncio | Async tool tests | Yes | >=0.25 (in dev deps) | -- |

**Missing dependencies:** None. All required dependencies are available.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.25+ |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/test_theory.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| THRY-01 | music21 importable, in dependencies | unit | `pytest tests/test_theory.py::test_music21_importable -x` | Wave 0 |
| THRY-02 | Theory tools registered with FastMCP | integration | `pytest tests/test_theory.py::test_theory_tools_registered -x` | Wave 0 |
| THRY-02 | Theory library exports work | unit | `pytest tests/test_theory.py::test_theory_barrel_exports -x` | Wave 0 |
| THRY-03 | MIDI to note (sharp default) | unit+integration | `pytest tests/test_theory.py::test_midi_to_note_sharp_default -x` | Wave 0 |
| THRY-03 | Note to MIDI | unit+integration | `pytest tests/test_theory.py::test_note_to_midi -x` | Wave 0 |
| THRY-03 | MIDI to note (key-aware enharmonic) | unit+integration | `pytest tests/test_theory.py::test_midi_to_note_key_aware -x` | Wave 0 |
| THRY-03 | Full MIDI range 0-127 | unit | `pytest tests/test_theory.py::test_full_midi_range -x` | Wave 0 |
| THRY-03 | MIDI out-of-range error at tool boundary | integration | `pytest tests/test_theory.py::test_midi_out_of_range -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_theory.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_theory.py` -- covers THRY-01, THRY-02, THRY-03 (all unit + integration tests)

## Sources

### Primary (HIGH confidence)
- music21 9.9.1 -- direct API testing against installed library (pitch.Pitch, key.Key, getEnharmonic, nameWithOctave)
- Existing codebase -- `MCP_Server/tools/notes.py`, `tools/__init__.py`, `server.py`, `connection.py`, `tests/conftest.py`, `pyproject.toml`

### Secondary (MEDIUM confidence)
- music21 import timing -- measured at 250ms for first `from music21 import pitch` (validates lazy import decision)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- music21 9.9.1 verified installed and tested directly
- Architecture: HIGH -- existing codebase patterns are clear and consistent across 14 tool modules
- Pitfalls: HIGH -- all pitfalls verified through direct testing (flat notation, enharmonic defaults, range boundaries)

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable domain, music21 API unlikely to change)
