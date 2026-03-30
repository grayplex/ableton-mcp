---
phase: 27-locator-and-scaffolding-commands
verified: 2026-03-28T06:00:00Z
status: human_needed
score: 9/9 must-haves verified
re_verification: false
human_verification:
  - test: "Open Ableton Live with a blank 4/4 session. Run generate_production_plan (genre=house, key=Am, bpm=125), then pass the output to scaffold_arrangement."
    expected: "Named locators appear in Arrangement view at bar positions matching bar_start values. Named MIDI tracks appear with role names (kick, bass, lead, etc.) and dedup suffixes where the same role spans multiple sections."
    why_human: "Ableton Live Object Model (LOM) socket dispatch cannot be exercised in unit tests — requires a live Ableton process."
  - test: "After scaffolding, call get_arrangement_overview."
    expected: "JSON returns locators list with 1-indexed bar values matching what is visible in Ableton, a flat tracks list matching the visible track names, and a non-zero session_length_bars."
    why_human: "Round-trip verification of beat-to-bar conversion against the live LOM requires a running Ableton session."
---

# Phase 27: Locator and Scaffolding Commands Verification Report

**Phase Goal:** Implement scaffold_arrangement and get_arrangement_overview MCP tools so an AI can write a production plan into Ableton Arrangement view as locators and MIDI tracks, and read back the arrangement state.
**Verified:** 2026-03-28
**Status:** human_needed (all automated checks pass; live Ableton verification pending)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | scaffold_arrangement MCP tool accepts a plan dict and creates locators + MIDI tracks in Ableton | VERIFIED | `@mcp.tool() def scaffold_arrangement` in MCP_Server/tools/scaffold.py:88; test_creates_locators_and_tracks passes |
| 2 | Locators are placed at correct beat positions derived from bar_start and session time signature | VERIFIED | `_bar_to_beat` called with `section["bar_start"]` and `beats_per_bar` from `get_session_info`; test_bar_to_beat_4_4 and test_bar_to_beat_3_4 pass |
| 3 | Track names follow role deduplication: "lead", "lead 2", "lead 3" for repeated roles | VERIFIED | `_deduplicate_roles` produces suffixed names; TestRoleDeduplication (4 tests) all pass |
| 4 | Playhead position is saved before scaffold and restored after | VERIFIED | `original_position = self._song.current_song_time` saved; restored at line 45 of handlers/scaffold.py |
| 5 | Existing cue point at target position is detected and skipped (toggle safety) | VERIFIED | `abs(cp.time - beat_position) < 0.001` check at line 29; renames instead of toggling; `existed: True` returned |
| 6 | get_arrangement_overview returns all locators with 1-indexed bar positions | VERIFIED | `_beat_to_bar` applied to each cue point; test_returns_locators_with_bar_positions: beat 64.0 -> bar 17 |
| 7 | get_arrangement_overview returns a flat list of track name strings | VERIFIED | `state["tracks"]` passed through directly as list of strings; test_returns_flat_track_names passes |
| 8 | get_arrangement_overview returns session_length_bars derived from song.song_length / beats_per_bar | VERIFIED | `int(state["song_length"] / beats_per_bar)` at line 182 of tools/scaffold.py; test_session_length_bars: 256/4=64 |
| 9 | Bar positions in overview match the bar_start convention from Phase 26 (1-indexed) | VERIFIED | `_beat_to_bar` uses `math.floor(beat / bpb) + 1`; beat 0.0 -> bar 1; test_beat_to_bar_4_4 confirms |

