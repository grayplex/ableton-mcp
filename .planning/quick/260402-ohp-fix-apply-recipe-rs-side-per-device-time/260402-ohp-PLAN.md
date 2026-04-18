---
phase: quick
plan: 260402-ohp
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/tools/mixing.py
  - AbletonMCP_Remote_Script/handlers/devices.py
  - tests/test_mixing.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "RS-side per-device timeout aligns with total MCP-side budget"
    - "MCP-side passes timeout to RS via command payload"
    - "RS-side uses passed timeout for response_queue.get, not hardcoded 30s"
  artifacts:
    - path: "MCP_Server/tools/mixing.py"
      provides: "timeout field in apply_recipe command payload"
    - path: "AbletonMCP_Remote_Script/handlers/devices.py"
      provides: "Dynamic timeout from payload in response_queue.get"
  key_links:
    - from: "MCP_Server/tools/mixing.py"
      to: "AbletonMCP_Remote_Script/handlers/devices.py"
      via: "timeout field in apply_recipe command payload"
      pattern: "timeout.*params"
---

<objective>
Fix timeout misalignment between MCP-side and RS-side in apply_recipe. Currently the
MCP side computes `max(30.0, len(devices) * 15.0)` but the RS side uses a hardcoded
`response_queue.get(timeout=30.0)`. For 3+ devices the MCP timeout (45s) can expire
before RS exhausts its 30s wait, or RS waits too long for a budget that's already gone.

Purpose: Prevent MCP timeout expiring while RS is still waiting on device loads.
Output: Aligned timeout — MCP passes its budget via payload, RS uses it.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@MCP_Server/tools/mixing.py
@AbletonMCP_Remote_Script/handlers/devices.py
@tests/test_mixing.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Pass timeout in command payload and use it on RS side</name>
  <files>MCP_Server/tools/mixing.py, AbletonMCP_Remote_Script/handlers/devices.py</files>
  <action>
1. In `MCP_Server/tools/mixing.py`, both `apply_mix_recipe` (line ~56) and
   `apply_master_recipe` (line ~83): add a `"timeout"` field to the command payload
   dict passed to `send_command("apply_recipe", {...})`. Set it to the same `timeout`
   value already computed (`max(30.0, len(devices_payload) * 15.0)`).

   Before:
   ```python
   result = conn.send_command("apply_recipe", {
       "track_index": track_index,
       "track_type": "track",
       "devices": devices_payload,
   }, timeout=timeout)
   ```

   After:
   ```python
   result = conn.send_command("apply_recipe", {
       "track_index": track_index,
       "track_type": "track",
       "devices": devices_payload,
       "timeout": timeout,
   }, timeout=timeout)
   ```

   Do the same for `apply_master_recipe`.

2. In `AbletonMCP_Remote_Script/handlers/devices.py`, in `_apply_recipe` (line ~2519):
   - Read `timeout` from params with a default: `total_timeout = params.get("timeout", 30.0)`
   - Replace the hardcoded `response_queue.get(timeout=30.0)` at line 2583 with
     `response_queue.get(timeout=total_timeout)`.
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_mixing.py -x -q 2>&1 | tail -5</automated>
  </verify>
  <done>
    - MCP side sends timeout in payload for both apply_mix_recipe and apply_master_recipe
    - RS side reads timeout from params and uses it for response_queue.get
    - Existing tests pass
  </done>
</task>

<task type="auto">
  <name>Task 2: Add test coverage for timeout passthrough</name>
  <files>tests/test_mixing.py</files>
  <action>
In `tests/test_mixing.py`, update the existing `test_apply_mix_recipe_sends_command`
(around line 440) and `test_apply_master_recipe_sends_command` (around line 490) tests
to also assert that the payload includes a `"timeout"` key matching
`max(30.0, len(devices_payload) * 15.0)`.

Add assertion after the existing payload checks:
```python
assert "timeout" in payload
assert payload["timeout"] == call_args[1]["timeout"]  # matches send_command kwarg
```

This ensures the payload timeout stays in sync with the send_command timeout.
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_mixing.py -x -q 2>&1 | tail -5</automated>
  </verify>
  <done>
    - Tests verify timeout field present in payload for both apply_mix_recipe and apply_master_recipe
    - Tests verify payload timeout matches send_command timeout kwarg
    - All tests pass
  </done>
</task>

</tasks>

<verification>
python -m pytest tests/test_mixing.py -x -q
</verification>

<success_criteria>
- MCP-side timeout budget is passed to RS via command payload
- RS-side uses the passed timeout instead of hardcoded 30s
- Existing and new tests pass
</success_criteria>

<output>
After completion, create `.planning/quick/260402-ohp-fix-apply-recipe-rs-side-per-device-time/260402-ohp-SUMMARY.md`
</output>
