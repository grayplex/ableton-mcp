---
phase: 37-descriptor-taxonomy-and-scoring-engine
plan: "01"
subsystem: sounds
tags: [scoring-engine, descriptor-taxonomy, mcp-tool, catalog]
dependency_graph:
  requires: [MCP_Server/sounds/catalog.py, MCP_Server/sounds/__init__.py]
  provides: [recommend(), list_descriptors(), list_sound_descriptors MCP tool]
  affects: [MCP_Server/tools/sounds.py, MCP_Server/tools/__init__.py, tests/test_sounds.py]
tech_stack:
  added: []
  patterns: [weighted-sum scoring, tokenize-lowercase-strip-punctuation, pkgutil auto-discovery]
key_files:
  created:
    - MCP_Server/tools/sounds.py
  modified:
    - MCP_Server/sounds/catalog.py
    - MCP_Server/sounds/__init__.py
    - MCP_Server/tools/__init__.py
    - tests/test_sounds.py
decisions:
  - "D-01: Tokenize by lowercase + whitespace split + strip punctuation -- simple and predictable"
  - "D-02: Weighted sum scoring over role and character affinity axes"
  - "D-03: Tie-breaking by (-score, id) alphabetically for determinism"
  - "D-04: Zero-score returns None"
  - "D-08: list_descriptors() derives vocabulary dynamically from union of all profile affinity keys"
metrics:
  duration: "~5m"
  completed: "2026-03-31"
  tasks: 4
  files: 5
---

# Phase 37 Plan 01: Descriptor Taxonomy and Scoring Engine Summary

**One-liner:** Weighted-sum scoring engine with tokenized descriptor matching over 6 instrument profiles, plus `list_sound_descriptors` MCP tool returning grouped role/character vocabulary.

## What Was Built

### catalog.recommend(descriptor)
Tokenizes the descriptor string (lowercase, strip punctuation, whitespace split), sums affinity weights from each instrument profile's `role` and `character` axes, and returns the top-scoring instrument dict. Returns `None` for empty input or all-zero scores.

Return shape:
```python
{
    "id": "wavetable",
    "name": "Wavetable",
    "score": 1.65,
    "browser_path": "Instruments/Wavetable",
    "category_hint": "Pads",
    "reasoning": "Best match for 'warm pad': Wavetable scores 1.65 — lush evolving pads with wavetable morphing"
}
```

### catalog.list_descriptors()
Derives vocabulary dynamically from the union of all registered profile affinity keys. Returns `{"role": sorted_list, "character": sorted_list}`. Always in sync with profiles.

### list_sound_descriptors MCP tool
Created `MCP_Server/tools/sounds.py` with `@mcp.tool()` decorated function that returns `json.dumps(list_descriptors())`. Registered in `tools/__init__.py` between `session` and `theory` alphabetically.

## Scoring Verification

| Query | Winner | Score | Reason |
|-------|--------|-------|--------|
| "warm pad" | wavetable | 1.65 | pad=0.95+warm=0.7 vs analog pad=0.55+warm=0.9=1.45 |
| "punchy kick" | drum_rack | 1.90 | kick=0.95+punchy=0.95, no competition |
| "organic" | simpler | 0.75 | only simpler has organic tag |
| "lush" | wavetable | 0.90 | only wavetable has lush tag |
| "tight" | drum_rack | 0.80 | only drum_rack has tight tag |
| "kick" | drum_rack | 0.95 | only drum_rack has kick in role |

Differentiation gate: At least 4 distinct instrument ids appear as top-1 across all single-tag queries (drum_rack, wavetable, simpler, and others).

## Test Results

All 62 tests in `tests/test_sounds.py` pass (18 new: 11 TestRecommend + 7 TestListDescriptors + 44 existing).

## Commits

- `905ef57` test(37-01): add failing TestRecommend and TestListDescriptors test classes
- `d775561` feat(37): add recommend() and list_descriptors() to sounds catalog
- `6d24210` feat(37): add list_sound_descriptors MCP tool and register sounds module

## Deviations from Plan

None - plan executed exactly as written. All implementation was completed across the three commits listed above.

## Known Stubs

None. All data is wired to live profile data from the 6 instrument modules.

## Self-Check: PASSED

- `/home/user/ableton-mcp/MCP_Server/sounds/catalog.py` - FOUND (recommend + list_descriptors present)
- `/home/user/ableton-mcp/MCP_Server/tools/sounds.py` - FOUND (list_sound_descriptors tool)
- `/home/user/ableton-mcp/MCP_Server/tools/__init__.py` - FOUND (sounds in import line)
- `/home/user/ableton-mcp/tests/test_sounds.py` - FOUND (TestRecommend + TestListDescriptors classes)
- All 62 tests pass: `python -m pytest tests/test_sounds.py -v` exits 0
