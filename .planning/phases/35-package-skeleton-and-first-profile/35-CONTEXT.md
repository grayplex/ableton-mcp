# Phase 35: Package Skeleton and First Profile - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the `MCP_Server/sounds/` package with pkgutil auto-discovery catalog and the Wavetable instrument profile as reference implementation. Browser paths validated against live Ableton session. This phase proves the data schema and browser paths are correct before committing to all 6 instrument profiles in Phase 36.

</domain>

<decisions>
## Implementation Decisions

### Profile Data Shape
- **D-01:** Descriptor affinities use a two-axis dict structure: `{"role": {"pad": 0.9, "lead": 0.6}, "character": {"warm": 0.8, "evolving": 0.9}}` with 0.0-1.0 weights per tag
- **D-02:** No schema version or type marker -- minimal PROFILE dict constant (like GENRE/RECIPE), add validation later if needed
- **D-03:** Strengths and weaknesses are short phrase lists: `["lush evolving pads", "wavetable morphing", "complex textures"]`
- **D-04:** Sonic character is a single string paragraph describing the instrument's identity

### Browser Path Format
- **D-05:** Browser paths stored as root path + categories dict: `{"root": "Instruments/Wavetable", "categories": {"pad": "Pads", "lead": "Leads", "bass": "Bass"}}`
- **D-06:** Validation failure logs a warning but keeps the path -- profiles work without live Ableton
- **D-07:** Only the instrument root path is validated against live Ableton; category sub-paths are best-effort hints (vary by Live edition/installed packs)

### Alias & Lookup Behavior
- **D-08:** Short abbreviations supported via aliases list in each profile (e.g., `["wavetable", "wt"]`), same pattern as genre blueprints
- **D-09:** `catalog.get_profile()` returns `None` for unknown instrument names -- matches mixing/catalog pattern
- **D-10:** Display names accepted via normalization (case-insensitive, whitespace/hyphen to underscore) -- `"Wavetable"`, `"wavetable"`, `"wave table"` all resolve

### Claude's Discretion
- No areas explicitly deferred to Claude's discretion in this phase

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Package Pattern References
- `MCP_Server/genres/catalog.py` -- Auto-discovery pattern via pkgutil.iter_modules, alias normalization, module-level registry
- `MCP_Server/genres/__init__.py` -- Package init pattern for pkgutil discovery
- `MCP_Server/mixing/catalog.py` -- Same auto-discovery pattern, role/genre alias resolution

### Data Shape References
- `MCP_Server/genres/techno.py` -- Reference for module structure (GENRE dict constant with aliases list)
- `MCP_Server/mixing/techno.py` -- Reference for RECIPE dict constant structure

### Requirements
- `.planning/REQUIREMENTS.md` -- PKG-01 (package structure) and INST-01 (Wavetable profile)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `genres/catalog.py` `_discover_genres()` -- Direct pattern to follow for `_discover_profiles()`
- `genres/catalog.py` `_normalize_alias()` -- Same normalization logic reusable
- `mixing/catalog.py` `_SKIP_MODULES` / `_ROLE_ALIASES` / `_GENRE_ALIASES` -- Alias map patterns

### Established Patterns
- Pure Python dicts for data modules (no classes) -- D-01 through D-04 in genre/mixing conventions
- Module-level `_registry` dict populated on first access (lazy init)
- `_SKIP_MODULES = {"catalog"}` to exclude infrastructure from discovery
- Each data module exports a single constant (GENRE, RECIPE) -- sounds/ will use PROFILE

### Integration Points
- `MCP_Server/sounds/__init__.py` -- New package init (pkgutil needs `__path__`)
- `MCP_Server/sounds/catalog.py` -- `get_profile()` public API, consumed by Phase 38 MCP tools
- `MCP_Server/sounds/wavetable.py` -- First profile module, reference for Phase 36

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches following the established genres/mixing patterns.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 35-package-skeleton-and-first-profile*
*Context gathered: 2026-03-31*
