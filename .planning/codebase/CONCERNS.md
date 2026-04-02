# Codebase Concerns

**Analysis Date:** 2026-04-02

---

## Known Limitations

**Prompt parser is English-only:**
- The signal lexicon (`MCP_Server/prompt/lexicon.py:1-13`) covers English keywords only. Non-English prompts pass tokens through as `raw_descriptors` with no signal extraction. This is documented in the file header but there is no translation layer or multilingual fallback.

---

## Technical Debt

**HIST-01 — Phase step-skipping is deferred:**
- When `active_phase_progress > 0.3`, `get_next_actions` should skip already-done steps. This is explicitly commented out: `# Skip steps if phase already started (progress > 0.3) — return all for now (HIST-01 deferred)` (`MCP_Server/orchestration/next_actions.py:197`).
- Impact: Claude receives redundant early steps (e.g., "create track") after a context refresh mid-phase. Wastes tool calls.
- Fix approach: Use `active_phase_progress` to offset the step slice, or check sentinel track names against live `get_all_tracks` output.

**Duplicate framing protocol implementation:**
- The length-prefix framing functions `_recv_exact`, `send_message`, `recv_message` are implemented verbatim in both `MCP_Server/protocol.py:1-39` and `AbletonMCP_Remote_Script/__init__.py:38-68`.
- Impact: Any framing bug or protocol change (e.g., max message size) must be fixed in two places across two separate Python runtimes.

---

## Bugs

**`_LIMITER` constant may not match Ableton's real class name:**
- `_LIMITER = "Limiter2"` in `MCP_Server/orchestration/phase_detection.py:12`. `DEVICE_PATHS` (`AbletonMCP_Remote_Script/handlers/devices.py:25`) keys on `"Limiter"`, and `MCP_Server/devices/catalog.py:1525` has key `"Limiter"`. The actual class name returned by `device.class_name` in Ableton's Python API is the ground truth.
- Impact: If Ableton reports the class as `"Limiter"` (not `"Limiter2"`), master phase detection never passes. The master short-circuit (`checkpoint.py:57`) also checks for `_LIMITER`, so it too would fail. Tests use mocked `class_name: "Limiter2"` so they pass regardless.
- Risk: High — only discoverable by running against real Ableton.
- Fix approach: Load a session with a Limiter on the master track and inspect `device.class_name` via a debug command or Ableton's console.

**Checkpoint cache not invalidated after write operations:**
- `invalidate_checkpoint_cache()` exists (`MCP_Server/orchestration/checkpoint.py:267`) but is never called by any MCP tool after a write operation.
- Impact: `get_checkpoint` returns stale data for up to 30 seconds (`_CACHE_TTL = 30.0`) after any mutation. Claude may re-attempt steps it has already completed.
- Fix approach: Call `invalidate_checkpoint_cache()` in `MCP_Server/tools/scaffold.py`, `tracks.py`, `clips.py`, and `devices.py` after write operations, or reduce `_CACHE_TTL` to 5 seconds.

**`_step()` drops the `phase` key from ExecutionStep output:**
- The `_step` factory in `MCP_Server/orchestration/execution.py:188-200` now includes `phase` in the output dict (fixed in quick task 260401-pp9). Confirmed: line 195 sets `"phase": phase`. No remaining bug here.

**`neo_soul_rnb` drum pattern used to fall back to `house`:**
- Fixed in quick task 260401-prt. `_GENRE_DRUM_GROUP` at `MCP_Server/orchestration/execution.py:150-163` now maps `neo_soul_rnb` to `"neo_soul_rnb"` with a dedicated pattern.

---

## Performance Concerns

**`get_ableton_connection()` pings on every call while holding the global lock:**
- Every MCP tool call invokes `get_ableton_connection()`, which holds `_connection_lock` and sends a `ping` round-trip before returning (`MCP_Server/connection.py:328-333`). This serializes all tool calls at the connection level. Concurrent async tool calls will queue behind the ping (up to `TIMEOUT_PING = 5.0s` per call).
- Fix approach: Skip the ping if `self.sock` is non-None and no recent error occurred; only ping on reconnection or after an exception.

**`get_mix_state` serializes full parameter lists — expensive for large sessions:**
- `get_checkpoint` calls `get_mix_state` which returns all parameters for every device on every track (`AbletonMCP_Remote_Script/handlers/devices.py:2768-2772`). Checkpoint only needs device class names, not parameter values.
- Impact: An 8-track session with 4 devices per track at ~30 parameters each generates ~960 parameter values over the socket per checkpoint.
- Fix approach: Add a lightweight `get_device_classes` RS command returning only `{track_name: [class_name, ...]}`.

