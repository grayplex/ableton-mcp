# Phase 31: Apply Recipe and Batch Parameter Tools - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Single-call recipe application — load required devices onto a track, convert natural-unit recipe values to normalized using catalog conversion metadata, set all parameters atomically, and support sidechain source routing by track name. Also ships a batch parameter setter as a Remote Script primitive (BATCH-01).

**New MCP tools in this phase:**
- `apply_mix_recipe(track_index, role, genre)` — loads devices + sets all params in one call
- `apply_master_recipe(genre)` — applies full master bus chain (GlueCompressor + MultibandDynamics + Limiter) to master track
- `set_sidechain_source(track_index, device_index, source_track_name)` — sets compressor sidechain source by track name

**New Remote Script commands:**
- `apply_recipe` — atomic load + set handler
- `set_sidechain_source` — name-resolving sidechain setter
- `set_device_parameters` (plural) — batch param setter primitive (BATCH-01)

This phase does NOT touch genre blueprints, recipe data for the 8 remaining genres (Phase 34), or state reading/gain staging (Phase 32).

</domain>

<decisions>
## Implementation Decisions

### Atomicity Strategy (APPLY-03, BATCH-01)

- **D-01:** A new Remote Script command `apply_recipe` handles the entire load + wait + set sequence in one socket round-trip. The RS handler: (1) checks the track's existing device chain, (2) loads any missing devices via browser path and blocks until `track.devices` confirms the device is present, (3) sets all parameters using their normalized values. No polling loop on the MCP side — atomicity is guaranteed inside the RS handler.

- **D-02:** Browser paths for built-in devices are hardcoded in the RS handler as a dict keyed by catalog class name:
  ```python
  DEVICE_PATHS = {
      "Eq8": "audio_effects/EQ Eight",
      "Compressor2": "audio_effects/Compressor",
      "GlueCompressor": "audio_effects/Glue Compressor",
      ...
  }
  ```
  Reliable for built-in devices; no live browser query needed at apply time.

- **D-03:** Natural-unit → normalized conversion happens **on the MCP side** before sending the command. The MCP tool reads the recipe (natural units), reads the catalog (conversion metadata), converts all values to normalized floats, then sends a payload of `{device_class: {param_name: normalized_value}}` to the RS handler. The RS handler only receives normalized values — no conversion logic in RS code.

### Device Conflict Handling

- **D-04:** When applying a recipe to a track that already has devices, **update params in place** — if a device of the required class already exists on the track, set its parameters without reloading it. Only load devices that are absent from the track. Match existing devices by `device.class_name` (not display name, which is user-renameable).

- **D-05:** If multiple devices of the same class exist on the track (e.g. two EQ Eights), the first match by index is used. No error — this is an edge case the user can resolve manually.

### Master Bus Recipe Scope (APPLY-02)

- **D-06:** Phase 31 authors full master bus recipes for the 4 core genres (house, techno, ambient, DnB) with the complete chain: **Glue Compressor + Multiband Dynamics + Limiter** parameter values per genre. These live in `MCP_Server/mixing/master_*.py` or as a `MASTER_RECIPE` constant alongside the existing `RECIPE` in each genre file — planner decides layout.

- **D-07:** `apply_master_recipe(genre)` applies the full chain to the master track (`track_type="master"`). It follows the same conflict handling as D-04: update-in-place if devices already exist. Phase 34 extends this to the remaining 8 genres.

### Sidechain Routing (SIDE-01)

- **D-08:** New RS command `set_sidechain_source` accepts `track_index`, `device_index`, and `source_track_name`. The RS handler resolves `source_track_name` → track index by iterating `Live.Song.tracks` at apply time.

- **D-09:** If `source_track_name` is not found in the session, **abort with error** — `apply_mix_recipe` fails with a clear error message naming the unresolved track. No partial state (recipe applied without sidechain configured). User fixes the track name and retries.

- **D-10:** `set_sidechain_source` is also exposed as a standalone MCP tool (not only called internally by `apply_mix_recipe`) so users can update sidechain routing independently.

