# Phase 11: Check for Live Object Model Gaps - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Audit the Live Object Model (LOM) specification against our 65 implemented MCP tools to identify missing capabilities and correctness issues. Produce a structured gap report organized by LOM class with Add/Backlog tiers, update REQUIREMENTS.md with new entries, and fix any correctness issues found inline.

</domain>

<decisions>
## Implementation Decisions

### Gap Prioritization
- Prioritize gaps by **AI music production value** — what helps Claude compose, arrange, and mix better
- Two-tier system: **Add** (implement) vs **Backlog** (capture for future)
- Backlog gaps are kept in a backlog section for potential future work, not discarded
- Existing v2 requirements (cue points, follow actions, tap tempo, metronome, groove, freeze/unfreeze) are **pre-approved** — gap analysis adds new gaps alongside them
- All four gap categories ranked as high-impact: scale & key awareness, scene workflow, note expressiveness, clip launch settings
- Specialized device APIs: **skip all except Simpler** — generic get/set_device_parameter covers everything else. Simpler's specialized API (crop, reverse, warp, slice) is uniquely valuable.

### Audit Scope
- **Core + secondary classes**: Song, Track, Clip, ClipSlot, Scene, Device, MixerDevice, Chain, DrumPad (core) plus GroovePool/Groove, CuePoint, Application, PluginDevice, SimplerDevice (secondary)
- **Audit existing implementations** for correctness: deprecated API usage, missing optional parameters, incorrect value ranges, missing edge case handling
- **Verify all value ranges** against the LOM spec — e.g., pitch_fine documented as -50 to 49 in LOM vs our -500 to 500 validation
- **Flag version-specific APIs** — mark gaps requiring Live 12.3+ (e.g., insert_device, Track.create_audio_clip) for compatibility awareness
- **Official LOM only** — do not include private _Framework APIs (undocumented, unstable)
- Skip: Track.back_to_arranger, naming convention audit (existing conventions deliberately chosen for AI clarity)

### Deliverable Format
- Gap report as `11-GAP-REPORT.md` in phase directory
- Organized **by LOM class** (Song, Track, Clip, Scene, etc.)
- Each gap entry: Add/Backlog tier, LOM property/function name, description, AI production value rationale
- Correctness issues found → **fix inline** as part of this phase
- **Update REQUIREMENTS.md** with new v2 entries for all "Add" tier gaps
- Roadmap phase creation is NOT part of this phase (comes later)

### Arrangement Support
- Arrangement view is **Add tier** — essential for song finalization
- Track.create_audio_clip (arrangement) and Track.create_midi_clip (arrangement): Add
- duplicate_clip_to_arrangement: Add — bridges session → arrangement workflow
- Song.play_selection: Add
- Song.jump_by: Add

### Device Management
- Track.insert_device (Live 12.3+): **Add** — huge simplification over browser-based loading for native devices
- Song.move_device: **Add** — lets AI reorganize effect chains
- PluginDevice.presets and selected_preset_index: **Add** — preset selection for VST/AU plugins

### Audio Clip Creation
- ClipSlot.create_audio_clip(path): **Add** — session view audio clip from file
- Track.create_audio_clip(path, position): **Add** — arrangement view audio clip from file
- Warp markers (get/add/move/remove): **Add** — essential for audio timing manipulation

### Sub-Routing
- Routing channels (sub-routing within types): **Backlog** — routing types cover 90% of use cases
- Track.back_to_arranger: **Skip**

### Claude's Discretion
- Whether to note naming convention mismatches between our tools and LOM conventions (user said "you decide")
- Organization of gap report within each LOM class section
- How to structure REQUIREMENTS.md updates (new section vs extending v2)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Live Object Model Specification
- `Max9-LOM-en.pdf` — Complete LOM reference for Live 12.3.5 / Max 9. 171 pages covering all API objects, properties, and functions. This is the PRIMARY reference for gap identification.

### Existing Requirements & Architecture
- `.planning/REQUIREMENTS.md` — Current v1 (complete) and v2 (deferred) requirements. Gap report adds new entries here.
- `.planning/ROADMAP.md` — Phase history and structure. Phase 11 details at bottom.
- `.planning/STATE.md` — Current project state, decisions log, velocity metrics.

### Existing Implementation (for correctness audit)
- `AbletonMCP_Remote_Script/handlers/` — All Remote Script handler modules (13 files)
- `MCP_Server/tools/` — All MCP tool modules (14 files)
- `AbletonMCP_Remote_Script/handlers/base.py` — Command registry (_READ_COMMANDS, _WRITE_COMMANDS, _BROWSER_COMMANDS)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_resolve_track(song, track_type, track_index)` in handlers/tracks.py: Track resolution helper supporting regular/return/master
- `_resolve_device(self, params)` in handlers/devices.py: Device resolution with chain navigation
- `_resolve_clip_slot(song, track_index, clip_index)` in handlers/clips.py: Clip slot resolution
- `_resolve_parameter(self, device, param_name, param_index)` in handlers/automation.py: Parameter lookup by name or index
- Mixin class pattern: All handler modules use mixin classes inherited by AbletonMCP
- Command registry: 4-tuple entries with self_scheduling flag in base.py

### Established Patterns
- Domain handler mixin → MCP tool module → smoke test (consistent across all 10 phases)
- JSON response format with json.dumps(result, indent=2) for all tools
- Conditional param building (only non-None values sent to send_command)
- _WRITE_COMMANDS vs _READ_COMMANDS vs _BROWSER_COMMANDS timeout tiers
- Patch get_ableton_connection at import site for test isolation

### Integration Points
- New handler mixins wire into AbletonMCP MRO in __init__.py
- New MCP tools register via @mcp.tool() in tools/ modules
- New commands added to _READ_COMMANDS, _WRITE_COMMANDS, or _BROWSER_COMMANDS in base.py
- conftest.py and test files follow existing smoke test patterns

</code_context>

<specifics>
## Specific Ideas

- pitch_fine range mismatch is a known correctness issue to investigate: LOM says -50 to 49, we validate -500 to 500
- insert_device (Live 12.3+) is a major workflow improvement — lets Claude skip browser navigation entirely for native devices
- Simpler's specialized API is uniquely valuable because it's the most commonly used sampler in Ableton
- The audit should surface gaps across the full "compose → arrange → mix" AI workflow

</specifics>

<deferred>
## Deferred Ideas

- Recording controls (record_mode, session_record, overdub) — mentioned but not selected for discussion; evaluate during gap analysis
- Sub-routing channels — routing types cover 90% of use cases, channels are backlog
- Track.back_to_arranger — skipped as niche
- Specialized device APIs beyond Simpler (Compressor sidechain, EQ8, Wavetable, Drift, etc.) — generic parameters sufficient

</deferred>

---

*Phase: 11-check-for-live-object-model-gaps*
*Context gathered: 2026-03-18*