**`apply_mix_recipe` and `apply_master_recipe` call `get_ableton_connection()` from an async executor thread:**
- Both tools call `conn.send_command(...)` inside `asyncio.get_event_loop().run_in_executor(None, ...)` (`MCP_Server/tools/mixing.py:62-68, 95-100`). `get_ableton_connection()` acquires `_connection_lock` from the thread pool thread, contending with any concurrent tool calls on the main thread.

**Sequential socket round-trips in checkpoint (partially fixed):**
- Quick task 260401-pye fixed the N+2 per-track clips loop by using `has_clips` from `get_arrangement_state` rather than issuing separate `get_arrangement_clips` per track. Checkpoint now makes exactly 2 socket calls (`get_arrangement_state` + `get_mix_state`). This concern is resolved for typical sessions.

---

## Fragile Areas

**Phase detection relies on track name substrings — breaks on custom names:**
- `_infer_completed_phases` (`MCP_Server/orchestration/checkpoint.py:49`) uses `_DRUM_NAMES = {"drum", "kick", "snare", "percussion", "beat"}` etc. A track named "808 Kit", "Pattern 1", or "Tom" does not match. Phase is permanently reported incomplete regardless of content.
- Safe modification: Any additions to name sets immediately affect all phase detection. Broad terms like `"beat"` can match unintended tracks.
- Test coverage: Tests use canonical names ("Drums", "Bass") — non-standard names are not covered.

**Master short-circuit can produce false "production complete":**
- If GlueCompressor and Limiter2 (or the real class name) are on the master track with `len(tracks) >= 2`, all phases are immediately returned as complete (`MCP_Server/orchestration/checkpoint.py:55-59`). A session with only a pre-loaded master bus and 2 scaffold tracks reports 100% completion.
- Safe modification: Test changes to this block with multi-track session fixtures.

**Sentinel value resolution depends on Claude understanding description hints:**
- `ExecutionStep.suggested_args` contains literal strings like `"<track_index>"` and `"<clip_index>"` (`MCP_Server/orchestration/execution.py:238-241`). There is no machine-enforceable contract ensuring Claude resolves these before calling the tool. A literal sentinel string passed as an integer argument fails at the MCP boundary.
- Safe modification: All sentinel steps should have `depends_on_step` pointing to a query step (`get_arrangement_overview`, `get_all_tracks`) that provides the needed value.

**Browser item loading depends on 1-tick schedule_message timing:**
- `_verify_load` fires after `schedule_message(1, ...)` — 1 Ableton scheduler tick (`AbletonMCP_Remote_Script/handlers/browser.py:462-471`). Under load (plugin scanning, large session), one tick may not be enough for device count to increase. The automatic retry (`browser.py:535-565`) adds one more tick. With retries exhausted, the load returns `{"loaded": False}`.
- Safe modification: Do not decrease the schedule delay. The 30-second `response_queue.get(timeout=30.0)` (`browser.py:484`) provides the outer bound.

**`apply_recipe` device loading has no cap on retries:**
- `AbletonMCP_Remote_Script/handlers/devices.py:2583` uses `response_queue.get(timeout=30.0)` for each device in the recipe. For `apply_master_recipe` with 3 devices, the worst-case timeout is `3 × 30s = 90s` before all failures surface. The MCP-side timeout `max(30.0, len(devices_payload) * 15.0)` (`MCP_Server/tools/mixing.py:61`) is calculated from MCP side, but the RS-side per-device queue wait is independent and can exceed it.

---

## Architectural Risks

**Connection singleton is not fully safe under concurrent tool calls:**
- `_ableton_connection` in `MCP_Server/connection.py:306` is protected by `_connection_lock` during creation and liveness validation. The per-connection `_send_lock` (added in quick task 260401-qhm, `connection.py:218, 267`) now serializes socket write+read cycles on the same connection. This prevents interleaved messages on a single socket. However, `get_ableton_connection()` holds `_connection_lock` while doing a ping, then returns the connection. A second caller acquires `_connection_lock` and also pings. Both then hold separate references and can call `send_command` concurrently — but `_send_lock` on the shared `AbletonConnection` instance serializes those. The design is correct as of 260401-qhm but is intricate and depends on callers using the same instance.

**No formal session-state persistence:**
- All production progress (completed phases, applied refinements, production brief) exists only in Ableton's live session and the in-memory MCP connection. A Claude context reset loses all orchestration state. HIST-01 (execution log) and REFN-03 (refinement log) are unimplemented, leaving resume-after-reset incomplete for any production beyond the setup phase.

