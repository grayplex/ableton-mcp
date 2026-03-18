# Requirements: AbletonMCP

**Defined:** 2026-03-10
**Core Value:** An AI assistant can produce actual music in Ableton — instruments load, notes play, effects shape sound, and the mix comes together.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Foundation

- [x] **FNDN-01**: Server runs on Python 3 only — all Python 2 compatibility code removed
- [x] **FNDN-02**: Remote Script uses Python 3.11 idioms (super(), f-strings, type hints, queue module)
- [x] **FNDN-03**: Socket protocol uses length-prefix framing instead of JSON-completeness parsing
- [x] **FNDN-04**: Global connection protected by threading.Lock for concurrent tool invocations
- [x] **FNDN-05**: All error handling uses specific exception types — no bare except:pass blocks
- [x] **FNDN-06**: Remote Script command dispatch uses dict-based router instead of if/elif chain
- [x] **FNDN-07**: MCP tools organized into domain modules (tracks, clips, mixing, etc.)
- [x] **FNDN-08**: Remote Script handlers organized into domain modules with @main_thread decorator
- [x] **FNDN-09**: Linting configured with ruff (target Python 3.11, PEP 8, import ordering)
- [x] **FNDN-10**: Test infrastructure with pytest + pytest-asyncio using FastMCP in-memory client

### Track Management

- [x] **TRCK-01**: User can create MIDI tracks at specified index
- [x] **TRCK-02**: User can create audio tracks at specified index
- [x] **TRCK-03**: User can create return tracks
- [x] **TRCK-04**: User can create group tracks
- [x] **TRCK-05**: User can delete any track by index
- [x] **TRCK-06**: User can duplicate any track by index
- [x] **TRCK-07**: User can rename any track
- [x] **TRCK-08**: User can set track color
- [x] **TRCK-09**: User can get detailed info about any track (name, type, devices, clips, routing)

### Mixing

- [x] **MIX-01**: User can set track volume (0.0–1.0 normalized)
- [x] **MIX-02**: User can set track pan (-1.0 to 1.0)
- [x] **MIX-03**: User can mute/unmute any track
- [x] **MIX-04**: User can solo/unsolo any track
- [x] **MIX-05**: User can arm/disarm any track for recording
- [x] **MIX-06**: User can set send levels for any track to any return
- [x] **MIX-07**: User can set master track volume
- [x] **MIX-08**: User can set return track volume and pan

### Clip Management

- [x] **CLIP-01**: User can create MIDI clips with specified length in any clip slot
- [x] **CLIP-02**: User can delete clips from any clip slot
- [x] **CLIP-03**: User can duplicate clips to another slot
- [x] **CLIP-04**: User can rename clips
- [x] **CLIP-05**: User can set clip loop enabled/disabled
- [x] **CLIP-06**: User can set clip loop start and end positions
- [x] **CLIP-07**: User can set clip start and end markers
- [x] **CLIP-08**: User can fire (launch) any clip
- [x] **CLIP-09**: User can stop any clip

### MIDI Editing

- [x] **MIDI-01**: User can add MIDI notes to a clip (pitch, start, duration, velocity)
- [x] **MIDI-02**: User can read back all notes from a clip
- [x] **MIDI-03**: User can remove notes from a clip (by time/pitch range)
- [x] **MIDI-04**: User can quantize notes in a clip (grid size, strength)
- [x] **MIDI-05**: User can transpose all notes in a clip by semitones

### Device & Browser

- [x] **DEV-01**: User can load instruments onto tracks via browser (working — currently broken)
- [x] **DEV-02**: User can load effects onto tracks via browser
- [x] **DEV-03**: User can get all parameters of any device (name, value, min, max)
- [x] **DEV-04**: User can set any device parameter by name or index
- [x] **DEV-05**: User can browse the Ableton browser tree by category
- [x] **DEV-06**: User can navigate browser items at a specific path
- [x] **DEV-07**: User can navigate into Instrument Racks, Drum Racks, and Effect Racks
- [x] **DEV-08**: User can get a bulk session state dump (all tracks, clips, devices in one call)

### Scene & Transport

- [x] **SCNE-01**: User can create scenes
- [x] **SCNE-02**: User can name scenes
- [x] **SCNE-03**: User can fire (launch) scenes
- [x] **SCNE-04**: User can delete scenes
- [x] **TRNS-01**: User can start playback
- [x] **TRNS-02**: User can stop playback
- [x] **TRNS-03**: User can continue playback from current position
- [x] **TRNS-04**: User can stop all clips
- [x] **TRNS-05**: User can set tempo
- [x] **TRNS-06**: User can set time signature (numerator and denominator)
- [x] **TRNS-07**: User can set loop region (enabled, start, length)
- [x] **TRNS-08**: User can get current playback position
- [x] **TRNS-09**: User can undo last action
- [x] **TRNS-10**: User can redo last undone action

### Automation

- [x] **AUTO-01**: User can get automation envelope for a device parameter in a clip
- [x] **AUTO-02**: User can insert automation breakpoints into a clip envelope
- [x] **AUTO-03**: User can clear automation envelopes from a clip

