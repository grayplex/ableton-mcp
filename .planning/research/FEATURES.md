# Feature Research

**Domain:** DAW control API / AI music production bridge (Ableton Live 12 MCP server)
**Researched:** 2026-03-10
**Confidence:** HIGH (Live Object Model well-documented by community; AbletonOSC, Ziforge liveapi-tools, and structure-void provide ground truth)

---

## Current State Baseline

The existing server has ~15 tools covering a narrow slice of the Live API:

| Tool | Status |
|------|--------|
| `get_session_info` | Working |
| `get_track_info` | Working |
| `create_midi_track` | Working |
| `set_track_name` | Working |
| `create_clip` | Working |
| `add_notes_to_clip` | Working |
| `set_clip_name` | Working |
| `set_tempo` | Working |
| `load_instrument_or_effect` | **Broken** — `load_browser_item` does not reliably load instruments |
| `fire_clip` | Working |
| `stop_clip` | Working |
| `start_playback` | Working |
| `stop_playback` | Working |
| `get_browser_tree` | Working |
| `get_browser_items_at_path` | Working |
| `load_drum_kit` | Working (brittle — depends on broken load_browser_item) |

Missing: audio tracks, return tracks, group tracks, mixing, sends, device parameters, automation, scenes, arrangement view, MIDI editing (get/delete/quantize), undo/redo, export, clip properties (loop, warp, pitch), routing.

---

## Feature Landscape

### Table Stakes (Users Expect These)

These are what any serious Ableton MCP server must have. Absent these, the server cannot produce music worth keeping.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Fix instrument loading** | Current implementation is silently broken — MIDI clips produce no sound | LOW | Root issue: `load_browser_item` finds item but loading may not persist; need to verify track is selected before load and device chain after |
| **Create audio track** | Every Ableton session has audio tracks; AI needs to create full arrangements | LOW | `song.create_audio_track(index)` exists in Live API |
| **Create return track** | Reverb/delay on returns is universal Ableton workflow | LOW | `song.create_return_track()` |
| **Create group track** | AI needs to organize tracks; groups are fundamental | MEDIUM | `song.create_group_track(index)` — grouping existing tracks is more complex |
| **Delete track** | AI will create wrong tracks; must be able to remove them | LOW | `song.delete_track(index)` |
| **Duplicate track** | Copy patterns to new tracks is basic workflow | LOW | `song.duplicate_track(index)` |
| **Track volume / pan** | Core mixing parameter — every DAW bridge exposes this | LOW | `track.mixer_device.volume.value`, `.panning.value` — writable |
| **Track mute / solo / arm** | Fundamental track state controls | LOW | `track.mute`, `track.solo`, `track.arm` — all writable |
| **Send levels** | Reverb/delay send amount is basic mixing | LOW | `track.mixer_device.sends[n].value` |
| **Set track color** | Track organization; AI should color-code by instrument family | LOW | `track.color` — writable integer |
| **Master track volume** | Final output level control | LOW | `song.master_track.mixer_device.volume.value` |
| **Return track volume/pan** | Wet return levels must be adjustable | LOW | Same API as normal tracks via `song.return_tracks[n]` |
| **Get clip notes** | AI needs to read back what notes exist to edit them | LOW | `clip.get_notes()` returns list of (pitch, time, duration, velocity, mute) tuples |
| **Remove notes from clip** | AI will add wrong notes; must clear or selectively remove | LOW | `clip.remove_notes(from_time, from_pitch, time_span, pitch_span)` |
| **Clip loop settings** | All clips loop — must control loop start/end/enabled | LOW | `clip.looping`, `clip.loop_start`, `clip.loop_end` |
| **Clip length / markers** | Setting clip start/end markers is basic editing | LOW | `clip.start_marker`, `clip.end_marker` |
| **Delete clip** | AI will create wrong clips; must be able to remove | LOW | `clip_slot.delete_clip()` |
| **Duplicate clip** | Copy clip to another slot | MEDIUM | `clip_slot.duplicate_clip_to(track_index, clip_slot_index)` |
| **Scene management** | Create, name, fire, delete scenes | LOW | `song.create_scene()`, `scene.fire()`, `scene.name`, `song.delete_scene(index)` |
| **Launch scene** | Firing scenes is core Session View workflow | LOW | `song.scenes[n].fire()` |
| **Get device parameters** | AI needs to read current parameter values before setting them | LOW | `device.parameters[n].name`, `.value`, `.min`, `.max` |
| **Set device parameter** | Adjust synth cutoff, reverb decay, etc. | LOW | `device.parameters[n].value = x` (already partially exposed but not as a clean tool) |
| **Add device to track** | Load effects/instruments from browser | MEDIUM | Fix existing broken implementation; `app.browser.load_item(item)` with track selected |
| **Undo / redo** | AI will make mistakes; undo is non-negotiable for usability | LOW | `song.undo()`, `song.redo()`, `song.can_undo`, `song.can_redo` |
| **Time signature control** | Beyond tempo — song structure | LOW | `song.signature_numerator`, `song.signature_denominator` — already read, need write |
| **Loop region** | Set arrangement loop for playback/export | LOW | `song.loop`, `song.loop_start`, `song.loop_length` |
| **Continue playback** | Resume from current position (not restart) | LOW | `song.continue_playing()` |
| **Stop all clips** | Halt entire session | LOW | `song.stop_all_clips()` |
| **Track stop** | Stop clips on a specific track | LOW | `track.stop_all_clips()` |
| **Clip pitch** | Pitch-shift audio clips (coarse/fine) | LOW | `clip.pitch_coarse`, `clip.pitch_fine` |
| **Clip gain** | Per-clip volume before track fader | LOW | `clip.gain` |
| **Clip warp on/off** | Toggle warping for audio clips | LOW | `clip.warping` |
| **Current playback position** | Know where the playhead is | LOW | `song.current_song_time` — readable |

