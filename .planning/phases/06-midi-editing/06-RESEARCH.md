# Phase 6: MIDI Editing - Research

**Researched:** 2026-03-14
**Domain:** Ableton Live Python API -- MIDI note manipulation via Remote Script
**Confidence:** HIGH

## Summary

Phase 6 implements five MIDI note operations: add, read, remove, quantize, and transpose. The context session has already locked the implementation decisions for all five operations including API choices, response formats, validation rules, and parameter designs.

The core technical challenge is migrating from the old `set_notes(tuple)` API to the Live 11+ `add_new_notes` API using `Live.Clip.MidiNoteSpecification` objects, and using `get_notes_extended` / `remove_notes_extended` for reading and removing notes. Quantize and transpose are computed in handler code (no Live API for these) -- they read notes with `get_notes_extended`, compute new values, then write back using `remove_notes_extended` + `add_new_notes`.

The project's established patterns (mixin handlers, `@command` decorator, `_resolve_clip_slot`, JSON response format, MCP tool wrappers) carry directly into this phase. The codebase already has a `NoteHandlers` mixin and an `add_notes_to_clip` MCP tool -- both need modification rather than creation from scratch.

**Primary recommendation:** Rewrite handlers/notes.py with 5 handler methods using Live 11+ APIs, then add/update MCP tools for all 5 operations. Quantize and transpose are handler-side computations that read-modify-write note data.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Note addition:** Append mode using Live 11+ `add_new_notes` API -- existing notes stay, new notes are added on top. Replace the current `set_notes(tuple)` implementation. Return `{note_count: N, clip_name: "..."}`. Keep `mute` parameter. Validate: pitch 0-127, velocity 1-127, duration > 0.
- **Get notes response:** Return core 5 properties per note: pitch, start_time, duration, velocity, mute. Always return ALL notes -- no time/pitch range filtering. Include note_count alongside notes array: `{note_count: N, notes: [...]}`. Sort by start_time ascending, ties broken by pitch (low to high).
- **Remove notes targeting:** Time + pitch range parameters: start_time_min, start_time_max, pitch_min, pitch_max -- all optional. Omitting a param means "no constraint" on that dimension. Return `{removed_count: N}`.
- **Quantize behavior:** Operates on ALL notes in clip. Grid size as float in beats (0.25 for 1/16th, 0.5 for 1/8th, 1.0 for 1/4). Strength defaults to 100% (full snap to grid), adjustable 0.0-1.0. Quantizes start times only.
- **Transpose behavior:** Operates on ALL notes in clip. Semitones as integer (positive = up, negative = down). Error if ANY note would go out of MIDI range (0-127). Error message includes the offending note's current pitch and the requested transposition.

### Claude's Discretion
- Whether remove_notes with no range params removes all notes or requires at least one range constraint
- Internal implementation of quantize algorithm (snap-to-nearest-grid-point)
- Whether quantize/transpose responses include the updated note count

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MIDI-01 | User can add MIDI notes to a clip (pitch, start, duration, velocity) | Live 11+ `add_new_notes` API with `MidiNoteSpecification` objects. Existing handler rewrite required. |
| MIDI-02 | User can read back all notes from a clip | `get_notes_extended(from_pitch=0, pitch_span=128, from_time=0, time_span=clip.length)` returns MidiNoteVector of MidiNote objects with pitch/start_time/duration/velocity/mute properties. |
| MIDI-03 | User can remove notes from a clip (by time/pitch range) | `remove_notes_extended(from_pitch, pitch_span, from_time, time_span)` API. Translate user's min/max params to from/span format. |
| MIDI-04 | User can quantize notes in a clip (grid size, strength) | Handler-side computation: read all notes, compute quantized start_times, write back via remove + add. No Live API for quantize. |
| MIDI-05 | User can transpose all notes in a clip by semitones | Handler-side computation: read all notes, validate range, add semitones to each pitch, write back via remove + add. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Live.Clip.MidiNoteSpecification | Live 11+ | Create note objects for `add_new_notes` | Official API for adding notes since Live 11; replaces old tuple-based `set_notes` |
| Live.Clip.MidiNote | Live 11+ | Note objects returned by `get_notes_extended` | Official read API; provides pitch, start_time, duration, velocity, mute properties |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `_resolve_clip_slot` | local (handlers/clips.py) | Validate track/clip indices | Every handler that operates on a clip slot |
| `@command` decorator | local (registry.py) | Register handler commands | All 5 new/updated handler methods |
| `format_error` | local (connection.py) | AI-friendly error messages | All MCP tool error handlers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `add_new_notes` (Live 11+) | `set_notes` (old API) | Old API overwrites all notes; new API appends. Decision is locked: use `add_new_notes`. |
| `get_notes_extended` (Live 11+) | `get_notes` (old API) | Old API returns tuples without note_id; new API returns MidiNote objects with richer data. Use new API. |
| `remove_notes_extended` (Live 11+) | Old `remove_notes` | Old API may not work correctly with MPE data in Live 11+. Use new API. |

