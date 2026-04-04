# Codebase Concerns

**Analysis Date:** 2026-04-02

---

## Known Limitations

**Prompt parser is English-only:**
- The signal lexicon (`MCP_Server/prompt/lexicon.py:1-13`) covers English keywords only. Non-English prompts pass tokens through as `raw_descriptors` with no signal extraction. This is documented in the file header but there is no translation layer or multilingual fallback.

**Track index sentinel resolution is stateless (staleness possible):**
- `ExecutionStep.suggested_args` uses `"<track_index>"` sentinels resolved at execution time via a query step. If the user adds or removes tracks in Ableton between plan generation and execution, the resolved index may target the wrong track. This is inherent to the stateless plan-then-execute architecture.
- Mitigations: All sentinel steps have explicit `depends_on_step` pointing to a query step (260402-rb4), so resolution always uses fresh track data. The window of staleness is limited to changes made between the query step and the dependent action step within a single phase execution.

---

## Bugs

**`_LIMITER` constant may not match Ableton's real class name:**
- `_LIMITER = "Limiter2"` in `MCP_Server/orchestration/phase_detection.py:12`. `DEVICE_PATHS` (`AbletonMCP_Remote_Script/handlers/devices.py:25`) keys on `"Limiter"`, and `MCP_Server/devices/catalog.py:1525` has key `"Limiter"`. The actual class name returned by `device.class_name` in Ableton's Python API is the ground truth.
- Impact: If Ableton reports the class as `"Limiter"` (not `"Limiter2"`), master phase detection in the sequential walk (`checkpoint.py:100-102`) never passes. Tests use mocked `class_name: "Limiter2"` so they pass regardless.
- Risk: High — only discoverable by running against real Ableton.
- Fix approach: Load a session with a Limiter on the master track and inspect `device.class_name` via a debug command or Ableton's console.

---

## Architectural Risks

**No formal session-state persistence:**
- All production progress (completed phases, applied refinements, production brief) exists only in Ableton's live session and the in-memory MCP connection. A Claude context reset loses all orchestration state. REFN-03 (refinement log) is unimplemented, leaving resume-after-reset incomplete for any production beyond the setup phase.

**Ableton `_Framework.ControlSurface` is an undocumented private API:**
- `from _Framework.ControlSurface import ControlSurface` (`AbletonMCP_Remote_Script/__init__.py:14`). The underscore prefix signals Ableton's private internal framework. Major Ableton version upgrades (e.g., Live 11 → 12) have historically changed or removed `_Framework` classes with no public notice.
- Fix approach: Monitor Ableton Live release notes. Add a startup check that catches `ImportError` on `_Framework` and logs a clear message.

---

## Test Coverage Gaps

**Real Ableton class name for Limiter not tested against live Ableton:**
- All tests use mocked `class_name: "Limiter2"`. Whether Ableton's actual `device.class_name` returns `"Limiter"` or `"Limiter2"` is untested. If wrong, master phase detection silently fails.
- Files: `tests/test_checkpoint.py:147`, `MCP_Server/orchestration/phase_detection.py:12`
- Priority: High

**Sentinel resolution by Claude not tested end-to-end:**
- No test verifies that Claude correctly resolves `"<track_index>"` string sentinels to integers before calling tools. Passing a literal sentinel string as an integer argument causes a type error at the MCP boundary.
- Note (260402-rb4): Structural invariant test `test_sentinel_steps_have_depends_on_step` now ensures all sentinel steps have `depends_on_step` set, guaranteeing Claude has an explicit dependency chain. True E2E with Claude remains untested.
- Files: `MCP_Server/orchestration/execution.py:256-286`
- Priority: Medium (lowered -- structural invariant now enforced)

**`apply_recipe` timeout scaling under plugin scan not tested:**
- `max(30.0, len(devices_payload) * 15.0)` MCP-side timeout may be exceeded by the RS-side per-device `response_queue.get(timeout=30.0)` in a slow plugin scan scenario.
- Files: `MCP_Server/tools/mixing.py:61`, `AbletonMCP_Remote_Script/handlers/devices.py:2583`
- Priority: Low

---

*Concerns audit: 2026-04-02*