### Differentiators (Competitive Advantage)

These go beyond what existing Ableton MCP implementations reliably offer. They make the difference between a toy and a production tool.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Clip automation (clip envelopes)** | AI can modulate filter sweeps, volume rides, panning within clips — not just static device params | HIGH | `clip.automation_envelope(parameter)` returns DeviceParameter envelope; `envelope.insert_step()`, `clear_all_envelopes()` — arrangement vs. session distinction is tricky |
| **Quantize clip notes** | Fix timing of AI-generated MIDI without full replace | MEDIUM | `clip.quantize(quantize_to, amount)` — e.g., quantize_to=5 for 16ths, amount=1.0 for 100% |
| **MIDI note selection** | Select/deselect notes for selective operations | LOW | `clip.select_all_notes()`, `clip.deselect_all_notes()`, `clip.get_selected_notes()`, `clip.replace_selected_notes()` — powerful for targeted editing |
| **Clip follow actions** | Randomized generative sequences — AI configures probabilistic clip launching | MEDIUM | `clip.follow_action_a`, `clip.follow_action_b`, `clip.follow_action_chance`, `clip.follow_action_time` |
| **Track freeze / unfreeze** | Freeze CPU-heavy tracks before complex operations | MEDIUM | `track.freeze()` / `track.unfreeze()` — not all track types support this |
| **Track routing control** | Route tracks to custom outputs (e.g., for stem export setup) | MEDIUM | `track.current_input_routing`, `track.current_output_routing`, `track.available_input_routing_types` |
| **Cue point management** | Named markers for arrangement navigation | MEDIUM | `song.set_or_delete_cue()`, `song.jump_to_next_cue()`, `song.get_cue_points()` |
| **Scene properties** | Set scene tempo, color, name for organized arrangements | LOW | `scene.tempo`, `scene.color`, `scene.name` |
| **Bulk track/clip data query** | Efficient state dump — get all track properties in one call | MEDIUM | Reduces round-trips from ~20 commands to 1; critical for AI to understand full session state |
| **Arrangement clip creation** | Place clips in Arrangement View (not just Session) | HIGH | Arrangement clips exist on tracks but are accessed differently — `track.arrangement_clips` is not writable directly; requires recording or complex API paths |
| **Device chain navigation (racks)** | Navigate into Instrument Racks, Drum Racks, Effect Racks | HIGH | `device.chains[n].devices[m]` — nested devices require recursive traversal; Drum Rack pads have their own chains |
| **MIDI clip transpose** | Transpose all notes in a clip without replacing them | MEDIUM | Not a single API call — must get_notes, transform, replace; but wrapping this as a tool adds real value |
| **Clip duplication to arrangement** | Duplicate Session clip to Arrangement timeline | HIGH | No direct API; workarounds involve recording into arrangement |
| **Tap tempo** | AI can synchronize BPM to a musical idea | LOW | `song.tap_tempo()` — simple but useful |
| **Metronome toggle** | Enable/disable click track | LOW | `song.metronome` — boolean writable |
| **Groove/swing control** | Apply groove templates and control global swing amount | MEDIUM | `song.groove_amount` (global), individual groove pool items more complex |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem like obvious additions but should be deliberately avoided or carefully scoped.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Audio export / render** | "Bounce to WAV" is a natural request after AI-created production | The Live Python API has no official export method. Workarounds require GUI automation (sending keyboard shortcuts via OS) which is brittle, platform-specific, and breaks across Live versions. The scope is also wrong — exporting is an offline operation, not DAW control. | Document this as out-of-scope. Link to Ableton's export docs. If a future Ableton API exposes export, add it then. |
| **Real-time audio input processing** | Analyzing live audio input to drive MIDI generation | MCP latency (100ms-1s round trips) makes this impractical. Also requires hardware configuration beyond the MCP server's scope. | Not applicable. For audio analysis, process audio files externally and load results. |
| **MIDI 2.0 features** | Live 12 added some MIDI 2.0 concepts | The Python Remote Script API does not expose MIDI 2.0 properties — it's UI-only in Live 12. Implementing fake MIDI 2.0 wrappers would mislead users. | Cover standard MIDI (pitch, velocity, duration) fully first. |
| **Video/clip triggers** | Ableton has video capabilities | Ableton's video support is minimal, rarely used in production, and not exposed meaningfully in the Python API. | Out of scope, per PROJECT.md. |
| **Max for Live device creation** | M4L is part of Ableton | M4L device development is a separate domain requiring Max/MSP knowledge. The MCP server can *load* M4L devices from the browser but cannot create or edit their internals. | Treat M4L devices as black boxes — load them, set parameters, but don't build them. |
| **Parameter listeners / real-time push** | "Notify me when volume changes" | The socket protocol is request-response, not pub/sub. Listeners in the Live API require persistent callbacks — adding a listener layer would require completely different socket architecture and introduce state management complexity. | Provide polling tools (get_track_info returns current state); AI can poll if needed. |
| **Direct .als file manipulation** | Editing the project file while Live is closed | .als is a gzip'd XML format that is undocumented and changes between versions. Manipulating it directly risks corrupting projects. Ableton may inject automation or warp data differently in future versions. | Use the live API exclusively while Ableton is running. |
| **Multi-session management** | Control multiple Live instances simultaneously | The socket server is one-to-one (port 9877, one connection). Supporting multiple instances would require port-per-instance configuration and complex state isolation. | One Live instance per MCP server. Document this clearly. |