## Architecture Patterns

### Handler Layer (Remote Script side)

```
AbletonMCP_Remote_Script/
├── handlers/
│   ├── notes.py          # NoteHandlers mixin -- 5 commands
│   └── clips.py          # _resolve_clip_slot (import and reuse)
```

### MCP Tool Layer (Server side)

```
MCP_Server/
├── tools/
│   ├── clips.py          # Keep existing tools; update add_notes_to_clip
│   └── notes.py          # NEW: get_notes, remove_notes, quantize_notes, transpose_notes
├── connection.py         # Add new commands to _WRITE_COMMANDS set
```

### Pattern 1: Reuse _resolve_clip_slot for Clip Access
**What:** Every note handler needs to resolve a clip from track_index + clip_index. Reuse the validated helper from clips.py.
**When to use:** Every handler in notes.py
**Example:**
```python
# Source: handlers/clips.py (existing pattern)
from AbletonMCP_Remote_Script.handlers.clips import _resolve_clip_slot

@command("get_notes")
def _get_notes(self, params):
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)
    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip
    # ... operate on clip
```

### Pattern 2: Read-Modify-Write for Quantize/Transpose
**What:** Operations that transform note data need to read all notes, compute changes, clear old notes, write new notes.
**When to use:** Quantize and transpose (no direct Live API for these).
**Example:**
```python
# Read all notes
notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
# Compute changes (in a list for modification)
# Remove all existing notes
clip.remove_notes_extended(0, 128, 0.0, clip.length)
# Write modified notes back
import Live
new_specs = []
for note in modified_notes:
    new_specs.append(Live.Clip.MidiNoteSpecification(
        pitch=note["pitch"],
        start_time=note["start_time"],
        duration=note["duration"],
        velocity=note["velocity"],
        mute=note["mute"],
    ))
clip.add_new_notes(tuple(new_specs))
```

### Pattern 3: MCP Tool with Optional Parameters
**What:** Remove notes has all-optional range params. Build params dict conditionally.
**When to use:** Any tool with optional parameters.
**Example:**
```python
# Source: MCP_Server/tools/clips.py set_clip_loop pattern
@mcp.tool()
def remove_notes(
    ctx: Context,
    track_index: int,
    clip_index: int,
    pitch_min: int | None = None,
    pitch_max: int | None = None,
    start_time_min: float | None = None,
    start_time_max: float | None = None,
) -> str:
    params: dict = {"track_index": track_index, "clip_index": clip_index}
    if pitch_min is not None:
        params["pitch_min"] = pitch_min
    # ... etc
```

