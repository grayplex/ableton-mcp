# Phase 20: Blueprint Infrastructure - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

A validated schema and catalog system exists, proven end-to-end with a complete house genre blueprint. Delivers: TypedDict schema for all six genre dimensions, auto-discovery catalog registry, alias resolution, subgenre merge logic, import-time validation, and a fully populated house genre as the canonical example.

</domain>

<decisions>
## Implementation Decisions

### Blueprint Data Format
- **D-01:** Blueprints are authored as Python dicts in `.py` files — matches existing codebase pattern (scales.py, progressions.py define data as Python dicts)
- **D-02:** Each genre file exports pure data only (one dict for base genre, one dict for subgenres) — no helper functions in genre files. Logic lives in the catalog/schema layer

### Genre Module Organization
- **D-03:** Blueprints live in `MCP_Server/genres/` — new top-level package alongside `theory/`. Clean separation: `theory/` = computation, `genres/` = reference data
- **D-04:** One file per genre — `house.py`, `techno.py`, `hip_hop_trap.py`, etc. Catalog auto-discovers all genre modules in the package
- **D-05:** Subgenres live in the same file as their parent genre — `house.py` exports both the base genre dict and a subgenres dict with deep/tech/progressive/acid entries. Merge logic lives in the catalog, not the genre file

### Schema Enforcement
- **D-06:** TypedDict defines the blueprint schema — provides IDE autocompletion and type hints for blueprint authors
- **D-07:** A `validate_blueprint()` function checks required keys and types at import time
- **D-08:** Validation raises ValueError per malformed genre, but the catalog catches it, logs the error, and excludes that genre — server starts with remaining valid genres. Fail per-genre, not per-server

### Blueprint Content Structure
- **D-09:** All six dimensions use structured data with typed fields — no prose text. Enables the palette bridge (Phase 24) to programmatically extract chords/scales
- **D-10:** Harmony dimension includes: `scales[]`, `chord_types[]`, `common_progressions[]` — all names must match theory engine types (for QUAL-02 cross-validation in Phase 24)
- **D-11:** Instrumentation uses generic roles — "kick", "bass", "pad", "lead", "hi-hats" — not Ableton-specific device names. Claude maps roles to devices contextually
- **D-12:** Arrangement includes section sequences with bar counts — `[{"name": "intro", "bars": 16}, {"name": "buildup", "bars": 8}, {"name": "drop", "bars": 32}, ...]`

### Claude's Discretion
- Rhythm dimension structure (time signature, BPM range already in top-level; drum pattern representation, swing/groove characteristics)
- Mixing dimension structure (frequency ranges, common effects, stereo field conventions)
- Production tips dimension structure (genre-specific techniques, common pitfalls)
- Catalog auto-discovery mechanism (package scanning, explicit registry, or `__init__.py` imports)
- Alias resolution implementation (dict mapping, function, or decorator)
- Subgenre merge strategy details (shallow dict merge as specified in INFR-04)
- Internal naming conventions for exported dicts (e.g., `HOUSE`, `HOUSE_SUBGENRES`)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Patterns
- `MCP_Server/theory/__init__.py` — Barrel export pattern to follow for `genres/` package
- `MCP_Server/theory/scales.py` — Reference for how data dicts are defined (SCALE_INTERVALS pattern)
- `MCP_Server/theory/progressions.py` — Reference for genre-tagged data dicts (COMMON_PROGRESSIONS)
- `MCP_Server/tools/theory.py` — Tool registration pattern (for Phase 21)

### Requirements
- `.planning/REQUIREMENTS.md` — INFR-01 through INFR-05, GENR-01 requirements for this phase
- `.planning/ROADMAP.md` — Phase 20 success criteria (5 criteria)

### Prior Architecture
- `.planning/codebase/CONVENTIONS.md` — Naming conventions, code style, import organization
- `.planning/codebase/STRUCTURE.md` — Directory layout and package organization

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/theory/scales.py` — `SCALE_INTERVALS` dict pattern: data defined as module-level constant, imported by other modules
- `MCP_Server/theory/progressions.py` — `COMMON_PROGRESSIONS` with genre tags: existing genre-to-data mapping pattern
- `MCP_Server/theory/__init__.py` — Barrel export pattern for package API

### Established Patterns
- One-file-per-domain in `theory/` (7 modules) — `genres/` follows same pattern (one-file-per-genre)
- Tool modules in `MCP_Server/tools/` — one `.py` per domain (15 modules)
- `json.dumps()` for all tool return values
- Type hints on all function signatures
- Standalone tests for pure computation in `tests/`

### Integration Points
- `MCP_Server/genres/` package needs to be importable by `MCP_Server/tools/` (Phase 21 tool wrappers)
- Theory engine types (chord_types, scale names) referenced in blueprints must match `theory/chords.py` and `theory/scales.py` supported values (validated in Phase 24)
- Catalog registry will be the entry point for Phase 21's `list_genre_blueprints` and `get_genre_blueprint` tools

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for the remaining dimensions (rhythm, mixing, production tips). The structured data pattern established for harmony and arrangement should carry through.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 20-blueprint-infrastructure*
*Context gathered: 2026-03-26*