---

## Feature Dependencies

```
Fix instrument loading
    └──enables──> Everything else (broken loading = no sound = useless server)

Create audio track
    └──requires──> Browser item loading (instruments/samples must load onto it)

Clip automation envelopes
    └──requires──> Device parameters (need to know which param to automate)
    └──requires──> Clip creation

Device chain navigation (racks)
    └──requires──> Get device info (need to inspect device type before traversing)

Arrangement clip creation
    └──requires──> Understanding of track arrangement view
    └──conflicts──> Session View clip operations (different code paths)

Track routing control
    └──requires──> Audio track creation (routing only meaningful if tracks exist)

Bulk session state query
    └──enhances──> All read operations (optimization, not prerequisite)

Scene management (fire)
    └──requires──> Clip creation (scenes with empty slots fire empty)

MIDI note transpose (as tool)
    └──requires──> Get clip notes
    └──requires──> Add notes to clip (replace cycle)

Quantize clip notes
    └──requires──> Clip creation with notes

Groove / swing
    └──enhances──> MIDI clip notes (groove makes them feel more human)
```

### Dependency Notes

- **Instrument loading is the critical path blocker**: Until loading instruments reliably works, all MIDI playback produces silence. Every other feature depends on this being correct.
- **Get clip notes requires Add notes**: The edit loop (get → transform → replace) requires both tools to work together. They should be tested as a pair.
- **Automation envelopes require device parameters**: You cannot automate a parameter you cannot identify. The `get_device_parameters` tool must exist before automation tools are useful.
- **Arrangement clips conflict with Session clips**: The Live API has different code paths for arrangement vs. session view clips. Arrangement clips are accessible on `track.arrangement_clips` but are read-mostly; creating arrangement clips is not directly supported via the standard clip slot API.

---

## MVP Definition

The existing server already has a working skeleton. MVP means: the server can create a fully playable, multi-instrument session with basic mixing.

### Launch With (v1) — The Production Floor