### Anti-Patterns to Avoid
- **Using `set_notes` instead of `add_new_notes`:** `set_notes` overwrites all existing notes. The decision is locked to use append-mode `add_new_notes`.
- **Using old `get_notes` API:** Returns tuples without note_id. Use `get_notes_extended` which returns MidiNote objects with all properties.
- **Passing dicts to `add_new_notes`:** Will throw "No registered converter" error. Must use `Live.Clip.MidiNoteSpecification` objects wrapped in a tuple.
- **Passing a list to `add_new_notes`:** Must pass a tuple, not a list. Use `tuple(specs_list)`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Clip slot validation | Custom track/clip bounds checking | `_resolve_clip_slot()` from handlers/clips.py | Already handles all edge cases with good error messages |
| Note addition | Manual `set_notes` with tuple building | `Live.Clip.MidiNoteSpecification` + `add_new_notes` | Old API overwrites; new API appends correctly |
| Note reading | Manual `get_notes` + tuple parsing | `get_notes_extended` | Returns proper MidiNote objects with all properties |
| Note removal | Manual `remove_notes` | `remove_notes_extended` | Required for MPE compatibility in Live 11+ |
| Error formatting | Custom error strings | `format_error(title, detail, suggestion)` | Established pattern for AI-friendly errors |

**Key insight:** The Live 11+ note API (`add_new_notes`, `get_notes_extended`, `remove_notes_extended`) is the only correct approach. The old tuple-based APIs (`set_notes`, `get_notes`, `remove_notes`) have compatibility issues with MPE data and should not be used.

## Common Pitfalls

### Pitfall 1: Passing Dicts Instead of MidiNoteSpecification Objects
**What goes wrong:** `add_new_notes` throws "No registered converter was able to produce a C++ rvalue of type struct NPythonClip::TNoteSpecification from this Python object"
**Why it happens:** `add_new_notes` expects `Live.Clip.MidiNoteSpecification` objects, not plain Python dicts
**How to avoid:** Always create `Live.Clip.MidiNoteSpecification(pitch=..., start_time=..., duration=..., velocity=..., mute=...)` objects
**Warning signs:** TypeError or converter error from Ableton

### Pitfall 2: Passing a List Instead of a Tuple to add_new_notes
**What goes wrong:** `add_new_notes` may reject a list argument
**Why it happens:** The API specifically expects a tuple (Python iterable, but tuple is the documented type)
**How to avoid:** Always wrap with `tuple()`: `clip.add_new_notes(tuple(note_specs))`
**Warning signs:** TypeError about argument type

### Pitfall 3: remove_notes_extended Uses from/span, Not min/max
**What goes wrong:** Wrong notes get removed or no notes removed
**Why it happens:** API takes `(from_pitch, pitch_span, from_time, time_span)` not `(pitch_min, pitch_max, time_min, time_max)`. Span is a relative offset from the start, not an absolute end value.
**How to avoid:** Convert user's min/max to from/span: `from_pitch = pitch_min`, `pitch_span = pitch_max - pitch_min + 1`, `from_time = start_time_min`, `time_span = start_time_max - start_time_min`
**Warning signs:** Tests show unexpected notes remaining or being removed

### Pitfall 4: get_notes_extended Time Span Too Short
**What goes wrong:** Not all notes are returned when reading "all notes"
**Why it happens:** `time_span` must cover the full clip length. Notes at the very end may be missed if span is too short.
**How to avoid:** Use `clip.length` as the time_span: `clip.get_notes_extended(0, 128, 0.0, clip.length)`
**Warning signs:** Missing notes near the end of a clip

### Pitfall 5: Quantize Rounding Ambiguity
**What goes wrong:** Notes at exactly the midpoint between grid lines could round unpredictably
**Why it happens:** Standard quantize uses nearest-grid-point, but midpoint behavior varies
**How to avoid:** Use `round(start_time / grid_size) * grid_size` -- Python's round() uses banker's rounding, which is fine for this use case
**Warning signs:** None -- this is a correctness detail

### Pitfall 6: Transpose Range Check Must Be Pre-Validated
**What goes wrong:** If validation happens after modification, some notes may be transposed while others are not
**Why it happens:** Decision is locked: "Error if ANY note would go out of MIDI range" -- this means check ALL notes before modifying ANY
**How to avoid:** First pass: check all notes for range validity. Second pass: apply transpose only if all pass.
**Warning signs:** Partial transposition (some notes moved, others at bounds)