**Score:** 9/9 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `AbletonMCP_Remote_Script/handlers/scaffold.py` | create_locator_at and scaffold_tracks Remote Script handlers | VERIFIED | 101 lines; `@command("create_locator_at", write=True)`, `@command("scaffold_tracks", write=True)`, `@command("get_arrangement_state")` all present; `class ScaffoldHandler` defined |
| `MCP_Server/tools/scaffold.py` | scaffold_arrangement and get_arrangement_overview MCP tools with helpers | VERIFIED | 195 lines; `@mcp.tool()` decorates both tools; `_deduplicate_roles`, `_bar_to_beat`, `_beat_to_bar` all present |
| `tests/test_scaffold.py` | Unit tests for all scaffold functionality | VERIFIED | 349 lines; `TestRoleDeduplication`, `TestBarToBeat`, `TestScaffoldArrangement`, `TestBarConversions`, `TestArrangementOverview`, `test_scaffold_tools_registered`, `test_overview_tool_registered` all present; 21/21 pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| MCP_Server/tools/scaffold.py | MCP_Server/connection.py | get_ableton_connection + send_command | WIRED | `from MCP_Server.connection import format_error, get_ableton_connection` at line 11; `ableton.send_command(...)` called in both tools |
| MCP_Server/tools/scaffold.py | AbletonMCP_Remote_Script/handlers/scaffold.py | send_command("create_locator_at") | WIRED | `ableton.send_command("create_locator_at", {...})` at line 122; matching `@command("create_locator_at", write=True)` in handler |
| MCP_Server/tools/scaffold.py | AbletonMCP_Remote_Script/handlers/scaffold.py | send_command("scaffold_tracks") | WIRED | `ableton.send_command("scaffold_tracks", {...})` at line 137; matching `@command("scaffold_tracks", write=True)` in handler |
| MCP_Server/tools/scaffold.py | AbletonMCP_Remote_Script/handlers/scaffold.py | send_command("get_arrangement_state") | WIRED | `ableton.send_command("get_arrangement_state")` at line 167; matching `@command("get_arrangement_state")` in handler |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| MCP_Server/tools/scaffold.py scaffold_arrangement | locators_created, tracks_result | send_command("create_locator_at") and send_command("scaffold_tracks") routed to LOM handlers | Yes — handlers read/write self._song.cue_points and self._song.tracks | FLOWING (in tests via mock; live path via socket dispatch to LOM) |
| MCP_Server/tools/scaffold.py get_arrangement_overview | state (cue_points, tracks, song_length) | send_command("get_arrangement_state") routed to LOM handler | Yes — handler iterates self._song.cue_points, self._song.tracks, reads self._song.song_length | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| scaffold_arrangement tool registered | python -m pytest tests/test_scaffold.py::test_scaffold_tools_registered -v | PASSED | PASS |
| get_arrangement_overview tool registered | python -m pytest tests/test_scaffold.py::test_overview_tool_registered -v | PASSED | PASS |
| All 21 scaffold tests | python -m pytest tests/test_scaffold.py -x -v | 21 passed | PASS |
| Live Ableton round-trip | Requires running Ableton process | Cannot test without server | SKIP — route to human verification |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCAF-01 | 27-01-PLAN.md | User can scaffold a full arrangement into Ableton — creates all named locators and named tracks in Arrangement view from a production plan in one atomic operation | SATISFIED | scaffold_arrangement tool wired end-to-end; creates locators via create_locator_at and tracks via scaffold_tracks in sequence; 5 integration tests pass |
| SCAF-02 | 27-02-PLAN.md | User can retrieve an arrangement overview from the active Ableton session — returns locators (with positions), track names, and session length for mid-session re-orientation | SATISFIED | get_arrangement_overview tool reads get_arrangement_state and returns {locators, tracks, session_length_bars}; 4 integration tests + 1 registration test pass |

No orphaned requirements detected. Both SCAF IDs are claimed by plans and verified in code.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No TODOs, FIXMEs, placeholder returns, or empty handler stubs found in phase files. Both tools return real JSON data. Error paths use `format_error` consistently rather than returning empty structures.

---

## Full Suite Note

Running `python -m pytest tests/ -x` reports 281 failures. These failures are **pre-existing** and not introduced by Phase 27. The root cause is `test_plan_tools.py` using module-level `sys.modules` mocking that poisons the `mcp_server` fixture for all subsequent test files when collected together. Running individual test files in isolation all pass. This was documented in the Phase 27 Plan 01 SUMMARY as a known pre-existing issue.

Evidence: `python -m pytest tests/test_transport.py` alone = 23 passed, 0 failed. `python -m pytest tests/test_scaffold.py` alone = 21 passed, 0 failed.

---

## Human Verification Required

### 1. scaffold_arrangement live round-trip

**Test:** Open Ableton Live with a blank session (4/4 time, any BPM). In Claude, call `generate_production_plan` with genre="house", key="Am", bpm=125. Pass the output dict to `scaffold_arrangement`.
**Expected:** Named locators appear in Arrangement view at the top, positioned at bar numbers matching the `bar_start` values. Named MIDI tracks appear below with role names. Roles that appear in multiple sections have numbered suffixes ("kick", "kick 2", etc.).
**Why human:** The socket dispatch to Ableton's LOM cannot be exercised in unit tests — requires a live Ableton process responding on the MCP socket.

### 2. get_arrangement_overview live readback

**Test:** After completing the scaffold above, call `get_arrangement_overview` with no arguments.
**Expected:** Returns JSON with `locators` list (each entry has `name` and `bar` matching what is visible in Ableton), `tracks` list (flat strings matching track names in Ableton), and `session_length_bars` greater than 0.
**Why human:** Verifying that beat-to-bar conversion matches the positions Ableton actually stored requires comparing the MCP output against the Ableton UI.

---

## Gaps Summary

No automated gaps found. All 9 truths verified, all 3 artifacts exist and are wired, all key links confirmed. Both SCAF requirements satisfied. The two human verification items are functional completeness checks that require a live Ableton session — they are non-blocking for code quality purposes.

---

_Verified: 2026-03-28_
_Verifier: Claude (gsd-verifier)_
