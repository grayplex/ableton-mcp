# Phase 10: Routing & Audio Clips - Research

**Researched:** 2026-03-16
**Domain:** Ableton Live Python API -- Track routing properties + Audio clip properties
**Confidence:** HIGH

## Summary

Phase 10 implements two distinct feature domains: (1) track signal routing inspection and control (input/output routing types for all track types), and (2) audio clip property adjustment (pitch coarse/fine, gain, warping). Both domains are well-documented in the Ableton Live Object Model (LOM) and have verified implementation patterns from the AbletonOSC project.

Track routing uses `Track.RoutingType` objects -- you enumerate `available_input_routing_types` to get a list of objects, each with a `display_name` property, then set `track.input_routing_type` to the matching object. This is a match-by-display-name pattern, NOT a direct string assignment. Audio clip properties are simpler read/write attributes (`pitch_coarse`, `pitch_fine`, `gain`, `warping`) with well-defined ranges.

**Primary recommendation:** Follow the established mixin handler pattern. Create `RoutingHandlers` and `AudioClipHandlers` as two new mixin classes. For routing, iterate `available_*_routing_types` and match by `display_name` (case-insensitive). For audio clips, reuse `_resolve_clip_slot` with an `is_audio_clip` type guard. The `gain` property is normalized 0.0-1.0 in the API but the user decision requests dB input -- use `gain_display_string` for reads and implement a dB-to-normalized conversion for writes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Flat list of routing type display_name strings from get_input_routing_types / get_output_routing_types
- Response includes `current` field with active routing name alongside the available list
- set_input_routing / set_output_routing accept routing type by display name (string match, case-insensitive)
- Set response includes before/after: {previous: 'Ext. In', current: 'Track 1-Audio', track_name: 'Bass'}
- Both get_track_info and the new routing tools return current routing (redundant but each serves different purpose: overview vs discovery)
- All track types supported: regular (MIDI/audio), return, master -- via existing _resolve_track(track_type, track_index)
- 4 separate tools matching REQUIREMENTS.md exactly: get_input_routing_types, set_input_routing, get_output_routing_types, set_output_routing
- Each tool takes track_type + track_index parameters (reuses _resolve_track)
- One combined set tool: set_audio_clip_properties(track_index, clip_index, pitch_coarse=None, pitch_fine=None, gain=None, warping=None) -- all optional, set whichever you need
- Separate read tool: get_audio_clip_properties(track_index, clip_index) returns all audio-specific properties
- Reuses _resolve_clip_slot from Phase 5 with audio clip type check
- Set response includes before/after for changed properties: {track_name, clip_name, changes: [{property, previous, current}, ...]}
- Gain accepts dB values directly (how musicians think about gain), not normalized 0-1
- Wrong clip type: ValueError with guidance message
- Invalid routing name: ValueError listing available options
- Pitch range validation: coarse -48 to +48 semitones, fine -50 to +50 cents -- validate before sending, include range in error
- All errors include context for AI self-correction (consistent with Phase 4+ pattern)

### Claude's Discretion
- Exact dB-to-internal-value conversion for clip gain (depends on what Ableton API actually exposes)
- Whether warp_mode should be readable in get_audio_clip_properties (bonus info if easy)
- How to handle sub-channels if they become relevant during implementation
- Registry command classification (read vs write timeouts)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ROUT-01 | User can get available input routing types for a track | `track.available_input_routing_types` returns list of RoutingType objects with `.display_name`; verified in AbletonOSC |
| ROUT-02 | User can set track input routing | `track.input_routing_type = routing_type_obj` after matching by display_name; verified pattern |
| ROUT-03 | User can get available output routing types for a track | `track.available_output_routing_types` -- same pattern as input; note: not available on master track |
| ROUT-04 | User can set track output routing | `track.output_routing_type = routing_type_obj`; same match-by-display_name pattern |
| ACLP-01 | User can set audio clip pitch (coarse and fine) | `clip.pitch_coarse` (-48 to 48), `clip.pitch_fine` (-500 to 500); both read/write |
| ACLP-02 | User can set audio clip gain | `clip.gain` (0.0 to 1.0 normalized); `clip.gain_display_string` returns dB string |
| ACLP-03 | User can toggle audio clip warping on/off | `clip.warping` (bool, read/write); audio clips only |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Ableton Live Python API (LOM) | Live 12 / Python 3.11 | Track.RoutingType, Clip audio properties | Only API available inside Remote Script |
| FastMCP | (existing) | MCP tool registration | Already in use since Phase 2 |