### Pitfall 7: Forgetting to Update _WRITE_COMMANDS in connection.py
**What goes wrong:** New write commands get READ timeout (10s) instead of WRITE timeout (15s)
**Why it happens:** `_timeout_for()` checks `_WRITE_COMMANDS` frozenset; new commands must be added
**How to avoid:** Add all new write commands to `_WRITE_COMMANDS` in connection.py
**Warning signs:** Intermittent timeouts on note operations

### Pitfall 8: Import Live Module at Module Level in Remote Script
**What goes wrong:** ImportError or NameError when handler runs
**Why it happens:** `Live` module is only available inside Ableton's Python runtime. Import at module level is fine for Remote Script code but will fail in tests.
**How to avoid:** Import `Live` at the top of handlers/notes.py (this is Remote Script code, not testable outside Ableton anyway)
**Warning signs:** ImportError mentioning `Live`

## Code Examples

Verified patterns from official sources and existing codebase:

### Adding Notes with add_new_notes (Live 11+ API)
```python
# Source: Ableton Forum (verified), Live 11 API docs
import Live

@command("add_notes_to_clip", write=True)
def _add_notes_to_clip(self, params):
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)
    notes = params.get("notes", [])

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip

    # Validate and build MidiNoteSpecification objects
    note_specs = []
    for note in notes:
        pitch = note.get("pitch", 60)
        start_time = note.get("start_time", 0.0)
        duration = note.get("duration", 0.25)
        velocity = note.get("velocity", 100)
        mute = note.get("mute", False)

        # Validation with AI-friendly error messages
        if not (0 <= pitch <= 127):
            raise ValueError(
                f"Pitch {pitch} out of range (0-127)"
            )
        if velocity < 1 or velocity > 127:
            raise ValueError(
                f"Velocity {velocity} out of range (1-127)"
            )
        if duration <= 0:
            raise ValueError(
                f"Duration {duration} must be > 0"
            )

        note_specs.append(Live.Clip.MidiNoteSpecification(
            pitch=pitch,
            start_time=start_time,
            duration=duration,
            velocity=velocity,
            mute=mute,
        ))

    clip.add_new_notes(tuple(note_specs))
    return {"note_count": len(notes), "clip_name": clip.name}
```

### Reading Notes with get_notes_extended
```python
# Source: Live 11 API docs (structure-void.com)
@command("get_notes")
def _get_notes(self, params):
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip

    # Get all notes in the clip
    midi_notes = clip.get_notes_extended(0, 128, 0.0, clip.length)

    # Convert MidiNote objects to dicts
    notes = []
    for note in midi_notes:
        notes.append({
            "pitch": note.pitch,
            "start_time": note.start_time,
            "duration": note.duration,
            "velocity": note.velocity,
            "mute": note.mute,
        })

    # Sort: start_time ascending, ties broken by pitch ascending
    notes.sort(key=lambda n: (n["start_time"], n["pitch"]))

    return {"note_count": len(notes), "notes": notes}
```

### Removing Notes with remove_notes_extended
```python
# Source: Live 11 API docs
# API: remove_notes_extended(from_pitch, pitch_span, from_time, time_span)

@command("remove_notes", write=True)
def _remove_notes(self, params):
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip

    # Convert optional min/max to from/span format
    pitch_min = params.get("pitch_min", 0)
    pitch_max = params.get("pitch_max", 127)
    start_time_min = params.get("start_time_min", 0.0)
    start_time_max = params.get("start_time_max", clip.length)

    from_pitch = pitch_min
    pitch_span = pitch_max - pitch_min + 1
    from_time = start_time_min
    time_span = start_time_max - start_time_min

    # Count notes before removal for response
    notes_before = clip.get_notes_extended(from_pitch, pitch_span, from_time, time_span)
    count = len(notes_before)

    clip.remove_notes_extended(from_pitch, pitch_span, from_time, time_span)
    return {"removed_count": count}
```