**Ableton `_Framework.ControlSurface` is an undocumented private API:**
- `from _Framework.ControlSurface import ControlSurface` (`AbletonMCP_Remote_Script/__init__.py:14`). The underscore prefix signals Ableton's private internal framework. Major Ableton version upgrades (e.g., Live 11 → 12) have historically changed or removed `_Framework` classes with no public notice.
- Fix approach: Monitor Ableton Live release notes. Add a startup check that catches `ImportError` on `_Framework` and logs a clear message.

**Three key packages absent from current dev environment:**
- `mcp` (FastMCP) is not installed; `ModuleNotFoundError: No module named 'mcp'` occurs on import of any `MCP_Server.tools.*` module. This causes ~411 test failures.
- `pytest-asyncio` is absent; `asyncio_mode = "auto"` in `pyproject.toml` has no effect; all `async def test_*` functions fail.
- `tiktoken` is absent; `tests/test_genre_quality.py` fails at import.
- Fix: `pip install mcp[cli] pytest-asyncio tiktoken` or `pip install -e ".[dev]"`.

**`get_arrangement_state` track index sentinel resolution requires extra round-trips:**
- `ExecutionStep.suggested_args` uses `"<track_index>"` sentinels. The description instructs Claude to resolve via `get_all_tracks()` or `get_arrangement_overview`. Every phase execution needs at least one extra socket call per new track for index resolution. If the user adds tracks in Ableton between plan generation and execution, the resolved index may be stale.

---

## Deferred Features

**HIST-01 — Execution history log:**
- No per-session log of executed steps. `get_next_actions` always returns the full checklist from step 1 regardless of steps already run. Claude must manually track which steps have been executed. Explicitly deferred (`next_actions.py:197`).

**PARA-01 — Parallel phase execution:**
- All phases are strictly sequential. `ProductionPhase.depends_on` is always `[phase_order[i-1]]`. Phases with no true data dependency (e.g., bass programming does not require drums) are not flagged as parallelizable.

**ADPT-01 — Adaptive agenda refinement:**
- `refine_agenda` tool was added in quick task 260401-q7f (`MCP_Server/tools/orchestration.py:131-154`). Basic instruction parsing is implemented; complex multi-step refinements may not be handled.

**REFN-03 — Refinement history log:**
- No session-scoped log of applied `SectionRefinementPlan` operations. `refine_section` cannot detect conflicting or redundant refinements. Calling it twice with opposite instructions applies both silently.

**RFNA-04 — Revert section refinement:**
- No revert capability for `apply_section_note_refinement` or `apply_section_device_refinement`. Ableton's native undo stack is the only recourse. Requires REFN-03 first.

**SNAP-03 — Cross-section comparison:**
- No `compare_sections` tool. Claude cannot programmatically diff `SectionState` between two named sections.

**PARS-03 — Prompt signal conflict resolution:**
- When contradictory signals appear in a prompt (e.g., "euphoric dark techno"), the parser resolves silently by last-wins. No `signal_conflicts` list in `ProductionBrief`.

**SESS-03 — Prompt history:**
- No `list_production_briefs()` tool. Session-scoped brief history is not persisted.

---

## Test Coverage Gaps

**Real Ableton class name for Limiter not tested against live Ableton:**
- All tests use mocked `class_name: "Limiter2"`. Whether Ableton's actual `device.class_name` returns `"Limiter"` or `"Limiter2"` is untested. If wrong, master phase detection silently fails.
- Files: `tests/test_checkpoint.py:147`, `MCP_Server/orchestration/phase_detection.py:12`
- Priority: High

**Sentinel resolution by Claude not tested end-to-end:**
- No test verifies that Claude correctly resolves `"<track_index>"` string sentinels to integers before calling tools. Passing a literal sentinel string as an integer argument causes a type error at the MCP boundary.
- Files: `MCP_Server/orchestration/execution.py:256-286`
- Priority: Medium

**`apply_recipe` timeout scaling under plugin scan not tested:**
- `max(30.0, len(devices_payload) * 15.0)` MCP-side timeout may be exceeded by the RS-side per-device `response_queue.get(timeout=30.0)` in a slow plugin scan scenario.
- Files: `MCP_Server/tools/mixing.py:61`, `AbletonMCP_Remote_Script/handlers/devices.py:2583`
- Priority: Low

---

*Concerns audit: 2026-04-02*
