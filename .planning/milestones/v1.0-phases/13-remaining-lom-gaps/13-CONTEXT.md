# Phase 13: Remaining LOM Gaps - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement all remaining "Add" tier gaps from the Phase 11 LOM gap report — everything deferred from Phase 12. This covers scene extensions, Simpler device operations (including full slicing), plugin presets, A/B compare, groove pool, mixer extended (crossfader), drum pad operations, clip follow actions, track freeze/unfreeze, and session audio clip creation from file.

</domain>

<decisions>
## Implementation Decisions

### Scope & Prioritization
- **All remaining Add-tier gaps included** — no trimming. Continues the "all Add-tier gaps get implemented" principle from Phase 12
- MIDA-01/MIDA-02 (select/deselect notes, replace selected) already covered by Phase 12's NOTE-04 and NOTE-05 — excluded from Phase 13
- ACRT-01 (session audio from file via ClipSlot.create_audio_clip) included
- TRKA-01 (freeze/unfreeze track actions) included — Phase 12 only added read-only is_frozen/can_be_frozen
- SESS-02 (clip follow actions) included — researcher should verify Live 12.3 follow action API from LOM spec, as Live 11+ changed follow actions significantly

### Plan Organization (3 plans by affinity)
- **Plan 1: Scene + Mixer extended** (~8 items) — Session-view controls
  - Scene: color, per-scene tempo/time_sig, fire_as_selected, is_empty (SCNX-01 to SCNX-06 minus SCNX-05 if already done)
  - Mixer: crossfader, crossfade_assign, panning_mode (MIXX-01 to MIXX-03)
- **Plan 2: Simpler + DrumPad + Plugin/Device** (~10 items) — Device-related
  - Simpler: crop, reverse, warp_as/double/half, playback_mode, full slice management (SMPL-01 to SMPL-05)
  - DrumPad: per-pad mute/solo, delete_all_chains (DRPD-01, DRPD-02)
  - Plugin: preset list/select (DEVX-03), A/B compare (DEVX-04)
- **Plan 3: Groove + Follow actions + Track freeze + Audio** (~6 items) — Miscellaneous remaining
  - Groove pool: list_grooves, get/set_groove_params, set_clip_groove (GRVX-01 to GRVX-03)
  - Follow actions: get/set follow action type/probability/time (SESS-02)
  - Track: freeze/unfreeze actions (TRKA-01)
  - Audio: create session audio clip from file (ACRT-01)
- Each plan delivers **handlers + MCP tools + smoke tests** (all-in-one pattern, matching Phase 12)

### Simpler API
- **Full Simpler + slicing** — all operations including slice management (insert/move/remove/clear slices)
- Sample loading: researcher should check the LOM spec for what SimplerDevice exposes for file handling and implement accordingly — no assumptions about adding/skipping sample loading tools
- SimplerDevice.Sample child object provides slice access

### DrumPad Addressing
- **By MIDI note number** — mute_drum_pad(track_index, device_index, note=36)
- Matches LOM's DrumPad.note property, unambiguous, works with any Drum Rack layout
- Existing get_rack_chains already returns pad note numbers for discoverability

### Groove Pool API
- **3 separate tools**: list_grooves, get/set_groove_params, set_clip_groove
- Clean separation: pool browsing, parameter control, and clip association are distinct operations
- New handler domain — no existing groove handler exists

### Scene Tempo
- **Expose as-is** with informative response noting "Scene tempo will override global tempo when fired"
- set_scene_tempo(scene_index, tempo, enabled=True) — enabled defaults to True when setting tempo
- Same pattern for per-scene time signature

### Plugin Presets
- **Separate tools**: list_plugin_presets and set_plugin_preset
- Only works on PluginDevice types — error if called on non-plugin device
- Discoverable, clean API surface

### Follow Actions
- **Full read/write** — get/set follow action type, probability, and time
- Researcher must verify Live 12.3 follow action API from LOM spec — Live 11+ may have expanded beyond the classic 2-action model

### Version Compatibility
- **Assume Live 12.3+** — consistent with Phase 12 decision
- No version guards or hasattr() checks
- A/B preset compare (Live 12.3+) included without version check

### Claude's Discretion
- Exact plan boundaries — may adjust the 3 logical groups if implementation dependencies warrant it
- Handler mixin naming for new domains (GrooveHandlers, SimplerHandlers, etc.)
- Whether to extend existing MCP tool modules or create new ones (e.g., grooves.py, simpler.py)
- Test organization for new tool modules
- Error message wording for domain-specific edge cases
- How to handle Simpler sample loading based on LOM research

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### LOM Specification
- `Max9-LOM-en.pdf` — Complete LOM reference for Live 12.3.5 / Max 9. 171 pages. PRIMARY reference for all API signatures, parameter types, and value ranges. Key sections for Phase 13: SimplerDevice, PluginDevice, Scene, MixerDevice, GroovePool, Groove, DrumPad, Clip (follow actions).

### Gap Report
- `.planning/phases/11-check-for-live-object-model-gaps/11-GAP-REPORT.md` — Complete gap report with 52 Add-tier and 26 Backlog-tier items organized by LOM class. Phase 13 implements the remaining Add-tier items not covered by Phase 12.