### Quantize Pattern (Handler-Side Computation)
```python
import Live

@command("quantize_notes", write=True)
def _quantize_clip_notes(self, params):
    # ... resolve clip ...
    grid_size = params.get("grid_size", 0.25)
    strength = params.get("strength", 1.0)

    # Read all notes
    midi_notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
    if len(midi_notes) == 0:
        return {"quantized_count": 0}

    # Extract note data
    note_data = []
    for note in midi_notes:
        note_data.append({
            "pitch": note.pitch,
            "start_time": note.start_time,
            "duration": note.duration,
            "velocity": note.velocity,
            "mute": note.mute,
        })

    # Quantize start times
    for note in note_data:
        original = note["start_time"]
        nearest_grid = round(original / grid_size) * grid_size
        note["start_time"] = original + (nearest_grid - original) * strength

    # Remove all notes and re-add with quantized positions
    clip.remove_notes_extended(0, 128, 0.0, clip.length)
    specs = []
    for note in note_data:
        specs.append(Live.Clip.MidiNoteSpecification(
            pitch=note["pitch"],
            start_time=note["start_time"],
            duration=note["duration"],
            velocity=note["velocity"],
            mute=note["mute"],
        ))
    clip.add_new_notes(tuple(specs))
    return {"quantized_count": len(note_data)}
```