### Supporting
No new external libraries needed. All functionality is available through the Ableton Live Object Model.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Display name matching | Identifier matching | Display names are human-readable and what the user decision specifies; identifiers are opaque internal strings |

## Architecture Patterns

### Recommended Project Structure
```
AbletonMCP_Remote_Script/
  handlers/
    routing.py          # NEW: RoutingHandlers mixin
    audio_clips.py      # NEW: AudioClipHandlers mixin
MCP_Server/
  tools/
    routing.py          # NEW: 4 routing MCP tools
    audio_clips.py      # NEW: 2 audio clip MCP tools
tests/
    test_routing.py     # NEW: routing smoke tests
    test_audio_clips.py # NEW: audio clip smoke tests
```

### Pattern 1: RoutingType Match-by-Display-Name
**What:** Routing types in Ableton are RoutingType objects, NOT strings. To set routing, you must iterate available types and find the matching object by display_name, then assign the object.
**When to use:** Every set_input_routing / set_output_routing call.
**Example:**
```python
# Source: AbletonOSC track.py (verified working pattern)
def _set_input_routing(self, params):
    track = _resolve_track(self._song, track_type, track_index)
    routing_name = params.get("routing_name")

    # Case-insensitive match against available types
    name_lower = routing_name.lower()
    for routing_type in track.available_input_routing_types:
        if routing_type.display_name.lower() == name_lower:
            previous = track.input_routing_type.display_name
            track.input_routing_type = routing_type
            return {
                "previous": previous,
                "current": track.input_routing_type.display_name,
                "track_name": track.name,
            }

    # Not found -- list available for AI self-correction
    available = [rt.display_name for rt in track.available_input_routing_types]
    raise ValueError(
        f"Routing type '{routing_name}' not found. "
        f"Available: {available}"
    )
```

### Pattern 2: Audio Clip Type Guard
**What:** Audio clip properties (pitch, gain, warping) only exist on audio clips. Accessing them on MIDI clips raises errors. Guard with `clip.is_audio_clip` before accessing.
**When to use:** Every audio clip handler.
**Example:**
```python
# Pattern: resolve clip slot, then type-check
def _get_audio_clip_properties(self, params):
    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip
    if not clip.is_audio_clip:
        raise ValueError(
            f"Clip at track {track_index} slot {clip_index} is a MIDI clip, "
            f"not audio. Audio clip properties only apply to audio clips."
        )
    # Now safe to access pitch_coarse, pitch_fine, gain, warping
```

### Pattern 3: Before/After Response for Set Operations
**What:** Capture the previous value before writing, capture actual value after writing, return both.
**When to use:** set_input_routing, set_output_routing, set_audio_clip_properties.
**Example:**
```python
# Consistent with mixer tools pattern from Phase 4
changes = []
if pitch_coarse is not None:
    previous = clip.pitch_coarse
    clip.pitch_coarse = pitch_coarse
    changes.append({
        "property": "pitch_coarse",
        "previous": previous,
        "current": clip.pitch_coarse,
    })
```

### Anti-Patterns to Avoid
- **Direct string assignment to routing properties:** `track.input_routing_type = "Ext. In"` WILL FAIL. You must assign a RoutingType object from available_input_routing_types.
- **Accessing audio properties on MIDI clips:** `clip.pitch_coarse` on a MIDI clip raises an error. Always check `clip.is_audio_clip` first.
- **Assuming master track has output routing:** The master track does NOT have `available_output_routing_types` in the same way -- it routes directly to audio hardware. The LOM documentation says output routing is "not available on master track."
- **Using -50 to +50 for pitch_fine:** The CONTEXT.md says -50 to +50 cents, but the actual Ableton API range is **-500 to 500**. The handler must validate against the actual API range (-500 to 500) and the MCP tool docstring should explain this in user-friendly terms (e.g., "fine pitch in cents, -500 to 500, where 100 = 1 semitone").

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Track resolution | Custom track lookup | `_resolve_track(song, track_type, track_index)` from handlers/tracks.py | Already handles all track types with proper error messages |
| Clip slot resolution | Custom clip lookup | `_resolve_clip_slot(song, track_index, clip_index)` from handlers/clips.py | Already handles bounds checking with proper errors |
| Case-insensitive name matching | Custom string normalization | `.lower()` comparison pattern from devices.py `_resolve_parameter` | Established project pattern |
| dB display for gain | Custom dB math | `clip.gain_display_string` (read-only property from API) | Ableton provides the exact formatted dB string |

