# Phase 29: Device Parameter Catalog and Role Taxonomy - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a queryable catalog of exact Ableton API parameter names, value ranges, and normalized-to-natural-unit conversion formulas for 12 built-in devices. Also define the canonical mixing role taxonomy used as lookup keys for recipes in later phases.

The 12 target devices: EQ Eight, Compressor, Glue Compressor, Drum Buss, Multiband Dynamics, Reverb, Delay, Auto Filter, Gate, Limiter, Envelope Follower, Utility.

The 9 roles: kick, bass, lead, pad, chords, vocal, atmospheric, return, master.

**Critical constraint:** Catalog entries MUST be validated against a live Ableton session — no hand-authored parameter names from documentation. The bootstrap process generates the static catalog.

No new Remote Script handlers needed. No recipe logic. No apply tools. Just the catalog data, a bootstrap script, and two MCP query tools.

</domain>

<decisions>
## Implementation Decisions

### D-01: Catalog Bootstrap Process
A one-time bootstrap script (e.g. `bootstrap_catalog.py` or `scripts/bootstrap_catalog.py`) runs against a live Ableton session and writes the catalog to a static Python file committed to the repo. The catalog is usable offline; the script is re-run if Ableton updates change parameter names or ranges.

The bootstrap script uses the existing `get_device_parameters` Remote Script command to query each of the 12 target devices from a live session, then writes the resulting parameter data into `MCP_Server/devices/catalog.py`.

### D-02: Catalog Storage Format
Single `MCP_Server/devices/catalog.py` module containing a `CATALOG` dict keyed by Ableton class name (e.g. `"Eq8"`, `"Compressor"`). Each entry holds display name, parameters list, and conversions. All 12 devices in one file.

```python
# MCP_Server/devices/catalog.py
CATALOG = {
    "Eq8": {
        "display_name": "EQ Eight",
        "parameters": [
            {
                "name": "Frequency 1 A",
                "min": 0.0,
                "max": 1.0,
                "is_quantized": False,
                "conversion": {
                    "type": "log",
                    "natural_min": 20,
                    "natural_max": 22050,
                    "unit": "Hz"
                }
            },
            ...
        ]
    },
    ...
}
```

### D-03: Unit Conversion Representation
Conversion formulas are stored as structured dicts on each parameter entry:
```python
"conversion": {
    "type": "log" | "linear" | "linear_db" | None,
    "natural_min": <number>,
    "natural_max": <number>,
    "unit": "Hz" | "dB" | "ms" | "%" | ...
}
```
Parameters with no conversion (already in natural units, or on/off toggles) omit the `conversion` key or set it to `None`. This format is serializable, diffable, and usable at runtime by recipe application code without `eval()`.

### D-04: MCP Tool Surface
Two focused tools:
- `get_device_catalog(device_name: str)` — accepts display name (e.g. `"EQ Eight"`) or class name (e.g. `"Eq8"`), returns that device's full parameter list with conversion info. Does NOT require Ableton to be running (reads from static catalog).
- `get_role_taxonomy()` — returns the canonical role list. Does NOT require Ableton to be running.

No `list_catalog_devices()` or `get_mix_catalog()` in this phase — keep tool surface minimal for now. Can be added in a later phase if needed.

### D-05: Role Taxonomy
Bare list stored in `MCP_Server/devices/roles.py` (or inline in `catalog.py`):
```python
ROLES = [
    "kick", "bass", "lead", "pad",
    "chords", "vocal", "atmospheric",
    "return", "master"
]
```
No gain targets or metadata in this phase — roles are just the canonical string identifiers used as recipe lookup keys. Gain staging targets belong in Phase 32 when they're actually used.

### Claude's Discretion
- Whether `ROLES` lives in `catalog.py` or a separate `roles.py` — either is fine
- Exact Ableton class names for each device (bootstrap script discovers these from live session)
- Which parameters have conversions vs. which are already in natural units (determined during bootstrap)
- How the bootstrap script handles devices not present in the live session (skip with warning or error)
- Internal structure of the bootstrap script (single script vs. module)
- Whether `get_device_catalog` accepts fuzzy name matching or exact only

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Device Infrastructure
- `MCP_Server/tools/devices.py` — existing `get_device_parameters` MCP tool — catalog tools go in the same module or a new `MCP_Server/tools/catalog.py`
- `AbletonMCP_Remote_Script/handlers/devices.py` — `_get_device_parameters` handler — bootstrap script uses this command (`"get_device_parameters"`) to query live Ableton

### Pattern Reference
- `MCP_Server/genres/catalog.py` — existing catalog pattern (pkgutil-based genre discovery) — catalog.py for devices should be simpler (no pkgutil needed, static dict)
- `MCP_Server/genres/schema.py` — schema/TypedDict pattern — consider TypedDict for catalog entries if type safety desired

### Requirements
- `CATL-01` (in REQUIREMENTS.md): exact requirement for catalog scope and validation constraint
- `ROLE-01` (in REQUIREMENTS.md): exact requirement for role taxonomy

### Success Criteria (from ROADMAP.md Phase 29)
1. Query any of 12 target devices → receive exact API parameter names matching `get_device_parameters` output
2. Retrieve normalized-to-natural-unit conversion formulas for parameters that use normalized storage
3. Retrieve role taxonomy and use identifiers as recipe lookup keys
4. Catalog validated against live Ableton — no hand-authored names

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_ableton_connection()` in `MCP_Server/connection.py` — bootstrap script uses this to send `get_device_parameters` commands to live Ableton
- `ableton.send_command("get_device_parameters", params)` — the exact call to query live device params
- `format_error()` in `MCP_Server/connection.py` — use in new MCP tools for consistent error responses

### Established Patterns
- MCP tools live in `MCP_Server/tools/*.py` decorated with `@mcp.tool()`
- Tool return type is always `str` (JSON-serialized)
- Static data lives in `MCP_Server/genres/` (genre blueprints) — device catalog follows same pattern at `MCP_Server/devices/`
- Parameter data shape from live Ableton: `{index, name, value, min, max, is_quantized}` — catalog extends this with `conversion`

### Integration Points
- Bootstrap script → writes `MCP_Server/devices/catalog.py`
- `MCP_Server/tools/catalog.py` (new) → reads from `MCP_Server/devices/catalog.py`, exposes 2 MCP tools
- Phase 30 recipes → import `CATALOG` from `MCP_Server/devices/catalog.py` to reference parameter names
- Phase 31 apply tool → imports `CATALOG` to look up parameter names before setting values

</code_context>

<specifics>
## Specific Ideas

No specific UI/UX references — this is pure data infrastructure. The key requirement is that the bootstrap process is runnable by a developer with Ableton open, and the resulting catalog.py is committed to the repo so downstream phases and tests can use it without a live session.

</specifics>

<deferred>
## Deferred Ideas

- `list_catalog_devices()` MCP tool — not needed for Phase 29 success criteria; add later if useful
- `get_mix_catalog()` full-dump tool — can be added if Claude needs bulk access; defer to when recipes are built
- Role metadata (gain targets, typical devices, descriptions) — Phase 32 adds gain targets when they're actually used for gain staging analysis
- Catalog versioning or update detection — out of scope for v1.4

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 29-device-parameter-catalog-and-role-taxonomy*
*Context gathered: 2026-03-28*
