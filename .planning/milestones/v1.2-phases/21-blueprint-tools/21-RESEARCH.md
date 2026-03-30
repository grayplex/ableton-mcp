# Phase 21: Blueprint Tools - Research

**Researched:** 2026-03-26
**Phase:** 21-blueprint-tools
**Goal:** Claude can discover available genres and retrieve full or section-filtered blueprints through MCP tools

## 1. Existing Catalog API (Phase 20 Output)

`MCP_Server/genres/catalog.py` provides three functions:

### `list_genres() -> List[dict]`
Returns `[{"id": str, "name": str, "bpm_range": [int, int], "subgenres": [str, ...]}, ...]`
Already matches TOOL-01 output shape from CONTEXT.md D-04.

### `get_blueprint(genre_id: str, subgenre: Optional[str] = None) -> Optional[dict]`
Returns full blueprint dict or None. Already handles alias resolution internally.
Missing: section filtering (TOOL-02 requirement).

### `resolve_alias(alias: str) -> Optional[dict]`
Returns `{"genre_id": str}` or `{"genre_id": str, "subgenre_id": str}` or None.
Used internally by `get_blueprint()`.

## 2. Tool Registration Pattern

From `MCP_Server/tools/theory.py`:

```python
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error
from MCP_Server.server import mcp

@mcp.tool()
def tool_name(ctx: Context, param: type) -> str:
    """Docstring for Claude.

    Parameters:
    - param: Description
    """
    try:
        result = library_function(param)
        return json.dumps(result)
    except Exception as e:
        return format_error("Error message", detail=str(e), suggestion="...")
```

Key patterns:
- `@mcp.tool()` decorator (no args)
- First param always `ctx: Context`
- Returns `json.dumps(result)` on success
- Returns `format_error(...)` on failure
- Docstring describes tool for Claude

## 3. Tool File Structure

New file: `MCP_Server/tools/genres.py`

Must be added to `MCP_Server/tools/__init__.py`:
```python
from . import arrangement, audio_clips, ..., genres, ...  # noqa: F401
```

## 4. Section Filtering Implementation

CONTEXT.md D-01: sections parameter is a list of strings.

The 6 valid section names (from schema.py TypedDicts):
- `instrumentation`
- `harmony`
- `rhythm`
- `arrangement`
- `mixing`
- `production_tips`

Section filtering is NOT in catalog.py — it should be done at the tool layer:
```python
# After getting full blueprint from catalog
if sections:
    filtered = {k: v for k, v in blueprint.items() if k in sections or k in META_KEYS}
    return json.dumps(filtered)
```

Where META_KEYS are always included: `id`, `name`, `bpm_range` (so Claude always knows what genre it's looking at even with filtered sections).

## 5. Tool Signatures

### list_genre_blueprints
```python
@mcp.tool()
def list_genre_blueprints(ctx: Context) -> str:
    """List all available genre blueprints with metadata."""
```
No parameters needed — wraps `list_genres()`.

### get_genre_blueprint
```python
@mcp.tool()
def get_genre_blueprint(
    ctx: Context,
    genre: str,
    subgenre: str | None = None,
    sections: list[str] | None = None,
) -> str:
    """Get a genre blueprint with optional section filtering."""
```

Flow:
1. Try `get_blueprint(genre, subgenre)`
2. If None → try `resolve_alias(genre)` for better error message
3. If still None → `format_error("Genre not found", ...)`
4. If sections → filter to requested sections + metadata keys
5. Return `json.dumps(result)`

## 6. Error Scenarios

| Scenario | Response |
|----------|----------|
| Genre not found | format_error("Genre not found", detail="'{genre}' not available", suggestion="Use list_genre_blueprints to see available genres") |
| Invalid section name | Silently ignore invalid sections, return valid ones. If ALL sections invalid, return just metadata + suggestion |
| No genres registered | list_genre_blueprints returns empty list `[]` |

## 7. Testing Strategy

### Unit Tests (extend tests/test_genres.py or new test_genre_tools.py)
1. list_genre_blueprints returns valid JSON with expected fields
2. get_genre_blueprint returns full blueprint
3. get_genre_blueprint with sections filter returns only requested sections + metadata
4. get_genre_blueprint with subgenre returns merged data
5. get_genre_blueprint with alias resolves correctly
6. get_genre_blueprint with invalid genre returns format_error

### Integration Tests (if mcp_server fixture available)
- Tool registration: tools appear in MCP tool list
- End-to-end: call tool, verify JSON response

Note: MCP integration tests require `mcp` module which may not be available in all environments. Pure unit tests (calling the tool functions directly) are more reliable.

## 8. Validation Architecture

**Coverage mapping:**
| Requirement | Test Approach |
|-------------|---------------|
| TOOL-01 | Verify list_genre_blueprints returns genres with name, BPM range, subgenres |
| TOOL-02 | Verify get_genre_blueprint with genre, sections filter, and subgenre params |

## 9. Risk Assessment

### Low Risk
- All catalog logic already tested in Phase 20
- Tool wrapper is thin — minimal new logic
- Section filtering is simple dict comprehension

### No Risk
- No Ableton Remote Script changes
- No new external dependencies
- No existing code modified (only new tools/genres.py + __init__.py import)

## RESEARCH COMPLETE
