---
phase: quick-260402-qyx
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/orchestration/schema.py
  - MCP_Server/orchestration/agenda.py
  - tests/test_production_agenda.py
autonomous: true
requirements: [PARA-01]
must_haves:
  truths:
    - "get_production_agenda returns phases where bass and drums both depend only on setup, not on each other"
    - "get_production_agenda returns phases where mix depends on all content phases (drums, bass, harmony, melody, sound_design, arrangement)"
    - "ProductionPhase includes a parallelizable bool field — true when the phase has no content-phase dependencies"
    - "All 12 genre agendas produce dependency graphs with no strict-sequential false edges"
  artifacts:
    - path: "MCP_Server/orchestration/schema.py"
      provides: "ProductionPhase with parallelizable field"
      contains: "parallelizable"
    - path: "MCP_Server/orchestration/agenda.py"
      provides: "True dependency map replacing linear chain"
      contains: "_PHASE_DEPS"
  key_links:
    - from: "MCP_Server/orchestration/agenda.py"
      to: "MCP_Server/orchestration/schema.py"
      via: "ProductionPhase construction"
      pattern: "parallelizable"
---

<objective>
Implement PARA-01: replace the strict sequential `depends_on` chain in production agenda generation with a true musical dependency map. Phases that don't require each other's output (e.g., bass does not need drums) will be marked independent and can run in parallel.

Purpose: Claude can run independent phases (bass + drums + harmony after setup) concurrently, reducing total production time and giving more flexibility mid-session.
Output: Updated schema with `parallelizable` field, updated agenda builder with `_PHASE_DEPS` map, and tests covering the new dependency semantics.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/codebase/CONCERNS.md

# Key files to read before implementing:
# - MCP_Server/orchestration/schema.py  (ProductionPhase TypedDict)
# - MCP_Server/orchestration/agenda.py  (get_agenda, AGENDA_CATALOG, _build_phase)
# - tests/test_production_agenda.py      (existing test patterns to follow)
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add parallelizable field to schema and implement true dependency map in agenda</name>
  <files>MCP_Server/orchestration/schema.py, MCP_Server/orchestration/agenda.py</files>
  <behavior>
    - After implementation, get_agenda("house") phases where phase_type is "bass" must have depends_on == ["setup"], not ["drums"]
    - get_agenda("house") phases where phase_type is "drums" must have depends_on == ["setup"], not ["setup"] via prior element — same result but for the right reason
    - get_agenda("house") phases where phase_type is "mix" must have depends_on containing "arrangement" and at least one content phase (e.g., "drums")
    - get_agenda("house") phases where phase_type is "master" must have depends_on == ["mix"]
    - Every ProductionPhase has a boolean field "parallelizable" — True when it has ≤1 dependency (i.e., only needs setup or nothing)
    - Phases that only depend on "setup" (drums, bass, harmony, melody, sound_design) are parallelizable=True
    - "arrangement", "mix", "master" are parallelizable=False (multi-dependency or downstream)
    - "setup" is parallelizable=False (it is the root, not parallelizable itself)
    - JSON output size constraint: still under 1600 chars for all 12 genres (the new field adds ~15 bytes per phase — verify this does not breach budget)
    - The existing strict-sequential depends_on test in test_production_agenda.py will break — update that test to reflect true deps
  </behavior>
  <action>
    Step 1 — schema.py: Add `parallelizable: bool` field to the `ProductionPhase` TypedDict. Add a comment explaining: "True if this phase can run concurrently with other phases of the same dependency level."

    Step 2 — agenda.py: Define `_PHASE_DEPS` dict mapping each phase_type to its true prerequisite phase_types (not positional predecessors). Musical dependency rules:

    ```python
    _PHASE_DEPS = {
        "setup":        [],               # root — no prerequisites
        "drums":        ["setup"],        # only needs tempo/key from setup
        "bass":         ["setup"],        # only needs tempo/key from setup
        "harmony":      ["setup"],        # only needs key/scale from setup
        "melody":       ["setup"],        # only needs key/scale from setup
        "sound_design": ["setup"],        # timbre work, no content dependency
        "arrangement":  ["drums", "bass", "harmony", "melody", "sound_design"],  # needs content
        "mix":          ["arrangement"],  # needs arrangement done
        "master":       ["mix"],          # needs mix done
    }
    ```

    NOTE: `arrangement` lists ALL content phases as deps, but a given genre's agenda may only contain a subset — filter `_PHASE_DEPS[phase_type]` to only include phase_types that actually appear in the current genre's `phase_types` list.

    Step 3 — `_build_phase`: Add `parallelizable` parameter. Compute it as `len(depends_on) <= 1 and phase_type != "setup"`.

    Step 4 — `get_agenda` loop: Replace the `depends_on = [phase_types[i - 1]] if i > 0 else []` line with:
    ```python
    raw_deps = _PHASE_DEPS.get(phase_type, [])
    depends_on = [d for d in raw_deps if d in phase_types]
    ```
    Pass `depends_on` to `_build_phase` along with the `parallelizable` calculation.

    Step 5 — Keep `refine_agenda` unchanged. The `add a second <phase>` path already sets `depends_on` manually — this is fine.

    Step 6 — Verify JSON size budget: after implementing, check that serialized agenda for all 12 genres stays under 1600 chars. If a genre exceeds it, trim roles further (reduce `[:4]` to `[:3]` in `_filter_roles` for drums).
  </action>
  <verify>
    <automated>python -m pytest tests/test_production_agenda.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>
    - All existing test_production_agenda.py tests pass (updated where needed for new dependency semantics)
    - get_agenda("house")["phases"] for bass has depends_on == ["setup"]
    - get_agenda("house")["phases"] for mix has "arrangement" in depends_on
    - Every phase dict has a "parallelizable" bool key
    - All 12 genre agendas serialize to under 1600 chars
  </done>