### Routing

- [x] **ROUT-01**: User can get available input routing types for a track
- [x] **ROUT-02**: User can set track input routing
- [x] **ROUT-03**: User can get available output routing types for a track
- [x] **ROUT-04**: User can set track output routing

### Audio Clip Controls

- [x] **ACLP-01**: User can set audio clip pitch (coarse and fine)
- [x] **ACLP-02**: User can set audio clip gain
- [x] **ACLP-03**: User can toggle audio clip warping on/off

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap. Derived from Phase 11 LOM gap analysis (2026-03-18).

### Session

- **SESS-01**: User can manage cue points (set, delete, jump to)
- **SESS-02**: User can configure clip follow actions (action type, chance, time)
- **SESS-03**: User can tap tempo
- **SESS-04**: User can toggle metronome
- **SESS-05**: User can set groove/swing amount
- **SESS-06**: User can capture and insert scene (capture currently playing clips)
- **SESS-07**: User can capture recently played MIDI input
- **SESS-08**: User can get/set clip trigger quantization globally
- **SESS-09**: User can control session recording mode
- **SESS-10**: User can get/set root note, scale name, and scale mode (key awareness)

### Arrangement

- **ARR-01**: User can create arrangement MIDI clips (start_time, length on track)
- **ARR-02**: User can create arrangement audio clips from file (file_path, position on track)
- **ARR-03**: User can list arrangement clips on a track
- **ARR-04**: User can duplicate session clip to arrangement (session-to-arrangement bridge)
- **ARR-05**: User can play arrangement selection
- **ARR-06**: User can jump by beats (relative position navigation)
- **ARR-07**: User can get song length / last event time (arrangement bounds)

### Scale & Key

- **SCLE-01**: User can get/set song root note
- **SCLE-02**: User can get/set song scale name
- **SCLE-03**: User can get song scale intervals
- **SCLE-04**: User can get/set song scale mode

### Clip Launch

- **CLNC-01**: User can get/set clip launch mode (trigger/gate/toggle/repeat)
- **CLNC-02**: User can get/set clip launch quantization (per-clip)
- **CLNC-03**: User can get/set clip legato mode
- **CLNC-04**: User can get/set clip velocity amount (velocity sensitivity)
- **CLNC-05**: User can get/set clip muted state (clip activator)

### Note Expression

- **NOTE-01**: User can set note probability (0.0-1.0) when adding notes
- **NOTE-02**: User can set note velocity deviation (-127 to 127) when adding notes
- **NOTE-03**: User can set note release velocity (0-127) when adding notes
- **NOTE-04**: User can select/deselect specific notes in a clip by ID
- **NOTE-05**: User can modify notes in-place via apply_note_modifications (Live 11+)
- **NOTE-06**: User can remove/duplicate/get notes by ID
- **NOTE-07**: User can use native quantize with swing support

### Scene Extended

- **SCNX-01**: User can get/set scene color
- **SCNX-02**: User can get/set per-scene tempo
- **SCNX-03**: User can get/set per-scene time signature
- **SCNX-04**: User can fire scene as selected (fire + advance)
- **SCNX-05**: User can capture and insert scene
- **SCNX-06**: User can check if scene is empty

### Device Extended

- **DEVX-01**: User can insert device at specific index on track (Live 12.3+)
- **DEVX-02**: User can move device between tracks/positions
- **DEVX-03**: User can list and select plugin presets
- **DEVX-04**: User can use A/B preset compare (Live 12.3+)

### Simpler

- **SMPL-01**: User can crop Simpler sample to active region
- **SMPL-02**: User can reverse Simpler sample
- **SMPL-03**: User can warp Simpler sample (warp_as, warp_double, warp_half)
- **SMPL-04**: User can get/set Simpler playback mode (Classic/One-Shot/Slicing)
- **SMPL-05**: User can manage Simpler slices (list, insert, move, remove, clear)

### Audio Creation

- **ACRT-01**: User can create audio clip in session view from file
- **ACRT-02**: User can create audio clip in arrangement from file
- **ACRT-03**: User can get/add/move/remove warp markers on audio clips

### Groove

- **GRVX-01**: User can list grooves in groove pool
- **GRVX-02**: User can read/set groove parameters (timing, quantization, random, velocity amounts)
- **GRVX-03**: User can associate groove with clip

### Mixer Extended

- **MIXX-01**: User can control crossfader
- **MIXX-02**: User can get/set track crossfade assignment (A/B)
- **MIXX-03**: User can get panning mode (stereo/split)

### DrumPad Extended

- **DRPD-01**: User can mute/solo individual drum pads
- **DRPD-02**: User can clear all chains from a drum pad

### MIDI Advanced

- **MIDA-01**: User can select/deselect specific notes in a clip
- **MIDA-02**: User can replace selected notes (selective editing workflow)

### Track Advanced

