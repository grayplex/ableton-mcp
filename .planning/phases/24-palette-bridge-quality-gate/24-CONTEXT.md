# Phase 24: Palette Bridge & Quality Gate - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

A new `get_genre_palette` MCP tool that takes a genre and key, reads the blueprint's harmony section, and returns key-resolved chord names, scale names, and progression chord names via the theory engine. Plus cross-validation ensuring all 12 genres meet token budget and theory-name correctness standards. Delivers: TOOL-03, QUAL-01, QUAL-02, QUAL-03.

</domain>

<decisions>
## Implementation Decisions

### Palette Tool Interface
- **D-01:** `get_genre_palette(genre, key)` — simple two-parameter interface. Subgenre resolved via alias (same as `get_genre_blueprint`). No explicit subgenre or scale_type parameters
- **D-02:** Returns resolved names only — chord names (e.g., "Cmin7", "Fmaj7"), scale names with root (e.g., "C dorian"), progression chord names. No MIDI pitches. Claude uses existing `build_chord`/`get_scale_pitches` tools when it needs MIDI
- **D-03:** Common progressions resolved from Roman numerals to chord names in key (e.g., "I-V-vi-IV" in C → ["Cmaj", "Gmaj", "Amin", "Fmaj"]). Roman numerals not preserved — output is the resolved form only

### Palette Error Handling
- **D-04:** If a blueprint references a chord_type or scale name the theory engine doesn't support, return partial results with an `unresolved` list showing which names couldn't be resolved. Graceful degradation, not hard failure

### Token Budget (QUAL-01)
- **D-05:** Measured using tiktoken with cl100k_base encoding — standard LLM token counting, pip-installable, reproducible
- **D-06:** What gets measured: `json.dumps()` of the full blueprint (what `get_genre_blueprint` returns with no section filter). This is exactly what Claude sees
- **D-07:** Soft cap with per-genre override — default range 800-1200 tokens enforced by test. Genres that genuinely need more space can declare a `MAX_TOKENS` override. Test still asserts the override ceiling

### Cross-Validation (QUAL-02)
- **D-08:** Single centralized all-genre test that iterates ALL 12 genres + ALL subgenres, validating every `chord_type` against `_QUALITY_MAP` and every scale name against `SCALE_CATALOG`. Replaces/supersedes per-genre validation tests as the source of truth. Auto-catches any new genre added later

### Test Strategy (QUAL-03)
- **D-09:** Mock-free integration tests for palette bridge — call `get_genre_palette` with real genres and real keys, verify output has correct chord names and scale names. Exercises real theory engine + genre catalog end-to-end. No mocking

### Claude's Discretion
- Palette tool file placement (likely `MCP_Server/tools/genres.py` alongside existing genre tools, or new file)
- Internal bridge function organization (in catalog.py, new bridge.py, or inline in tool)
- Token budget test implementation details (test fixture structure, parametrization)
- Centralized cross-validation test structure
- Whether to add tiktoken as a dev/test dependency only or as a runtime dependency
- Output JSON structure for the palette (field names, nesting)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Genre Infrastructure
- `MCP_Server/genres/catalog.py` — `get_blueprint()`, `list_genres()`, `resolve_alias()` — palette tool will call `get_blueprint` to read harmony section
- `MCP_Server/genres/schema.py` — TypedDict definitions, `validate_blueprint()`, `_SECTION_SPEC`
- `MCP_Server/genres/__init__.py` — Barrel exports for the genres package

### Theory Engine (bridge targets)
- `MCP_Server/theory/chords.py` — `build_chord(root, quality, octave)` for chord resolution, `_QUALITY_MAP` for validation (26 chord qualities)
- `MCP_Server/theory/scales.py` — `get_scale_pitches(root, scale_name)` for scale resolution, `SCALE_CATALOG` for validation (38 scales)
- `MCP_Server/theory/progressions.py` — `generate_progression(key, numerals, scale_type)` for progression resolution

### Existing Tool Pattern
- `MCP_Server/tools/genres.py` — Existing genre tools (`list_genre_blueprints`, `get_genre_blueprint`). New palette tool follows same pattern: `@mcp.tool()`, `Context` param, `json.dumps()`, `format_error()`
- `MCP_Server/tools/__init__.py` — Tool auto-registration via import
- `MCP_Server/connection.py` — `format_error()` helper for structured error responses

### Reference Blueprint
- `MCP_Server/genres/house.py` — Canonical genre blueprint. Harmony section structure is what the palette bridge reads

### Requirements
- `.planning/REQUIREMENTS.md` — TOOL-03, QUAL-01, QUAL-02, QUAL-03 for this phase
- `.planning/ROADMAP.md` — Phase 24 success criteria (4 criteria)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/genres/catalog.py` — `get_blueprint()` already resolves aliases and merges subgenres. Palette tool just calls this, reads `harmony` key, and passes to theory engine
- `MCP_Server/theory/chords.py` — `build_chord()` resolves root+quality to chord. `_QUALITY_MAP` has 26 supported qualities
- `MCP_Server/theory/scales.py` — `SCALE_CATALOG` has 38 supported scales. `get_scale_pitches()` resolves root+scale_name
- `MCP_Server/theory/progressions.py` — `generate_progression()` resolves Roman numerals in a key to chords
- `MCP_Server/tools/genres.py` — Existing tool module with `META_KEYS`, `SECTION_KEYS` constants and error handling pattern

### Established Patterns
- Tool modules import from library packages and wrap with `@mcp.tool()` + try/except + `format_error()`
- All tool functions take `ctx: Context` as first param, return `json.dumps(result)`
- Genre blueprints store harmony as: `{"scales": [...], "chord_types": [...], "common_progressions": [...]}`
- Tests in `tests/test_genres.py` — per-genre validation classes

### Integration Points
- New palette tool adds to `MCP_Server/tools/genres.py` (or new file)
- Bridge function reads blueprint harmony section via `get_blueprint()`, resolves each field via theory engine functions
- Centralized cross-validation test iterates `catalog.list_genres()` + `_subgenres` registry
- tiktoken needed as test dependency for token budget measurement

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. The palette bridge is a straightforward connector between the genre catalog's harmony data and the theory engine's resolution functions.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 24-palette-bridge-quality-gate*
*Context gathered: 2026-03-27*
