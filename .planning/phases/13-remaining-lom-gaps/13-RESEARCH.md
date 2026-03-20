# Phase 13: Remaining LOM Gaps - Research

**Researched:** 2026-03-19
**Domain:** Ableton Live Object Model (LOM) -- Scene, SimplerDevice, PluginDevice, MixerDevice, GroovePool, DrumPad, Clip (groove), ClipSlot (audio), Track (freeze), Device (A/B compare)
**Confidence:** HIGH

## Summary

Phase 13 implements all remaining "Add" tier gaps from the Phase 11 LOM gap report -- approximately 24 items spanning 7 LOM classes. Research covered the LOM specification (Max9-LOM-en.pdf, 171 pages) for every API surface involved, the existing codebase patterns (14 handler modules, 15 MCP tool modules, 160 passing tests), and Phase 12's established patterns for gap implementation.

Two critical findings emerged from LOM research: (1) **Follow actions are NOT exposed in the LOM spec for Live 12.3.5** -- the Clip class has no follow_action properties, meaning SESS-02 cannot be implemented via the Python Remote Script API; (2) **Track freeze/unfreeze are read-only properties only** -- `is_frozen` and `can_be_frozen` exist but there are no `freeze()` or `unfreeze()` action functions, meaning TRKA-01 freeze/unfreeze actions cannot be implemented (Phase 12 already added the read-only state query).

All other gap items are fully supported by the LOM with clear API signatures verified against the spec. The implementation follows the established Phase 12 pattern: handler mixin + MCP tool module + smoke tests, delivered in 3 plans organized by affinity.

**Primary recommendation:** Implement all gaps except SESS-02 (follow actions -- not in LOM) and TRKA-01 freeze/unfreeze actions (no API -- read-only state already covered). Adjust the 3-plan structure to redistribute items from Plan 3 since two items are blocked.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **All remaining Add-tier gaps included** -- no trimming. Continues the "all Add-tier gaps get implemented" principle from Phase 12
- MIDA-01/MIDA-02 (select/deselect notes, replace selected) already covered by Phase 12's NOTE-04 and NOTE-05 -- excluded from Phase 13
- ACRT-01 (session audio from file via ClipSlot.create_audio_clip) included
- TRKA-01 (freeze/unfreeze track actions) included -- Phase 12 only added read-only is_frozen/can_be_frozen
- SESS-02 (clip follow actions) included -- researcher should verify Live 12.3 follow action API from LOM spec
- **Plan 1: Scene + Mixer extended** (~8 items) -- Session-view controls
- **Plan 2: Simpler + DrumPad + Plugin/Device** (~10 items) -- Device-related
- **Plan 3: Groove + Follow actions + Track freeze + Audio** (~6 items) -- Miscellaneous remaining
- Each plan delivers handlers + MCP tools + smoke tests (all-in-one pattern, matching Phase 12)
- **Full Simpler + slicing** -- all operations including slice management
- **DrumPad by MIDI note number** -- mute_drum_pad(track_index, device_index, note=36)
- **3 separate groove tools**: list_grooves, get/set_groove_params, set_clip_groove
- **Scene tempo exposed as-is** with informative response noting "Scene tempo will override global tempo when fired"
- **Separate plugin tools**: list_plugin_presets and set_plugin_preset
- **Full follow action read/write** -- get/set follow action type, probability, and time
- **Assume Live 12.3+** -- no version guards or hasattr() checks
- **A/B preset compare** (Live 12.3+) included without version check

### Claude's Discretion
- Exact plan boundaries -- may adjust the 3 logical groups if implementation dependencies warrant it
- Handler mixin naming for new domains (GrooveHandlers, SimplerHandlers, etc.)
- Whether to extend existing MCP tool modules or create new ones (e.g., grooves.py, simpler.py)
- Test organization for new tool modules
- Error message wording for domain-specific edge cases
- How to handle Simpler sample loading based on LOM research

