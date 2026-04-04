---
phase: quick-260404-esg
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/tools/mixing.py
  - MCP_Server/mixing/freq_bands.py
  - tests/test_section_mixing.py
autonomous: true
requirements: [SECMIX-01, SECMIX-02, SECMIX-03]
must_haves:
  truths:
    - "Claude can apply a mix recipe to a specific section of a track via MCP tool"
    - "Claude can detect frequency conflicts between tracks in a section via MCP tool"
    - "Claude can set up sidechain automation for kick/bass relationships via MCP tool"
  artifacts:
    - path: "MCP_Server/tools/mixing.py"
      provides: "Three new MCP tools: apply_section_mix_recipe, detect_frequency_conflicts, setup_sidechain_chain"
    - path: "MCP_Server/mixing/freq_bands.py"
      provides: "Frequency band definitions and conflict detection logic"
    - path: "tests/test_section_mixing.py"
      provides: "Unit tests for all three new tools"
  key_links:
    - from: "MCP_Server/tools/mixing.py"
      to: "MCP_Server/mixing/freq_bands.py"
      via: "import detect_conflicts"
      pattern: "from MCP_Server\\.mixing\\.freq_bands import"
    - from: "MCP_Server/tools/mixing.py"
      to: "MCP_Server/mixing/catalog.py"
      via: "get_recipe for per-section application"
      pattern: "get_recipe\\("
---

<objective>
Add three new MCP tools for section-aware mixing: per-section recipe application,
frequency conflict detection, and sidechain chain automation.

Purpose: Currently `apply_mix_recipe` applies globally to a track. Claude needs
per-section mixing control, the ability to spot frequency masking between tracks,
and one-call sidechain setup. These are the three deferred features from CONCERNS.md.

Output: Three new MCP tools registered and tested, one new freq_bands module.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@MCP_Server/tools/mixing.py (existing mixing tools — extend this file)
@MCP_Server/tools/refinement.py (get_section_state, apply_section_device_refinement — reuse patterns)
@MCP_Server/tools/automation.py (insert_envelope_breakpoints — used for sidechain automation)
@MCP_Server/mixing/catalog.py (get_recipe, list_recipes — recipe lookup)
@MCP_Server/devices/convert.py (convert_recipe_to_payload — recipe to RS payload)
@MCP_Server/tools/analysis.py (_infer_role — role inference from track name)
@MCP_Server/tools/intelligence.py (_find_track — track name substring matching)
@MCP_Server/tools/__init__.py (tool registration — already imports mixing)
@tests/test_mixing.py (existing test patterns for mixing tools)

<interfaces>
<!-- Key types and contracts the executor needs -->

From MCP_Server/mixing/catalog.py:
```python
def get_recipe(role: str, genre: str) -> Optional[dict]:
    # Returns {device_class: {param_name: natural_value}} or None

def list_recipes() -> List[str]:
    # Returns sorted genre IDs
```

From MCP_Server/devices/convert.py:
```python
def convert_recipe_to_payload(recipe: dict) -> list[dict]:
    # Converts natural-unit recipe to normalized payload for apply_recipe RS command
```

From MCP_Server/tools/analysis.py:
```python
def _infer_role(track_name: str) -> str | None:
    # Case-insensitive ROLES substring match, first wins
```

From MCP_Server/tools/intelligence.py:
```python
def _find_track(mix_state: dict, track_name: str) -> dict | None:
    # Searches tracks, return_tracks, master by name substring
```

From MCP_Server/tools/refinement.py:
```python
def _find_track_index(arrangement_tracks: list, track_name: str):
    # Find track index by case-insensitive substring match
```

From MCP_Server/devices/catalog.py:
```python
ROLES = ['kick', 'bass', 'lead', 'pad', 'chords', 'vocal', 'atmospheric', 'return', 'master']
```

