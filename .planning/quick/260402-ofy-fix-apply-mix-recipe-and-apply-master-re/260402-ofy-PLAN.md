---
phase: quick
plan: 260402-ofy
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/tools/mixing.py
  - tests/test_mixing.py
  - .planning/codebase/CONCERNS.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "apply_mix_recipe and apply_master_recipe are synchronous def (not async def)"
    - "No run_in_executor or asyncio imports remain in mixing.py"
    - "Both tools call conn.send_command directly on the calling thread"
    - "All existing tests pass with the sync conversion"
  artifacts:
    - path: "MCP_Server/tools/mixing.py"
      provides: "Sync apply_mix_recipe and apply_master_recipe tools"
      contains: "def apply_mix_recipe"
    - path: "tests/test_mixing.py"
      provides: "Updated tests calling sync functions directly"
  key_links:
    - from: "MCP_Server/tools/mixing.py"
      to: "MCP_Server/connection.py"
      via: "get_ableton_connection().send_command() — direct call, no executor"
      pattern: "conn\\.send_command"
---

<objective>
Convert apply_mix_recipe and apply_master_recipe from async to sync to eliminate run_in_executor lock contention.

Purpose: Both tools currently use `loop.run_in_executor(None, lambda: conn.send_command(...))` which causes the executor thread to contend with `_connection_lock` and `_send_lock`. FastMCP automatically runs sync tools in a thread pool, so the manual executor dance is unnecessary and harmful.

Output: Synchronous tool functions with no asyncio usage, updated tests, resolved CONCERNS.md entry.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@MCP_Server/tools/mixing.py
@MCP_Server/connection.py
@tests/test_mixing.py
@.planning/codebase/CONCERNS.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Convert apply_mix_recipe and apply_master_recipe to sync</name>
  <files>MCP_Server/tools/mixing.py, tests/test_mixing.py</files>
  <action>
In MCP_Server/tools/mixing.py:

1. Remove `import asyncio` (line 3) — no longer needed.
2. Convert `apply_mix_recipe` (line 34) from `async def` to `def`:
   - Change signature: `def apply_mix_recipe(ctx: Context, track_index: int, role: str, genre: str) -> str:`
   - Remove the `await ctx.info(...)` call (lines 56-59). The progress info is not critical — the return value already communicates what was applied.
   - Remove `loop = asyncio.get_event_loop()` and `await loop.run_in_executor(...)` (lines 63-68).
   - Replace with direct call: `result = conn.send_command("apply_recipe", {"track_index": track_index, "track_type": "track", "devices": devices_payload}, timeout=timeout)`
   - Keep the `timeout = max(30.0, len(devices_payload) * 15.0)` calculation.
   - Keep `conn = get_ableton_connection()` call.

3. Convert `apply_master_recipe` (line 73) from `async def` to `def`:
   - Change signature: `def apply_master_recipe(ctx: Context, genre: str) -> str:`
   - Remove the `await ctx.info(...)` call (lines 90-93).
   - Remove `loop = asyncio.get_event_loop()` and `await loop.run_in_executor(...)` (lines 97-102).
   - Replace with direct call: `result = conn.send_command("apply_recipe", {"track_index": 0, "track_type": "master", "devices": devices_payload}, timeout=timeout)`
   - Keep the timeout calculation and connection acquisition.

In tests/test_mixing.py:

4. Update `_mock_ctx()` (line 428-431): Change `ctx.info = AsyncMock()` to `ctx.info = MagicMock()` since ctx.info is no longer awaited. Actually, ctx.info is no longer called at all, so this mock is only needed for other test patterns. Keep it as MagicMock for safety.

5. In TestApplyMixRecipe: Replace all `asyncio.run(apply_mix_recipe(...))` calls with direct `apply_mix_recipe(...)` calls:
   - Line 443: `result = apply_mix_recipe(ctx, 0, "kick", "house")`
   - Line 455: `result = apply_mix_recipe(ctx, 0, "invalid_role", "house")`
   - Line 464: `apply_mix_recipe(ctx, 0, "kick", "house")`
   - Line 477: `apply_mix_recipe(ctx, 0, "kick", "house")`

6. In TestApplyMasterRecipe: Replace all `asyncio.run(apply_master_recipe(...))` calls with direct calls:
   - Line 494: `result = apply_master_recipe(ctx, "house")`
   - Line 506: `apply_master_recipe(ctx, "house")`
   - Line 515: `result = apply_master_recipe(ctx, "invalid_genre")`

7. In TestBatchParameterSetting: Replace `asyncio.run(apply_mix_recipe(...))` with direct call:
   - Line 559: `apply_mix_recipe(ctx, 0, "kick", "house")`

8. Remove unused imports from tests/test_mixing.py: `asyncio` (line 11) and `AsyncMock` (line 15) are no longer needed. Keep `MagicMock` and other imports.
  </action>
  <verify>
    <automated>cd /home/user/ableton-mcp && python -m pytest tests/test_mixing.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>Both functions are sync def, no asyncio usage in mixing.py, all 30+ mixing tests pass without asyncio.run()</done>
</task>

<task type="auto">
  <name>Task 2: Update CONCERNS.md to mark contention issue resolved</name>
  <files>.planning/codebase/CONCERNS.md</files>
  <action>
In .planning/codebase/CONCERNS.md, update the performance concern on lines 49-51:

Change:
```
**`apply_mix_recipe` and `apply_master_recipe` call `get_ableton_connection()` from an async executor thread:**
- Both tools call `conn.send_command(...)` inside `asyncio.get_event_loop().run_in_executor(None, ...)` (`MCP_Server/tools/mixing.py:62-68, 95-100`). `get_ableton_connection()` acquires `_connection_lock` from the thread pool thread, contending with any concurrent tool calls on the main thread.
```

To:
```
**`apply_mix_recipe` and `apply_master_recipe` executor thread contention:** RESOLVED (260402-ofy) -- Converted both tools from async to sync def. FastMCP runs sync tools in its own thread pool, eliminating the manual run_in_executor and associated lock contention.
```
  </action>
  <verify>
    <automated>cd /home/user/ableton-mcp && grep -c "RESOLVED (260402-ofy)" .planning/codebase/CONCERNS.md</automated>
  </verify>
  <done>CONCERNS.md entry marked as resolved with quick task ID reference</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/test_mixing.py -x -q` — all tests pass
- `grep -c "async def" MCP_Server/tools/mixing.py` returns 0
- `grep -c "run_in_executor" MCP_Server/tools/mixing.py` returns 0
- `grep -c "import asyncio" MCP_Server/tools/mixing.py` returns 0
</verification>

<success_criteria>
- apply_mix_recipe and apply_master_recipe are synchronous functions
- No asyncio imports or run_in_executor patterns remain in mixing.py
- All existing mixing tests pass (updated to call sync functions directly)
- CONCERNS.md entry marked resolved
</success_criteria>

<output>
After completion, create `.planning/quick/260402-ofy-fix-apply-mix-recipe-and-apply-master-re/260402-ofy-SUMMARY.md`
</output>
