---
phase: 36-instrument-profile-authoring
plan: 01
subsystem: sounds
tags: [instrument-profiles, analog, operator, drift, simpler, drum-rack, tdd]
dependency_graph:
  requires: [sounds-package, wavetable-profile]
  provides: [all-instrument-profiles]
  affects: [MCP_Server/sounds/analog.py, MCP_Server/sounds/operator.py, MCP_Server/sounds/drift.py, MCP_Server/sounds/simpler.py, MCP_Server/sounds/drum_rack.py, tests/test_sounds.py]
tech_stack:
  added: []
  patterns: [pkgutil-auto-discovery, profile-dict-constant]
key_files:
  created: [MCP_Server/sounds/analog.py, MCP_Server/sounds/operator.py, MCP_Server/sounds/drift.py, MCP_Server/sounds/simpler.py, MCP_Server/sounds/drum_rack.py]
  modified: [tests/test_sounds.py]
decisions: []
metrics:
  duration: 8m
  completed: "2026-03-31T00:00:00Z"
  tasks_completed: 7
  tasks_total: 7
  test_count: 44
  test_pass: 44
  lines_added: 195
---

# Phase 36 Plan 01: Instrument Profile Authoring Summary

**One-liner:** Five native Ableton instrument profiles (Analog, Operator, Drift, Simpler, Drum Rack) authored as pure-Python PROFILE dicts following the Wavetable reference schema, completing the 6-instrument catalog for Phase 37's scoring engine.

## Objective

Author the 5 remaining native Ableton instrument profiles in `MCP_Server/sounds/`, extend `tests/test_sounds.py` with `TestAllSixProfiles`, and ensure `list_profiles()` returns exactly 6 profiles. All tests green.

## What Was Built

### Profile Modules Created

| File | id | aliases | Role affinities |
|------|----|---------|----------------|
| `MCP_Server/sounds/analog.py` | analog | analog, al | bass:0.85, lead:0.8, keys:0.7, pad:0.55 |
| `MCP_Server/sounds/operator.py` | operator | operator, op | keys:0.85, bass:0.8, lead:0.75, pad:0.5 |
| `MCP_Server/sounds/drift.py` | drift | drift | bass:0.8, lead:0.75, keys:0.7, pad:0.65 |
| `MCP_Server/sounds/simpler.py` | simpler | simpler, smplr | keys:0.7, bass:0.7, lead:0.65, pad:0.6 |
| `MCP_Server/sounds/drum_rack.py` | drum_rack | drum rack, drum_rack, dr, drumsrack | kick:0.95, snare:0.95, hihat:0.9, percussion:0.9 |

### Test Coverage

Extended `tests/test_sounds.py` with `TestAllSixProfiles` class (27 tests):
- `test_six_profiles_discovered` — list_profiles() returns exactly 6
- `test_all_profile_ids` — all 6 ids present
- Per-instrument alias resolution tests (5 tests)
- `test_drum_rack_percussion_roles` — kick, snare, hihat in role affinities
- `test_simpler_mentions_modes` — Classic, One-Shot, Slice in sonic_character
- Parametrized schema/shape/range tests across all 6 profiles (18 tests)

**Total test count:** 44 (17 pre-existing + 27 new), all passing.

## Verification Results

```
python -m pytest tests/test_sounds.py -v
44 passed, 2 warnings in 0.05s

from MCP_Server.sounds import list_profiles
['analog', 'drift', 'drum_rack', 'operator', 'simpler', 'wavetable']  # 6 profiles

get_profile('dr')['descriptor_affinities']['role']['kick'] → True
get_profile('simpler')['sonic_character'] contains 'One-Shot' → True
```

## Deviations from Plan

### Pre-existing context

Three of the five profile files (analog.py, operator.py) were already committed to the branch from prior automation (`c6295d1`, `7120088`), and `tests/test_sounds.py` already had `TestAllSixProfiles` committed (`cd22808`). The plan was structured around TDD RED→GREEN flow but the RED state was already established. Drift was untracked (not yet committed). This plan execution completed: drift commit, simpler creation+commit, drum_rack creation+commit.

### Pre-existing test failures (out of scope)

- `tests/test_genre_quality.py` — `ModuleNotFoundError: No module named 'tiktoken'` — pre-existing, unrelated to this plan.
- `tests/test_arrangement.py` — async test without pytest-asyncio — pre-existing, unrelated to this plan.

These are logged to deferred-items for a future environment setup plan.

## Commits

| Hash | Description |
|------|-------------|
| cd22808 | test(36-01): add failing TestAllSixProfiles class (TDD RED) |
| 7120088 | feat(36-01): author Analog instrument profile |
| c6295d1 | feat(36-01): author Operator instrument profile |
| b9d64e7 | feat(36-01): author Drift instrument profile |
| e7a4240 | feat(36-01): author Simpler instrument profile |
| 2661794 | feat(36-01): author Drum Rack instrument profile |

## Self-Check: PASSED

All 5 profile files exist and are committed. 44 tests pass. list_profiles() returns 6 instruments. All acceptance criteria met.