### Deferred Ideas (OUT OF SCOPE)
- All 26 Backlog-tier items from gap report (recording overdub, tempo nudge, count-in, scrubbing, Ableton Link, etc.)

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCNX-01 | User can get/set scene color | Scene.color / Scene.color_index (get/set) confirmed in LOM p114. Uses same COLOR_NAMES dict as tracks. |
| SCNX-02 | User can get/set per-scene tempo | Scene.tempo (float, -1 when disabled) + Scene.tempo_enabled (bool). Confirmed LOM pp114-115. |
| SCNX-03 | User can get/set per-scene time signature | Scene.time_signature_numerator/denominator (int, -1 when disabled) + Scene.time_signature_enabled (bool). LOM p115. |
| SCNX-04 | User can fire scene as selected (fire + advance) | Scene.fire_as_selected(force_legato=False). Fires selected scene then selects next. LOM p116. |
| SCNX-06 | User can check if scene is empty | Scene.is_empty (bool, read-only). LOM p114. |
| MIXX-01 | User can control crossfader | MixerDevice.crossfader (DeviceParameter, master track only). LOM p95. |
| MIXX-02 | User can get/set track crossfade assignment (A/B) | MixerDevice.crossfade_assign (int: 0=A, 1=none, 2=B, not on master). LOM p96. |
| MIXX-03 | User can get panning mode | MixerDevice.panning_mode (int: 0=Stereo, 1=Split Stereo). LOM p96. |
| SMPL-01 | User can crop Simpler sample | SimplerDevice.crop(). LOM p121. |
| SMPL-02 | User can reverse Simpler sample | SimplerDevice.reverse(). LOM p122. |
| SMPL-03 | User can warp Simpler sample | SimplerDevice.warp_as(beats), warp_double(), warp_half(). Guarded by can_warp_as/double/half. LOM pp120-122. |
| SMPL-04 | User can get/set Simpler playback mode | SimplerDevice.playback_mode (int: 0=Classic, 1=One-Shot, 2=Slicing). LOM p120. |
| SMPL-05 | User can manage Simpler slices | Sample.slices (list of int), Sample.insert_slice(time), move_slice(src,dst), remove_slice(time), clear_slices(). LOM pp109-112. |
| DRPD-01 | User can mute/solo individual drum pads | DrumPad.mute (bool), DrumPad.solo (bool). LOM p77. |
| DRPD-02 | User can clear all chains from a drum pad | DrumPad.delete_all_chains(). LOM p77. |
| DEVX-03 | User can list and select plugin presets | PluginDevice.presets (StringVector), selected_preset_index (int, get/set). LOM p97. |
| DEVX-04 | User can use A/B preset compare | Device.can_compare_ab (bool), is_using_compare_preset_b (bool), save_preset_to_compare_ab_slot(). Live 12.3+. LOM pp61-62. |
| GRVX-01 | User can list grooves in groove pool | Song.groove_pool.grooves (list of Groove). LOM p83. |
| GRVX-02 | User can read/set groove parameters | Groove.base (int 0-5), name (symbol), timing_amount/quantization_amount/random_amount/velocity_amount (float). LOM p82. |
| GRVX-03 | User can associate groove with clip | Clip.groove (Groove object, get/set). LOM p26. |
| SESS-02 | User can configure clip follow actions | **BLOCKED: Not in LOM spec.** The Clip class in Max9-LOM-en.pdf has NO follow_action properties. This API is not exposed via the Python Remote Script. |
| TRKA-01 | User can freeze/unfreeze tracks | **PARTIALLY BLOCKED:** Track.is_frozen and Track.can_be_frozen are read-only properties (already implemented in Phase 12). There are NO freeze() or unfreeze() action functions in the LOM. |
| ACRT-01 | User can create audio clip in session view from file | ClipSlot.create_audio_clip(path). Must be on audio track, track not frozen. LOM p48. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11 | Ableton Live 12 runtime | Ableton-embedded interpreter |
| mcp[cli] | 1.26.0 | MCP server SDK | Project standard since Phase 1 |
| FastMCP | (bundled) | In-memory test client | Built into mcp SDK |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test framework | All smoke tests |
| pytest-asyncio | 0.23.x | Async test support | MCP tool tests |
| ruff | 0.9.x | Linting | Pre-commit checks |

No new libraries needed. Phase 13 uses the same stack as all previous phases.

## Architecture Patterns

