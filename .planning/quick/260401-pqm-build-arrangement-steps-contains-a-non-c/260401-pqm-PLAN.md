---
phase: quick-260401-pqm
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/orchestration/next_actions.py
  - MCP_Server/orchestration/execution.py
  - tests/test_next_actions.py
autonomous: true
requirements: [QUICK-PQM]
must_haves:
  truths:
    - "Steps with non-callable tool_name (em-dash or empty) are filtered out before being returned to Claude"
    - "get_next_actions_result never returns a step where tool_name is not a real MCP tool"
    - "The arrangement phase checklist still reports correct total_steps and estimated_tool_calls"
  artifacts:
    - path: "MCP_Server/orchestration/next_actions.py"
      provides: "Filtering of non-callable steps before returning to caller"
      contains: "tool_name"
    - path: "tests/test_next_actions.py"
      provides: "Test proving non-callable steps are filtered"
  key_links:
    - from: "MCP_Server/orchestration/next_actions.py"
      to: "MCP_Server/orchestration/execution.py"
      via: "get_execution_plan returns steps, get_next_actions_result filters them"
      pattern: "tool_name.*—"
---

<objective>
Filter non-callable placeholder steps (tool_name == "---" em-dash or empty) from the steps
returned by get_next_actions_result, so Claude never tries to call a non-existent tool.

Purpose: Step 5 in _build_arrangement_steps has tool_name: "---" (em-dash) and empty
suggested_args. While excluded from estimated_tool_calls, it is still included in the
steps list returned to Claude via get_next_actions. Claude must never receive a step
it cannot execute as a tool call.

Output: Filtered steps in get_next_actions_result, updated test coverage.
</objective>

<execution_context>
@.planning/quick/260401-pqm-build-arrangement-steps-contains-a-non-c/260401-pqm-PLAN.md
</execution_context>

<context>
@MCP_Server/orchestration/execution.py (contains _build_arrangement_steps with the placeholder step at line 370-372)
@MCP_Server/orchestration/next_actions.py (contains get_next_actions_result which returns steps to Claude)
@tests/test_next_actions.py (existing test file for next_actions)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rebase worktree onto misc-fixes</name>
  <files></files>
  <action>
    Before making any code changes, rebase this worktree onto the latest misc-fixes branch
    to pick up changes from other parallel agents:

    ```bash
    git fetch origin misc-fixes
    git rebase origin/misc-fixes
    ```

    If there are conflicts, resolve them sensibly (other agents are working on the same
    orchestration files).
  </action>
  <verify>
    <automated>git log --oneline -5</automated>
  </verify>
  <done>Worktree is up to date with latest misc-fixes</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Filter non-callable steps from get_next_actions_result and mark placeholder in execution.py</name>
  <files>MCP_Server/orchestration/next_actions.py, MCP_Server/orchestration/execution.py, tests/test_next_actions.py</files>
  <behavior>
    - Test: get_next_actions_result("house", phase_name="arrangement") returns steps where
      every step has a callable tool_name (none are "---" em-dash, empty string, or None)
    - Test: The filtered steps still contain the other 4 arrangement steps (steps 1-4)
    - Test: Non-callable steps are converted to description-only notes in the response
      (their description text is preserved as a "notes" field or similar) so Claude still
      sees the instruction but does not try to call it as a tool
  </behavior>
  <action>
    **In MCP_Server/orchestration/next_actions.py:**

    In get_next_actions_result, after `steps = checklist["steps"][:n]` (appears twice in the
    function -- both the explicit-phase path around line 122 and the checkpoint path around
    line 173), filter the steps to separate callable from non-callable:

    ```python
    # Define a helper at module level (near top, after imports):
    _NON_CALLABLE = frozenset({"—", "\u2014", "", None})  # em-dash, empty, None

    def _filter_steps(steps):
        """Separate callable steps from description-only placeholders."""
        callable_steps = []
        notes = []
        for s in steps:
            if s.get("tool_name") in _NON_CALLABLE:
                notes.append(s.get("description", ""))
            else:
                callable_steps.append(s)
        return callable_steps, notes
    ```

    Then at both sites where steps are returned, call `_filter_steps`:
    ```python
    steps, notes = _filter_steps(checklist["steps"][:n])
    ```

    Include `"notes": notes` in the returned dict (only if notes is non-empty, to keep
    responses compact).

    **In MCP_Server/orchestration/execution.py:**

    On line 372, add a comment to the placeholder step making the intent explicit:
    ```python
    # Non-callable placeholder — filtered by next_actions before returning to Claude
    _step(5, "Review evaluate_session output and apply each item in top_fixes",
          "\u2014", {}, pt, 4),
    ```

    **In tests/test_next_actions.py:**

    Add a new test:
    ```python
    def test_arrangement_steps_exclude_non_callable():
        """Arrangement checklist steps returned by get_next_actions_result
        never include non-callable placeholder tool names."""
        result = get_next_actions_result("house", phase_name="arrangement")
        assert "error" not in result
        steps = result["steps"]
        # All returned steps must have a real tool_name
        for step in steps:
            assert step["tool_name"] not in {"—", "\u2014", "", None}, (
                f"Step {step['step_number']} has non-callable tool_name: {step['tool_name']!r}"
            )
        # The placeholder description should appear in notes
        assert len(result.get("notes", [])) >= 1
        assert any("top_fixes" in n for n in result["notes"])
    ```

    Also add a test confirming callable steps are preserved:
    ```python
    def test_arrangement_callable_steps_preserved():
        """Arrangement checklist preserves the 4 callable steps."""
        result = get_next_actions_result("house", phase_name="arrangement")
        steps = result["steps"]
        assert len(steps) == 4
        tool_names = [s["tool_name"] for s in steps]
        assert "get_arrangement_overview" in tool_names
        assert "get_arrangement_progress" in tool_names
        assert "evaluate_session" in tool_names
        assert "get_section_checklist" in tool_names
    ```
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_next_actions.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>
    - No step with tool_name "---" (em-dash) or empty is ever returned in the "steps" list
    - Placeholder description text preserved in "notes" field
    - All 4 callable arrangement steps still returned
    - All existing tests still pass
  </done>
</task>

</tasks>

<verification>
```bash
cd I:/ableton-mcp && python -m pytest tests/test_next_actions.py tests/test_execution.py -x -q
```
All tests pass, including new tests for non-callable step filtering.
</verification>

<success_criteria>
- get_next_actions_result never returns steps with non-callable tool_name
- Placeholder description preserved as notes for Claude's awareness
- All existing tests continue to pass
- New tests cover the filtering behavior
</success_criteria>

<output>
After completion, create `.planning/quick/260401-pqm-build-arrangement-steps-contains-a-non-c/260401-pqm-SUMMARY.md`
</output>