Recipe structure (e.g., house.py):
```python
RECIPE = {
    "kick": {
        "Eq8": {"1 Frequency A": 30, "2 Frequency A": 60, ...},
        "Compressor2": {"Threshold": -18, ...},
    },
    "bass": { ... },
    ...
}
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Create freq_bands module and frequency conflict detection logic</name>
  <files>MCP_Server/mixing/freq_bands.py, tests/test_section_mixing.py</files>
  <behavior>
    - Test: detect_conflicts returns empty list when no tracks share frequency bands
    - Test: detect_conflicts flags kick + bass as conflicting in sub/low bands (20-250 Hz)
    - Test: detect_conflicts flags lead + vocal competing in mid range (250 Hz - 4 kHz)
    - Test: conflict entry includes band_name, frequency_range, tracks involved, and severity
    - Test: role with no EQ recipe entry is treated as "unknown band presence" (no crash)
  </behavior>
  <action>
Create `MCP_Server/mixing/freq_bands.py` with:

1. **FREQ_BANDS dict** — Define standard mixing frequency bands:
   - `sub`: 20-60 Hz
   - `low`: 60-250 Hz
   - `low_mid`: 250-500 Hz
   - `mid`: 500-2000 Hz
   - `upper_mid`: 2000-4000 Hz
   - `presence`: 4000-6000 Hz
   - `brilliance`: 6000-20000 Hz

2. **ROLE_PRIMARY_BANDS dict** — Map each role to its primary frequency bands (where it should dominate):
   - `kick`: ["sub", "low"]
   - `bass`: ["sub", "low", "low_mid"]
   - `lead`: ["mid", "upper_mid"]
   - `pad`: ["low_mid", "mid"]
   - `chords`: ["low_mid", "mid", "upper_mid"]
   - `vocal`: ["mid", "upper_mid", "presence"]
   - `atmospheric`: ["presence", "brilliance"]

3. **detect_conflicts(tracks: list[dict]) -> list[dict]** function:
   - Input: list of `{"name": str, "role": str | None, "eq_bands": list[dict]}` where eq_bands come from EQ8 analysis
   - For each frequency band, find which tracks have a boost (gain > 0 dB) in that band's range (based on Eq8 filter frequency + gain from the recipe or current device params)
   - When 2+ tracks boost the same band AND neither has that band as primary, flag as HIGH conflict
   - When 2+ tracks boost the same band AND one has it as primary, flag as MEDIUM conflict (the non-primary track is competing)
   - Return: list of `{"band": str, "freq_range": [low, high], "tracks": [str], "severity": "high"|"medium", "suggestion": str}`
   - Suggestion: e.g., "Cut bass EQ at 300 Hz to reduce masking with chords" (using the non-primary track name)

4. **extract_eq_bands(recipe_or_params: dict) -> list[dict]** helper:
   - Parse Eq8 filter data (frequency + gain + filter on) from either a recipe dict or live device params
   - Return list of `{"frequency": float, "gain": float, "type": str}` for active bands with non-zero gain

Create `tests/test_section_mixing.py` with tests for the above behaviors. Write tests FIRST (RED), then implement (GREEN).
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_section_mixing.py -x -v -k "freq" 2>&1 | tail -20</automated>
  </verify>
  <done>freq_bands module exists with detect_conflicts and extract_eq_bands, all frequency conflict tests pass</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Add three new MCP tools to mixing.py</name>
  <files>MCP_Server/tools/mixing.py, tests/test_section_mixing.py</files>
  <behavior>
    - Test: apply_section_mix_recipe finds section locator, applies recipe per-section with automation breakpoints
    - Test: apply_section_mix_recipe returns error when section not found
    - Test: detect_frequency_conflicts returns conflict list for a multi-track session
    - Test: detect_frequency_conflicts returns empty conflicts when session has no EQ overlap
    - Test: setup_sidechain_chain finds kick track and bass track, calls set_sidechain_source on bass compressor
    - Test: setup_sidechain_chain returns error when source track not found
  </behavior>
  <action>
Add three new `@mcp.tool()` functions to `MCP_Server/tools/mixing.py`:

**1. `apply_section_mix_recipe(ctx, section_name, track_index, role, genre)`**
   - Looks up recipe via `get_recipe(role, genre)` and converts via `convert_recipe_to_payload`
   - Gets arrangement state to find section locator boundaries (same pattern as `get_section_state` in refinement.py)
   - For each device in the recipe payload, iterates each parameter and writes automation breakpoints scoped to the section's beat range using `conn.send_command("insert_envelope_breakpoints", ...)` — the breakpoints set the parameter value at section start and hold it through section end
   - This gives TRUE per-section variation (unlike `apply_section_device_refinement` which only sets params globally)
   - Returns: `{"section": str, "track_index": int, "role": str, "genre": str, "devices_applied": int, "automation_points": int}` or error if section/recipe not found
   - Import `_beat_to_bar` from `MCP_Server.tools.scaffold` for bar display in response

**2. `detect_frequency_conflicts(ctx, section_name, genre)`**
   - Gets arrangement state + mix state for the section (reuse pattern from `get_section_state`)
   - For each track with clips in the section, infer role via `_infer_role`, look up recipe EQ settings via `get_recipe(role, genre)`
   - Extract EQ bands from recipes using `extract_eq_bands` from freq_bands module
   - Call `detect_conflicts` from freq_bands module
   - Returns: `{"section": str, "genre": str, "tracks_analyzed": int, "conflicts": [...], "suggestions": [str]}`
   - Each conflict includes band, frequency range, track names, severity, and a concrete fix suggestion

**3. `setup_sidechain_chain(ctx, source_track_name, target_track_name, target_device_index=None)`**
   - Finds both tracks in mix_state via `_find_track`
   - If `target_device_index` is None, auto-detect: find first Compressor2 on target track from its devices list
   - Calls `conn.send_command("set_sidechain_source", ...)` with the resolved device index
   - Returns: `{"source": str, "target": str, "device_index": int, "status": "sidechain_connected"}` or error
   - This wraps existing `set_sidechain_source` RS command but with auto-detection and name-based lookup (no manual index hunting)

Add corresponding tests to `tests/test_section_mixing.py`. Mock `get_ableton_connection` using the conftest pattern (discovered `_GAC_PATCH_TARGETS`). Write tests FIRST (RED), then implement (GREEN).

Important: The conftest.py auto-discovers GAC patch targets, so the new import in mixing.py will be auto-patched. Use the same mock patterns as test_mixing.py (mock mcp module if needed for standalone test runs).
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_section_mixing.py -x -v 2>&1 | tail -30</automated>
  </verify>
  <done>All three MCP tools registered and callable, all tests pass, no existing tests broken</done>
</task>

<task type="auto">
  <name>Task 3: Verify full test suite and update CONCERNS.md</name>
  <files>MCP_Server/mixing/__init__.py, .planning/codebase/CONCERNS.md</files>
  <action>
1. Run the full test suite to ensure no regressions: `python -m pytest tests/ -x --timeout=30`

2. Update `MCP_Server/mixing/__init__.py` to export the new freq_bands module's public API:
   - Add `from .freq_bands import detect_conflicts, extract_eq_bands, FREQ_BANDS, ROLE_PRIMARY_BANDS`
   - Add these to `__all__`

3. Read and update `.planning/codebase/CONCERNS.md`:
   - In the "Deferred Features" section, mark the "Section-aware mixing, frequency conflict detection, full sidechain automation" item as RESOLVED
   - Add a note: "Resolved: 2026-04-04 — implemented apply_section_mix_recipe, detect_frequency_conflicts, and setup_sidechain_chain MCP tools"
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/ -x --timeout=30 2>&1 | tail -10</automated>
  </verify>
  <done>Full test suite passes, CONCERNS.md updated, freq_bands exports available from MCP_Server.mixing</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/test_section_mixing.py -x -v` passes all new tests
- `python -m pytest tests/ -x --timeout=30` passes (no regressions)
- `python -c "from MCP_Server.mixing.freq_bands import detect_conflicts, FREQ_BANDS; print('OK')"` succeeds
- CONCERNS.md deferred feature marked as resolved
</verification>

<success_criteria>
- Three new MCP tools available: apply_section_mix_recipe, detect_frequency_conflicts, setup_sidechain_chain
- Frequency band definitions and conflict detection logic in dedicated module
- Per-section mixing applies automation breakpoints scoped to section boundaries (not global)
- Sidechain setup auto-detects compressor device index from track name
- All tests pass including new and existing
</success_criteria>

<output>
After completion, create `.planning/quick/260404-esg-implement-section-aware-mixing-per-secti/260404-esg-SUMMARY.md`
</output>