### Recommended Project Structure (Phase 13 additions)
```
AbletonMCP_Remote_Script/handlers/
    scenes.py          # EXTEND -- add scene color, tempo, time_sig, fire_as_selected, is_empty
    mixer.py           # EXTEND -- add crossfader, crossfade_assign, panning_mode
    devices.py         # EXTEND -- add simpler ops, plugin presets, A/B compare, drum pad ops
    grooves.py         # NEW -- groove pool handler mixin (GrooveHandlers)
    clips.py           # EXTEND -- add create_session_audio_clip, set_clip_groove
    tracks.py          # EXTEND -- freeze/unfreeze if API found (research: NOT possible)
    __init__.py        # UPDATE -- add grooves import

MCP_Server/tools/
    scenes.py          # EXTEND -- scene extended tools
    mixer.py           # EXTEND -- crossfader tools
    devices.py         # EXTEND -- simpler, plugin preset, A/B compare, drum pad tools
    grooves.py         # NEW -- groove pool MCP tools
    clips.py           # EXTEND -- session audio clip, clip groove tools
    __init__.py        # UPDATE -- add grooves import

tests/
    test_scenes.py     # EXTEND -- scene extended tests
    test_mixer.py      # EXTEND -- crossfader tests
    test_devices.py    # EXTEND -- simpler, plugin, A/B, drum pad tests
    test_grooves.py    # NEW -- groove pool tests
    test_clips.py      # EXTEND -- session audio, clip groove tests
```

### Pattern 1: Handler Mixin with @command Decorator
**What:** Each domain defines a mixin class with @command-decorated methods
**When to use:** All new handlers
**Example:**
```python
# Source: AbletonMCP_Remote_Script/registry.py + established pattern
from AbletonMCP_Remote_Script.registry import command

class GrooveHandlers:
    """Mixin class for groove pool command handlers."""

    @command("list_grooves")
    def _list_grooves(self, params=None):
        """List all grooves in the groove pool."""
        try:
            grooves = []
            for i, groove in enumerate(self._song.groove_pool.grooves):
                grooves.append({
                    "index": i,
                    "name": groove.name,
                })
            return {"grooves": grooves}
        except Exception as e:
            self.log_message(f"Error listing grooves: {e}")
            raise
```

### Pattern 2: Device Resolution for Specialized Devices
**What:** Use existing `_resolve_device()` then check device type before accessing specialized properties
**When to use:** SimplerDevice, PluginDevice operations
**Example:**
```python
@command("get_simpler_info")
def _get_simpler_info(self, params):
    """Get Simpler device info including playback mode and sample."""
    try:
        device, track = self._resolve_device(params)
        # Check if device is actually a Simpler
        if not hasattr(device, 'playback_mode'):
            raise ValueError(
                f"Device '{device.name}' is not a Simpler device"
            )
        result = {
            "device_name": device.name,
            "playback_mode": device.playback_mode,
            "can_warp_as": device.can_warp_as,
            "can_warp_double": device.can_warp_double,
            "can_warp_half": device.can_warp_half,
        }
        if device.sample:
            result["sample"] = {
                "file_path": device.sample.file_path,
                "length": device.sample.length,
                "slices": list(device.sample.slices),
            }
        return result
    except Exception as e:
        self.log_message(f"Error getting Simpler info: {e}")
        raise
```

### Pattern 3: DrumPad Resolution by Note Number
**What:** Find a DrumPad within a Drum Rack by its MIDI note number
**When to use:** DrumPad mute/solo/delete operations
**Example:**
```python
def _resolve_drum_pad(self, device, note):
    """Resolve a drum pad by MIDI note number."""
    for pad in device.drum_pads:
        if pad.note == note:
            return pad
    raise ValueError(
        f"No drum pad with note {note} found in '{device.name}'. "
        f"Available notes: {[p.note for p in device.drum_pads if p.chains]}"
    )
```

### Pattern 4: MCP Tool Module with Conditional Params
**What:** MCP tools use conditional param building and json.dumps response
**When to use:** All new MCP tool functions
**Example:**
```python
@mcp.tool()
def set_scene_tempo(
    ctx: Context,
    scene_index: int,
    tempo: float,
    enabled: bool = True,
) -> str:
    """Set per-scene tempo. Scene tempo overrides global tempo when fired.

    Parameters:
    - scene_index: Index of the scene
    - tempo: Tempo in BPM
    - enabled: Whether scene tempo is active (default: True)
    """
    try:
        ableton = get_ableton_connection()
        params = {"scene_index": scene_index, "tempo": tempo}
        if enabled is not None:
            params["enabled"] = enabled
        result = ableton.send_command("set_scene_tempo", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set scene tempo",
            detail=str(e),
            suggestion="Verify scene_index is valid",
        )
```