### Requirements & Architecture
- `.planning/REQUIREMENTS.md` — v2 requirements: SCNX-01 to SCNX-06, DEVX-03, DEVX-04, SMPL-01 to SMPL-05, ACRT-01, GRVX-01 to GRVX-03, MIXX-01 to MIXX-03, DRPD-01, DRPD-02, SESS-02, TRKA-01.
- `.planning/ROADMAP.md` — Phase history, success criteria patterns, plan structure conventions.
- `.planning/STATE.md` — Project state, decisions log, velocity metrics.

### Prior Phase Context
- `.planning/phases/12-fill-in-missing-gaps/12-CONTEXT.md` — Phase 12 decisions. Deferred items section lists exactly what Phase 13 should implement. Version compatibility decision (Live 12.3+).
- `.planning/phases/11-check-for-live-object-model-gaps/11-CONTEXT.md` — Phase 11 decisions including audit scope and gap prioritization.

### Existing Implementation
- `AbletonMCP_Remote_Script/handlers/` — All Remote Script handler modules (14 files). Mixin pattern, command registry.
- `AbletonMCP_Remote_Script/handlers/base.py` — Command registry (_READ_COMMANDS, _WRITE_COMMANDS, _BROWSER_COMMANDS) with 4-tuple entries.
- `AbletonMCP_Remote_Script/handlers/devices.py` — _resolve_device helper for device navigation. Key for Simpler/Plugin device access.
- `AbletonMCP_Remote_Script/handlers/scenes.py` — Existing scene handlers (create, name, fire, delete). Extend for color/tempo/time_sig.
- `MCP_Server/tools/` — All MCP tool modules (15 files). @mcp.tool() decorator pattern.
- `MCP_Server/connection.py` — send_command function, timeout tiers.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_resolve_device(self, params)` in handlers/devices.py — Device resolution with chain navigation. Needed for Simpler/Plugin device access and DrumPad navigation.
- `_resolve_track(song, track_type, track_index)` in handlers/tracks.py — Track resolution for regular/return/master. Used by all track-referencing commands.
- `_resolve_clip_slot(song, track_index, clip_index)` in handlers/clips.py — Clip slot resolution. Needed for follow actions and session audio clip creation.
- `get_rack_chains` in handlers/devices.py — Already returns DrumPad info with note numbers. DrumPad mute/solo builds on this.
- `SceneHandlers` mixin in handlers/scenes.py — Existing scene operations. Scene extensions (color, tempo) extend this mixin.
- `COLOR_NAMES` dict in handlers/tracks.py — 70 snake_case color names for Ableton palette. Reusable for scene color support.

### Established Patterns
- Domain handler mixin → MCP tool module → smoke test (consistent across all 12 phases)
- JSON response format with json.dumps(result, indent=2) for all tools
- Conditional param building — only non-None values sent to send_command
- _WRITE_COMMANDS vs _READ_COMMANDS vs _BROWSER_COMMANDS timeout tiers
- Patch get_ableton_connection at import site for test isolation

### Integration Points
- New handler mixins wire into AbletonMCP MRO in AbletonMCP_Remote_Script/handlers/__init__.py
- New MCP tools register via @mcp.tool() in MCP_Server/tools/ modules
- New commands added to _READ_COMMANDS, _WRITE_COMMANDS, or _BROWSER_COMMANDS in base.py
- conftest.py and test files follow existing smoke test patterns
- SimplerDevice accessed via device chain on track (same path as any device)

</code_context>

<specifics>
## Specific Ideas

- Follow actions: researcher should specifically look at Live 12.3 LOM spec to see if follow actions expanded beyond the classic 2-action model (follow_action_0/1 + probability)
- Simpler sample loading: researcher should check what SimplerDevice exposes for file handling in the LOM and implement whatever the API supports
- DrumPad addressing by note number (e.g., 36 = C1) matches the existing get_rack_chains output which already includes note numbers per pad
- Groove pool is a Song-level object (song.groove_pool.grooves) — new handler domain with no existing code
- Per-scene tempo: response should note that scene tempo overrides global tempo when fired

</specifics>

<deferred>
## Deferred Ideas

### Backlog (from gap report — 26 items)
- Recording-specific overdub controls (arrangement_overdub, overdub, punch_in/out)
- Tempo nudge (nudge_down/up) — DJ-style mixing
- Count-in duration — recording preference
- Session automation record — manual workflow
- Scrubbing (scrub_by, clip scrub/stop_scrub)
- Ableton Link sync (force_link_beat_time, is_ableton_link_enabled)
- Tempo follower
- MIDI recording quantization
- Back to arranger (per-track)
- Input/output routing channel set (sub-routing channels vary by hardware)
- Playing/fired slot index — monitoring only
- Track visibility/selection state
- Implicit arm (Push-specific)
- Input/output meter readings (high CPU)
- Track performance impact — monitoring only
- Clip position alias, ram_mode, is_overdubbing/is_recording, will_record_on_start
- Playing position/status in clip — monitoring only
- set_fire_button_state — controller emulation
- Move playing position in clip
- ClipSlot has_stop_button
- Group slot state queries
- Scene is_triggered — monitoring only
- Device latency (latency_in_samples/ms) — monitoring only
- Quantize pitch (pitch-specific quantize) — niche editing

None — all Add-tier items are included in Phase 13. Only Backlog-tier items remain.

</deferred>

---

*Phase: 13-remaining-lom-gaps*
*Context gathered: 2026-03-19*
