---
phase: quick-260401-pjl
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/orchestration/phase_detection.py
  - MCP_Server/orchestration/checkpoint.py
  - MCP_Server/orchestration/next_actions.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Phase name sets and device class constants exist in exactly one place"
    - "checkpoint.py and next_actions.py import constants from phase_detection.py"
    - "All existing tests pass after the refactor"
  artifacts:
    - path: "MCP_Server/orchestration/phase_detection.py"
      provides: "Shared phase-detection constants"
      exports: ["_DRUM_NAMES", "_BASS_NAMES", "_HARMONY_NAMES", "_MELODY_NAMES", "_COMPRESSOR", "_GLUE_COMPRESSOR", "_LIMITER"]
  key_links:
    - from: "MCP_Server/orchestration/checkpoint.py"
      to: "MCP_Server/orchestration/phase_detection.py"
      via: "from MCP_Server.orchestration.phase_detection import ..."
    - from: "MCP_Server/orchestration/next_actions.py"
      to: "MCP_Server/orchestration/phase_detection.py"
      via: "from MCP_Server.orchestration.phase_detection import ..."
---

<objective>
Extract duplicated phase-detection constants from checkpoint.py and next_actions.py into a shared module.

Purpose: Eliminate the acknowledged duplication (next_actions.py:12 comment) so changes to phase name sets or device class strings only need to happen in one place.
Output: New MCP_Server/orchestration/phase_detection.py; updated imports in checkpoint.py and next_actions.py.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Rebase worktree onto misc-fixes</name>
  <files></files>
  <action>
    Before making any code changes, rebase the current worktree onto the latest misc-fixes branch to pick up parallel agent commits:

    ```
    git fetch origin
    git rebase origin/misc-fixes
    ```

    If there are conflicts, resolve them before proceeding. The rebase must complete cleanly.
  </action>
  <verify>
    <automated>git log --oneline -5</automated>
  </verify>
  <done>git status shows clean working tree on top of misc-fixes HEAD; no merge conflicts remain.</done>
</task>

<task type="auto">
  <name>Task 2: Create shared phase_detection.py and update imports</name>
  <files>MCP_Server/orchestration/phase_detection.py, MCP_Server/orchestration/checkpoint.py, MCP_Server/orchestration/next_actions.py</files>
  <action>
    1. Create MCP_Server/orchestration/phase_detection.py with a module docstring and all shared constants extracted from both files:

    ```python
    """Shared constants for phase-detection heuristics used by checkpoint and next_actions."""

    # Track name substrings -> phase association
    _DRUM_NAMES = {"drum", "kick", "snare", "percussion", "beat"}
    _BASS_NAMES = {"bass", "sub"}
    _HARMONY_NAMES = {"chord", "pad", "harm", "keys", "piano", "strings", "organ"}
    _MELODY_NAMES = {"lead", "melody", "mel", "synth", "arp"}

    # Device class names from get_mix_state RS output
    _COMPRESSOR = "Compressor2"
    _GLUE_COMPRESSOR = "GlueCompressor"
    _LIMITER = "Limiter2"
    ```

    2. In checkpoint.py:
       - Remove the five constant definitions (_DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER — note _EQ and _DRUM_DEVICE are NOT duplicated and must remain in checkpoint.py).
       - Add import after existing imports: `from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER`

    3. In next_actions.py:
       - Remove the four name-set constant definitions (_DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES) and the three device class string definitions (_COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER).
       - Remove the comment "# Phase completion heuristics (same as checkpoint.py, duplicated for clarity)".
       - Add import after existing imports: `from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER`
       - _EFFECT_CLASSES is NOT duplicated — leave it in next_actions.py.
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -c "from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _GLUE_COMPRESSOR; print('import ok')"</automated>
  </verify>
  <done>phase_detection.py exists with all seven constants; checkpoint.py and next_actions.py import from it; neither file defines the constants locally.</done>
</task>

<task type="auto">
  <name>Task 3: Run tests and commit</name>
  <files></files>
  <action>
    Run the full test suite to confirm nothing regressed:

    ```
    cd I:/ableton-mcp && python -m pytest tests/ -x -q
    ```

    All tests must pass. If any fail, fix the import or constant name before committing.

    Then commit with message:
    ```
    refactor(quick-260401-pjl): extract phase-detection constants into shared module
    ```

    Include all three modified/created files in the commit:
    - MCP_Server/orchestration/phase_detection.py
    - MCP_Server/orchestration/checkpoint.py
    - MCP_Server/orchestration/next_actions.py
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/ -x -q</automated>
  </verify>
  <done>All tests pass; git log shows the refactor commit on top of the rebased misc-fixes branch.</done>
</task>

</tasks>

<verification>
- python -c "from MCP_Server.orchestration.phase_detection import _DRUM_NAMES, _BASS_NAMES, _HARMONY_NAMES, _MELODY_NAMES, _COMPRESSOR, _GLUE_COMPRESSOR, _LIMITER; print('ok')"
- grep -n "_DRUM_NAMES" MCP_Server/orchestration/checkpoint.py — should show only the import line, not a definition
- grep -n "_DRUM_NAMES" MCP_Server/orchestration/next_actions.py — should show only the import line, not a definition
- python -m pytest tests/ -x -q — all pass
</verification>

<success_criteria>
phase_detection.py contains exactly the seven shared constants; checkpoint.py and next_actions.py each have one import line for them and zero local definitions; all tests pass.
</success_criteria>

<output>
After completion, create .planning/quick/260401-pjl-deduplicate-phase-detection-constants-fr/260401-pjl-SUMMARY.md
</output>