- [x] **Fix instrument loading** — Without this, nothing plays. Priority zero.
- [ ] **Create audio track** — Complete track type coverage
- [ ] **Create return track** — Reverb/delay setup
- [ ] **Delete track** — Clean up mistakes
- [ ] **Track volume / pan** — Basic mixing
- [ ] **Track mute / solo** — Arrangement workflow
- [ ] **Send levels** — Route to reverb/delay
- [ ] **Get clip notes** — Read MIDI back for editing
- [ ] **Remove notes from clip** — Selective editing
- [ ] **Clip loop settings** (loop on/off, loop_start, loop_end) — All clips loop
- [ ] **Scene create / name / fire** — Session View is the primary workflow
- [ ] **Get device parameters** — Know what can be adjusted
- [ ] **Set device parameter** — Tweak synths/effects
- [ ] **Undo / redo** — Safety net for AI mistakes
- [ ] **Stop all clips** — Emergency stop
- [ ] **Continue playback** — Resume without restart

### Add After Validation (v1.x) — Production Quality

- [ ] **Bulk session state query** — AI context efficiency (reduce round-trips)
- [ ] **Quantize clip notes** — Timing correction
- [ ] **MIDI note transpose** — Harmonic variation
- [ ] **Clip pitch / gain / warp** — Audio clip control
- [ ] **Track color** — Organization
- [ ] **Scene color / tempo** — Scene properties
- [ ] **Cue point management** — Arrangement navigation
- [ ] **Track routing control** — Advanced signal flow
- [ ] **Tap tempo** — BPM workflow
- [ ] **Metronome toggle** — Click track

### Future Consideration (v2+) — Power User Features

- [ ] **Clip automation envelopes** — High complexity, high value; needs careful design to be usable by AI
- [ ] **Device chain navigation (racks)** — Complex traversal; needs robust error handling for deeply nested chains
- [ ] **Track freeze / unfreeze** — Useful but edge case
- [ ] **Clip follow actions** — Generative music use case; complex parameter set
- [ ] **Arrangement clip creation** — Requires research into Live API limitations; may be impossible cleanly

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Fix instrument loading | HIGH | LOW | P1 |
| Get/remove clip notes | HIGH | LOW | P1 |
| Track volume/pan/mute/solo/arm | HIGH | LOW | P1 |
| Send levels | HIGH | LOW | P1 |
| Create audio/return/group track | HIGH | LOW | P1 |
| Delete track | HIGH | LOW | P1 |
| Scene create/fire/name | HIGH | LOW | P1 |
| Get/set device parameters | HIGH | LOW | P1 |
| Undo / redo | HIGH | LOW | P1 |
| Clip loop settings | HIGH | LOW | P1 |
| Bulk session state query | HIGH | MEDIUM | P1 |
| Quantize clip notes | MEDIUM | LOW | P2 |
| MIDI note transpose (tool) | MEDIUM | LOW | P2 |
| Clip pitch / gain / warp | MEDIUM | LOW | P2 |
| Track color | MEDIUM | LOW | P2 |
| Scene color / tempo | MEDIUM | LOW | P2 |
| Cue point management | MEDIUM | MEDIUM | P2 |
| Track routing control | MEDIUM | MEDIUM | P2 |
| Tap tempo / metronome | LOW | LOW | P2 |
| Clip follow actions | MEDIUM | MEDIUM | P3 |
| Clip automation envelopes | HIGH | HIGH | P3 |
| Device chain / rack navigation | HIGH | HIGH | P3 |
| Track freeze / unfreeze | LOW | MEDIUM | P3 |
| Arrangement clip creation | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch (v1)
- P2: Should have, add when possible (v1.x)
- P3: Nice to have, future consideration (v2+)

---

## Competitor Feature Analysis

Four known Ableton MCP server implementations exist as of March 2026:

| Feature | ahujasid/ableton-mcp (original, ~this codebase) | uisato/ableton-mcp-extended | Simon-Kansara (OSC-based) | Ziforge/liveapi-tools |
|---------|------|------|------|------|
| MIDI track creation | Yes | Yes | Yes | Yes |
| Audio track creation | No | Yes | Yes | Yes |
| Return track creation | No | Yes | Yes | Yes |
| Instrument loading | Yes (broken) | Yes | Via OSC | Yes |
| Basic MIDI note add | Yes | Yes | Yes | Yes |
| Get clip notes | No | No | Yes | Yes |
| Quantize notes | No | No | Yes | Yes |
| Track volume/pan | Partial (read only) | Yes | Yes | Yes |
| Send levels | No | No | Yes | Yes |
| Scene management | No | Yes | Yes | Yes |
| Device parameters | Partial | Yes | Yes | Yes |
| Undo/redo | No | No | Yes | Yes |
| Automation envelopes | No | No | No | Yes |
| Clip loop settings | No | Yes | Yes | Yes |
| Track routing | No | No | Yes | Yes |
| Bulk state query | No | No | Yes (OSC bulk) | Yes |
| Arrangement view | No | No | Partial | Yes |
| Follow actions | No | No | No | Yes |
| Take lanes (Live 12) | No | No | No | Yes |

