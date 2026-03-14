# Deferred Items - Phase 04

## Pre-existing Issues

### MCP SDK 1.26.0 call_tool return type change
- **Discovered during:** Plan 04-02, Task 2
- **Issue:** `mcp.server.fastmcp.FastMCP.call_tool()` now returns a tuple `(content_list, metadata)` instead of just `content_list`. All existing smoke tests across all domains (tracks, transport, browser, clips, devices, session) use `result[0].text` which should be `result[0][0].text`.
- **Affected files:** tests/test_tracks.py, tests/test_transport.py, tests/test_browser.py, tests/test_clips.py, tests/test_devices.py, tests/test_session.py
- **Scope:** 26 pre-existing test failures across 6 test files
- **Fix:** Replace `result[0].text` with `result[0][0].text` in all affected test files (simple find-and-replace)
- **Note:** test_mixer.py was written with the correct pattern from the start
