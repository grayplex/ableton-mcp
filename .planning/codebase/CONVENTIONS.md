# Coding Conventions

**Analysis Date:** 2026-04-02

## Naming Patterns

**Files:**
- Snake_case module names: `agenda.py`, `next_actions.py`, `mix_balance.py`, `gain_targets.py`
- Tool modules mirror domain nouns exactly: `tracks.py`, `transport.py`, `theory.py`, `orchestration.py`
- Schema files always named `schema.py` within their package (e.g., `MCP_Server/genres/schema.py`, `MCP_Server/evaluation/schema.py`)
- Catalog/registry data in `catalog.py` files: `MCP_Server/genres/catalog.py`, `MCP_Server/mixing/catalog.py`, `MCP_Server/devices/catalog.py`

**Functions:**
- Public API: snake_case — `get_agenda`, `get_execution_plan`, `get_checkpoint`, `midi_to_note`
- Private helpers: leading underscore — `_make_conn`, `_has_name_match`, `_timeout_for`, `_check_bpm_range`, `_force_sharp`, `_parse_note_name`
- Tool registration functions match the MCP tool name exactly: `def get_track_info` registers as `"get_track_info"` via `@mcp.tool()`

**Variables:**
- snake_case throughout
- Module-level public constants: UPPER_SNAKE_CASE — `AGENDA_CATALOG`, `RHYTHM_CATALOG`, `SCALE_CATALOG`, `GAIN_TARGETS`, `ROLES`
- Module-level private constants: leading underscore + UPPER_SNAKE_CASE — `_WRITE_COMMANDS`, `_BROWSER_COMMANDS`, `_PHASE_GOALS`, `_DRUM_NAMES`, `_NOTE_RE`

**Types / Classes:**
- TypedDict names: PascalCase — `ProductionAgenda`, `ProductionPhase`, `ExecutionStep`, `GenreBlueprint`, `EvaluationIssue`, `DimensionScore`
- Dataclass names: PascalCase — `AbletonConnection` (`MCP_Server/connection.py`)
- Test classes: `Test` prefix + PascalCase subject — `TestProductionAgendaCatalog`, `TestCheckpoint`, `TestProtocolRoundtrip`, `TestRecipeParameterNames`

## TypedDict Pattern

All structured data objects are `TypedDict` — not dataclasses, Pydantic models, or plain dicts.
TypedDicts are JSON-serializable without `.asdict()` and are defined in a dedicated `schema.py`
file within each sub-package. Inline comments annotate field semantics:

```python
# MCP_Server/orchestration/schema.py
class ExecutionStep(TypedDict):
    step_number: int
    description: str         # plain English: what this step does
    tool_name: str           # exact registered MCP tool name
    suggested_args: dict     # {param: value}; session-state values use "<sentinel>" strings
    depends_on_step: Optional[int]
    phase: str               # phase_id this step belongs to
```

Schema files:
- `MCP_Server/genres/schema.py` — `GenreBlueprint`, `InstrumentationSection`, `HarmonySection`, `ArrangementEntry`
- `MCP_Server/evaluation/schema.py` — `EvaluationIssue`, `DimensionScore`, `SessionScore`
- `MCP_Server/orchestration/schema.py` — `ProductionAgenda`, `ProductionPhase`, `PhaseChecklist`, `ExecutionStep`, `SessionStats`
- `MCP_Server/refinement/schema.py` — `SectionState`, `ClipSummary`, `TrackStateEntry`
- `MCP_Server/prompt/schema.py` — `ProductionBrief`

`total=False` is used for optional fields in TypedDicts (e.g., `ArrangementEntry` splits into
`_ArrangementEntryRequired` for required fields and `ArrangementEntry` with `total=False` for optional):

```python
class ArrangementEntry(_ArrangementEntryRequired, total=False):
    energy: int
    roles: List[str]
    transition_in: str
```

## Tool Registration Pattern (`@mcp.tool()`)

Every MCP-exposed tool lives in `MCP_Server/tools/` and follows this exact structure:

```python
# MCP_Server/tools/transport.py
from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp

@mcp.tool()
def set_tempo(ctx: Context, tempo: float) -> str:
    """Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM (valid range: 20-999)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_tempo", {"tempo": tempo})
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error(
            "Failed to set tempo", detail=str(e), suggestion="Tempo must be between 20 and 999 BPM"
        )
```

