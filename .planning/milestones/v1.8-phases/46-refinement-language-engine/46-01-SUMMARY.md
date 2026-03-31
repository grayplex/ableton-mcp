---
phase: 46-refinement-language-engine
plan: 01
subsystem: refinement
tags: [lexicon, interpreter, refine-prompt, typed-dicts, mcp-tools]
dependency_graph:
  requires: []
  provides:
    - RefinementVector TypedDict
    - REFINEMENT_LEXICON (22 adjectives)
    - build_section_refinement_plan
    - interpret_section_refinement MCP tool
    - refine_prompt MCP tool
  affects:
    - MCP_Server/refinement/schema.py
    - MCP_Server/tools/refinement.py
tech_stack:
  added: []
  patterns:
    - Lexicon-to-vector mapping with None-field skip
    - Greedy longest-match instruction tokenization
    - Selective brief re-derivation with diff output
key_files:
  created:
    - MCP_Server/refinement/interpreter.py
    - tests/test_refinement_language.py
  modified:
    - MCP_Server/refinement/schema.py
    - MCP_Server/refinement/lexicon.py
    - MCP_Server/tools/refinement.py
decisions:
  - "interpreter.py avoids importing from MCP_Server.tools to prevent circular imports; uses inline beat-to-bar logic instead"
  - "refine_prompt detects explicit BPM in raw text via regex in addition to classify_prompt tempo_signals"
  - "test_refine_prompt_mood_only uses 'make it dark' not 'make it darker' — 'darker' is in REFINEMENT_LEXICON but not MOOD_MAP"
metrics:
  duration_minutes: 25
  completed_date: "2026-03-31"
  tasks_completed: 6
  files_changed: 5
---

# Phase 46 Plan 01: Refinement Language Engine Summary

**One-liner:** 22-adjective REFINEMENT_LEXICON mapping aesthetic words to multi-domain RefinementVector deltas, with interpreter producing per-track SectionRefinementPlan and refine_prompt enabling partial ProductionBrief re-derivation with diff output.

## What Was Built

### MCP_Server/refinement/lexicon.py (already existed, verified correct)
- `RefinementVector` TypedDict with `HarmonicDelta`, `TimbralDelta`, `DynamicDelta` sub-types
- `REFINEMENT_LEXICON` with 22 adjectives: darker, brighter, warmer, colder, harder, softer, heavier, lighter, sparser, denser, higher, lower, more_energetic, less_energetic, more_melodic, more_rhythmic, more_spacious, tighter, dirtier, cleaner, more_dark, more_bright
- "darker" canonical: `{register:-3, mode:minor, filter:-25%, brightness:-2dB, velocity:-8}`

### MCP_Server/refinement/schema.py (already had all TypedDicts)
- `NoteOperation`, `DeviceChange`, `TrackRefinementEntry`, `SectionRefinementPlan` TypedDicts confirmed present

### MCP_Server/refinement/interpreter.py (new)
- `_normalize_instruction(text)`: greedy longest-match scan, 3→2→1 word tries
- `_merge_vectors(keys)`: accumulate deltas with D-07 clamping (register:[-12,12], filter:[-80,80], brightness:[-12,12], velocity:[-40,40], density:[-2,2], reverb/compression:[-0.5,0.5])
- `_scale_substitutions_from_mode_bias(mode_bias)`: minor→pc4→3, pc9→8; major→pc3→4, pc8→9
- `_compute_device_changes(track_devices, timbral, dynamic)`: maps AutoFilter/Frequency, Eq8/Gain4, Reverb/Wet-Dry, Compressor2/Ratio
- `build_section_refinement_plan(section_name, instruction, conn)`: full RS read + plan assembly

### MCP_Server/tools/refinement.py (extended)
- `interpret_section_refinement(ctx, section_name, instruction)` MCP tool: reads section state, returns JSON SectionRefinementPlan
- `refine_prompt(ctx, brief, refinement_text)` MCP tool: classifies signals, selectively re-derives affected ProductionBrief fields, returns `{"brief": updated, "diff": changed_fields}`

### tests/test_refinement_language.py (new, 15 tests)
All 15 tests pass. Plan specified 12 minimum.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Circular import: interpreter.py → MCP_Server.tools.scaffold**
- **Found during:** Step 6 (test run)
- **Issue:** `interpreter.py` imported `_beat_to_bar` from `MCP_Server.tools.scaffold`. The `MCP_Server.tools.__init__` eagerly imports all tools including `refinement.py`, which imports `interpreter.py` — creating a circular import.
- **Fix:** Removed `_beat_to_bar` import from interpreter.py. The beat-to-bar conversion was not actually needed in the interpreter (section range already in beats; clips are filtered by beat position directly).
- **Files modified:** `MCP_Server/refinement/interpreter.py`
- **Commit:** e69a380

**2. [Rule 1 - Bug] Explicit BPM not triggering tempo re-derivation**
- **Found during:** Step 6 — `test_refine_prompt_tempo_explicit` failed
- **Issue:** Plan's `if signals["tempo_signals"]:` check won't fire for "140 BPM" text because `classify_prompt` produces tempo_signals only from the TEMPO_MAP vocabulary (slow/fast/etc), not from raw numeric BPM values. The BPM regex extraction lives inside `_derive_tempo(raw_prompt=...)`.
- **Fix:** Added `_has_explicit_bpm = bool(re.search(...))` check alongside `signals["tempo_signals"]`. Both conditions trigger tempo re-derivation.
- **Files modified:** `MCP_Server/tools/refinement.py`
- **Commit:** e69a380

**3. [Rule 1 - Bug] test_refine_prompt_mood_only used "make it darker" not "make it dark"**
- **Found during:** Design-time inspection of MOOD_MAP
- **Issue:** Plan specified `"make it darker"` for the mood test, but "darker" is in `REFINEMENT_LEXICON` only — not in `classify_prompt`'s `MOOD_MAP`. Only "dark" exists in MOOD_MAP with scale_bias="minor".
- **Fix:** Test uses `"make it dark"` which correctly produces a mood_signal with scale_bias="minor" → key_feel changes to minor mode.
- **Files modified:** `tests/test_refinement_language.py`
- **Commit:** e69a380

## Known Stubs

None — all data paths are wired. `build_section_refinement_plan` reads live RS state. `refine_prompt` calls actual derivation functions from `deriver.py`.

## Self-Check: PASSED

Files verified:
- `/home/user/ableton-mcp/MCP_Server/refinement/interpreter.py` — FOUND
- `/home/user/ableton-mcp/tests/test_refinement_language.py` — FOUND
- Commit e69a380 — verified via git log
- 15/15 tests passing
