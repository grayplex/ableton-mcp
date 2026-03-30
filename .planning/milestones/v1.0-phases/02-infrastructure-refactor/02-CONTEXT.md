# Phase 2: Infrastructure Refactor - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Reorganize the codebase into domain modules so adding any new MCP tool requires touching exactly one domain module and one handler file. Split the monolithic MCP_Server/server.py (797 lines, 17 tools) and AbletonMCP_Remote_Script/__init__.py (1229 lines, all handlers) into focused domain modules. Configure linting and establish test infrastructure. No new user-facing features — this is pure structural refactoring to support 50+ commands in Phases 3-10.

</domain>

<decisions>
## Implementation Decisions

### Domain module boundaries
- Keep browser and devices as **separate modules** — browser.py handles navigation/search, devices.py handles parameters/chains. Loading bridges both but separation is cleaner.
- Keep transport and scenes as **separate modules** — transport.py (play, stop, tempo, time sig, loop) and scenes.py (create, fire, delete) stay distinct.
- Remote Script splits into: base.py, transport.py, tracks.py, clips.py, notes.py, devices.py, mixer.py, scenes.py, browser.py
- MCP server splits into tools/ domain modules mirroring the same domains

### Command registry pattern
- **Evolve** Phase 1's dict-based `_build_command_table()` into a formal registry with `@command('name')` decorator
- Each domain module decorates its handlers, registry auto-collects them
- This replaces roadmap plan 02-02's "replace if/elif" since Phase 1 already did dict dispatch — the work is now "formalize the registry for scalability"

### Tool naming convention
- **Standardize all tool names** during the split — verb_noun pattern (get_track_info, create_clip, set_tempo, fire_clip, add_notes)
- Rename health-check to snake_case (health_check or get_health)
- This is pre-release so no backward compatibility concerns
- **Polish all tool docstrings** — standardize format: one-line summary + parameter descriptions. Better AI tool selection.

### Linting (ruff)
- **Moderate strictness** — PEP 8 + import ordering + basic type checking
- Line length 100
- Ignore some stylistic rules — practical for project size
- Target Python 3.11 for Remote Script, Python 3.10+ for MCP server

### Testing
- **Smoke tests per domain** — each domain module gets 1-2 smoke tests verifying tools register and respond. ~15-20 tests total.
- **Mock only** — all tests run without Ableton via mocked socket responses. CI-friendly, fast, deterministic. No integration tests in Phase 2.
- Uses FastMCP in-memory client (no socket needed for MCP-side tests)
- **Reorganize Phase 1 tests** into new domain structure (tests/test_tracks.py, tests/test_clips.py, etc.)

### Claude's Discretion
- Whether MCP tools/ module names mirror Remote Script handler names exactly or group differently for AI client perspective
- Exact @command decorator implementation details (class-based registry vs module-level collector)
- Which Phase 1 tests to keep vs rewrite during reorganization
- Specific ruff rule selection within "moderate" guidance

</decisions>

<specifics>
## Specific Ideas

- User is "hands-off on the Remote Script side" — wants it to work without thinking about internals (from Phase 1 context)
- The refactor should make future phases (3-10) feel mechanical: "add handler, add tool, done"
- Error messages designed for AI consumption — technical detail is valuable (from Phase 1 context)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_build_command_table()`: Already builds dict dispatch — evolve into decorator-based registry
- `format_error()`: AI-friendly error formatting helper — keep and share across domain modules
- `send_message()`/`recv_message()`: Length-prefix protocol functions — already standalone, can be imported from protocol module
- `schedule_message()` pattern: Ableton main-thread dispatch — `@main_thread` decorator wraps this
- 5 existing test files: test_connection.py, test_dispatch.py, test_instrument_loading.py, test_protocol.py, test_python3_cleanup.py

### Established Patterns
- `@mcp.tool()` decorator pattern for all MCP tools — keep this, add to domain modules
- `send_command(type, params)` JSON protocol — stable from Phase 1
- `self.log_message()` for Remote Script logging — keep using Ableton's built-in logger
- Tiered timeout constants (TIMEOUT_READ, TIMEOUT_WRITE, TIMEOUT_BROWSER, TIMEOUT_PING) — keep in connection module

### Integration Points
- `MCP_Server/server.py`: 17 tools + AbletonConnection class + lifespan handler → split into tools/ + connection module
- `AbletonMCP_Remote_Script/__init__.py`: AbletonMCP class + all handlers → split into handlers/ package
- `pyproject.toml`: Entry point config — may need update if server.py moves
- `tests/conftest.py`: Test fixtures — update for new module structure

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-infrastructure-refactor*
*Context gathered: 2026-03-13*