Key rules:
- First parameter is always `ctx: Context` (imported from `mcp.server.fastmcp`)
- Return type is always `str` (JSON string)
- Every tool returns `json.dumps(result)` on success, `format_error(...)` on failure
- `indent=2` is standard for all tool returns
- Tool module file imports `from MCP_Server.server import mcp` to access the `@mcp.tool()` decorator

## Optional Parameter Pattern

When tools accept optional parameters that should be omitted (not sent as `None`) from the
wire command, build the params dict conditionally before calling `send_command`:

```python
# MCP_Server/tools/transport.py, lines 127-136
params: dict = {}
if enabled is not None:
    params["enabled"] = enabled
if start is not None:
    params["start"] = start
if length is not None:
    params["length"] = length
result = ableton.send_command("set_loop_region", params)
```

This pattern appears in `set_loop_region`, `set_scale`, `set_session_record`, `jump_to_cue`, and
`set_loop_region`. All optional tool parameters use `type | None = None` union syntax (Python 3.10+).

## Import Alias Pattern (`_build_chord = build_chord`)

Library functions imported into tool modules use a leading-underscore alias to signal
"this is the pure implementation; the decorated function is the public tool":

```python
# MCP_Server/tools/theory.py
from MCP_Server.theory import build_chord as _build_chord
from MCP_Server.theory import get_scale_pitches as _get_scale_pitches
from MCP_Server.theory import voice_lead_chords as _voice_lead_chords
```

Tool functions call `_build_chord(...)` internally, preventing shadowing of the public tool
function name at module level. This pattern appears throughout `MCP_Server/tools/theory.py`
for all ~20 theory functions and similarly in `MCP_Server/tools/analysis.py` for helper
functions like `_meter_to_db` and `_infer_role`.

## RS Command Pattern (`send_command`)

Ableton-connected tools follow a uniform three-line body before error handling:

```python
ableton = get_ableton_connection()
result = ableton.send_command("command_name", {"param": value})
return json.dumps(result, indent=2)
```

`send_command` always receives a string command type and a dict of params. For no-param
commands, either omit the second argument or pass no params:

```python
result = ableton.send_command("start_playback")    # no params at all
result = ableton.send_command("create_return_track", {})  # explicit empty dict
```

The command type string is the authoritative identifier — it must match exactly what the
remote script handles and must be listed in `_WRITE_COMMANDS` or `_BROWSER_COMMANDS` in
`MCP_Server/connection.py` if it is a write or browser operation; otherwise it is treated as
a read with `TIMEOUT_READ = 10.0s`.

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

The `format_error` function (`MCP_Server/connection.py` line 192) produces:
```
Error: Failed to build chord
Suggestion: Check root and quality parameters
Debug: <exception string>
```

Orchestration and library modules that do not reach the connection layer return plain dicts
with an `"error"` key instead:

```python
return {"error": f"Unknown genre: {genre_id}"}
```

This two-tier convention is consistent:
- `format_error` string — tool layer (`MCP_Server/tools/`)
- `{"error": "..."}` dict — pure library layer (`MCP_Server/orchestration/`, `MCP_Server/theory/`, etc.)

## Error Handling Strategy

- **Tool layer** (`MCP_Server/tools/`): catch-all `except Exception as e` wrapping the entire
  tool body → `format_error`
- **Library layer**: raise `ValueError` for invalid input (e.g., unknown scale name, bad chord
  quality); return `{"error": "..."}` dict for recoverable domain failures (unknown genre, invalid
  phase/section combination)
- **Connection layer** (`AbletonConnection.send_command`): separate `except` clauses for
  `TimeoutError`, `ConnectionError/BrokenPipeError/ConnectionResetError`, `json.JSONDecodeError`,
  and `Exception` — each logs the error and resets `self.sock = None` before re-raising
- No silent swallowing; every `except` block returns an error value or re-raises

## Module-Level State

Module-level variables are used sparingly for stateful tracking:

```python
# MCP_Server/tools/transport.py, line 11
_consecutive_undo_count = 0
```

Such variables are always prefixed with `_` and documented with a comment explaining their
purpose. Test files that exercise stateful tools reset the state explicitly in the test body:

```python
# tests/test_transport.py, line 149
transport_module._consecutive_undo_count = 0
```

The connection module uses module-level `_ableton_connection` and `_connection_lock` (a
`threading.Lock`) for singleton connection management in `MCP_Server/connection.py` lines 306-307.

