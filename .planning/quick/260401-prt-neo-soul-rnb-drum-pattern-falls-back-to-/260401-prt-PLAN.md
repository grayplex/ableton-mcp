---
phase: quick-260401-prt
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/orchestration/execution.py
  - tests/test_phase_execution.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "neo_soul_rnb drum plan uses swing-feel kick/snare pattern, not four-on-the-floor house"
    - "neo_soul_rnb drum plan passes all existing phase execution tests"
  artifacts:
    - path: "MCP_Server/orchestration/execution.py"
      provides: "neo_soul_rnb entry in _DRUM_PATTERNS and _GENRE_DRUM_GROUP"
      contains: "neo_soul_rnb.*neo_soul_rnb"
  key_links:
    - from: "_GENRE_DRUM_GROUP['neo_soul_rnb']"
      to: "_DRUM_PATTERNS['neo_soul_rnb']"
      via: "dict key lookup"
      pattern: "neo_soul_rnb.*neo_soul_rnb"
---

<objective>
Fix the `neo_soul_rnb` drum pattern fallback in `_GENRE_DRUM_GROUP`. Currently it maps to `"house"` (four-on-the-floor) which is genre-inappropriate. Neo-soul/R&B uses a swing-feel or live-kit pattern: kick on beat 1 with an anticipation on the "and" of 2, snare on beats 2 and 4, sparse 8th-note hi-hats.

Purpose: Genre-appropriate drum suggestions for neo_soul_rnb.
Output: New `"neo_soul_rnb"` entry in `_DRUM_PATTERNS`, updated mapping in `_GENRE_DRUM_GROUP`, and a test asserting the pattern is not house.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add neo_soul_rnb drum pattern and fix mapping</name>
  <files>MCP_Server/orchestration/execution.py, tests/test_phase_execution.py</files>
  <behavior>
    - Test: get_execution_plan("drums", "neo_soul_rnb") does not error
    - Test: The add_notes_to_clip step for neo_soul_rnb does NOT contain a note at start_time=2.0 with velocity=100 and pitch=36 (the house "kick on 3" note) — i.e. it is not the house pattern
    - Test: The add_notes_to_clip step for neo_soul_rnb DOES contain a snare note (pitch 38) on beat 2 (start_time=1.0)
  </behavior>
  <action>
FIRST: Rebase onto misc-fixes before any edits:
```
git fetch origin misc-fixes && git rebase origin/misc-fixes
```

Write the failing test in `tests/test_phase_execution.py` inside `TestPhaseExecutionPlan`:

```python
def test_drums_neo_soul_rnb_not_house_pattern(self):
    """neo_soul_rnb drums should use a swing/R&B pattern, not four-on-the-floor house."""
    result = get_execution_plan("drums", "neo_soul_rnb")
    assert "error" not in result
    notes_steps = [s for s in result["steps"] if s["tool_name"] == "add_notes_to_clip"]
    all_notes = []
    for step in notes_steps:
        all_notes.extend(step.get("suggested_args", {}).get("notes", []))
    # House pattern has kick (pitch 36) at start_time=2.0 — neo_soul_rnb must not
    house_kick_on_3 = any(
        n["pitch"] == 36 and n["start_time"] == 2.0 and n["velocity"] == 100
        for n in all_notes
    )
    assert not house_kick_on_3, "neo_soul_rnb should not use the house drum pattern"
    # Must have snare (pitch 38) on beat 2 (start_time=1.0) — characteristic R&B feel
    has_snare_on_2 = any(n["pitch"] == 38 and n["start_time"] == 1.0 for n in all_notes)
    assert has_snare_on_2, "neo_soul_rnb should have snare on beat 2"
```

Run the test — it should fail (RED) because neo_soul_rnb still maps to "house".

Then fix `MCP_Server/orchestration/execution.py`:

1. Add a `"neo_soul_rnb"` entry to `_DRUM_PATTERNS` (after the "trance" group). Neo-soul/R&B pattern: kick on beat 1, anticipation kick on the "and" of 2, snare on beats 2 and 4, sparse open 8th hi-hats. Keep to D-07 budget (kick≤4, snare≤2, hi-hat≤4):

```python
# Neo-soul / R&B — swing feel, kick anticipation, snare on 2+4
"neo_soul_rnb": {
    "kick_clap": [
        _note(36, 0.0, 0.25, 100),   # kick beat 1
        _note(36, 1.5, 0.25, 85),    # kick anticipation (and-of-2)
        _note(38, 1.0, 0.25, 100),   # snare beat 2
        _note(38, 3.0, 0.25, 100),   # snare beat 4
    ],
    "hihat": [
        _note(42, 0.0, 0.25, 65),    # hi-hat beat 1
        _note(42, 1.0, 0.25, 60),    # hi-hat beat 2
        _note(42, 2.0, 0.25, 65),    # hi-hat beat 3
        _note(42, 3.0, 0.25, 60),    # hi-hat beat 4
    ],
    "clap_pitch": 38,
},
```

2. Update `_GENRE_DRUM_GROUP` — change:
```python
"neo_soul_rnb": "house",  # default to house pattern
```
to:
```python
"neo_soul_rnb": "neo_soul_rnb",
```

Run the test again — it should pass (GREEN).
  </action>
  <verify>
    <automated>python -m pytest tests/test_phase_execution.py::TestPhaseExecutionPlan::test_drums_neo_soul_rnb_not_house_pattern tests/test_phase_execution.py -x -q</automated>
  </verify>
  <done>All test_phase_execution tests pass; neo_soul_rnb drum plan uses swing-feel pattern with snare on beats 2 and 4, not four-on-the-floor house kicks</done>
</task>

</tasks>

<verification>
Run the full test suite to confirm no regressions:

```
python -m pytest tests/test_phase_execution.py tests/test_execution.py -q
```

All tests must pass.
</verification>

<success_criteria>
- `_DRUM_PATTERNS` contains a `"neo_soul_rnb"` key with swing-feel kick/snare layout
- `_GENRE_DRUM_GROUP["neo_soul_rnb"]` is `"neo_soul_rnb"`, not `"house"`
- `test_drums_neo_soul_rnb_not_house_pattern` passes
- Full `test_phase_execution.py` suite passes (no regressions)
</success_criteria>

<output>
After completion, create `.planning/quick/260401-prt-neo-soul-rnb-drum-pattern-falls-back-to-/260401-prt-SUMMARY.md`
</output>