### Anti-Patterns to Avoid
- **Don't check device type via class_name string matching for SimplerDevice** -- use `hasattr(device, 'playback_mode')` or `hasattr(device, 'sample')` which is reliable across Ableton versions.
- **Don't assume Groove objects can be created** -- grooves come from Ableton's groove pool (loaded via browser). We can only list, read/set parameters, and assign to clips.
- **Don't try to freeze/unfreeze tracks** -- the LOM has no freeze() or unfreeze() functions. Only is_frozen/can_be_frozen read-only state is available.
- **Don't try to implement follow actions** -- they are not in the LOM spec for Live 12.3.5.
- **Don't access crossfader on non-master tracks** -- MixerDevice.crossfader is master-track-only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Device type checking | String comparison on class_name | `hasattr()` for type-specific properties | class_name varies by Ableton version |
| Scene color mapping | Custom color→index mapping | Existing `COLOR_NAMES` / `COLOR_INDEX_TO_NAME` from tracks.py | Already has 70 Ableton colors |
| Device navigation | Manual track→device traversal | `_resolve_device(params)` from devices.py | Handles chains, nested racks |
| Track resolution | Direct song.tracks[i] access | `_resolve_track(song, type, index)` from tracks.py | Handles track/return/master |
| Clip slot resolution | Direct clip_slots[i] access | `_resolve_clip_slot(song, track_idx, clip_idx)` from clips.py | Validates bounds |

## Common Pitfalls

### Pitfall 1: Scene Tempo Returns -1 When Disabled
**What goes wrong:** Reading Scene.tempo returns -1.0 when tempo_enabled is False, which could be misinterpreted as an error.
**Why it happens:** Ableton uses -1 as sentinel for "disabled" scene tempo.
**How to avoid:** Always return tempo_enabled alongside tempo value. When setting tempo, also set tempo_enabled=True. Response should note that -1 means "using song tempo."
**Warning signs:** Tempo value of -1 in get_scene_info response.

### Pitfall 2: Crossfader is Master-Track-Only
**What goes wrong:** Accessing MixerDevice.crossfader on a regular track raises an error.
**Why it happens:** Only the master track's MixerDevice has the crossfader DeviceParameter.
**How to avoid:** Access crossfader via `self._song.master_track.mixer_device.crossfader`. For crossfade_assign, access via track's own mixer_device but NOT on master.
**Warning signs:** AttributeError on mixer_device.crossfader for non-master tracks.

### Pitfall 3: DrumPad.solo Does Not Auto-Unsolo Others
**What goes wrong:** Soloing a drum pad doesn't unsolo other pads (unlike track solo).
**Why it happens:** LOM spec explicitly states "Does not automatically turn Solo off in other chains."
**How to avoid:** Document this behavior in tool description. Optionally provide an exclusive parameter that manually unsolos other pads first.
**Warning signs:** Multiple drum pads soloed simultaneously.

### Pitfall 4: SimplerDevice.sample May Be None
**What goes wrong:** Accessing device.sample properties when no sample is loaded crashes.
**Why it happens:** SimplerDevice has no sample loaded when first inserted.
**How to avoid:** Always check `device.sample is not None` before accessing sample properties (slices, file_path, etc.).
**Warning signs:** NoneType errors on sample access.

### Pitfall 5: Slice Times Are in Sample Frames, Not Beats
**What goes wrong:** Slice positions interpreted as beats when they're in sample frames.
**Why it happens:** Sample.slices returns positions in sample frames (divide by sample_rate for seconds).
**How to avoid:** Document that slice times are in sample frames. Include sample_rate in response for client-side conversion.
**Warning signs:** Enormous slice time values (e.g., 44100 for 1 second at 44.1kHz).

### Pitfall 6: PluginDevice.presets Only Works on Plugin Devices
**What goes wrong:** Accessing .presets on a native Ableton device raises an error.
**Why it happens:** Only PluginDevice (VST/AU) has the presets property.
**How to avoid:** Check device type before accessing presets. Use `hasattr(device, 'presets')` guard.
**Warning signs:** AttributeError when calling list_plugin_presets on Wavetable, Operator, etc.