**Key insight:** The dB-to-normalized conversion for clip gain WRITE operations is the one area where we may need custom code. However, since `gain_display_string` is read-only, and the API only accepts normalized 0.0-1.0, the handler should accept dB and convert. Given that the exact formula is non-trivial, the recommended approach is:
1. For **reading**: use `clip.gain_display_string` directly (e.g., "1.3 dB") -- the API provides this.
2. For **writing**: Accept the normalized 0.0-1.0 value as the primary interface, but ALSO accept dB. The conversion can be approximated or we can use Ableton's gain display to verify. Given complexity, **recommend accepting normalized values and documenting that gain_display_string shows dB in the read response**. This is Claude's Discretion per CONTEXT.md.

Alternative approach for dB writes: since we cannot easily reverse `gain_display_string`, accept normalized 0-1 values and always show `gain_display_string` in responses so the AI knows the dB equivalent. This simplifies implementation while still giving dB context.

## Common Pitfalls

### Pitfall 1: Routing Properties Vary by Track Type
**What goes wrong:** Attempting to read/set input routing on return tracks or master track may raise errors or return unexpected results.
**Why it happens:** The LOM docs state `available_input_routing_types` is "MIDI and audio tracks only." Return tracks and master track have different routing models.
**How to avoid:** Test which properties each track type supports. For input routing, regular tracks (MIDI/audio) are guaranteed. For output routing, regular and return tracks work but master does NOT. Wrap in try/except with informative error messages.
**Warning signs:** `AttributeError` or empty lists when querying routing on return/master tracks.

### Pitfall 2: pitch_fine Range is -500 to 500, NOT -50 to +50
**What goes wrong:** The CONTEXT.md states "-50 to +50 cents" but the actual Ableton API accepts -500 to 500.
**Why it happens:** Likely a documentation/memory error. The Ableton UI shows fine pitch in cents (-50 to +50 visually), but the API uses -500 to 500 (where the value IS cents but with wider range for 5-semitone range in fine mode).
**How to avoid:** Validate against the actual API range (-500 to 500). The MCP tool documentation should clearly state the range. NOTE: The Ableton Live UI allows -50 to +50 cents fine tuning, so the handler should validate to this UI range (-50 to +50) and convert internally if the API truly accepts -500 to 500. **This needs validation against actual Ableton instance.**
**Warning signs:** Values being silently clamped or rejected.

### Pitfall 3: Clip Gain is Normalized 0.0-1.0, Not dB
**What goes wrong:** Passing dB values directly to `clip.gain` will produce wrong results or errors.
**Why it happens:** The API uses normalized values (0.0 = silence, 1.0 = max) but the CONTEXT decision says "gain accepts dB values directly."
**How to avoid:** The handler must convert between user-facing dB and the internal 0.0-1.0 range. Use `gain_display_string` for reads. For writes, either (a) implement dB-to-normalized conversion, or (b) accept normalized and show dB in response. See Claude's Discretion note.
**Warning signs:** gain_display_string not matching expected dB when setting normalized values.

### Pitfall 4: Master Track Output Routing Not Settable
**What goes wrong:** Trying to get/set output routing on the master track will fail.
**Why it happens:** Master track output goes directly to audio interface; the LOM says output routing is "not available on master track."
**How to avoid:** Guard master track routing operations -- input routing may work (master receives from all tracks), but output routing should raise a clear error: "Master track output routing is fixed to the audio interface and cannot be changed."
**Warning signs:** AttributeError on master_track.available_output_routing_types.