- **TRKA-01**: User can freeze/unfreeze tracks
- **TRKA-02**: User can create arrangement clips (if API supports it)
- **TRKA-03**: User can set scene tempo per scene
- **TRKA-04**: User can stop all clips on a single track
- **TRKA-05**: User can get available input/output routing channels (sub-routing)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Audio export / render | Live Python API does not expose export functions; only brittle GUI automation possible |
| Real-time audio input processing | MCP latency (100ms-1s) makes this impractical; requires hardware config |
| MIDI 2.0 features | Python Remote Script API does not expose MIDI 2.0 properties |
| Video features | Ableton's video support is minimal and not exposed in Python API |
| Max for Live device creation | Separate domain requiring Max/MSP knowledge; can load M4L devices but not create them |
| Parameter listeners / real-time push | Socket protocol is request-response; listeners need different architecture |
| Direct .als file manipulation | Undocumented gzip'd XML format; risks corrupting projects |
| Multi-session management | Socket server is one-to-one; port-per-instance adds complexity for edge-case benefit |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FNDN-01 | Phase 1 | Complete |
| FNDN-02 | Phase 1 | Complete |
| FNDN-03 | Phase 1 | Complete |
| FNDN-04 | Phase 1 | Complete |
| FNDN-05 | Phase 1 | Complete |
| FNDN-06 | Phase 1 | Complete |
| FNDN-07 | Phase 2 | Complete |
| FNDN-08 | Phase 2 | Complete |
| FNDN-09 | Phase 2 | Complete |
| FNDN-10 | Phase 2 | Complete |
| TRCK-01 | Phase 3 | Complete |
| TRCK-02 | Phase 3 | Complete |
| TRCK-03 | Phase 3 | Complete |
| TRCK-04 | Phase 3 | Complete |
| TRCK-05 | Phase 3 | Complete |
| TRCK-06 | Phase 3 | Complete |
| TRCK-07 | Phase 3 | Complete |
| TRCK-08 | Phase 3 | Complete |
| TRCK-09 | Phase 3 | Complete |
| MIX-01 | Phase 4 | Complete |
| MIX-02 | Phase 4 | Complete |
| MIX-03 | Phase 4 | Complete |
| MIX-04 | Phase 4 | Complete |
| MIX-05 | Phase 4 | Complete |
| MIX-06 | Phase 4 | Complete |
| MIX-07 | Phase 4 | Complete |
| MIX-08 | Phase 4 | Complete |
| CLIP-01 | Phase 5 | Complete |
| CLIP-02 | Phase 5 | Complete |
| CLIP-03 | Phase 5 | Complete |
| CLIP-04 | Phase 5 | Complete |
| CLIP-05 | Phase 5 | Complete |
| CLIP-06 | Phase 5 | Complete |
| CLIP-07 | Phase 5 | Complete |
| CLIP-08 | Phase 5 | Complete |
| CLIP-09 | Phase 5 | Complete |
| MIDI-01 | Phase 6 | Complete |
| MIDI-02 | Phase 6 | Complete |
| MIDI-03 | Phase 6 | Complete |
| MIDI-04 | Phase 6 | Complete |
| MIDI-05 | Phase 6 | Complete |
| DEV-01 | Phase 7 | Complete |
| DEV-02 | Phase 7 | Complete |
| DEV-03 | Phase 7 | Complete |
| DEV-04 | Phase 7 | Complete |
| DEV-05 | Phase 7 | Complete |
| DEV-06 | Phase 7 | Complete |
| DEV-07 | Phase 7 | Complete |
| DEV-08 | Phase 7 | Complete |
| SCNE-01 | Phase 8 | Complete |
| SCNE-02 | Phase 8 | Complete |
| SCNE-03 | Phase 8 | Complete |
| SCNE-04 | Phase 8 | Complete |
| TRNS-01 | Phase 8 | Complete |
| TRNS-02 | Phase 8 | Complete |
| TRNS-03 | Phase 8 | Complete |
| TRNS-04 | Phase 8 | Complete |
| TRNS-05 | Phase 8 | Complete |
| TRNS-06 | Phase 8 | Complete |
| TRNS-07 | Phase 8 | Complete |
| TRNS-08 | Phase 8 | Complete |
| TRNS-09 | Phase 8 | Complete |
| TRNS-10 | Phase 8 | Complete |
| AUTO-01 | Phase 9 | Complete |
| AUTO-02 | Phase 9 | Complete |
| AUTO-03 | Phase 9 | Complete |
| ROUT-01 | Phase 10 | Complete |
| ROUT-02 | Phase 10 | Complete |
| ROUT-03 | Phase 10 | Complete |
| ROUT-04 | Phase 10 | Complete |
| ACLP-01 | Phase 10 | Complete |
| ACLP-02 | Phase 10 | Complete |
| ACLP-03 | Phase 10 | Complete |

**Coverage:**
- v1 requirements: 53 total, all complete
- v2 requirements: 58 total (from LOM gap analysis)
- Mapped to phases: 53 (v1)
- Unmapped: 0 (v1)

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-18 after Phase 11 LOM gap analysis — 58 v2 requirements added across 13 categories*