### Pitfall 7: Clip.groove Returns a Groove Object (Not Index)
**What goes wrong:** Trying to set clip groove by index instead of Groove reference.
**Why it happens:** The LOM property is `Clip.groove` which takes/returns a Groove object.
**How to avoid:** Look up groove by index from song.groove_pool.grooves, then assign the object to clip.groove. To clear, the approach needs investigation (may need to set to None or use a different method).
**Warning signs:** TypeError when setting clip.groove to an integer.

### Pitfall 8: Groove Parameters Are Floats, Base Is an Index
**What goes wrong:** Treating Groove.base as a float or string when it's an integer index.
**Why it happens:** base uses index 0-5 (1/4, 1/8, 1/8T, 1/16, 1/16T, 1/32) while other params are 0.0-1.0 floats.
**How to avoid:** Document the base mapping. Validate base as int 0-5, others as floats.
**Warning signs:** Setting base to 1/16 (string) instead of 3 (int).

## Code Examples

### Scene Color (extending SceneHandlers)
```python
# Source: LOM spec p114 + existing set_track_color pattern
from AbletonMCP_Remote_Script.handlers.tracks import COLOR_NAMES, COLOR_INDEX_TO_NAME

@command("set_scene_color", write=True)
def _set_scene_color(self, params):
    """Set scene color by friendly name."""
    scene_index = params.get("scene_index", 0)
    color = params.get("color", "")
    try:
        scenes = self._song.scenes
        if scene_index < 0 or scene_index >= len(scenes):
            raise IndexError(f"Scene index {scene_index} out of range (0-{len(scenes) - 1})")
        if color not in COLOR_NAMES:
            valid = ", ".join(sorted(COLOR_NAMES.keys()))
            raise ValueError(f"Unknown color '{color}'. Valid colors: {valid}")
        scene = scenes[scene_index]
        scene.color_index = COLOR_NAMES[color]
        return {"scene_index": scene_index, "name": scene.name, "color": color}
    except Exception as e:
        self.log_message(f"Error setting scene color: {e}")
        raise
```

### Scene Tempo (with informative response)
```python
# Source: LOM spec p114-115
@command("set_scene_tempo", write=True)
def _set_scene_tempo(self, params):
    """Set per-scene tempo. Overrides global tempo when scene is fired."""
    scene_index = params.get("scene_index", 0)
    tempo = params.get("tempo")
    enabled = params.get("enabled", True)
    try:
        scenes = self._song.scenes
        if scene_index < 0 or scene_index >= len(scenes):
            raise IndexError(f"Scene index {scene_index} out of range (0-{len(scenes) - 1})")
        scene = scenes[scene_index]
        if tempo is not None:
            scene.tempo = tempo
        scene.tempo_enabled = enabled
        return {
            "scene_index": scene_index,
            "name": scene.name,
            "tempo": scene.tempo,
            "tempo_enabled": scene.tempo_enabled,
            "note": "Scene tempo will override global tempo when this scene is fired"
                    if scene.tempo_enabled else "Scene tempo disabled, using song tempo",
        }
    except Exception as e:
        self.log_message(f"Error setting scene tempo: {e}")
        raise
```

### Crossfader Control (master track only)
```python
# Source: LOM spec pp94-96
@command("set_crossfader", write=True)
def _set_crossfader(self, params):
    """Set the crossfader position (-1.0 left to 1.0 right)."""
    value = params.get("value")
    try:
        crossfader = self._song.master_track.mixer_device.crossfader
        crossfader.value = value
        return {"crossfader": crossfader.value}
    except Exception as e:
        self.log_message(f"Error setting crossfader: {e}")
        raise
```

### DrumPad Mute by Note
```python
# Source: LOM spec pp76-77
@command("set_drum_pad_mute", write=True)
def _set_drum_pad_mute(self, params):
    """Mute/unmute a drum pad by MIDI note number."""
    note = params.get("note")
    mute = params.get("mute")
    try:
        device, track = self._resolve_device(params)
        if not device.can_have_drum_pads:
            raise ValueError(f"Device '{device.name}' is not a Drum Rack")
        pad = self._resolve_drum_pad(device, note)
        pad.mute = mute
        return {"note": note, "name": pad.name, "mute": pad.mute}
    except Exception as e:
        self.log_message(f"Error setting drum pad mute: {e}")
        raise
```

