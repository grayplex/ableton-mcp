# Phase 32: Device State Reader and Gain Staging - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Session-wide mix state snapshot and role-based gain staging analysis. Two new MCP tools:
- `get_mix_state()` — snapshot of current device parameters for every device on every track
- `check_gain_staging()` — per-track dBFS estimates from live meters, compared against role-based targets, with out-of-range tracks flagged

This phase does NOT modify any device parameters, does not add recipe data, and does not implement mix adjustment suggestions (Phase 33).

</domain>

<decisions>
## Implementation Decisions

### get_mix_state Scope (STATE-01)

- **D-01:** Include **all track types**: regular tracks + return tracks + master track. Full session snapshot — Phase 33 `suggest_mix_adjustments` needs master chain state too. Matches "every track" language in STATE-01.

- **D-02:** Each track entry contains **device params only** — no mixer state (volume, pan, sends). Volume/pan is already accessible via existing `get_track_info`/`get_volume` tools. Keeps output focused on what Phase 33 actually needs to diff against recipes.

### Gain Staging Meter Source (GAIN-01)

- **D-03:** Use **`output_meter_level`** for per-track dBFS estimates — reads live signal level (0.0–1.0 normalized) from Ableton's track meter and converts to dBFS. This is actual signal strength, not fader position.

- **D-04:** When all meters read 0.0 (session not playing), the tool must warn: something like `"All meters are 0 — play the session to get live meter readings"`. Report the raw values regardless; don't abort.

### Role Resolution for Gain Staging (GAIN-01, GAIN-02)

- **D-05:** Role is **inferred from track name** via case-insensitive substring match against the ROLES list (`kick`, `bass`, `lead`, `pad`, `chords`, `vocal`, `atmospheric`, `return`, `master`). Examples: `"KICK_01"` → `kick`, `"bass_synth"` → `bass`. First match wins.

- **D-06:** Tracks with **no role match** are still included in the output with their meter level but marked `"role": null` — no false negatives on unrecognized tracks. They are excluded from the flag comparison (can't compare without a target).

- **D-07:** MIDI tracks with no instrument loaded (GAIN-02) are **excluded from gain staging analysis** entirely. Identify by checking `len(track.devices) == 0` on the RS side. These are v1.3 scaffold tracks — no false-positive flags.

### Claude's Discretion

- Exact dBFS target ranges per role (e.g. kick: -12 to -6 dBFS, bass: -14 to -8 dBFS) — planner researches mixing conventions and authors these
- Where gain targets live: new `MCP_Server/devices/gain_targets.py` or inline constant in the new analysis tool module
- How `output_meter_level` maps to dBFS (Ableton meters are peak, 0.0 = −∞, 1.0 = 0 dBFS — likely a simple `20 * log10(value)` for non-zero)
- Whether `get_mix_state` skips tracks with zero devices or includes them with an empty `devices: []` list
- New RS command name(s) for reading all-track device state in one round-trip vs. looping `get_device_parameters` calls on the MCP side

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Device/Mixing Infrastructure
- `AbletonMCP_Remote_Script/handlers/devices.py` — `_get_device_parameters` handler (lines 82–119); pattern for reading device params per track
- `AbletonMCP_Remote_Script/handlers/mixer_helpers.py` — `_to_db()` conversion (normalized volume → dB); may be reusable or referenced for meter conversion
- `MCP_Server/tools/mixing.py` — existing `apply_mix_recipe`, `apply_master_recipe`, `set_sidechain_source` tools; new state/gain tools go in this module or a new `MCP_Server/tools/analysis.py`

### Role and Catalog Data
- `MCP_Server/devices/catalog.py` — `ROLES` list (line 2242); gain targets belong adjacent to this
- `MCP_Server/mixing/catalog.py` — `get_recipe(role, genre)` pattern; Phase 33 will use `get_mix_state` output alongside recipes

### Requirements
- `STATE-01` (REQUIREMENTS.md) — single-call session-wide device state snapshot
- `GAIN-01` (REQUIREMENTS.md) — per-track dBFS from meter levels, role-based targets, flag out-of-range
- `GAIN-02` (REQUIREMENTS.md) — exclude MIDI tracks with no instrument from gain staging

### Success Criteria (from ROADMAP.md Phase 32)
1. `get_mix_state` returns current device params for every device on every track in one MCP call
2. `check_gain_staging` returns per-track dBFS estimates vs. role-based targets with out-of-range tracks flagged
3. Gain staging excludes MIDI tracks with no instrument loaded

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_get_device_parameters` RS handler — already reads `device.parameters` with name/value/min/max; `get_mix_state` RS handler is a session-wide loop of the same logic
- `_to_db()` in `mixer_helpers.py` — converts normalized volume; meter_level → dBFS will need a similar conversion (`20 * log10(meter_level)` for peak meters)
- `format_error()` / `get_ableton_connection()` in `MCP_Server/connection.py` — standard error/connection pattern
- `self._song.tracks`, `self._song.return_tracks`, `self._song.master_track` — RS access pattern for all track types (established in existing handlers)

### Established Patterns
- RS `@command` (no `write=True`) for read-only handlers
- MCP tools: `@mcp.tool()`, `ctx: Context` first arg, return type `str` (JSON)
- Track type routing via `track_type` param already used in `get_device_parameters`

### Integration Points
- `get_mix_state` output → consumed by Phase 33 `suggest_mix_adjustments` (diffs against recipe)
- `check_gain_staging` → reads `output_meter_level` and role inferred from `track.name`
- GAIN-02 check: `len(track.devices) == 0` on MIDI tracks → skip

</code_context>

<specifics>
## Specific Ideas

- `get_mix_state` RS response shape: `{tracks: [{index, name, type, devices: [{class_name, device_name, parameters: [{name, value}]}]}], return_tracks: [...], master_track: {...}}`
- `check_gain_staging` output per track: `{index, name, role, meter_db, target_range, status: "ok"|"too_hot"|"too_quiet"|"unknown"}` — role null → status "unknown", excluded MIDI tracks omitted entirely
- All-meters-zero warning appended to result as a top-level `"warning"` field rather than an error

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 32-device-state-reader-and-gain-staging*
*Context gathered: 2026-03-28*
