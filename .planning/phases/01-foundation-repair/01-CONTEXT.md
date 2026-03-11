# Phase 1: Foundation Repair - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the broken correctness issues that make the current server unreliable: instrument loading race condition, Python 2 dead code, bare exception swallowing, thread-unsafe global connection, and O(n²) JSON parsing. After this phase, the existing ~15 tools work reliably — no silent failures, no race conditions, no Python 2 remnants.

</domain>

<decisions>
## Implementation Decisions

### Error Reporting
- Clean message first, technical detail in a debug section below — gives AI both actionable info and diagnostic context
- Include suggested fixes in error messages (e.g., "Connection lost. Ensure Ableton is running and Remote Script is loaded.")
- Normalize Ableton error messages into consistent format while preserving the original message
- Response metadata format: Claude's discretion per tool

### Loading Verification
- Claude picks the most reliable verification approach (device count, name match, or both)
- One automatic retry on load failure before reporting error
- Load results must report what device was actually loaded: "Loaded 'Analog' on track 3 (device chain: Analog, Reverb)"
- Fix the 'nstruments' typo AND add basic browser path caching to prevent UI freezes on large libraries

### Connection Behavior
- Claude picks initial connection strategy (fail fast vs retry)
- Auto-reconnect silently on next tool call when connection drops mid-session — seamless for AI
- Add a health-check/ping tool in Phase 1 that reports connection state, Ableton version, and basic session info

### Existing Tools Scope
- Claude picks whether to keep load_instrument_or_effect and load_drum_kit separate or consolidate
- Keep snake_case naming convention for all tools
- Minimal browser tool fix in Phase 1 — fix typo and loading only, defer browser API redesign to Phase 7
- Health-check tool belongs in Phase 1 as a foundation concern

### Claude's Discretion
- Response metadata format (structured JSON vs simple strings) — pick what works best per tool
- Instrument load verification strategy (device count vs name match vs both)
- Initial connection attempt strategy (fail fast vs retry with delay)
- Whether to consolidate load_instrument_or_effect + load_drum_kit into one tool or keep separate
- Ableton error normalization approach (passthrough with wrapper vs full normalization)

</decisions>

<specifics>
## Specific Ideas

- User is "hands-off" on the Remote Script side — they want it to work but don't want to think about the internals
- Error messages should be useful to an AI assistant, not a human — technical detail is valuable
- The health-check tool should give the AI enough context to know if it can proceed or needs to tell the user something

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AbletonConnection` dataclass: solid foundation, needs thread lock added and socket framing upgraded
- `server_lifespan` async context manager: connection lifecycle management pattern is correct
- `get_ableton_connection()` singleton pattern: right idea, needs Lock protection
- `_process_command()` in Remote Script: has the command routing structure, needs dict-based dispatch (Phase 2)

### Established Patterns
- `@mcp.tool()` decorator pattern for all tools — keep this
- `send_command(type, params)` JSON protocol — keep the shape, upgrade the framing
- `schedule_message()` for main-thread dispatch in Remote Script — keep this, it's the correct Ableton pattern
- `self.log_message()` for Remote Script logging — keep using Ableton's built-in logger

### Integration Points
- `MCP_Server/server.py`: All 15 existing tools live here — will be modified in place
- `AbletonMCP_Remote_Script/__init__.py`: Single 800+ line file — will be cleaned but not split (splitting is Phase 2)
- `pyproject.toml`: Package config — may need updates for Python 3.11 target
- Socket protocol on port 9877: Both sides must upgrade to length-prefix framing simultaneously

### Known Bugs to Fix
- Line 675 in Remote Script: `'nstruments'` typo breaks path-based browser navigation for instruments
- Lines 59, 194, 206, 820 in Remote Script: bare `except: pass` blocks swallow all errors
- Line 211 in server.py: bare `except: pass` in connection validation
- Lines 12-15 in Remote Script: Python 2 Queue import hack
- Line 1 in Remote Script: `from __future__ import` dead code
- `receive_full_response()`: O(n²) JSON parsing on every chunk

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-repair*
*Context gathered: 2026-03-10*