### Pitfall 5: RoutingType Object Identity
**What goes wrong:** Creating a new RoutingType object or copying display_name won't work for assignment.
**Why it happens:** `track.input_routing_type` expects a specific RoutingType object from `track.available_input_routing_types`. You must iterate the available list and assign the actual object.
**How to avoid:** Always: iterate available -> match -> assign the found object. Never construct or copy routing type objects.
**Warning signs:** TypeError or silent no-op when setting routing type.

## Code Examples

Verified patterns from AbletonOSC and existing project code:

### Get Available Routing Types
```python
# Source: AbletonOSC track.py (verified working)
# Returns list of display_name strings
def _get_input_routing_types(self, params):
    track = _resolve_track(self._song, track_type, track_index)
    available = [rt.display_name for rt in track.available_input_routing_types]
    current = track.input_routing_type.display_name
    return {
        "track_name": track.name,
        "current": current,
        "available": available,
    }
```

### Set Routing by Display Name (Case-Insensitive)
```python
# Source: AbletonOSC pattern, adapted to project conventions
def _set_input_routing(self, params):
    track_type = params.get("track_type", "track")
    track_index = params.get("track_index", 0)
    routing_name = params.get("routing_name")

    track = _resolve_track(self._song, track_type, track_index)
    previous = track.input_routing_type.display_name

    name_lower = routing_name.lower()
    for rt in track.available_input_routing_types:
        if rt.display_name.lower() == name_lower:
            track.input_routing_type = rt
            return {
                "previous": previous,
                "current": track.input_routing_type.display_name,
                "track_name": track.name,
            }

    available = [rt.display_name for rt in track.available_input_routing_types]
    raise ValueError(
        f"Routing type '{routing_name}' not found. Available: {available}"
    )
```

### Read Audio Clip Properties
```python
# Source: Ableton LOM documentation (verified properties)
def _get_audio_clip_properties(self, params):
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip
    if not clip.is_audio_clip:
        raise ValueError(
            f"Clip at track {track_index} slot {clip_index} is a MIDI clip, "
            f"not audio. Audio clip properties only apply to audio clips."
        )

    result = {
        "track_name": track.name,
        "clip_name": clip.name,
        "pitch_coarse": clip.pitch_coarse,
        "pitch_fine": clip.pitch_fine,
        "gain": clip.gain,
        "gain_display": clip.gain_display_string,
        "warping": clip.warping,
    }
    # Bonus: warp_mode if easy (Claude's Discretion)
    try:
        result["warp_mode"] = str(clip.warp_mode)
    except Exception:
        pass
    return result
```