### Claude's Discretion
- Whether master bus recipes live as `MASTER_RECIPE` constants in existing genre files or in separate `master_house.py` etc. files
- Exact normalized parameter values for master bus recipes (GlueCompressor ratio, MultibandDynamics thresholds, Limiter ceiling) per genre
- Internal structure of the `apply_recipe` RS handler (single method vs. helper decomposition)
- Whether `set_device_parameters` RS primitive (BATCH-01) is also exposed as a standalone MCP tool or only used internally

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Recipe and Catalog Data
- `MCP_Server/mixing/catalog.py` — `get_recipe(role, genre)` public API; mixing auto-discovery pattern
- `MCP_Server/mixing/house.py`, `techno.py`, `ambient.py`, `drum_and_bass.py` — existing `RECIPE` constants (natural units); master recipes to be added in this phase
- `MCP_Server/devices/catalog.py` — `CATALOG` dict with conversion metadata; MCP tool uses this to convert natural → normalized before sending to RS

### Existing RS Infrastructure
- `AbletonMCP_Remote_Script/handlers/devices.py` — existing `load_browser_item` and `set_device_parameter` handlers; new `apply_recipe`, `set_sidechain_source`, `set_device_parameters` handlers go here
- `AbletonMCP_Remote_Script/handlers/base.py` — `@command` decorator and handler base pattern

### Tool Patterns
- `MCP_Server/tools/catalog.py` — existing mixing tool pattern (`get_mix_recipe`); `apply_mix_recipe` and `apply_master_recipe` go in `MCP_Server/tools/mixing.py`
- `MCP_Server/tools/devices.py` — `load_instrument_or_effect`, `set_device_parameter` tool patterns

### Requirements
- `APPLY-01`, `APPLY-02`, `APPLY-03` (REQUIREMENTS.md) — apply tool requirements and atomicity constraint
- `BATCH-01` (REQUIREMENTS.md) — batch parameter setting in single socket round-trip
- `SIDE-01` (REQUIREMENTS.md) — sidechain source by track name

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/mixing/catalog.py` — `get_recipe(role, genre)` for recipe lookup
- `MCP_Server/devices/catalog.py` — `CATALOG[class_name]["parameters"]` entries with `conversion` dicts for unit conversion
- `format_error()` in `MCP_Server/connection.py` — consistent error responses
- `get_ableton_connection()` in `MCP_Server/connection.py` — socket communication

### Established Patterns
- RS `@command` decorator with `write=True` for state-mutating handlers (see `set_device_parameter`)
- MCP tools: `@mcp.tool()`, `ctx: Context` first arg, return type `str`
- RS handlers use `self._song.tracks[i].devices` to access device chain
- `load_browser_item` RS handler is the precedent for browser-based device loading

### Integration Points
- Phase 31 MCP tools → read from `MCP_Server/mixing/` (recipes) and `MCP_Server/devices/catalog.py` (conversions)
- Phase 31 `apply_recipe` RS command → writes to `track.devices` and `device.parameters`
- Phase 32 (`get_mix_state`) → reads from `track.devices`; depends on device chain Phase 31 creates
- Phase 33 (`suggest_mix_adjustments`) → compares live state against recipes Phase 31 applies

</code_context>

<specifics>
## Specific Ideas

- MCP payload shape for `apply_recipe` RS command: `{track_index, track_type, devices: [{class_name, params: {param_name: normalized_value}}]}`
- RS handler iterates `devices` list: for each entry, find existing device by `class_name` or load via `DEVICE_PATHS[class_name]`, then set each param by name lookup in `device.parameters`
- Master track: `track_type="master"` maps to `Live.Song.master_track` in RS handler

</specifics>

<deferred>
## Deferred Ideas

- Full master bus recipes for 8 remaining genres (synthwave, hip-hop/trap, dubstep, trance, lo-fi, future bass, disco/funk, neo-soul/R&B) — Phase 34 scope
- Auto-wire all genre-conventional sidechain connections in one call — v1.5 future requirement
- `set_device_parameters` as a standalone user-facing MCP tool — Claude's discretion; may be useful for power users but not required by any SC

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 31-apply-recipe-and-batch-parameter-tools*
*Context gathered: 2026-03-28*
