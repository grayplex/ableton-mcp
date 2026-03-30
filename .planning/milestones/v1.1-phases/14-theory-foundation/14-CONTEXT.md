# Phase 14: Theory Foundation - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate music21 as a dependency, establish the `MCP_Server/theory/` library package with core pitch mapping utilities, register a `tools/theory.py` tool module with FastMCP, and deliver working MIDI-to-note and note-to-MIDI MCP tools with test infrastructure. This is the foundation for all subsequent theory phases (15-19).

</domain>

<decisions>
## Implementation Decisions

### Module Structure
- **D-01:** `MCP_Server/theory/` package organized as one file per domain — `pitch.py` (Phase 14), then `chords.py`, `scales.py`, `progressions.py`, `analysis.py`, `voicing.py` in subsequent phases
- **D-02:** Single `MCP_Server/tools/theory.py` file for all theory MCP tool definitions (matching flat `tools/` convention)
- **D-03:** Barrel exports from `MCP_Server/theory/__init__.py` — tools import via `from MCP_Server.theory import midi_to_note`

### Output Format
- **D-04:** All theory tool output includes both MIDI numbers and note names (e.g., `{"midi": 60, "name": "C4"}`)
- **D-05:** Compound results use rich note objects, not flat parallel arrays (e.g., `"notes": [{"midi": 60, "name": "C4"}, ...]`)
- **D-06:** Tools return `json.dumps()` strings, matching existing tool pattern throughout the codebase
- **D-07:** Success returns data directly; errors use `format_error()` — no status envelope wrapper

### Foundation Scope
- **D-08:** Phase 14 ships working MCP tools (`midi_to_note`, `note_to_midi`) — not just library scaffolding. Proves the full pipeline: music21 → theory lib → tool → Claude
- **D-09:** Tests are standalone — no `mock_connection` needed since theory tools are pure computation (no Ableton connection)
- **D-10:** Both unit tests (theory/ library functions) and integration tests (MCP tool calls via `mcp_server` fixture)

### Enharmonic Naming
- **D-11:** Key-aware enharmonic spelling via music21 default — C# in A major, Db in Ab major
- **D-12:** When no key context is provided, default to sharps (e.g., `midi_to_note(61)` → "C#4")

### Dependency & Import
- **D-13:** music21 is a required dependency in `pyproject.toml` `[project.dependencies]`, not an optional extra
- **D-14:** Lazy import — music21 imported inside theory/ functions on first call, not at module level. Keeps server startup fast when theory tools aren't used

### Tool Naming
- **D-15:** No prefix on theory tool names — `midi_to_note`, `build_chord`, not `theory_midi_to_note`. Claude distinguishes by context

### MIDI Validation
- **D-16:** Validate MIDI values (0-127) at the MCP tool boundary layer. Internal theory/ library functions accept any range for flexibility

### Octave Convention
- **D-17:** C4 = MIDI 60 (scientific pitch notation, music21 default). Not Ableton's C3 = 60 display convention

### Claude's Discretion
- Theory/ library internal API design (function signatures, helper utilities)
- music21 object conversion patterns (how to wrap/unwrap music21 Pitch, Chord, etc.)
- Test organization within test file(s)
- `pyproject.toml` packaging updates (adding `MCP_Server.theory` to `[tool.setuptools]`)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Codebase Patterns
- `MCP_Server/tools/notes.py` — Reference tool module pattern (imports, @mcp.tool() decoration, json.dumps return, format_error usage)
- `MCP_Server/tools/__init__.py` — Tool registration via import (will need theory.py added)
- `MCP_Server/connection.py` — `format_error()` utility for error responses
- `MCP_Server/server.py` — FastMCP server setup, `mcp` instance creation
- `tests/conftest.py` — Test fixture pattern (mcp_server fixture for tool integration tests)
- `pyproject.toml` — Dependency and packaging configuration

### Project Planning
- `.planning/REQUIREMENTS.md` — THRY-01, THRY-02, THRY-03 acceptance criteria
- `.planning/ROADMAP.md` — Phase 14 deliverables and Phase 15-19 structure (module layout affects all)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/tools/` — 14 existing tool modules, all following same pattern: import mcp from server, @mcp.tool() decorator, json.dumps() return, format_error() for errors
- `MCP_Server/connection.py:format_error()` — Standard error formatting utility
- `tests/conftest.py:mcp_server` fixture — Returns live FastMCP server for in-memory tool testing

### Established Patterns
- Tool modules import `mcp` from `MCP_Server.server` and register via `@mcp.tool()` decorator
- Tool registration happens by importing module in `tools/__init__.py`
- All tools take `ctx: Context` as first parameter
- All tools return `str` (json.dumps on success, format_error on failure)
- Tests use `mcp_server.call_tool()` for integration testing

### Integration Points
- `pyproject.toml` — Add music21 to dependencies, add MCP_Server.theory to packages
- `MCP_Server/tools/__init__.py` — Add theory import for tool registration
- `tests/` — New test_theory.py with standalone tests (no mock_connection patching needed)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 14-theory-foundation*
*Context gathered: 2026-03-24*