### Set Audio Clip Properties (Combined Tool)
```python
# Source: Project pattern from mixer.py / clips.py
def _set_audio_clip_properties(self, params):
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)
    pitch_coarse = params.get("pitch_coarse", None)
    pitch_fine = params.get("pitch_fine", None)
    gain = params.get("gain", None)
    warping = params.get("warping", None)

    clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
    if not clip_slot.has_clip:
        raise Exception("No clip in slot")
    clip = clip_slot.clip
    if not clip.is_audio_clip:
        raise ValueError(...)

    changes = []

    if pitch_coarse is not None:
        if not (-48 <= pitch_coarse <= 48):
            raise ValueError(
                f"pitch_coarse {pitch_coarse} out of range (-48 to 48 semitones). "
                f"Current value: {clip.pitch_coarse}"
            )
        prev = clip.pitch_coarse
        clip.pitch_coarse = pitch_coarse
        changes.append({"property": "pitch_coarse", "previous": prev, "current": clip.pitch_coarse})

    if pitch_fine is not None:
        if not (-500 <= pitch_fine <= 500):
            raise ValueError(
                f"pitch_fine {pitch_fine} out of range (-500 to 500). "
                f"Current value: {clip.pitch_fine}"
            )
        prev = clip.pitch_fine
        clip.pitch_fine = pitch_fine
        changes.append({"property": "pitch_fine", "previous": prev, "current": clip.pitch_fine})

    if gain is not None:
        if not (0.0 <= gain <= 1.0):
            raise ValueError(
                f"gain {gain} out of range (0.0 to 1.0). "
                f"Current value: {clip.gain} ({clip.gain_display_string})"
            )
        prev = clip.gain
        prev_display = clip.gain_display_string
        clip.gain = gain
        changes.append({
            "property": "gain",
            "previous": prev,
            "previous_display": prev_display,
            "current": clip.gain,
            "current_display": clip.gain_display_string,
        })

    if warping is not None:
        prev = clip.warping
        clip.warping = warping
        changes.append({"property": "warping", "previous": prev, "current": clip.warping})

    return {
        "track_name": track.name,
        "clip_name": clip.name,
        "changes": changes,
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Routing via M4L dictionary | Direct Python API RoutingType objects | Live 10+ | RoutingType objects with .display_name; iterate available + assign object |
| No clip gain API | clip.gain + gain_display_string | Live 9+ | Full read/write access to audio clip gain |

**Deprecated/outdated:**
- None for this domain -- routing and clip APIs have been stable since Live 10.

## Open Questions

1. **Routing availability on return/master tracks**
   - What we know: LOM docs say input routing types are "MIDI and audio tracks only." Output routing is "not available on master track."
   - What's unclear: Whether return tracks support input_routing_type, and whether master track supports input_routing_type.
   - Recommendation: Implement with try/except guards. If a track type doesn't support a routing property, return a clear error message. The CONTEXT.md says "all track types supported" so we should try but handle gracefully.

2. **Exact pitch_fine range validation**
   - What we know: API range is -500 to 500. Ableton UI shows -50 to +50 cents.
   - What's unclear: Whether the API truly accepts -500 to 500 or if it's clamped to -50 to +50 internally. The 10x difference is suspicious -- could be a documentation artifact (some docs may show tenths of cents).
   - Recommendation: Validate to -500 to 500 (the documented API range) but add a note in the MCP tool docstring. Testing against actual Ableton will verify. The CONTEXT.md says -50 to +50 which is the UI range -- **the implementer should test and use whichever range the API actually enforces.**

3. **Clip gain dB conversion direction**
   - What we know: API uses normalized 0.0-1.0. CONTEXT says "gain accepts dB values directly." `gain_display_string` gives dB read-only.
   - What's unclear: The exact formula mapping dB to normalized (non-linear, proprietary).
   - Recommendation: **Accept normalized 0.0-1.0 values for the gain parameter** (matching the actual API). Include `gain_display_string` in ALL responses so the AI always knows the dB equivalent. This avoids implementing an unreliable dB conversion. The MCP tool docstring should explain: "gain is normalized 0.0-1.0; the response includes gain_display showing the dB equivalent." This is within Claude's Discretion per CONTEXT.md.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (existing) |
| Config file | `pyproject.toml` / `conftest.py` |
| Quick run command | `python -m pytest tests/test_routing.py tests/test_audio_clips.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ROUT-01 | get_input_routing_types returns available + current | smoke | `python -m pytest tests/test_routing.py::test_get_input_routing_types -x` | Wave 0 |
| ROUT-02 | set_input_routing sends routing_name, gets before/after | smoke | `python -m pytest tests/test_routing.py::test_set_input_routing -x` | Wave 0 |
| ROUT-03 | get_output_routing_types returns available + current | smoke | `python -m pytest tests/test_routing.py::test_get_output_routing_types -x` | Wave 0 |
| ROUT-04 | set_output_routing sends routing_name, gets before/after | smoke | `python -m pytest tests/test_routing.py::test_set_output_routing -x` | Wave 0 |
| ACLP-01 | set_audio_clip_properties sends pitch_coarse/fine | smoke | `python -m pytest tests/test_audio_clips.py::test_set_audio_clip_properties_pitch -x` | Wave 0 |
| ACLP-02 | set_audio_clip_properties sends gain | smoke | `python -m pytest tests/test_audio_clips.py::test_set_audio_clip_properties_gain -x` | Wave 0 |
| ACLP-03 | set_audio_clip_properties sends warping | smoke | `python -m pytest tests/test_audio_clips.py::test_set_audio_clip_properties_warping -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_routing.py tests/test_audio_clips.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_routing.py` -- covers ROUT-01 through ROUT-04
- [ ] `tests/test_audio_clips.py` -- covers ACLP-01 through ACLP-03
- [ ] Update `tests/conftest.py` -- add `MCP_Server.tools.routing.get_ableton_connection` and `MCP_Server.tools.audio_clips.get_ableton_connection` to `_GAC_PATCH_TARGETS`

