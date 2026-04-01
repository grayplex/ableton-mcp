# Coding Conventions

**Analysis Date:** 2026-04-01

## Naming Patterns

**Files:**
- Snake_case modules: `agenda.py`, `next_actions.py`, `mix_balance.py`
- Tool modules mirror domain nouns: `tracks.py`, `theory.py`, `orchestration.py`
- Schema files always named `schema.py` within their package

**Functions:**
- Public API: snake_case — `get_agenda`, `get_execution_plan`, `get_checkpoint`
- Private helpers: leading underscore — `_make_conn`, `_has_name_match`, `_timeout_for`, `_check_bpm_range`
- Tool registration functions match the MCP tool name exactly: `def get_track_info` registers as `"get_track_info"`

**Variables:**
- snake_case throughout
- Module-level constants: UPPER_SNAKE_CASE — `AGENDA_CATALOG`, `RHYTHM_CATALOG`, `_BROWSER_COMMANDS`
- Private module constants: leading underscore + UPPER_SNAKE_CASE — `_WRITE_COMMANDS`, `_PHASE_GOALS`, `_DRUM_NAMES`

**Types / Classes:**
- TypedDict names: PascalCase — `ProductionAgenda`, `ProductionPhase`, `ExecutionStep`, `GenreBlueprint`
- Dataclasses: PascalCase — `AbletonConnection`
- Test classes: `Test` prefix + PascalCase subject — `TestProductionAgendaCatalog`, `TestCheckpoint`

## TypedDict Pattern

All structured data objects are `TypedDict` — not dataclasses, Pydantic models, or plain dicts.
TypedDicts are JSON-serializable without `.asdict()` and are defined in a dedicated `schema.py`
file within each sub-package. Inline comments annotate field semantics:

```python
class ExecutionStep(TypedDict):
    step_number: int
    description: str         # plain English: what this step does
    tool_name: str           # exact registered MCP tool name
    suggested_args: dict     # {param: value}; session-state values use "<sentinel>" strings
    depends_on_step: Optional[int]
    phase: str               # phase_id this step belongs to
```

Schema files:
- `MCP_Server/genres/schema.py`
- `MCP_Server/evaluation/schema.py`
- `MCP_Server/orchestration/schema.py`
- `MCP_Server/refinement/schema.py`
- `MCP_Server/prompt/schema.py`

## Tool Registration Pattern (`@mcp.tool()`)

Every MCP-exposed tool lives in `MCP_Server/tools/` and follows this exact structure:

```python
from MCP_Server.server import mcp

@mcp.tool()
def tool_name(ctx: Context, param: type, optional: type = default) -> str:
    """One-sentence summary. Returns description.

    Parameters:
    - param: Description
    - optional: Description (default X)
    """
    try:
        result = _library_function(param, optional)
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to do thing",
            detail=str(e),
            suggestion="What to check",
        )
```

Key rules:
- First parameter is always `ctx: Context` (imported from `mcp.server.fastmcp`)
- Return type is always `str` (JSON string)
- Every tool returns `json.dumps(result)` on success, `format_error(...)` on failure
- `indent=2` used for reference data tools (theory, analysis); omitted for orchestration tools that prioritise token economy

## Import Alias Pattern (`_build_chord = build_chord`)

Library functions imported into tool modules use a leading-underscore alias to signal "this is the pure implementation; the decorated function is the public tool":

```python
from MCP_Server.theory import build_chord as _build_chord
from MCP_Server.theory import get_scale_pitches as _get_scale_pitches
from MCP_Server.theory import voice_lead_chords as _voice_lead_chords
```

Then tool functions call `_build_chord(...)` internally. This pattern appears throughout
`MCP_Server/tools/theory.py` for all ~20 theory functions. The `_` prefix prevents shadowing
the public tool function name at the module level.

## RS Command Pattern (`send_command`)

Ableton-connected tools follow a uniform three-line body before error handling:

```python
ableton = get_ableton_connection()
result = ableton.send_command("command_name", {"param": value})
return json.dumps(result, indent=2)
```

`send_command` always receives a string command type and a dict of params. The return value
is the `result` key from the wire protocol (already a dict). See `MCP_Server/connection.py`
for the full list of recognised read vs. write vs. browser commands.

## `format_error` Return Pattern

All error returns at the tool boundary use `MCP_Server.connection.format_error`, never raw
strings or `json.dumps({"error": ...})`:

```python
return format_error(
    "Failed to build chord",           # message: AI-readable summary
    detail=str(e),                     # debug: exception string
    suggestion="Check root and quality parameters",  # suggestion: what to fix
)
```

Orchestration and library modules that don't reach the connection layer return plain dicts
with an `"error"` key instead:

```python
return {"error": f"Unknown genre: {genre_id}"}
```

