# Phase 21: Blueprint Tools - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

MCP tool wrappers that expose the genre catalog (built in Phase 20) to Claude. Delivers two tools: `list_genre_blueprints` (discovery) and `get_genre_blueprint` (retrieval with section filtering and subgenre support). This is a thin wrapper phase — catalog logic already exists.

</domain>

<decisions>
## Implementation Decisions

### Section Filtering
- **D-01:** `sections` parameter is a list of strings — e.g., `get_genre_blueprint(genre="house", sections=["harmony", "rhythm"])`. Clean, typed, easy for Claude to construct
- **D-02:** When no `sections` filter is provided, return the full blueprint (all 6 dimensions). Claude always gets the complete picture by default

### Tool Output Shape
- **D-03:** `get_genre_blueprint` returns the nested dict structure directly as JSON via `json.dumps()` — preserves the dimensional grouping from the catalog
- **D-04:** `list_genre_blueprints` returns a summary per genre: `{"id": "house", "name": "House", "bpm_range": [120,130], "subgenres": ["deep_house", "tech_house", ...]}`. Enough to decide what to request without being token-heavy

### Error Handling
- **D-05:** Use the existing `format_error()` pattern from `MCP_Server/connection.py` — structured errors with type, detail, and suggestion fields. Matches all other tools
- **D-06:** Always try alias resolution before erroring on genre not found — "deep house" resolves to house/deep_house automatically. Only error if alias also fails. Makes the tool forgiving

### Claude's Discretion
- Tool file placement (new `MCP_Server/tools/genres.py` or extend existing file)
- Parameter naming and docstrings
- Whether to include `subgenre` as a separate parameter or part of the genre string
- Invalid section name handling (ignore silently, warn, or error)
- Test structure and fixture patterns

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Implementation Patterns
- `MCP_Server/tools/theory.py` — Tool registration pattern to follow (`@mcp.tool()`, `Context` param, `json.dumps()`, `format_error()`)
- `MCP_Server/tools/__init__.py` — Tool auto-registration via import (new genres module must be added here)
- `MCP_Server/connection.py` — `format_error()` helper for structured error responses

### Genre Infrastructure (Phase 20 output)
- `MCP_Server/genres/__init__.py` — Barrel exports: `get_blueprint`, `list_genres`, `resolve_alias`
- `MCP_Server/genres/catalog.py` — Catalog functions the tools will wrap
- `MCP_Server/genres/schema.py` — TypedDict definitions for type hints

### Requirements
- `.planning/REQUIREMENTS.md` — TOOL-01, TOOL-02 requirements for this phase
- `.planning/ROADMAP.md` — Phase 21 success criteria (4 criteria)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/genres/catalog.py` — `list_genres()`, `get_blueprint(genre_id, subgenre)`, `resolve_alias()` already implemented and tested
- `MCP_Server/connection.py` — `format_error()` helper for structured error responses
- `MCP_Server/server.py` — `mcp` FastMCP instance for `@mcp.tool()` registration

### Established Patterns
- Tool modules import from library packages and wrap with `@mcp.tool()` + error handling
- All tool functions take `ctx: Context` as first param
- Return `json.dumps(result)` for success, `format_error(...)` for errors
- `MCP_Server/tools/__init__.py` imports all tool modules to trigger registration

### Integration Points
- New `MCP_Server/tools/genres.py` imports from `MCP_Server.genres` and registers with `mcp`
- `MCP_Server/tools/__init__.py` needs to import the new genres module
- Tests in `tests/` — can extend `test_genres.py` or create new `test_genre_tools.py`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — standard tool wrapper following the theory.py pattern. The catalog does the heavy lifting; tools just expose it with proper MCP interface and error handling.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 21-blueprint-tools*
*Context gathered: 2026-03-26*