### Transpose Pattern (Pre-Validation Then Apply)
```python
import Live

@command("transpose_notes", write=True)
def _transpose_clip_notes(self, params):
    # ... resolve clip ...
    semitones = params.get("semitones", 0)

    midi_notes = clip.get_notes_extended(0, 128, 0.0, clip.length)
    if len(midi_notes) == 0:
        return {"transposed_count": 0}

    # Pre-validate ALL notes before modifying any
    note_data = []
    for note in midi_notes:
        new_pitch = note.pitch + semitones
        if new_pitch < 0 or new_pitch > 127:
            raise ValueError(
                f"Transposing pitch {note.pitch} by {semitones} semitones "
                f"would result in {new_pitch}, which is outside MIDI range (0-127)"
            )
        note_data.append({
            "pitch": new_pitch,
            "start_time": note.start_time,
            "duration": note.duration,
            "velocity": note.velocity,
            "mute": note.mute,
        })

    # All validated -- apply
    clip.remove_notes_extended(0, 128, 0.0, clip.length)
    specs = []
    for note in note_data:
        specs.append(Live.Clip.MidiNoteSpecification(
            pitch=note["pitch"],
            start_time=note["start_time"],
            duration=note["duration"],
            velocity=note["velocity"],
            mute=note["mute"],
        ))
    clip.add_new_notes(tuple(specs))
    return {"transposed_count": len(note_data)}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `clip.set_notes(tuple_of_tuples)` | `clip.add_new_notes(tuple_of_MidiNoteSpecs)` | Live 11 (2021) | Old API overwrites all notes; new API appends. Old API loses MPE data. |
| `clip.get_notes(time, pitch, time_span, pitch_span)` | `clip.get_notes_extended(from_pitch, pitch_span, from_time, time_span)` | Live 11 (2021) | Old returns tuples; new returns MidiNote objects with note_id. Parameter order differs. |
| `clip.remove_notes(time, pitch, time_span, pitch_span)` | `clip.remove_notes_extended(from_pitch, pitch_span, from_time, time_span)` | Live 11 (2021) | Required for MPE compatibility. Parameter order differs from old API. |

**Deprecated/outdated:**
- `set_notes`: Overwrites all notes. Replaced by `add_new_notes` (append mode).
- `get_notes`: Returns bare tuples. Replaced by `get_notes_extended` (MidiNote objects).
- `remove_notes`: May break MPE data. Replaced by `remove_notes_extended`.

**IMPORTANT parameter order difference:**
- Old `get_notes(from_time, from_pitch, time_span, pitch_span)` -- time first
- New `get_notes_extended(from_pitch, pitch_span, from_time, time_span)` -- pitch first

## Open Questions

1. **MidiNote.mute property type**
   - What we know: MidiNoteSpecification accepts `mute=True/False` (bool). MidiNote objects should have `.mute` property.
   - What's unclear: Whether `.mute` returns Python `bool` or `int` (0/1). The old tuple API returned 0/1 ints.
   - Recommendation: Convert to `bool()` when reading: `"mute": bool(note.mute)` for consistent JSON output.

2. **Empty clip behavior for get_notes_extended**
   - What we know: Clip with no notes should return empty MidiNoteVector.
   - What's unclear: Whether `clip.length` on an empty MIDI clip is 0.0 or the initial clip length.
   - Recommendation: Newly created clips have their specified length even when empty. `clip.length` should work. If somehow it's 0, use a large fallback value.

3. **Concurrent note access**
   - What we know: Write commands are dispatched on Ableton's main thread via `schedule_message`.
   - What's unclear: Whether read commands (`get_notes`) need main thread access too.
   - Recommendation: Register `get_notes` as a read command (no `write=True` flag). If issues arise during UAT, switch to write=True. The `get_notes_extended` call should be safe from the socket thread.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.25+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_notes.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MIDI-01 | Add notes returns JSON with note_count and clip_name | smoke | `pytest tests/test_notes.py::test_add_notes_returns_json -x` | Wave 0 |
| MIDI-02 | Get notes returns JSON with note_count and notes array | smoke | `pytest tests/test_notes.py::test_get_notes_returns_json -x` | Wave 0 |
| MIDI-03 | Remove notes sends correct params and returns removed_count | smoke | `pytest tests/test_notes.py::test_remove_notes_returns_json -x` | Wave 0 |
| MIDI-04 | Quantize notes sends grid_size and strength params | smoke | `pytest tests/test_notes.py::test_quantize_notes_returns_json -x` | Wave 0 |
| MIDI-05 | Transpose notes sends semitones param | smoke | `pytest tests/test_notes.py::test_transpose_notes_returns_json -x` | Wave 0 |
| MIDI-01 | All 5 note tools registered as MCP tools | smoke | `pytest tests/test_notes.py::test_note_tools_registered -x` | Wave 0 |
| MIDI-01 | add_notes_to_clip updated to return JSON (not plain text) | smoke | `pytest tests/test_notes.py::test_add_notes_json_format -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_notes.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_notes.py` -- covers MIDI-01 through MIDI-05 (smoke tests with mocked connection)
- [ ] Add `"MCP_Server.tools.notes.get_ableton_connection"` to `_GAC_PATCH_TARGETS` in conftest.py (new tool module)

*(Note: No framework install needed -- pytest infrastructure already exists and passes.)*

## Sources

### Primary (HIGH confidence)
- [Live 11 API documentation (structure-void.com)](https://structure-void.com/PythonLiveAPI_documentation/Live11.0.xml) -- Clip class methods: add_new_notes, get_notes_extended, remove_notes_extended signatures and descriptions
- [Ableton Forum: Remote scripts add new notes](https://forum.ableton.com/viewtopic.php?t=243936) -- Working MidiNoteSpecification example code, constructor parameters, common error with dict approach
- [What's New in Live 11, Part 2 (Cycling '74)](https://cycling74.com/articles/what's-new-in-live-11-part-2) -- Live 11 note API overview: dictionaries, note IDs, MPE preservation

### Secondary (MEDIUM confidence)
- [Note API changes for Live 11 (Ableton help)](https://help.ableton.com/hc/en-us/articles/360021922519-Note-API-changes-for-Live-11) -- MPE compatibility explanation, remove_notes_extended requirement
- Existing codebase: handlers/notes.py, handlers/clips.py, tools/clips.py, connection.py -- established patterns and integration points

### Tertiary (LOW confidence)
- MidiNote object property names (pitch, start_time, duration, velocity, mute) -- inferred from MidiNoteSpecification constructor params and API symmetry. Not directly verified from official property documentation but highly likely based on multiple corroborating sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Live 11+ note APIs are well-documented across official and community sources
- Architecture: HIGH -- follows established codebase patterns exactly (mixin handlers, MCP tools, registry, connection)
- Pitfalls: HIGH -- key pitfalls (dict vs MidiNoteSpecification, list vs tuple, from/span vs min/max) verified from forum posts and API docs
- Code examples: MEDIUM -- MidiNote read property names inferred, not directly verified from official class docs

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable APIs, no breaking changes expected)
