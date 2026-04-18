---
phase: quick-260401-pws
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/orchestration/execution.py
  - tests/test_phase_execution.py
autonomous: true
requirements: [QUICK-PWS]

must_haves:
  truths:
    - "Each genre produces a distinct bass note pattern in get_execution_plan"
    - "House bass uses a root-fifth pumping pattern; dubstep uses half-time sub-bass"
    - "All 12 genres produce bass steps without error"
    - "Token budget (< 2000 chars per checklist) is preserved"
  artifacts:
    - path: "MCP_Server/orchestration/execution.py"
      provides: "_BASS_PATTERNS dict and _GENRE_BASS_GROUP mapping"
      contains: "_BASS_PATTERNS"
    - path: "tests/test_phase_execution.py"
      provides: "Test verifying per-genre bass pattern variation"
      contains: "test_bass_patterns_vary_by_genre"
  key_links:
    - from: "_build_bass_steps"
      to: "_BASS_PATTERNS"
      via: "_GENRE_BASS_GROUP lookup"
      pattern: "_BASS_PATTERNS\\[.*bass_group"
---

<objective>
Add per-genre bass seed note patterns to `_build_bass_steps` in execution.py, mirroring the existing `_DRUM_PATTERNS` / `_GENRE_DRUM_GROUP` architecture used for drums.

Purpose: Currently all 12 genres share an identical 4-note bass pattern (root C2 + F2). A house bass line and a dubstep wobble bass are generated identically, producing homogeneous results regardless of genre.

Output: Genre-differentiated bass patterns with tests confirming variation.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@MCP_Server/orchestration/execution.py
@tests/test_phase_execution.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Add _BASS_PATTERNS dict, _GENRE_BASS_GROUP mapping, and wire _build_bass_steps</name>
  <files>MCP_Server/orchestration/execution.py, tests/test_phase_execution.py</files>
  <behavior>
    - Test: bass/house and bass/dubstep produce different note arrays (different pitches or timings)
    - Test: all 12 genres (excluding ambient which has no special bass group) return valid bass checklists without error
    - Test: no bass checklist exceeds 2000 chars (existing test_json_output_under_2000_chars already covers this but verify explicitly)
    - Test: house bass pattern contains root note (pitch 36) at start_time 0.0
    - Test: hip_hop_trap bass pattern differs from house (different timing/pitch pattern)
  </behavior>
  <action>
IMPORTANT: Before any code changes, rebase the worktree branch off of `misc-fixes`.

**1. Add `_BASS_PATTERNS` dict** (after `_DRUM_PATTERNS`, around line 94) with these genre-group seed patterns. All patterns are 1-bar (4 beats), using `_note()` helper. Keep to 4 notes max per pattern (D-07 token budget). All pitches in bass register (C1=24 to C3=48):

- **"house"**: Root-fifth pumping eighth-note pattern. Classic four-on-floor bass.
  ```
  _note(36, 0.0, 0.5, 90), _note(36, 1.0, 0.25, 80),
  _note(36, 2.0, 0.5, 90), _note(41, 3.0, 0.5, 85)
  ```

- **"techno"**: Driving monotone root with short staccato hits.
  ```
  _note(36, 0.0, 0.25, 100), _note(36, 1.0, 0.25, 100),
  _note(36, 2.0, 0.25, 100), _note(36, 3.0, 0.25, 100)
  ```

- **"hiphop"**: Syncopated 808 sub pattern, swing feel with longer sustain.
  ```
  _note(36, 0.0, 1.0, 100), _note(36, 1.5, 0.5, 85),
  _note(34, 2.5, 1.0, 95), _note(36, 3.5, 0.5, 80)
  ```

- **"dubstep"**: Half-time sub-bass with wide intervals for wobble feel.
  ```
  _note(36, 0.0, 1.5, 110), _note(29, 2.0, 1.0, 105),
  _note(36, 3.0, 0.5, 100), _note(31, 3.5, 0.5, 95)
  ```

- **"trance"**: Rolling arpeggiated bass, root-octave-fifth motion.
  ```
  _note(36, 0.0, 0.5, 95), _note(48, 0.5, 0.5, 80),
  _note(43, 2.0, 0.5, 90), _note(36, 3.0, 1.0, 95)
  ```

