# Phase 30: Core Mix Recipes - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Build role × genre mix recipes for the 4 core genres (house, techno, ambient, DnB). Each recipe provides EQ, compression, reverb/delay, panning, and dynamics parameter values for a given role.

The 4 genres: house, techno, ambient, DnB.
The 9 roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master.

All 9 roles are authored for every genre — non-typical roles (e.g. ambient kick, techno vocal) receive safe generic values rather than being omitted.

**No new Remote Script handlers needed.** This is pure data + one MCP query tool. The apply tool that uses these recipes is Phase 31.

</domain>

<decisions>
## Implementation Decisions

### D-01: Parameter Value Format
Recipe values are stored in **natural units** (Hz, dB, ms, %, etc.) — not normalized 0.0–1.0.

Examples:
- EQ frequency: `80` (Hz), not `0.041`
- Compressor threshold: `-18` (dB), not `0.3`
- Reverb decay: `2400` (ms), not `0.55`

Phase 31's apply tool is responsible for converting natural units to normalized using the catalog's `conversion` metadata before sending values to Ableton. This keeps recipe files human-readable and authorable.

### D-02: Recipe Completeness
Recipes cover **all sound-shaping parameters** — every parameter in the catalog that affects tone, dynamics, or space for a given device. This is comprehensive but not exhaustive.

**Included:** Threshold, Ratio, Attack, Release, Gain, Frequency, Gain bands, Decay, Wet/Dry, Pan, LFO Amount, etc.

**Excluded:** `Device On`, `LegacyMode`, model selectors, and other non-sound-shaping housekeeping params. These are not authored in recipes and Phase 31 must not set them.

The planner should determine which catalog parameters are "sound-shaping" vs. "housekeeping" per device. A reasonable heuristic: if the parameter meaningfully affects the audio output (not device enable/bypass or legacy compatibility flags), it belongs in the recipe.

### D-03: Role Coverage Per Genre
**All 9 roles are authored for every genre.** Non-typical role/genre combinations receive safe, genre-appropriate generic values rather than being omitted. Examples:
- Ambient kick: light transient shaping (gentle EQ, very light compression, no Drum Buss)
- Techno vocal: clean utility EQ + light compression (no heavy vocal processing)
- House atmospheric: wide reverb + subtle pad-like EQ

This ensures Phase 31 can always find a recipe for any role/genre combination without fallback logic.

### D-04: Not-Applicable Device Handling
When a role/genre combination doesn't use a device type, **omit that device from the recipe entirely**. Phase 31 loads and sets only devices present in the recipe.

Example: an ambient kick recipe includes Eq8 and Compressor2 but omits DrumBuss and Reverb — Phase 31 will not load those devices.

No `None` markers or explicit skip keys.

### D-05: Auto-Discovery Pattern
Recipe modules follow the same pkgutil auto-discovery pattern as genre blueprints:
- One file per genre: `MCP_Server/mixing/house.py`, `techno.py`, `ambient.py`, `drum_and_bass.py`
- Each file exports a `RECIPE` constant (dict keyed by role → device class name → param name → value)
- `MCP_Server/mixing/catalog.py` auto-discovers recipe modules via `pkgutil.iter_modules`
- Adding a new genre recipe file requires zero registration code (satisfies SC #3)

### D-06: MCP Tool Surface
One new tool in this phase: `get_mix_recipe(role: str, genre: str) -> str`
- Returns the full recipe dict for that role/genre combination as JSON
- Accepts role aliases (e.g. "kick drum" → "kick") and genre aliases (e.g. "drum and bass" → "dnb")
- Returns an error if role or genre is not found

### Claude's Discretion
- Which catalog parameters are classified as "sound-shaping" vs. "housekeeping" per device
- Exact natural-unit values for each role/genre combination (this is the musical authoring work)
- Whether `RECIPE` lives in a `recipes/` subdirectory or directly in `MCP_Server/mixing/`
- Internal structure of the mixing catalog (validation on import vs. query time)
- Whether `get_mix_recipe` returns the full device spec or a summary

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Device Catalog (parameter names and conversions)
- `MCP_Server/devices/catalog.py` — CATALOG dict with 327 live-validated parameters across 12 devices; recipe parameter names MUST match entries in this catalog exactly
- `MCP_Server/devices/__init__.py` — `get_catalog_entry()` and `get_roles()` public API

### Auto-Discovery Pattern to Mirror
- `MCP_Server/genres/catalog.py` — pkgutil-based auto-discovery pattern; mixing catalog should mirror this
- `MCP_Server/genres/house.py` — genre module pattern (pure Python dict, `GENRE` constant) — recipe modules follow same structure with `RECIPE` constant

### Existing MCP Tool Pattern
- `MCP_Server/tools/catalog.py` — `get_device_catalog` and `get_role_taxonomy` tools; `get_mix_recipe` follows same pattern

### Requirements
- `RECIP-01` (in REQUIREMENTS.md): exact requirement for Phase 30 scope and success criteria
- Success criteria SC #2: recipe values reference catalog parameter names — no recipe can specify a name absent from the catalog
- Success criteria SC #3: pkgutil auto-discovery — zero registration code to add a new genre

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/devices/catalog.py` — `CATALOG` dict; recipe modules import this for parameter name validation
- `MCP_Server/genres/catalog.py` — `_discover_genres()` and `_ensure_initialized()` pattern; mixing catalog mirrors this exactly
- `format_error()` in `MCP_Server/connection.py` — use in `get_mix_recipe` for consistent error responses
- `MCP_Server/server.py` — `mcp` instance for `@mcp.tool()` decorators

### Established Patterns
- Genre modules: pure Python dicts, no helper functions, one `GENRE` constant per file
- MCP tools: `@mcp.tool()` decorator, `ctx: Context` first arg, return type `str` (JSON-serialized)
- Auto-discovery: `pkgutil.iter_modules` on package path, skip `_`-prefixed and infrastructure modules
- Static data packages: `MCP_Server/genres/` and `MCP_Server/devices/` as precedent for `MCP_Server/mixing/`

### Integration Points
- Recipe modules → imported by `MCP_Server/mixing/catalog.py` via pkgutil
- `MCP_Server/tools/mixing.py` (new) → calls `get_recipe(role, genre)` from mixing catalog, exposes `get_mix_recipe` MCP tool
- Phase 31 apply tool → imports both `CATALOG` (for param name lookup + conversion) and `get_recipe()` (for target values)
- Tests → import mixing catalog directly; validate all recipe param names against CATALOG entries

</code_context>

<specifics>
## Specific Ideas

- Recipe structure: `RECIPE[role][device_class_name][param_name] = natural_value`
- Example: `RECIPE["kick"]["Eq8"]["1 Frequency A"] = 80` (Hz)
- Catalog class names must be used as device keys (e.g. `"Compressor2"` not `"Compressor"`, per Phase 29 finding)

</specifics>

<deferred>
## Deferred Ideas

- `list_mix_recipes()` MCP tool — not needed for SC; can add later if Claude needs discovery
- Master bus recipes (`MSTR-01`) — Phase 34 scope
- Recipe quality gate (token budget check analogous to genre blueprints) — nice to have, not required
- Sidechain routing hints in recipes — Phase 31/31 scope (SIDE-01)

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 30-core-mix-recipes*
*Context gathered: 2026-03-28*
