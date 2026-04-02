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
- Impact: If Ableton reports the class as `"Limiter"` (not `"Limiter2"`), master phase detection in the sequential walk (`checkpoint.py:100-102`) never passes. Tests use mocked `class_name: "Limiter2"` so they pass regardless.
- Risk: High — only discoverable by running against real Ableton.
- Fix approach: Load a session with a Limiter on the master track and inspect `device.class_name` via a debug command or Ableton's console.

---

## Architectural Risks

**No formal session-state persistence:**
- All production progress (completed phases, applied refinements, production brief) exists only in Ableton's live session and the in-memory MCP connection. A Claude context reset loses all orchestration state. HIST-01 (execution log) and REFN-03 (refinement log) are unimplemented, leaving resume-after-reset incomplete for any production beyond the setup phase.

**Ableton `_Framework.ControlSurface` is an undocumented private API:**
- `from _Framework.ControlSurface import ControlSurface` (`AbletonMCP_Remote_Script/__init__.py:14`). The underscore prefix signals Ableton's private internal framework. Major Ableton version upgrades (e.g., Live 11 → 12) have historically changed or removed `_Framework` classes with no public notice.
- Fix approach: Monitor Ableton Live release notes. Add a startup check that catches `ImportError` on `_Framework` and logs a clear message.

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
- Note (260402-rb4): Structural invariant test `test_sentinel_steps_have_depends_on_step` now ensures all sentinel steps have `depends_on_step` set, guaranteeing Claude has an explicit dependency chain. True E2E with Claude remains untested.
- Files: `MCP_Server/orchestration/execution.py:256-286`
- Priority: Medium (lowered -- structural invariant now enforced)

**`apply_recipe` timeout scaling under plugin scan not tested:**
- `max(30.0, len(devices_payload) * 15.0)` MCP-side timeout may be exceeded by the RS-side per-device `response_queue.get(timeout=30.0)` in a slow plugin scan scenario.
- Files: `MCP_Server/tools/mixing.py:61`, `AbletonMCP_Remote_Script/handlers/devices.py:2583`
- Priority: Low

---

*Concerns audit: 2026-04-02*