- **"neo_soul_rnb"**: Smooth walking bass with chromatic approach, longer notes.
  ```
  _note(36, 0.0, 1.0, 85), _note(40, 1.0, 1.0, 80),
  _note(43, 2.0, 1.0, 85), _note(41, 3.0, 1.0, 80)
  ```

**2. Add `_GENRE_BASS_GROUP` mapping** (right after `_GENRE_DRUM_GROUP`), mapping each genre_id to a bass pattern group:

```python
_GENRE_BASS_GROUP = {
    "house":        "house",
    "disco_funk":   "house",
    "lo_fi":        "house",
    "techno":       "techno",
    "drum_and_bass": "techno",
    "hip_hop_trap": "hiphop",
    "dubstep":      "dubstep",
    "trance":       "trance",
    "synthwave":    "trance",
    "future_bass":  "trance",
    "ambient":      "trance",
    "neo_soul_rnb": "neo_soul_rnb",
}
```

**3. Update `_build_bass_steps`** (line 235) to look up bass_group and use pattern:

Replace the hardcoded `bass_notes` assignment (lines 238-241) with:
```python
bass_group = _GENRE_BASS_GROUP.get(genre_id, "house")
bass_pattern = _BASS_PATTERNS[bass_group]
bass_notes = bass_pattern
```

**4. Add tests** to `tests/test_phase_execution.py`:

```python
def test_bass_patterns_vary_by_genre(self):
    """Different genre groups produce different bass note patterns."""
    house = get_execution_plan("bass", "house")
    dubstep = get_execution_plan("bass", "dubstep")
    hiphop = get_execution_plan("bass", "hip_hop_trap")
    assert "error" not in house
    assert "error" not in dubstep
    assert "error" not in hiphop

    def extract_bass_notes(result):
        for s in result["steps"]:
            if s["tool_name"] == "add_notes_to_clip":
                return s["suggested_args"].get("notes", [])
        return []

    house_notes = extract_bass_notes(house)
    dubstep_notes = extract_bass_notes(dubstep)
    hiphop_notes = extract_bass_notes(hiphop)

    # Each genre group must produce distinct patterns
    assert house_notes != dubstep_notes, "house and dubstep bass should differ"
    assert house_notes != hiphop_notes, "house and hip_hop_trap bass should differ"
    assert dubstep_notes != hiphop_notes, "dubstep and hip_hop_trap bass should differ"

def test_bass_all_genres_no_error(self):
    """All 12 genres produce valid bass checklists."""
    genres = [
        "house", "techno", "ambient", "hip_hop_trap", "drum_and_bass",
        "dubstep", "trance", "synthwave", "future_bass", "lo_fi",
        "neo_soul_rnb", "disco_funk",
    ]
    for g in genres:
        result = get_execution_plan("bass", g)
        assert "error" not in result, f"bass/{g} returned error: {result.get('error')}"
```

Place these two test methods inside the existing `TestPhaseExecutionPlan` class.
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_phase_execution.py -x -v 2>&1 | tail -30</automated>
  </verify>
  <done>
    - _BASS_PATTERNS has 6 distinct genre-group entries (house, techno, hiphop, dubstep, trance, neo_soul_rnb)
    - _GENRE_BASS_GROUP maps all 12 genre_ids to a bass pattern group
    - _build_bass_steps uses genre-specific lookup instead of hardcoded notes
    - test_bass_patterns_vary_by_genre passes (house != dubstep != hiphop)
    - test_bass_all_genres_no_error passes (all 12 genres)
    - Existing test_json_output_under_2000_chars still passes
    - All existing tests in test_phase_execution.py still pass
  </done>
</task>

</tasks>

<verification>
```bash
cd I:/ableton-mcp && python -m pytest tests/test_phase_execution.py -x -v
```
All tests pass including new bass variation tests and existing token budget / step numbering tests.
</verification>

<success_criteria>
- get_execution_plan("bass", "house") and get_execution_plan("bass", "dubstep") produce different note arrays
- All 12 genres return valid bass checklists
- No checklist exceeds 2000 chars
- All existing tests continue to pass
</success_criteria>

<output>
After completion, create `.planning/quick/260401-pws-build-bass-steps-uses-identical-static-n/260401-pws-SUMMARY.md`
</output>