### Session Audio Clip from File
```python
# Source: LOM spec p48 -- ClipSlot.create_audio_clip(path)
@command("create_session_audio_clip", write=True)
def _create_session_audio_clip(self, params):
    """Create an audio clip in session view from a file."""
    track_index = params.get("track_index", 0)
    clip_index = params.get("clip_index", 0)
    file_path = params.get("file_path")
    try:
        if file_path is None:
            raise ValueError("file_path parameter is required")
        clip_slot, track = _resolve_clip_slot(self._song, track_index, clip_index)
        clip_slot.create_audio_clip(file_path)
        return {
            "created": True,
            "track_name": track.name,
            "file_path": file_path,
            "clip_name": clip_slot.clip.name if clip_slot.has_clip else None,
        }
    except Exception as e:
        self.log_message(f"Error creating session audio clip: {e}")
        raise
```

### Groove Pool Operations
```python
# Source: LOM spec pp81-83 -- Groove, GroovePool
@command("get_groove_params")
def _get_groove_params(self, params):
    """Get parameters of a groove by index."""
    groove_index = params.get("groove_index", 0)
    try:
        grooves = self._song.groove_pool.grooves
        if groove_index < 0 or groove_index >= len(grooves):
            raise IndexError(f"Groove index {groove_index} out of range (0-{len(grooves) - 1})")
        groove = grooves[groove_index]
        return {
            "index": groove_index,
            "name": groove.name,
            "base": groove.base,
            "timing_amount": groove.timing_amount,
            "quantization_amount": groove.quantization_amount,
            "random_amount": groove.random_amount,
            "velocity_amount": groove.velocity_amount,
        }
    except Exception as e:
        self.log_message(f"Error getting groove params: {e}")
        raise
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No groove API | Groove/GroovePool classes | Live 11.0 | Full groove pool access |
| No A/B compare | Device.can_compare_ab + save_preset_to_compare_ab_slot | Live 12.3 | A/B preset comparison |
| Follow actions via UI only | Still UI only -- not in LOM | N/A | SESS-02 blocked |
| Track freeze via UI only | is_frozen/can_be_frozen read-only | Unknown | Read-only state only |

**Deprecated/outdated:**
- Follow actions: Despite being a core Live feature since Live 1.0, follow action properties are NOT exposed in the Python Remote Script LOM as of Live 12.3.5. They may be accessible via Max for Live but not via the standard LOM.

## Open Questions

1. **Follow Actions API**
   - What we know: The Clip class in Max9-LOM-en.pdf (Live 12.3.5) has NO follow_action properties. Exhaustive PDF search for "follow" found only Song.follow_song (transport follow) and tempo_follower_enabled.
   - What's unclear: Whether a future Live update will expose follow actions, or if they're only accessible via Max for Live / internal APIs.
   - Recommendation: **Drop SESS-02 from Phase 13.** Document as "not available in LOM" in the gap report. Cannot be implemented.

2. **Track Freeze/Unfreeze Actions**
   - What we know: Track has is_frozen (bool, read-only) and can_be_frozen (bool, read-only). There are NO freeze() or unfreeze() functions in the Track class. Phase 12 already implemented get_track_freeze_state.
   - What's unclear: Whether freeze/unfreeze could be triggered indirectly (e.g., via application commands).
   - Recommendation: **Drop TRKA-01 freeze/unfreeze actions from Phase 13.** The read-only state query is already implemented. Document as "LOM limitation."

3. **SimplerDevice Type Detection**
   - What we know: `hasattr(device, 'playback_mode')` or `hasattr(device, 'sample')` reliably identifies SimplerDevice.
   - What's unclear: The exact `class_name` string for SimplerDevice (likely "OriginalSimpler" but not documented in LOM spec).
   - Recommendation: Use `hasattr` checks rather than class_name string matching for robustness.

4. **Clip Groove Assignment: Clearing**
   - What we know: `Clip.groove` is a get/set property that takes a Groove object.
   - What's unclear: How to clear/remove a groove assignment from a clip (set to None? set to empty?).
   - Recommendation: Try `clip.groove = None` to clear. If that fails, document the limitation.

5. **SimplerDevice Sample Loading**
   - What we know: SimplerDevice has a `sample` child (Sample class) with file_path (read-only). There is NO load_sample() function on SimplerDevice in the LOM spec.
   - What's unclear: Whether sample loading requires browser navigation (like instrument loading) or if there's another path.
   - Recommendation: Do NOT implement sample loading tools. SimplerDevice operations (crop, reverse, warp, slicing) work on the currently loaded sample. Users load samples via the browser tools.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio 0.23.x |
| Config file | pyproject.toml (pytest section) |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCNX-01 | set/get scene color | smoke | `python -m pytest tests/test_scenes.py -x -q` | Extend existing |
| SCNX-02 | set/get scene tempo | smoke | `python -m pytest tests/test_scenes.py -x -q` | Extend existing |
| SCNX-03 | set/get scene time sig | smoke | `python -m pytest tests/test_scenes.py -x -q` | Extend existing |
| SCNX-04 | fire scene as selected | smoke | `python -m pytest tests/test_scenes.py -x -q` | Extend existing |
| SCNX-06 | scene is_empty | smoke | `python -m pytest tests/test_scenes.py -x -q` | Extend existing |
| MIXX-01 | crossfader control | smoke | `python -m pytest tests/test_mixer.py -x -q` | Extend existing |
| MIXX-02 | crossfade assign | smoke | `python -m pytest tests/test_mixer.py -x -q` | Extend existing |
| MIXX-03 | panning mode | smoke | `python -m pytest tests/test_mixer.py -x -q` | Extend existing |
| SMPL-01 | simpler crop | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| SMPL-02 | simpler reverse | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| SMPL-03 | simpler warp | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| SMPL-04 | simpler playback mode | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| SMPL-05 | simpler slices | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| DRPD-01 | drum pad mute/solo | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| DRPD-02 | drum pad clear chains | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| DEVX-03 | plugin presets | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| DEVX-04 | A/B compare | smoke | `python -m pytest tests/test_devices.py -x -q` | Extend existing |
| GRVX-01 | list grooves | smoke | `python -m pytest tests/test_grooves.py -x -q` | Wave 0 |
| GRVX-02 | groove params | smoke | `python -m pytest tests/test_grooves.py -x -q` | Wave 0 |
| GRVX-03 | clip groove assign | smoke | `python -m pytest tests/test_clips.py -x -q` | Extend existing |
| ACRT-01 | session audio clip | smoke | `python -m pytest tests/test_clips.py -x -q` | Extend existing |
| SESS-02 | follow actions | N/A | N/A | BLOCKED - not in LOM |
| TRKA-01 | freeze/unfreeze | N/A | N/A | BLOCKED - no API |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `tests/test_grooves.py` -- new file for groove pool tests
- [ ] `conftest.py` -- add `MCP_Server.tools.grooves.get_ableton_connection` to `_GAC_PATCH_TARGETS`
- [ ] `MCP_Server/tools/__init__.py` -- add grooves import
- [ ] `AbletonMCP_Remote_Script/handlers/__init__.py` -- add grooves import

## LOM API Reference Summary

### Scene (LOM pp113-116)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| color | int | R/W | RGB value 0x00rrggbb |
| color_index | long | R/W | Index into Ableton palette |
| is_empty | bool | R/O | True if no clips in scene |
| tempo | float | R/W | -1 when disabled |
| tempo_enabled | bool | R/W | Active state |
| time_signature_numerator | int | R/W | -1 when disabled |
| time_signature_denominator | int | R/W | -1 when disabled |
| time_signature_enabled | bool | R/W | Active state |
| fire_as_selected(force_legato) | func | -- | Fires selected scene, selects next |

### SimplerDevice (LOM pp119-122)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| sample | Sample | child | None if no sample loaded |
| can_warp_as | bool | R/O | Guard for warp_as() |
| can_warp_double | bool | R/O | Guard for warp_double() |
| can_warp_half | bool | R/O | Guard for warp_half() |
| playback_mode | int | R/W | 0=Classic, 1=One-Shot, 2=Slicing |
| slicing_playback_mode | int | R/W | 0=Mono, 1=Poly, 2=Thru |
| crop() | func | -- | Crop loaded sample |
| reverse() | func | -- | Reverse loaded sample |
| warp_as(beats) | func | -- | Warp to beat count |
| warp_double() | func | -- | Double tempo |
| warp_half() | func | -- | Half tempo |

### Sample (LOM pp106-112)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| file_path | unicode | R/O | Sample file path |
| length | int | R/O | Length in sample frames |
| sample_rate | int | R/O | Sample rate |
| slices | list of int | R/O | Slice positions in sample frames |
| slicing_sensitivity | float | R/W | 0.0-1.0 |
| slicing_style | int | R/W | 0=Transient,1=Beat,2=Region,3=Manual |
| slicing_beat_division | int | R/W | 0-10 (1/16 to 4 Bars) |
| slicing_region_count | int | R/W | Region count |
| insert_slice(time) | func | -- | Time in sample frames |
| move_slice(src, dst) | func | -- | Both in sample frames |
| remove_slice(time) | func | -- | Time in sample frames |
| clear_slices() | func | -- | Manual mode only |
| reset_slices() | func | -- | Reset to original |

### PluginDevice (LOM p97)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| presets | StringVector | R/O | List of preset names |
| selected_preset_index | int | R/W | Currently selected preset |

### Device A/B Compare (LOM pp61-62)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| can_compare_ab | bool | R/O | Live 12.3+ |
| is_using_compare_preset_b | bool | R/O | Live 12.3+ |
| save_preset_to_compare_ab_slot() | func | -- | Live 12.3+ |

### MixerDevice (LOM pp94-96)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| crossfader | DeviceParameter | child | Master track only |
| crossfade_assign | int | R/W | 0=A, 1=none, 2=B. Not on master. |
| panning_mode | int | R/O | 0=Stereo, 1=Split Stereo |

### GroovePool / Groove (LOM pp81-83)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| groove_pool.grooves | list of Groove | R/O | Song-level access |
| Groove.name | symbol | R/W | Groove name |
| Groove.base | int | R/W | 0-5 grid index |
| Groove.timing_amount | float | R/W | Timing amount |
| Groove.quantization_amount | float | R/W | Quantization amount |
| Groove.random_amount | float | R/W | Random amount |
| Groove.velocity_amount | float | R/W | Velocity amount |

### DrumPad (LOM pp76-77)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| mute | bool | R/W | Pad mute state |
| solo | bool | R/W | No auto-unsolo |
| note | int | R/O | MIDI note number |
| name | symbol | R/O | Pad name |
| delete_all_chains() | func | -- | Clears pad contents |

### Clip Groove (LOM p26)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| groove | Groove | R/W | Groove object ref |
| has_groove | bool | R/O | True if groove assigned |

### ClipSlot Session Audio (LOM p48)
| Property/Function | Type | Access | Notes |
|-------------------|------|--------|-------|
| create_audio_clip(path) | func | -- | Audio track only, not frozen |

## Sources

### Primary (HIGH confidence)
- Max9-LOM-en.pdf -- Complete LOM specification for Live 12.3.5 / Max 9, 171 pages. All API signatures verified directly against this document.
  - Scene: pp113-116
  - SimplerDevice: pp119-122
  - Sample: pp106-112
  - PluginDevice: p97
  - Device (A/B): pp59-62
  - MixerDevice: pp94-96
  - GroovePool: p83
  - Groove: pp81-82
  - DrumPad: pp76-77
  - Clip (groove): p26
  - ClipSlot (create_audio_clip): p48
  - Track (freeze): pp151-163

### Secondary (HIGH confidence)
- Existing codebase analysis: 14 handler modules, 15 MCP tool modules, 160 passing tests. Pattern consistency verified across all files.
- Phase 12 CONTEXT.md: Deferred items list confirms Phase 13 scope.
- Phase 11 GAP-REPORT.md: Complete gap inventory with Add/Backlog tier assignments.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, same patterns as 12 prior phases
- Architecture: HIGH -- extending established handler/tool/test pattern
- Pitfalls: HIGH -- all verified against LOM spec, crossfader/groove/simpler edge cases documented
- API surfaces: HIGH -- every function/property verified against 171-page LOM spec
- Blocked items: HIGH -- exhaustive PDF search confirms follow_action and freeze/unfreeze are NOT in LOM

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable -- LOM spec for Live 12.3.5 is fixed)