**Our approach:** Match Ziforge's coverage (the most comprehensive implementation) via the native socket/Remote Script architecture rather than OSC. OSC adds a dependency (AbletonOSC must be installed separately) while socket-based is self-contained.

---

## Live API Coverage Map

What the Live Object Model exposes, mapped to implementation priority:

### Song Object (global session state)
- **Implemented:** `tempo`, `signature_numerator/denominator` (read), `is_playing`, track/return counts, master volume/pan
- **Must add:** `undo()`, `redo()`, `can_undo`, `can_redo`, `create_audio_track()`, `create_return_track()`, `delete_track()`, `duplicate_track()`, `create_scene()`, `delete_scene()`, `loop`/`loop_start`/`loop_length`, `stop_all_clips()`, `continue_playing()`, `metronome`, `groove_amount`, `clip_trigger_quantization`, `current_song_time`, cue point methods
- **Later:** `capture_midi()` (Live 10+), `set_or_delete_cue()`, `tap_tempo()`

### Track Object
- **Implemented:** `name`, `mute`, `solo`, `arm`, `volume` (read via info), `panning` (read via info)
- **Must add:** Write volume/pan, `sends[n].value`, `color`, `stop_all_clips()`, `has_audio_input`, `has_midi_input` (already read but not in separate tools)
- **Later:** `input_routing_type/channel`, `output_routing_type/channel`, `fold_state`, `freeze()`/`unfreeze()`

### Clip Object
- **Implemented:** `name`, `length`, `is_playing`, `is_recording` (read via track info), `fire()`, `stop()`, `set_notes()` (via add_notes_to_clip)
- **Must add:** `get_notes()`, `remove_notes()`, `looping`, `loop_start`, `loop_end`, `start_marker`, `end_marker`, `delete_clip()`, `duplicate_loop()`
- **Later:** `pitch_coarse`, `pitch_fine`, `gain`, `warping`, `warp_mode`, `quantize()`, `select_all_notes()`, `automation_envelope()`, follow action properties

### ClipSlot Object
- **Implemented:** `fire()`, `stop()`, `has_clip`, `create_clip()`
- **Must add:** `delete_clip()`
- **Later:** `duplicate_clip_to()`

### Device/DeviceParameter Object
- **Implemented:** Device name/class listed in track info; `load_browser_item()` (broken)
- **Must add:** `parameters[n].value` (read+write), `parameters[n].name/min/max`, fix browser item loading
- **Later:** Chain/rack navigation, `automation_envelope()` per device parameter

### Scene Object
- **Implemented:** Nothing (no scene tools)
- **Must add:** `name`, `fire()`, `color`, `song.create_scene()`, `song.delete_scene()`
- **Later:** `tempo` per scene, `fire_as_selected()`

### MixerDevice Object
- **Implemented:** Volume/panning in track info (read only)
- **Must add:** Write volume, pan, sends; return track mixer; master track mixer

---

## Sources

- [AbletonOSC - full OSC command reference](https://github.com/ideoforms/AbletonOSC) — HIGH confidence, actively maintained, exposes full LOM
- [Live Object Model Reference (Max 5 docs)](https://docs.cycling74.com/legacy/max5/refpages/m4l-ref/m4l_live_object_model.html) — HIGH confidence, canonical Cycling74 documentation
- [Structure Void - Live 10.0.1 Python API XML](https://structure-void.com/PythonLiveAPI_documentation/Live10.0.1.xml) — HIGH confidence, community-generated from actual API
- [Ziforge/ableton-liveapi-tools - 220 tools across 44 categories](https://github.com/Ziforge/ableton-liveapi-tools) — HIGH confidence, production implementation
- [Ableton Live 12 MIDI Remote Scripts source](https://github.com/gluon/AbletonLive12_MIDIRemoteScripts) — HIGH confidence, actual Ableton source
- [AbletonOSC NIME 2023 paper](https://nime.org/proceedings/2023/nime2023_60.pdf) — MEDIUM confidence, peer-reviewed overview of LOM scope
- [Ableton Export API docs](https://ableton.github.io/export/) — LOW confidence for Python API (export not exposed in Remote Script API)
- [Ableton Forum - clip.quantize() discussion](https://forum.ableton.com/viewtopic.php?t=244945) — MEDIUM confidence, community verification of quantize API

---
*Feature research for: Ableton Live 12 MCP server (DAW control API)*
*Researched: 2026-03-10*