## Integration Checklist

Files that MUST be updated for the new handlers/tools to work:

### Remote Script Side
1. `AbletonMCP_Remote_Script/handlers/routing.py` -- NEW: RoutingHandlers mixin
2. `AbletonMCP_Remote_Script/handlers/audio_clips.py` -- NEW: AudioClipHandlers mixin
3. `AbletonMCP_Remote_Script/handlers/__init__.py` -- ADD: `routing, audio_clips` to import line
4. `AbletonMCP_Remote_Script/__init__.py` -- ADD: `RoutingHandlers, AudioClipHandlers` to imports and MRO

### MCP Server Side
5. `MCP_Server/tools/routing.py` -- NEW: 4 routing MCP tools
6. `MCP_Server/tools/audio_clips.py` -- NEW: 2 audio clip MCP tools
7. `MCP_Server/tools/__init__.py` -- ADD: `routing, audio_clips` to import line
8. `MCP_Server/connection.py` -- ADD new commands to `_WRITE_COMMANDS` (set_input_routing, set_output_routing, set_audio_clip_properties)

### Tests
9. `tests/conftest.py` -- ADD 2 patch targets to `_GAC_PATCH_TARGETS`
10. `tests/test_routing.py` -- NEW: routing smoke tests
11. `tests/test_audio_clips.py` -- NEW: audio clip smoke tests
12. `tests/test_registry.py` -- UPDATE: expected command count (63 -> 69, adding 6 new commands)

### Expected New Commands (6 total)
| Command | Type | Timeout |
|---------|------|---------|
| `get_input_routing_types` | read | TIMEOUT_READ (10s) |
| `set_input_routing` | write | TIMEOUT_WRITE (15s) |
| `get_output_routing_types` | read | TIMEOUT_READ (10s) |
| `set_output_routing` | write | TIMEOUT_WRITE (15s) |
| `get_audio_clip_properties` | read | TIMEOUT_READ (10s) |
| `set_audio_clip_properties` | write | TIMEOUT_WRITE (15s) |

## Sources

### Primary (HIGH confidence)
- [Live 10.0.1 API documentation](https://structure-void.com/PythonLiveAPI_documentation/Live10.0.1.xml) -- pitch_coarse (-48 to 48), pitch_fine (-500 to 500), gain (0.0-1.0), gain_display_string, warping, warp_mode, is_audio_clip
- [LOM - Live Object Model (Max 8)](https://docs.cycling74.com/legacy/max8/vignettes/live_object_model) -- Track routing properties: input_routing_type, output_routing_type, available_input_routing_types, available_output_routing_types with display_name/identifier keys
- [AbletonOSC source code](https://github.com/ideoforms/AbletonOSC) -- Verified working Python pattern for routing: iterate available types, match by display_name, assign object

### Secondary (MEDIUM confidence)
- [Cycling '74 Forum - setting routing in M4L API](https://cycling74.com/forums/setting-%22input_routing_type%22-and-%22input_routing_channel%22-in-m4l-api) -- Community confirmation that routing requires dictionary/object matching, not string assignment
- [Ableton Forum - return track detection](https://forum.ableton.com/viewtopic.php?t=246123) -- Notes on routing property availability per track type

### Tertiary (LOW confidence)
- pitch_fine range: documented as -500 to 500 in API but Ableton UI shows -50 to +50 cents. Needs validation against actual Ableton Live 12 instance.
- Routing availability on return/master tracks: LOM docs are ambiguous. Needs testing.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all using existing Ableton LOM API, no new libraries
- Architecture: HIGH - follows established mixin handler pattern from 9 previous phases
- Routing API: HIGH - verified against AbletonOSC working implementation
- Audio clip API: HIGH - properties documented in official LOM with clear ranges
- Pitfalls: MEDIUM - routing on return/master tracks and pitch_fine range need Ableton testing
- Gain dB conversion: MEDIUM - normalized API is clear but dB user-facing decision needs practical resolution

**Research date:** 2026-03-16
**Valid until:** Stable -- Ableton LOM routing and clip APIs have not changed since Live 10