## Import Organization

**Order (enforced by ruff/isort):**
1. Standard library
2. Third-party (`mcp`, `music21`, `pytest`)
3. First-party (`MCP_Server.*`, `AbletonMCP_Remote_Script.*`)

**Path aliases:** None — all imports use full dotted paths from package root.

**`__init__.py` re-exports:** Sub-packages expose their public API via `__init__.py`.
F401 (unused import) is suppressed in `__init__.py` files via ruff config.

**Tool package bootstrap:** `MCP_Server/tools/__init__.py` imports all tool modules in a
single line to trigger `@mcp.tool()` registration:

```python
from . import analysis, arrangement, audio_clips, automation, browser, catalog, clips, \
    devices, evaluation, execution, genres, grooves, intelligence, mixer, mixing, notes, \
    orchestration, plans, prompt, refinement, routing, scaffold, scenes, session, sounds, \
    theory, tracks, transport  # noqa: F401
```

`MCP_Server/server.py` then does `import MCP_Server.tools  # noqa: E402, F401` after the
`mcp` instance is created (line 43). New tool modules must be added to both this import and
`_GAC_PATCH_TARGETS` in `tests/conftest.py`.

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
    "harmony": {"scales": [...], "chord_types": [...], "common_progressions": [...]},
    "rhythm": {"time_signature": "4/4", ...},
    "arrangement": {"sections": [{"name": "intro", "bars": 16, "energy": 2, "roles": [...]}]},
    "mixing": {...},
    "production_tips": {"techniques": [...], "pitfalls": [...]},
}
SUBGENRES = [...]
```

Validation against `GenreBlueprint` schema runs at catalog import time via `validate_blueprint()`
in `MCP_Server/genres/schema.py`. Callers catch `ValueError` per genre (fail-per-genre, not
fail-per-server).

## Docstring Style

**Modules:** Single-sentence summary + brief elaboration listing key public names.

```python
"""Evaluation schema: issue types, dimension scores, and session score model.

All types are TypedDicts for JSON-serializable construction without .asdict().
grade_from_score() is a module-level helper used by all evaluators.
"""
```

**Tools:** Summary sentence. "Parameters:" block with `- name: Description` bullets.
Include valid ranges inline. Do not add a "Returns:" section — return type is always `str`.

```python
"""Set the tempo of the Ableton session.

Parameters:
- tempo: The new tempo in BPM (valid range: 20-999)
"""
```

**TypedDict fields:** Inline `# comment` on same line as annotation (not separate docstring).

**Short helpers:** One-sentence docstring only.

**Test functions:** One-sentence docstring stating what the test asserts (imperative voice):
```python
def test_set_tempo_calls_send_command(mcp_server, mock_connection):
    """set_tempo invokes send_command with correct tempo value."""
```

## Linting and Formatting

**Tool:** `ruff` (line-length 100, target Python 3.11)
**Rules enforced:** E, F, W (pycodestyle/pyflakes), I (isort), B (bugbear), UP (pyupgrade)
**Ignores:**
- `E501` — line-too-long handled by line-length setting
- `B905` — zip() without strict= not needed
- `F401` — in `__init__.py` files (re-exports are intentional)
- `B011` — `assert False` OK in tests
- `UP035` — deprecated imports allowed in `AbletonMCP_Remote_Script/` (legacy _Framework patterns)

**Config:** `pyproject.toml` `[tool.ruff]` and `[tool.ruff.lint]` sections
Run linting: `ruff check .`

## File Organization Rules

- One domain per tool file: `MCP_Server/tools/theory.py` owns all theory tools; `tracks.py`
  owns all track tools
- Pure logic lives in sub-packages (`MCP_Server/theory/`, `MCP_Server/orchestration/`);
  `MCP_Server/tools/` contains only thin `@mcp.tool()` wrappers
- Schema TypedDicts always in `schema.py` within the same sub-package, never inlined in tool files
- Catalog/registry data in `catalog.py` files — never in schema or tool files
- Module-level private dicts/frozensets for lookup tables (e.g., `_WRITE_COMMANDS`,
  `_BROWSER_COMMANDS`, `_PHASE_GOALS`) rather than inline conditionals in function bodies
- `MCP_Server/protocol.py` is the single source of truth for the socket framing protocol —
  both the MCP server and the Ableton remote script must use this exact implementation

---

*Convention analysis: 2026-04-02*