</task>

<task type="auto">
  <name>Task 2: Add parallel dependency tests and update CONCERNS.md</name>
  <files>tests/test_production_agenda.py, .planning/codebase/CONCERNS.md</files>
  <action>
    In tests/test_production_agenda.py, add a new test class `TestParallelDependencies` with these test cases:

    1. `test_bass_depends_only_on_setup` — get_agenda("house"), find bass phase, assert depends_on == ["setup"]
    2. `test_drums_depends_only_on_setup` — get_agenda("house"), find drums phase, assert depends_on == ["setup"]
    3. `test_harmony_depends_only_on_setup` — get_agenda("house"), find harmony phase, assert depends_on == ["setup"]
    4. `test_mix_depends_on_arrangement` — get_agenda("house"), find mix phase, assert "arrangement" in depends_on
    5. `test_master_depends_on_mix` — get_agenda("house"), find master phase, assert depends_on == ["mix"]
    6. `test_parallelizable_field_present_on_all_phases` — get_agenda("house"), assert all phases have "parallelizable" key with bool value
    7. `test_drums_bass_harmony_are_parallelizable` — get_agenda("house"), drums/bass/harmony phases have parallelizable == True
    8. `test_mix_master_are_not_parallelizable` — get_agenda("house"), mix and master have parallelizable == False
    9. `test_ambient_parallel_deps` — get_agenda("ambient"), harmony phase depends_on == ["setup"] (ambient has no drums)
    10. `test_arrangement_deps_filtered_to_genre` — get_agenda("techno"), arrangement phase depends_on contains only phase_types that exist in techno agenda (no "harmony" or "melody" since techno lacks them)

    In CONCERNS.md: Remove PARA-01 from the "Deferred Features" section (or mark it resolved). Update the entry:
    - Change the PARA-01 bullet to: "**PARA-01 — Parallel phase execution: RESOLVED** — `depends_on` in `ProductionAgenda` now reflects true musical dependencies. Phases with `parallelizable: true` (drums, bass, harmony, melody, sound_design) can execute concurrently after setup. Claude must coordinate parallel execution manually."
  </action>
  <verify>
    <automated>python -m pytest tests/test_production_agenda.py -x -q -k "Parallel" 2>&1 | tail -20</automated>
  </verify>
  <done>
    - All 10 new TestParallelDependencies tests pass
    - CONCERNS.md PARA-01 entry updated to RESOLVED
    - Full test suite (test_production_agenda.py) still green
  </done>
</task>

</tasks>

<verification>
Run full test suite to confirm no regressions:

```bash
python -m pytest tests/test_production_agenda.py -v 2>&1 | tail -30
```

Spot-check agenda output for correctness:

```python
import json
from MCP_Server.orchestration.agenda import get_agenda
agenda = get_agenda("house")
for p in agenda["phases"]:
    print(p["phase_id"], p["depends_on"], p["parallelizable"])
```

Expected output (house):
```
setup [] False
drums ['setup'] True
bass ['setup'] True
harmony ['setup'] True
melody ['setup'] True
arrangement ['drums', 'bass', 'harmony', 'melody'] False
sound_design ['setup'] True
mix ['arrangement'] False
master ['mix'] False
```
(Note: house has sound_design after arrangement — its deps are still just ["setup"] since sound_design is content work, not arrangement-dependent. Arrangement deps filter to what's in the genre.)
</verification>

<success_criteria>
- `ProductionPhase` schema has `parallelizable: bool` field
- `get_agenda` uses `_PHASE_DEPS` map, not positional predecessors
- Bass and drums both have `depends_on == ["setup"]` in house agenda
- Mix depends on arrangement (not directly on bass/drums/harmony)
- All 12 genre agendas remain under 1600 chars serialized
- 10+ new parallel dependency tests pass
- CONCERNS.md PARA-01 entry marked resolved
- All existing tests still pass
</success_criteria>

<output>
After completion, create `.planning/quick/260402-qyx-implement-parallel-phase-execution-suppo/260402-qyx-SUMMARY.md`
</output>