This two-tier convention is consistent:
- `format_error` string — tool layer (`MCP_Server/tools/`)
- `{"error": "..."}` dict — pure library layer (`MCP_Server/orchestration/`, `MCP_Server/theory/`, etc.)

## Error Handling Strategy

- **Tool layer** (`MCP_Server/tools/`): catch-all `except Exception as e` wrapping the entire tool body → `format_error`
- **Library layer**: raise `ValueError` for invalid input; return `{"error": "..."}` dict for recoverable domain failures (unknown genre, invalid phase/section combination)
- **Specific exception handling**: `ValueError` is caught separately before the catch-all where the distinction matters — e.g., `get_scale_pitches` distinguishes "unknown scale name" (ValueError) from other failures
- No silent swallowing; every `except` block returns an error value or re-raises

## Import Organization

**Order (enforced by ruff/isort):**
1. Standard library
2. Third-party (`mcp`, `music21`, `pytest`)
3. First-party (`MCP_Server.*`, `AbletonMCP_Remote_Script.*`)

**Path aliases:** None — all imports use full dotted paths from package root.

**`__init__.py` re-exports:** Sub-packages expose their public API via `__init__.py`
(e.g., `MCP_Server/theory/__init__.py` re-exports `midi_to_note`, `build_chord`, etc.).
F401 (unused import) is suppressed in `__init__.py` files via ruff config.

**Tool package bootstrap:** `MCP_Server/tools/__init__.py` imports all tool modules in a single
line to trigger `@mcp.tool()` registration:

```python
from . import analysis, arrangement, audio_clips, ..., transport  # noqa: F401
```

`MCP_Server/server.py` then does `import MCP_Server.tools  # noqa: E402, F401` after
the `mcp` instance is created.

## Genre Data Pattern

Genre blueprints are pure Python dicts (not TypedDicts, not classes) stored in module-level
`GENRE` constants. Subgenres live in the same file as their parent genre in a `SUBGENRES` list.
Data-only: no helper functions in genre files.

```python
# MCP_Server/genres/house.py
GENRE = {
    "name": "House",
    "id": "house",
    "bpm_range": [120, 130],
    "aliases": ["house music", "house_music"],
    "instrumentation": {"roles": [...]},
    ...
}
SUBGENRES = [...]
```

Validation against `GenreBlueprint` schema runs at catalog import time via
`validate_blueprint()` in `MCP_Server/genres/schema.py`. Callers catch `ValueError`
per genre (fail-per-genre, not fail-per-server).

## Docstring Style

**Modules:** Single-sentence summary + brief elaboration.

```python
"""Production agenda catalog: genre-specific ordered phase lists.

AGENDA_CATALOG maps genre_id -> list of phase definition dicts.
get_agenda(genre, brief) returns a ProductionAgenda TypedDict.
"""
```

**Tools:** Summary sentence. "Returns" description. "Args:" / "Parameters:" block
with `- name: Description` bullets. Include example values inline.

```python
"""Get an ordered production phase agenda for a genre.

Returns a ProductionAgenda with phases in genre-appropriate order ...

Args:
    genre: Genre id or alias (e.g., "house", "techno", "lo_fi")
    brief: Optional JSON string of a ProductionBrief (from interpret_prompt).

Returns:
    JSON string with ProductionAgenda or {"error": "..."} on unknown genre.
"""
```

**TypedDict fields:** Inline `# comment` on same line as annotation (not separate docstring).

**Short helpers:** One-sentence docstring only.

## Linting and Formatting

**Tool:** `ruff` (line-length 100, target Python 3.11)
**Rules enforced:** E, F, W (pycodestyle/pyflakes), I (isort), B (bugbear), UP (pyupgrade)
**Ignores:** E501 (line-too-long handled by line-length setting), B905 (zip without strict)
**Config:** `pyproject.toml` `[tool.ruff]` and `[tool.ruff.lint]` sections

Run linting: `ruff check .`

## File Organization Rules

- One domain per tool file: `MCP_Server/tools/theory.py` owns all theory tools, `tracks.py` owns all track tools
- Pure logic lives in sub-packages (`MCP_Server/theory/`, `MCP_Server/orchestration/`); `MCP_Server/tools/` only contains thin `@mcp.tool()` wrappers
- Schema TypedDicts always in `schema.py` within the same sub-package, never inlined in tool files
- Catalog/registry data in `catalog.py` files (e.g., `MCP_Server/genres/catalog.py`, `MCP_Server/mixing/catalog.py`, `MCP_Server/devices/catalog.py`)
- Module-level private dicts/frozensets for lookup tables (e.g., `_WRITE_COMMANDS`, `_PHASE_GOALS`) rather than inline conditionals

---

*Convention analysis: 2026-04-01*
